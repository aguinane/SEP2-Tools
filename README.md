# SEP2-Tools

[![PyPI version](https://img.shields.io/pypi/pyversions/sep2tools)][pypi]
[![PyPi downloads](https://img.shields.io/pypi/dw/sep2tools)][pypi]

[pypi]: https://pypi.org/project/sep2tools/

This library provides some useful functions for working with IEEE 2030.5 (SEP2).

Note this library used to also include some functions for creating and validating certificates. This has now been moved to a seperate [SEP2-Certs](https://github.com/aguinane/SEP2-Certs) package. 

A webpage version for some of the functions is also [available here](https://aguinane.github.io/SEP2-Tools/). 

## Helper Functions

### Generating IDs

```python
from sep2tools.ids import generate_mrid

EXAMPLE_PEN = 1234
mrid = generate_mrid(EXAMPLE_PEN)
print(mrid)  # 2726-D70C-C6C2-40DB-B78E-9B38-0000-1234
```

### Bitmap Hex Mappings

Some helper functions are provided for calculating the hex representation of SEP2 bitmap fields.

```python
from sep2tools.hexmaps import get_role_flag

binval, hexval = get_role_flag(is_mirror=1, is_der=1, is_submeter=1)
print(binval)  # 0000000001001001
print(hexval)  # 0049
```
