# StackHut allows you to rapidly deploy your code as an API in the cloud.
# This tutorial briefly describes how you can develop, test and deploy a simple service on StackHut within a few minutes. 

# Make sure we have stackhut installed

stackhut -V

# Register/Login to Docker (used to store your StackHut images for deployment)

docker login

# Login to StackHut, create an account at <www.stackhut.com> via GitHub

stackhut login

stackhut info

# let's create a Python project using Alpine Linux
mkdir demo-python
cd demo-python
stackhut init alpine python

# and we're good to go, the project is set up, with a Git repo too - aren't we nice...
ls

# The ``Hutfile`` is a YAML config file regarding our stack and dependencies
pygmetize -l yaml ./Hutfile

# There's also a README.md to describe your service
pygmetize -g README.md

# api.idl describes our service interface, these entrypoints will be accessible over HTTP. 
# It uses a Java-like syntax to describe the service interface using JSON types - more info at http://barrister.bitmechanic.com/docs.html
# Let's take a look
pygmetize -l java api.idl

# We are exposing a single function, add, that takes two ints, and returns an int. 
# Now let's add a new function, ``multiply``, and write the corresponding signature - all pretty straightforward,
nano api.idl
# yes - nano ftw!

# Having defined our interface we may write our code
# The app code lives in app.py (or app.js for JS, and so on)
pygmetize -g app.py

# The service is a plain old Python class with a function for each entrypoint. add has already been implemented
# Now let's write multiply

nano app.py

# Now we're done coding, so let's build, run, and test our service before we deploy
# We can build our service, i.e. packaging up everything into a container image to deploy in the cloud

stackhut build

# Great, now let's test if it runs correctly beforehand deploying
# The file test_request.json represents a HTTP request to our service. 

pygmetize ./test_request.json

# This is a JSON-RPC object that specifies the service, method, and parameters configured for the add endpoint

# Let's run our service using this file to test our add function,
stackhut run test_request.json

# So that all worked, and we can view the JSON-RPC reposonse in /run_result/response.json
pygmentize ./run_result/response.json

# Let's modify test_request.json to test our multiply function and run it again,
nano ./test_request.json
stackhut run test_request.json
pygmentize ./run_result/response.json

# Fantastic, this all worked also. We're now ready to deploy and host the service live on StackHut.

# This couldn't be simpler,
stackhut deploy

This packages and builds your service, and then deploys it to StackHut along with metadata such that it may be searched, viewed, and importantly, used, on the platform. 
As soon as this completes,
# Great, so your API is live on https://api.stackhut.com/run and can be browsed from <https://www.stackhut.com/#/services>
# The service is ready to receive requests from anywhere via HTTP - check the coreesponding screencast demostrating how to use a service
# Thanks for your time - we can't wait to see what you build... 

