PYTHON ?= python3

.PHONY: all build test add-built-files precommit

all: build

build:
	cd tex && \
	latexmk -pdf -f -aux-directory=aux -output-directory=../pdf ./*.tex
	@if grep -l 'No hyphenation patterns were preloaded' tex/aux/*.log; then \
		printf '%s\n' 'Missing hyphenation patterns. Install the required language package (for Russian: tlmgr install hyphen-russian) and rebuild.'; \
		exit 1; \
	fi
	rm -r tex/aux

add-built-files:
	git add pdf/

test:
	$(PYTHON) tests/check_layout.py $(if $(BASELINE),--baseline "$(BASELINE)")

precommit: build add-built-files

