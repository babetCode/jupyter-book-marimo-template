import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.ui.slider(0,1,.1)
    return


if __name__ == "__main__":
    app.run()
