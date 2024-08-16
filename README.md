# SEP2-Tools

This library provides some useful functions for working with IEEE 2030.5 (SEP2).

## Install

```sh
pip install sep2tools
```

## Certificate Usage

Create a SERCA, and MICA .

```sh
python -m sep2tools create-serca
python -m sep2tools create-mica certs/serca.pem certs/serca.key
```

To create a device certificate, first create a key and CSR.
And then sign using the MICA.

```sh
python -m sep2tools create-key --key-file certs/dev-ABC.key
python -m sep2tools create-cert certs/dev-ABC.csr certs/mica.pem certs/mica.key --pen 12345 --serno ABC
python -m sep2tools cert-lfdi certs/dev-ABC-cert.pem
```
