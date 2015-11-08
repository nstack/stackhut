# StackHut allows you to rapidly deploy your code as an API in the cloud
# this screencast shows creating and deploying a simple service on StackHut

# first make sure we have StackHut (and Docker) installed
sudo pip3 install stackhut > /dev/null
stackhut -V

# login/register with Docker (to store your StackHut services)
docker login

# login to StackHut, create an account at https://www.stackhut.com first
stackhut login
stackhut info

# let's create a Python 3 project using Alpine Linux
mkdir demo-python
cd demo-python
stackhut init alpine python

# the project is set up, with a Git repo too - aren't we nice...
ls

# the ``Hutfile`` is a YAML config file regarding our stack and dependencies
alias ccat pygmentize
ccat -l yaml ./Hutfile

# api.idl describes our service interface with a Java-like syntax
# these entrypoints will be accessible over HTTP
# let's take a look
ccat -l java api.idl

# we're exposing a single function, "add"
# let's write the signature for a new function, "multiply" 
# yes - nano ftw!
nano api.idl

// multiply 2 integers and return the result
multiply(x int, y int) int

# now we may write our code
# this lives in app.py (or app.js for JS, etc.)
ccat app.py

# the service is a Python class with a function for each entrypoint
# "add" has already been implemented, let's write "multiply"
nano app.py

def multiply(self, x, y):
    return x * y

# we're done coding, and can build and run our service locally
# first let's build our service, i.e. packaging into an image
stackhut build

# great, and now let's test our service
# the file 'test_request.json' models a HTTP request to the API
# this is a JSON-RPC object that describes the call
ccat ./test_request.json

# we'll run our service with this file to test "add"
stackhut run test_request.json

# that worked, we can view the response in ./run_result/response.json
ccat ./run_result/response.json

# let's modify "test_request.json" to test our multiply function
nano ./test_request.json
stackhut run test_request.json
ccat ./run_result/response.json

git commit -am "Working service"

# fantastic, everything is working
# we're now ready to deploy and host the service live on StackHut
# this couldn't be simpler
stackhut deploy

# great, the API is live, see https://www.stackhut.com/#/u/mands/demo-python
# it can be used via a HTTP POST to https://api.stackhut.com/run
# as shown in http://docs.stackhut.com/getting_started/tutorial_use.html
# thanks for your time - we can't wait to see what you build... 

