# SEP2-Tools

This library provides some useful functions for working with IEEE 2030.5 (SEP2).

## Install

```sh
pip install sep2tools
```

## Certificate Creation


Note the below CLI commands are only appropriate for testing purposes.
For production certificates, use the actual functions to set appropriate policies and settings.


Create a SERCA, and a MICA.

```sh
python -m sep2tools create-serca
python -m sep2tools create-mica certs/serca.pem certs/serca.key
```

To create a device certificate, first create a Key and CSR.
And then sign using the MICA.

```sh
python -m sep2tools create-key --key-file certs/dev-ABC.key
python -m sep2tools create-cert certs/dev-ABC.csr certs/mica.pem certs/mica.key --pen 12345 --serno ABC
```

## Certificate Inspection

Get the LFDI for a certificate. It will also do some validation checks.

```sh
python -m sep2tools cert-lfdi certs/dev-ABC-cert.pem
```


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