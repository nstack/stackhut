"use strict"
// {{ scaffold.name }} service

let stackhut = require('./stackhut')

// create each service as either an ES6 class or an object of functions
class DefaultService {
    constructor() {
        // empty
    }

    add(x, y) {
        return x + y
    }
}

// export the services here
module.exports = {
    Default : new DefaultService()
}
