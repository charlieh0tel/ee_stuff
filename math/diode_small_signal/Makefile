# Define the document name (without the .tex extension)
DOC = diode_smallsignal

COMPILER = pdflatex
FLAGS = -interaction=nonstopmode -halt-on-error

all: $(DOC).pdf

regimes_figure.pdf: make_regimes_figure.py
	python3 make_regimes_figure.py

$(DOC).pdf: $(DOC).tex regimes_figure.pdf
	$(COMPILER) $(FLAGS) $(DOC).tex
	$(COMPILER) $(FLAGS) $(DOC).tex

clean:
	rm -f *.aux *.log *.out *.fls *.fdb_latexmk *.synctex.gz

cleanall: clean
	rm -f $(DOC).pdf regimes_figure.pdf

# Tell Make that these targets aren't actual files
.PHONY: all clean cleanall
