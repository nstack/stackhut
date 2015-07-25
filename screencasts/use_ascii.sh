# this screencast shows using a StackHut service from your application
# whether in Python, JS, Ruby ... or even the shell! 
# you can find many services at https://stackhut.com/#/services
# we will be using the service 'mands/demo-python', created in http://docs.stackhut.com/getting_started/tutorial_create.html

# let's first view the documentation
open http://stackhut.com/#/u/mands/demo-python

# it has two methods, 'add' and 'multiply'. We can call these via JSON-RPC over a HTTP POST request
# thankfully JSON-RPC is very simple!
# let's write some JSON to call 'add' from 'mands/demo-python' with two parameters
mkdir demo
cd demo
nano test_request.json

# we can call this simply by making a HTTP POST request to https://api.stackhut.com/run
# let's use the 'http' tool (https://github.com/jkbrzt/httpie)
http POST https://api.stackhut.com/run @./test_request.json 

# the JSON-RPC response contains the return value in the 'result' field
# let's pipe into 'jq' (http://stedolan.github.io/jq/)
http POST https://api.stackhut.com/run @./test_request.json | jq ."result"

# so it turns out that 2 plus 2 does equals 4, great!
# and if we send invalid data...
nano test_request.json
http POST https://api.stackhut.com/run @./test_request.json 

# the JSON-RPC response now has an 'error' field
# the system caught the mistake and you can deal with it programmatically
http POST https://api.stackhut.com/run @./test_request.json | jq ."error"."code"

# we hope this shows how you can call any StackHut service from your code
# it's as easy as making a JSON POST request
# thanks for your time - we can't wait to see how you make use of it... 

