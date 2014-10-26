# Packrat Makefile

PYVENV ?= pyvenv

# Whether to use wheels
USE_WHEEL := --no-use-wheel

# The endpoint to serve web requests on
WEB_HOST := 0.0.0.0
WEB_PORT := 5000

#
# Rules
#

# Catch-all
all: ve

ve: etc/requirements.txt
	test -e ve || { $(PYVENV) ve; ve/bin/pip install -U pip setuptools; }
	ve/bin/pip install -r $< $(USE_WHEEL)
	touch $@

run: ve
	WEB_HOST=$(WEB_HOST) \
		WEB_PORT=$(WEB_PORT) \
		ve/bin/python packrat/packrat.py
