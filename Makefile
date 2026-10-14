PYTHON ?= python3
PDF ?= pdf/short-yandex.pdf

.PHONY: all build test check-pdf add-built-files precommit

all: build

build:
	cd tex && \
	latexmk -pdf -interaction=nonstopmode -halt-on-error -aux-directory=aux -output-directory=../pdf ./*.tex
	@if grep -l 'No hyphenation patterns were preloaded' tex/aux/*.log; then \
		printf '%s\n' 'Missing hyphenation patterns. Install the required language package (for Russian: tlmgr install hyphen-russian) and rebuild.'; \
		exit 1; \
	fi
	rm -r tex/aux

add-built-files:
	git add pdf/

test:
	$(PYTHON) tests/check_profile.py
	$(PYTHON) tests/check_layout.py $(if $(BASELINE),--baseline "$(BASELINE)")

check-pdf:
	$(PYTHON) tests/check_layout.py --pdf "$(PDF)"

precommit: build add-built-files

