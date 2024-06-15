import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import asn1
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509.oid import NameOID, ObjectIdentifier
from dateutil import tz

log = logging.getLogger(__name__)

DEFAULT_OUTPUT = Path("certs")

ANY_POLICY_OID = ObjectIdentifier("2.5.29.32.0")  # OID for "X509v3 Any Policy"

# IEEE 2030.5 device type assignments (Section 6.11.7.2)
SEP2_DEV_GENERIC = ObjectIdentifier("1.3.6.1.4.1.40732.1.1")
SEP2_DEV_MOBILE = ObjectIdentifier("1.3.6.1.4.1.40732.1.2")
SEP2_DEV_POSTMANUF = ObjectIdentifier("1.3.6.1.4.1.40732.1.3")

# IEEE 2030.5 policy assignments (Section 6.11.7.3)
SEP2_TEST_CERT = ObjectIdentifier("1.3.6.1.4.1.40732.2.1")
SEP2_TEST_SELFSIGNED = ObjectIdentifier("1.3.6.1.4.1.40732.2.2")
SEP2_TEST_SERVPROV = ObjectIdentifier("1.3.6.1.4.1.40732.2.3")
SEP2_TEST_BULK_CERT = ObjectIdentifier("1.3.6.1.4.1.40732.2.4")

# HardwareModuleName (Section 6.11.7.4)
SEP2_HARDWARE_MODULE_NAME = ObjectIdentifier("1.3.6.1.5.5.7.8.4")


def random_id() -> str:
    return str(uuid.uuid4()).replace("-", "")[:10].upper()


def generate_key(
    key_file: Path | None = None, generate_csr: bool = True
) -> tuple[Path, Path | None]:
    """Generate a Private Key and Certificate Signing Request (CSR)"""

    if not key_file:
        output_dir = DEFAULT_OUTPUT
        output_dir.mkdir(exist_ok=True)
        name = random_id()
        key_file = output_dir / f"{name}.key"

    key = ec.generate_private_key(ec.SECP256R1)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(key_file, "wb") as fh:
        fh.write(key_pem)
        log.info("Created Key at %s", key_file)

    csr_file = None
    if generate_csr:
        csr_file = key_file.with_suffix(".csr")
        subject_name = ""
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(x509.Name(subject_name))
            .sign(key, SHA256())
        )
        csr_pem = csr.public_bytes(serialization.Encoding.PEM)
        with open(csr_file, "wb") as fh:
            fh.write(csr_pem)
            log.info("Created CSR at %s", csr_file)

    return key_file, csr_file


def convert_pem_to_der(filename: Path) -> Path:
    """Convert a PEM file to DER Certificate"""
    with open(filename, "rb") as pem_file:
        cert_data = pem_file.read()
    cert = x509.load_pem_x509_certificate(cert_data)
    der_data = cert.public_bytes(encoding=serialization.Encoding.DER)
    output_der_path = filename.with_suffix(".der")
    with open(output_der_path, "wb") as fh:
        fh.write(der_data)
        log.info("Created %s from %s", output_der_path, filename)
    return output_der_path


def generate_serca(
    key_file: Path,
    cert_file: Path | None = None,
    org_name: str = "Smart Energy",
    country_name: str = "AU",
) -> Path:
    """Use a CSR and MICA key pair to generate a SEP2 Certificate"""

    if not cert_file:
        output_dir = key_file.parent
        output_dir.mkdir(exist_ok=True)
        if key_file.suffix == "pem":
            cert_name = f"{key_file.stem}-root.pem"
        else:
            cert_name = f"{key_file.stem}.pem"
        cert_file = output_dir / cert_name

    with open(key_file, "rb") as pem_file:
        pem_data = pem_file.read()
    key = serialization.load_pem_private_key(pem_data, password=None)

    valid_from = datetime.now(tz=tz.UTC)
    valid_to = datetime(9999, 12, 31, 23, 59, 59, 0)  # as per standard

    policies = [x509.PolicyInformation(ANY_POLICY_OID, None)]

    # Define the Subject Name
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, country_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org_name),
            x509.NameAttribute(NameOID.COMMON_NAME, "IEEE 2030.5 Root"),
            x509.NameAttribute(NameOID.SERIAL_NUMBER, "1"),
        ]
    )

    # Generate a Subject Key Identifier (SKI)
    ski = key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    ski_digest = hashes.Hash(hashes.SHA1(), backend=default_backend())
    ski_digest.update(ski)
    ski_value = ski_digest.finalize()

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_to)
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier(ski_value),
            critical=False,
        )
        .add_extension(
            x509.CertificatePolicies(policies=policies),
            critical=True,
        )
        .sign(key, SHA256())
    )

    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    with open(cert_file, "wb") as fh:
        fh.write(cert_pem)
        log.info("Created SERCA %s", cert_file)

    convert_pem_to_der(cert_file)

    return cert_file


def generate_device_certificate(
    filename: Path,
    csr_path: Path,
    mica_cert_path: Path,
    mica_key_path: Path,
    hardware_type_oid: str,
    hardware_serial_number: str,
    policy_oids: list[ObjectIdentifier],
    serca_cert_path: Optional[Path] = None,
) -> Path:
    """Use a CSR and MICA key pair to generate a SEP2 Certificate"""

    with open(csr_path, "rb") as pem_file:
        csr_data = pem_file.read()
    csr = x509.load_pem_x509_csr(csr_data)
    with open(mica_cert_path, "rb") as pem_file:
        mica_pem_data = pem_file.read()
    mica_cert = x509.load_pem_x509_certificate(mica_pem_data)
    with open(mica_key_path, "rb") as pem_file:
        pem_data = pem_file.read()
    mica_key = serialization.load_pem_private_key(pem_data, password=None)
    valid_from = datetime.now(tz=tz.UTC)
    valid_to = datetime(9999, 12, 31, 23, 59, 59, 0)  # as per standard

    policies = [x509.PolicyInformation(oid, None) for oid in policy_oids]

    # SAN OtherName encoder
    encoder = asn1.Encoder()
    encoder.start()
    encoder.enter(asn1.Numbers.Sequence)
    encoder.write(str(hardware_type_oid), asn1.Numbers.ObjectIdentifier)
    encoder.write(str(hardware_serial_number), asn1.Numbers.OctetString)
    encoder.leave()
    hw_module_name = encoder.output()

    sname = x509.Name("")  # SubjectName should be blank

    issuer_name = mica_cert.subject
    iname = x509.Name(issuer_name)
    cert = (
        x509.CertificateBuilder()
        .subject_name(sname)
        .issuer_name(iname)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_to)
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                key_agreement=True,
                key_cert_sign=False,
                crl_sign=False,
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                mica_cert.extensions.get_extension_for_class(
                    x509.SubjectKeyIdentifier
                ).value
            ),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName(
                general_names=[
                    x509.OtherName(SEP2_HARDWARE_MODULE_NAME, hw_module_name)
                ]
            ),
            critical=True,
        )
        .add_extension(
            x509.CertificatePolicies(policies=policies),
            critical=True,
        )
        .sign(mica_key, SHA256())
    )

    serca_pem_data = ""
    if serca_cert_path:
        with open(serca_cert_path, "rb") as pem_file:
            serca_pem_data = pem_file.read()

    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    with open(filename, "wb") as fh:
        fh.write(cert_pem)
        # Append the intermediate certificate
        fh.write(mica_pem_data)
        # Append the root certificate
        if serca_pem_data:
            fh.write(serca_pem_data)
        log.info("Created Cert %s", filename)
    return filename
