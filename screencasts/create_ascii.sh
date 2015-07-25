# StackHut allows you to rapidly deploy your code as an API in the cloud
# this screencast shows creating and deploying a simple service on StackHut

# first make sure we have stackhut installed
pip3 install --user stackhut
stackhut -V

# login/register with Docker (to store your StackHut services)
docker login

# login to StackHut, create an account at https://www.stackhut.com first
stackhut login
stackhut info

# let's create a Python project using Alpine Linux
mkdir demo-python
cd demo-python
stackhut init alpine python

# and we're good to go, the project is set up, with a Git repo too - aren't we nice...
ls

# the ``Hutfile`` is a YAML config file regarding our stack and dependencies
alias ccat pygmetize
ccat -l yaml ./Hutfile

# there's also a README.md to describe your service
cat README.md

# api.idl describes our service interface, these entrypoints will be accessible over HTTP
# it uses a Java-like syntax to describe the service interface using JSON types (http://barrister.bitmechanic.com/docs.html)
# let's take a look
ccat -l java api.idl

# we are exposing a single function, add, that takes two ints, and returns an int
# now let's write the signature for a new function, 'multiply' 
nano api.idl
# yes - nano ftw!

# now we may write our code
# this lives in app.py (or app.js for JS, and so on)
ccat app.py

# the service is a plain old Python class with a function for each entrypoint
# 'add' has already been implemented, let's write 'multiply'
nano app.py

# we're done coding, and can now build, run, and test our service before we deploy
# let's build our service, i.e. packaging up everything into a container image
stackhut build

# great, let's test it runs correctly before deploying
# the file 'test_request.json' models a HTTP request to our service 
# this is a JSON-RPC object that describes the service, method, and parameters
ccat ./test_request.json

# let's run our service with this file to test our 'add' function
stackhut run test_request.json

# that worked, and we can view the JSON-RPC reposonse in ./run_result/response.json
ccat ./run_result/response.json

# let's modify 'test_request.json' to test our multiply function
nano ./test_request.json
stackhut run test_request.json
ccat ./run_result/response.json

git commit -am "Working service"

# fantastic, everything is working
# we're now ready to deploy and host the service live on StackHut
# this couldn't be simpler
stackhut deploy

# great, your API is live on https://api.stackhut.com/run and can be browsed from https://www.stackhut.com/#/services
# it can receive requests from anywhere via HTTP, as shown in http://docs.stackhut.com/getting_started/tutorial_use.html
# Thanks for your time - we can't wait to see what you build... 

