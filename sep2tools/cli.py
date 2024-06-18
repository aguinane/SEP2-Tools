import logging
from pathlib import Path

import typer

from .cert_create import generate_device_certificate, generate_key, generate_serca
from .cert_id import get_certificate_lfdi
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
    version: bool = typer.Option(False, "--version", callback=version_callback),
) -> None:
    """sep2tools

    Functions for working with IEEE 2030.5 (SEP2)
    """
    pass


@app.command()
def cert_lfdi(filepath: Path, verbose: bool = False) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    if not filepath.exists():
        msg = f"No such file {filepath}"
        raise FileNotFoundError(msg)

    lfdi = get_certificate_lfdi(filepath)
    typer.echo(f"The LFDI is: {lfdi}")


@app.command()
def create_key(verbose: bool = False) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    key, csr = generate_key()


@app.command()
def create_serca(verbose: bool = False) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    key_file = Path("root.key")
    key, csr = generate_key(key_file, generate_csr=False)
    generate_serca(key)


@app.command()
def create_cert(
    csr_path: Path,
    ca_cert: Path,
    ca_key: Path,
    pen: int = 12345,
    serno: str = "1",
    verbose: bool = False,
) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    cert_fp = generate_device_certificate(csr_path, ca_cert, ca_key, pen, serno)
    lfdi = get_certificate_lfdi(cert_fp)
    typer.echo(f"The LFDI is: {lfdi}")
