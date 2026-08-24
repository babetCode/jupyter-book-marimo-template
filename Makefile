export PYTHONUTF8 = 1

.PHONY: sync-notebooks book-build book-start clean

sync-notebooks:
	uv run python scripts/sync_notebooks.py

book-build: sync-notebooks
	cd content && uv run jupyter-book build --html --strict

book-start:
	uv run python scripts/sync_notebooks.py --serve --port 3102 --server-port 4102

clean:
	rm -rf content/_build _build .jupyter-book-marimo .bin