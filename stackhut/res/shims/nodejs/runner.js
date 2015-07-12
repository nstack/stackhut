#!/usr/bin/env iojs
"use strict"
// Copyright 2015 StackHut Ltd.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// any 1st & 3rd-party modules here
let fs = require('fs');
let path = require('path');
let process = require('process');
// load the app to call into
let app = require('./app');
let stackhut = require('./stackhut')
// let util = require('util');
// console.log('app - \n\t', util.inspect(app, false, null));
// console.log('stackhut - \n\t', util.inspect(stackhut, false, null));

const REQ_JSON = 'req.json'
const RESP_JSON = 'resp.json'

// simple error handling
function gen_error(code, msg) {
    return { error: code, msg: msg }
}

// custom write file as stupid Node can't write to a named pipe otherwise!
function write_resp(resp) {
    let buf = new Buffer(resp);
    let fd = fs.openSync(RESP_JSON, 'w');
    fs.writeSync(fd, buf, 0, buf.length, -1);
    fs.closeSync(fd);
}

function run(req) {
    // tell the client helper the current taskid
    stackhut.req_id = req['req_id']

    let ms = req['method'].split('.');
    let iface_name = ms[0];
    let func_name = ms[1];
    let params = req['params'];

    // get the iface, then the func, and call it dync
    if (iface_name in app) {
        let iface_impl = app[iface_name];

        if (func_name in iface_impl) {
            let func_impl = iface_impl[func_name];
            let resp = func_impl.apply(iface_impl, params);
            // return the result
            return { result: resp }
        }
        else { return gen_error(-32601, 'Method not found') }
    }
    else { return gen_error(-32601, 'Service not found') }
}

// top-level error handling
process.on('uncaughtException', function(err) {
    console.log('Uncaught Exception - %s', err)
    let resp = gen_error(-32000, err.toString())
    // fs.writeFileSync(RESP_JSON, JSON.stringify(resp), 'utf8');
    write_resp(JSON.stringify(resp));
    process.exit(0);
})

// Main
// open the json req
let req = JSON.parse(fs.readFileSync(REQ_JSON, 'utf8'));

process.chdir(path.join('.stackhut', req['req_id']))

// run the command
let resp = run(req)
// console.log('res - %j', resp);
process.chdir(stackhut.root_dir)

// save the json resp
write_resp(JSON.stringify(resp));
// fs.writeFileSync(RESP_JSON, JSON.stringify(resp), 'utf8');
process.exit(0);
