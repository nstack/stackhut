# This screencast shows how to access a StackHut service from within your application, whether it is written in Python, JS, Ruby...
# ...or even the shell!. 

# You can find all kinds of services at https://stackhut.com/#/services

# We will be using the service mands/demo-python, this was created in the corresponding screencast.

# Let's view the documentation
open http://stackhut.com/#/u/mands/demo-python

# It has two methods, add and multiply. We can call these cloud services via `JSON-RPC <http://www.jsonrpc.org/>`_ transported over a HTTP(S) POST request.

# Thankfully JSON-RPC is a very simple protocol and this is much simpler than it sounds!
# Let's write a bit of JSON to call the method 'add' from mands/demo-python with a two parameters. 

mkdir demo
cd demo
nano test_request.json

# We can perform this call by simply sending a HTTP POST request, with content-type ``application/json`` to ``https://api.stackhut.com/run``. 

# To do this we can use using the 'http' tool - https://github.com/jkbrzt/httpie

http POST https://api.stackhut.com/run @./test_request.json 

# The response object is the JSON-RPC response, containing the return value in the 'result' field

# Let's pipe this JSON into jq (http://stedolan.github.io/jq/) and play with the data

http POST https://api.stackhut.com/run @./test_request.json > jq 

# So it turns out that 2 + 2 = 4, great!

# And what happens if we send some invalid data,

nano test_request.json

http POST https://api.stackhut.com/run @./test_request.json 

# As before we receive a JSON-RPC response object, but now has an 'error' field
# So the system caught the mistake and you can deal with it programmatically 

http POST https://api.stackhut.com/run @./test_request.json > jq message

# We hope this shows how you can call any StackHut service from your code
# It's as easy as making a JSON POST request
# Thanks for your time - we can't wait to see how you make use of it... 
