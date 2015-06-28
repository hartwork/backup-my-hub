# Copyright (C) 2015 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

PREFIX = /usr/local
DESTDIR = /

PEP8 = pep8

all:

pep8:
	$(PEP8) .

dist:
	$(RM) MANIFEST
	./setup.py sdist

install:
	./setup.py install --prefix "$(PREFIX)" --root "$(DESTDIR)"

.PHONY: all dist install pep8
