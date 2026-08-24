# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.24.0",
#     "numpy==2.5.2",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np

    return mo, np


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This is a markdown cell with $\LaTeX$.
    """)
    return


@app.cell
def _():
    my_str = "hello"
    return (my_str,)


@app.cell(hide_code=True)
def _(mo, my_str):
    mo.md(rf"""
    This is a markdown cell with f-string: {my_str}
    """)
    return


@app.function
# reusable function
def my_function(x):
    return x+x


@app.cell
def _(np):
    np.ones(10)
    return


@app.function
# another reusable function
def my_other_function(x):
    return x+x


if __name__ == "__main__":
    app.run()
