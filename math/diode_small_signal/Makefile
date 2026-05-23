DOCS = diode_smallsignal diode_reactive diode_not_squarelaw_newsletter
PDFS = $(DOCS:=.pdf)

COMPILER = pdflatex
FLAGS = -interaction=nonstopmode -halt-on-error

all: $(PDFS)

regimes_figure.pdf: make_regimes_figure.py
	python3 make_regimes_figure.py

diode_smallsignal.pdf: diode_smallsignal.tex regimes_figure.pdf
	$(COMPILER) $(FLAGS) diode_smallsignal.tex
	$(COMPILER) $(FLAGS) diode_smallsignal.tex

diode_reactive.pdf: diode_reactive.tex
	$(COMPILER) $(FLAGS) diode_reactive.tex
	$(COMPILER) $(FLAGS) diode_reactive.tex

diode_not_squarelaw_newsletter.pdf: diode_not_squarelaw_newsletter.tex
	$(COMPILER) $(FLAGS) diode_not_squarelaw_newsletter.tex
	$(COMPILER) $(FLAGS) diode_not_squarelaw_newsletter.tex

lint: make_regimes_figure.py
	ruff check make_regimes_figure.py
	ruff format make_regimes_figure.py

clean:
	rm -f *.aux *.log *.out *.fls *.fdb_latexmk *.synctex.gz

cleanall: clean
	rm -f $(PDFS) regimes_figure.pdf

.PHONY: all lint clean cleanall
