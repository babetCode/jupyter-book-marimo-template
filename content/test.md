---
title: Test
---

```{marimo-config}
:pyproject:
    requires-python = ">=3.13"
    dependencies = [
        "numpy==2.5.2",
    ]
```

```{marimo} python
import marimo as mo
import numpy as np
```

This is a markdown cell with $\LaTeX$.

```{marimo} python
:name: foobar
my_str = "hello"
```

```{marimo} python
:hide-code: true
mo.md(rf"""
This is a markdown cell with f-string: {my_str}
""")
```

```{marimo} python
:name: my_function
# reusable function
def my_function(x):
    return x+x
```

```{marimo} python
:echo: true
:output: false
np.ones(10)
```

```{marimo} python
:name: my_other_function
:echo: true
:output: false
def my_other_function(x):
    return x+x
```
