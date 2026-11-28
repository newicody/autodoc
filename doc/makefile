DOT := $(shell find docs/architecture -name "*.dot")
SVG := $(DOT:.dot=.svg)

all: $(SVG)

%.svg: %.dot
	dot -Tsvg $< -o $@

clean:
	find docs/architecture -name "*.svg" -delete
