---
title: Test
width: medium
---


```{marimo} python
import marimo as mo
import numpy as np
```

This is a markdown cell with $\LaTeX$.

```{marimo} python
my_str = "hello"
```

```{marimo} python
mo.md(rf"""
This is a markdown cell with f-string: {my_str}
""")
```

```{marimo} python
# reusable function
def my_function(x):
    return x+x
```

```{marimo} python
np.ones(10)
```

```{marimo} python
# another reusable function
def my_other_function(x):
    return x+x
```
