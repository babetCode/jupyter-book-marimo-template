---
title: Example
---

Some miscellaneous demos.
<!---->
## Reactive plots

```{marimo} python
:hide-code: true
:name: slider
import marimo as mo

slider = mo.ui.slider(-1,1,.1, label="slope")
slider
```

```{marimo} python
:hide-code: true
:name: figure
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
```

## Glossary references
<!---->
{term}`Signal`
