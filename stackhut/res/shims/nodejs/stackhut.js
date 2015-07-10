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

let request = require('request')
let url = "http://localhost:4000/jsonrpc"

let id_val = 0
let req_id = null

module.exports.root_dir = __dirname

function make_call(method) {
    let params = [].slice.call(arguments, 1);
    params.unshift(req_id)

    payload = {
        'method': method,
        'params': params,
        'jsonrpc': '2.0',
        'id': id_val,
    }

    request(
    { method: 'POST'
    , uri: url
    , body: payload
    , json: true
    }
    , function (error, response, body) {
        id_val += 1

        if(response.statusCode => 200 && response.statusCode < 300){
            console.log('got the stackhut result')
        if ('result' in body) {
            return body['result'];
        } else {
            throw body['error']
        }
        } else {
            console.log('error: '+ response.statusCode)
            throw body
        }
    }
}


// stackhut library functions
module.exports.put_file = function(fname, make_public):
    let make_public = typeof make_public !== 'undefined' ? make_public : true;
    return make_call('put_file', fname, make_public)

module.exports.download_file = function(url, fname):
    let fname = typeof fname !== 'undefined' ? fname : null;
    return make_call('download_file', url, fname)

module.exports.download_file = function(cmd, stdin):
    let stdin = typeof stdin !== 'undefined' ? stdin : '';
    return make_call('run_command', cmd)
