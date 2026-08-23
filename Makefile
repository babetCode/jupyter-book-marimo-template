export PYTHONUTF8 = 1

.PHONY: book-build book-start clean

book-build:
	cd book && uv run jupyter-book build --html --strict

book-start:
	cd content && uv run jupyter-book start --port 3102 --server-port 4102

clean:
	rm -rf content/_build _build .jupyter-book-marimo .bin