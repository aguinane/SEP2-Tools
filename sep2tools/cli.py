import logging
from pathlib import Path
from typing import Optional

import typer

from .cert_create import generate_device_certificate, generate_key, generate_serca
from .cert_id import (
    get_der_certificate_lfdi,
    get_pem_certificate_lfdi,
    is_pem_certificate,
)
from .version import __version__

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"
app = typer.Typer()
DEFAULT_DIR = Path(".")


def version_callback(value: bool):
    if value:
        typer.echo(f"sep2tools version: {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback
    ),
) -> None:
    """sep2tools

    Functions for working with IEEE 2030.5 (SEP2)
    """
    pass


@app.command()
def cert_lfdi(
    filepath: Path, verbose: bool = typer.Option(False, "--verbose", "-v")
) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    if not filepath.exists():
        msg = f"No such file {filepath}"
        raise FileNotFoundError(msg)

    if is_pem_certificate(filepath):
        lfdi = get_pem_certificate_lfdi(filepath)
    else:
        lfdi = get_der_certificate_lfdi(filepath)
    typer.echo(f"The LFDI is: {lfdi}")


@app.command()
def create_key(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    key, csr = generate_key()


@app.command()
def create_serca(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    key_file = Path("root.key")
    key, csr = generate_key(key_file, generate_csr=False)
    serca = generate_serca(key)


@app.command()
def create_cert(
    csr_path: Path,
    ca_cert: Path,
    ca_key: Path,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    hw_oid = "12345"
    hw_sn = "1"
    cert = generate_device_certificate(csr_path, ca_cert, ca_key, hw_oid, hw_sn)
