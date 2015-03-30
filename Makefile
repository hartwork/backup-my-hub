# Copyright (C) 2015 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GPL v2 or later

PEP8 = pep8

all:

pep8:
	$(PEP8) .

.PHONY: all pep8
