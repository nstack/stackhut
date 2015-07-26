# this screencast shows how to use a StackHut service from your code
# whether in Python, JS, Ruby ... or even the shell! 
# you can find many services at https://stackhut.com/#/services
# we will be using the service "mands/demo-python"
# (as created in http://docs.stackhut.com/getting_started/tutorial_create.html)

# let's first view the documentation
open "http://stackhut.com/#/u/mands/demo-python"

# so it has 2 methods, "add" and "multiply", we can call these via a JSON-RPC HTTP request
# thankfully JSON-RPC is very simple!
# let's write some JSON to call "add" from 'mands/demo-python' with 2 parameters
mkdir demo
cd demo
nano test_request.json


{
    "service": "mands/demo-python",
    "req": {
        "method": "add",
        "params": [2, 2]
    }
}


# we can call this through a HTTP POST request to https://api.stackhut.com/run
# let's use the "http" tool (https://github.com/jkbrzt/httpie)
http POST https://api.stackhut.com/run @./test_request.json 

# the JSON-RPC response contains the return value in the "result" field
# let's pipe it into "jq" (http://stedolan.github.io/jq/)
http POST https://api.stackhut.com/run @./test_request.json | jq '.response.result'

# so it turns out that 2 + 2 = 4, great! :)
# and if we send invalid data...
nano test_request.json
http POST https://api.stackhut.com/run @./test_request.json 

# the JSON-RPC response now has an "error" field
# the system caught the mistake and you can deal with it programmatically
http POST https://api.stackhut.com/run @./test_request.json | jq '.response.error.code'

# we hope this shows how you can call any StackHut service from your code
# it's as easy as making a JSON-based POST request
# thanks for your time - we can't wait to see how you make use of it... 

