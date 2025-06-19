all: build

build:
	cd tex && \
	latexmk -pdf -aux-directory=aux -output-directory=../pdf ./*.tex && \
	rm -r aux

add-built-files:
	git add pdf/

precommit: build add-built-files

