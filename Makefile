.PHONY: clean-pyc clean-build api_docs clean

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "api_docs - generate Sphinx HTML documentation, including API api_docs"
	@echo "release - package and upload a release"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr stackhut.build/
	rm -fr stackhut.dist/
	rm -fr .eggs/
	rm -fr *-wheel *-sdist
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint:
	-flake8 stackhut tests

test:
	python3 setup.py test

test-all:
	tox

coverage:
	coverage run --source stackhut setup.py test
	coverage report -m
	coverage html
	xdg-open htmlcov/index.html

api_docs:
	rm -f api_docs/stackhut.rst
	rm -f api_docs/modules.rst
	sphinx-apidoc -o api_docs/ stackhut
	$(MAKE) -C api_docs clean
	$(MAKE) -C api_docs html
	xdg-open api_docs/_build/html/index.html

release: dist
	git push
	git push --tags
	twine upload dist/*

dist: clean
	python3 setup.py bdist_wheel
	ls -l dist

install: clean
	python3 setup.py install


