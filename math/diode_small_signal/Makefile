DOC = diode_smallsignal

COMPILER = pdflatex
FLAGS = -interaction=nonstopmode -halt-on-error

all: $(DOC).pdf

regimes_figure.pdf: make_regimes_figure.py
	python3 make_regimes_figure.py

$(DOC).pdf: $(DOC).tex regimes_figure.pdf
	$(COMPILER) $(FLAGS) $(DOC).tex
	$(COMPILER) $(FLAGS) $(DOC).tex

lint: make_regimes_figure.py
	ruff check make_regimes_figure.py
	ruff format make_regimes_figure.py

clean:
	rm -f *.aux *.log *.out *.fls *.fdb_latexmk *.synctex.gz

cleanall: clean
	rm -f $(DOC).pdf regimes_figure.pdf

.PHONY: all lint clean cleanall
