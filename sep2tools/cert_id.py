import hashlib
import logging
from itertools import zip_longest
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization

log = logging.getLogger(__name__)


def group_hex(item: str, group_size: int = 4) -> str:
    """Group into groups of four"""

    def grouper(iterable, n, fillvalue=None):
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue=fillvalue)

    return "-".join("".join(x) for x in grouper(item, n=group_size))


def get_lfdi(fingerprint: str, group: bool = True) -> str:
    """Long-form device identifier (LFDI)
    The LFDI SHALL be the certificate fingerprint left-truncated to 160 bits.
    For display purposes, this SHALL be expressed as 40 hexadecimal digits in
    groups of four.
    """
    lfdi = fingerprint.replace("-", "")[0:40].upper()
    if not group:
        return lfdi
    return group_hex(lfdi)


def get_sfdi(fingerprint, group: bool = True) -> str:
    """Short-form device identifier (SFDI)
    The SFDI SHALL be the certificate fingerprint left-truncated to 36 bits.
    For display purposes, this SHALL be expressed as 11 decimal (base 10) digits,
    with an additional sum-of-digits checksum digit right concatenated.
    """
    trunc = fingerprint.replace("-", "")[0:9]
    sfdi = int(trunc, base=16)  # Convert from Base 16 to Base 10
    digits = map(int, str(sfdi))
    checksum = 10 - sum(digits) % 10
    if checksum == 10:
        checksum = 0

    full_sfdi = str(sfdi) + str(checksum)
    if not group:
        return full_sfdi
    return group_hex(full_sfdi, 3)


def get_fingerprint(cert_path: Path) -> str:
    """Certificate fingerprint
    The certificate fingerprint is the result of performing a SHA256 operation
    over the whole DER-encoded certificate and is used to derive the SFDI and LFDI.
    """
    with open(cert_path, "rb") as f:
        fbytes = f.read()  # read entire file as bytes
        readable_hash = hashlib.sha256(fbytes).hexdigest().upper()
        return readable_hash


def is_pem_certificate(cert_path: Path) -> bool:
    with open(cert_path, "rb") as f:
        first_line = f.readline()
        return b"-----BEGIN CERTIFICATE-----" in first_line


def get_der_certificate_lfdi(cert_path: Path, group: bool = True):
    """Load X.509 DER Certificate and return LFDI"""

    if not cert_path.exists():
        raise ValueError(f"Cert not found at {cert_path}")

    fingerprint = get_fingerprint(cert_path)
    return get_lfdi(fingerprint, group=group)


def get_pem_certificate_lfdi(cert_path: Path, group: bool = True):
    """Load X.509 DER Certificate in PEM format and return LFDI"""

    if not cert_path.exists():
        raise ValueError(f"Cert not found at {cert_path}")

    with open(cert_path, "rb") as pem_file:
        cert_data = pem_file.read()

    cert = x509.load_pem_x509_certificate(cert_data)
    der_bytes = cert.public_bytes(serialization.Encoding.DER)
    fingerprint = hashlib.sha256(der_bytes).hexdigest().upper()
    lfdi = get_lfdi(fingerprint, group=group)
    return lfdi


def get_certificate_lfdi(cert_path: Path, group: bool = True):
    """Load X.509 DER Certificate in PEM or DER format and return LFDI"""
    if is_pem_certificate(cert_path):
        lfdi = get_pem_certificate_lfdi(cert_path, group=group)
    else:
        lfdi = get_der_certificate_lfdi(cert_path, group=group)
    return lfdi
