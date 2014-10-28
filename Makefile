# Packrat Makefile

PYVENV ?= pyvenv

# Whether to use wheels
USE_WHEEL := --no-use-wheel

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
	ve/bin/python packrat/packrat.py etc/packrat.ini
