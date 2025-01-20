import logging
from pathlib import Path
from typing import Optional

import typer

from .cert_create import (
    generate_device_certificate,
    generate_key,
    generate_mica,
    generate_serca,
)
from .cert_id import get_certificate_lfdi
from .cert_validate import validate_certificate
from .version import __version__

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"
app = typer.Typer()
DEFAULT_DIR = Path("certs")


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

    validate_certificate(filepath)


@app.command()
def create_key(
    key_file: Optional[Path] = None,  # noqa: UP007
    hostname: str = "",
    verbose: bool = False,
) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    hostnames = None if not hostname else [hostname]
    key, csr = generate_key(key_file, generate_csr=True, hostnames=hostnames)


@app.command()
def create_serca(
    org_name: str = "Smart Energy",
    verbose: bool = False,
    output_dir: Path = DEFAULT_DIR,
) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    output_dir.mkdir(exist_ok=True)
    key_file = output_dir / "serca.key"
    key, csr = generate_key(key_file, generate_csr=False)
    generate_serca(key, org_name=org_name)


@app.command()
def create_mica(
    ca_cert: Path,
    ca_key: Path,
    org_name: str = "Example Org",
    verbose: bool = False,
    output_dir: Path = DEFAULT_DIR,
) -> None:
    log_level = "DEBUG" if verbose else "INFO"
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    output_dir.mkdir(exist_ok=True)
    key_file = output_dir / "mica.key"
    key, csr = generate_key(key_file, generate_csr=True)
    generate_mica(csr, ca_cert, ca_key, org_name=org_name)


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

    cert_fp = generate_device_certificate(
        csr_path, ca_cert, ca_key, pen=pen, hardware_serial_number=serno
    )
    lfdi = get_certificate_lfdi(cert_fp)
    typer.echo(f"The LFDI is: {lfdi}")
