build:
	latexmk -pdf -aux-directory=aux -output-directory=pdf *.tex
	rm -r aux
