import logging
from datetime import datetime
from pathlib import Path

from cryptography import x509
from cryptography.x509 import Certificate

from .cert_id import is_pem_certificate

log = logging.getLogger(__name__)
INDEF_EXPIRY = datetime(9999, 12, 31, 23, 59, 59, 0)  # As per standard


def load_certificate(cert_path: Path) -> Certificate:
    if not cert_path.exists():
        raise ValueError(f"Cert not found at {cert_path}")
    with open(cert_path, "rb") as pem_file:
        cert_data = pem_file.read()
    if is_pem_certificate(cert_path):
        cert = x509.load_pem_x509_certificate(cert_data)
    else:
        cert = x509.load_der_x509_certificate(cert_data)
    return cert


def get_pem_certificate_policy_oids(cert_path: Path) -> list[str]:
    """Load X.509 DER Certificate in PEM format and return Policy OIDs"""

    cert = load_certificate(cert_path)

    oids = []
    cert_policies = cert.extensions.get_extension_for_oid(
        x509.ExtensionOID.CERTIFICATE_POLICIES
    ).value
    for policy in cert_policies:
        oid = policy.policy_identifier.dotted_string
        oids.append(oid)
    return oids


def validate_pem_certificate(cert_path: Path) -> bool:
    """Load X.509 DER Certificate in PEM format and validate"""

    cert = load_certificate(cert_path)
    valid = True

    # Check the validity period
    current_time = datetime.utcnow()
    if not cert.not_valid_before <= current_time:
        msg = "Certificate is not valid yet. "
        msg += "Not valid before {cert.not_valid_before}"
        log.error(msg)
        valid = False
    if not current_time <= cert.not_valid_after:
        msg = "Certificate is no longer valid. "
        msg += "Not valid after {cert.not_valid_after}"
        log.error(msg)
        valid = False
    if cert.not_valid_after != INDEF_EXPIRY:
        msg = f"Certificate expiry not {INDEF_EXPIRY} as per standard. "
        msg += f"Expires {cert.not_valid_after}"
        log.warning(msg)
        valid = False

    # Verify the OIDs
    sep2_dev_type = False
    dev_oid_start = "1.3.6.1.4.1.40732.1."
    oids = get_pem_certificate_policy_oids(cert_path)
    for oid in oids:
        if dev_oid_start in oid:
            sep2_dev_type = True
    if not sep2_dev_type:
        msg = "At least one SEP2 device type assignment policy must be specified. "
        msg += f"That is an OID like {dev_oid_start}.X"
        log.error(msg)
        valid = False

    return valid
