import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Some miscellaneous demos.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reactive plots
    """)
    return


@app.cell(hide_code=True)
def slider():
    import marimo as mo

    slider = mo.ui.slider(-1,1,.1, label="slope")
    slider
    return mo, slider


@app.cell(hide_code=True)
def figure(mo, slider):
    import matplotlib.pyplot as plt
    plt.style.use('default')

    from textwrap import dedent

    def graphic(x):
        return mo.Html(
            dedent(f'''\
            <style>
                .dark .graphic {{ 
                    filter: invert(1) hue-rotate(180deg); 
                }}
            </style>
            <div class="graphic">
                {mo.as_html(x)}
            </div>
            ''')
        )

    m = slider.value
    fig, ax = plt.subplots()

    ax.plot([0, 1], [0, m])
    ax.axis([0, 1, -1, 1])
    graphic(fig)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Glossary references
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    {term}`Signal`
    """)
    return


if __name__ == "__main__":
    app.run()
