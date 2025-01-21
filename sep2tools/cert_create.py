import logging
import uuid
from datetime import datetime
from pathlib import Path

import asn1
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509.oid import ExtensionOID, NameOID, ObjectIdentifier
from dateutil import tz

log = logging.getLogger(__name__)

DEFAULT_OUTPUT = Path("certs")

INDEF_EXPIRY = datetime(9999, 12, 31, 23, 59, 59, 0)  # As per standard

ANY_POLICY_OID = ObjectIdentifier("2.5.29.32.0")  # OID for "X509v3 Any Policy"

# IEEE 2030.5 device type assignments (Section 6.11.7.2)
SEP2_DEV_GENERIC = ObjectIdentifier("1.3.6.1.4.1.40732.1.1")
SEP2_DEV_MOBILE = ObjectIdentifier("1.3.6.1.4.1.40732.1.2")
SEP2_DEV_POSTMANUF = ObjectIdentifier("1.3.6.1.4.1.40732.1.3")

# IEEE 2030.5 policy assignments (Section 6.11.7.3)
SEP2_TEST_CERT = ObjectIdentifier("1.3.6.1.4.1.40732.2.1")
SEP2_SELFSIGNED = ObjectIdentifier("1.3.6.1.4.1.40732.2.2")
SEP2_SERVPROV = ObjectIdentifier("1.3.6.1.4.1.40732.2.3")
SEP2_BULK_CERT = ObjectIdentifier("1.3.6.1.4.1.40732.2.4")

# HardwareModuleName (Section 6.11.7.4)
SEP2_HARDWARE_MODULE_NAME = ObjectIdentifier("1.3.6.1.5.5.7.8.4")


DEFAULT_MICA_POLICIES = [
    SEP2_DEV_GENERIC,
    SEP2_TEST_CERT,
]


DEFAULT_DEV_POLICIES = [
    SEP2_DEV_GENERIC,
    SEP2_TEST_CERT,
    SEP2_SELFSIGNED,
    SEP2_BULK_CERT,
]


def random_id() -> str:
    return str(uuid.uuid4()).replace("-", "")[:10].upper()


def generate_key(
    key_file: Path | None = None,
    generate_csr: bool = True,
    hostnames: list[str] | None = None,
) -> tuple[Path, Path | None]:
    """Generate a Private Key and Certificate Signing Request (CSR)"""

    if not key_file:
        output_dir = DEFAULT_OUTPUT
        output_dir.mkdir(exist_ok=True)
        name = random_id()
        key_file = output_dir / f"{name}.key"

    key = ec.generate_private_key(ec.SECP256R1())
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

        # Subject Alternative Names (SANs)
        san_list = []
        if hostnames:
            msg = "Note that SEP2 Certificates do not require a hostname"
            log.warning(msg)
            for name in hostnames:
                san = x509.DNSName(name)
                san_list.append(san)

        cb = x509.CertificateSigningRequestBuilder()
        cb = cb.subject_name(x509.Name(subject_name))
        if hostnames:
            cb = cb.add_extension(
                x509.SubjectAlternativeName(san_list),
                critical=False,
            )

        csr = cb.sign(key, SHA256())

        csr_pem = csr.public_bytes(serialization.Encoding.PEM)
        with open(csr_file, "wb") as fh:
            fh.write(csr_pem)
            log.info("Created CSR at %s", csr_file)

    return key_file, csr_file


def convert_pem_to_der(pem_file: Path, der_file: Path | None = None) -> Path:
    """Convert a PEM file to DER Certificate"""
    with open(pem_file, "rb") as fh:
        cert_data = fh.read()
    cert = x509.load_pem_x509_certificate(cert_data)
    der_data = cert.public_bytes(encoding=serialization.Encoding.DER)

    if not der_file:
        der_file = pem_file.with_suffix(".cer")
    with open(der_file, "wb") as fh:
        fh.write(der_data)
        log.info("Created %s from %s", der_file, pem_file)
    return der_file


def generate_serca(
    key_file: Path,
    cert_file: Path | None = None,
    org_name: str = "Smart Energy",
    country_name: str = "AU",
) -> tuple[Path, Path]:
    """Use a CSR and MICA key pair to generate a SEP2 Certificate"""

    if not cert_file:
        output_dir = key_file.parent
        output_dir.mkdir(exist_ok=True)
        if key_file.suffix == "pem":
            cert_name = f"{key_file.stem}-serca.pem"
        else:
            cert_name = f"{key_file.stem}.pem"
        cert_file = output_dir / cert_name

    with open(key_file, "rb") as fh:
        pem_data = fh.read()
    key = serialization.load_pem_private_key(pem_data, password=None)

    valid_from = datetime.now(tz=tz.UTC)
    valid_to = INDEF_EXPIRY  # as per standard

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

    cb = x509.CertificateBuilder()
    cb = cb.subject_name(subject)
    cb = cb.issuer_name(subject)
    cb = cb.public_key(key.public_key())
    cb = cb.serial_number(x509.random_serial_number())
    cb = cb.not_valid_before(valid_from)
    cb = cb.not_valid_after(valid_to)
    cb = cb.add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )
    cb = cb.add_extension(
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
    cb = cb.add_extension(
        x509.SubjectKeyIdentifier(ski_value),
        critical=False,
    )
    cb = cb.add_extension(
        x509.CertificatePolicies(policies=policies),
        critical=True,
    )
    cert = cb.sign(key, SHA256())

    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    with open(cert_file, "wb") as fh:
        fh.write(cert_pem)
        log.info("Created SERCA %s", cert_file)

    der_file = convert_pem_to_der(cert_file)

    return cert_file, der_file


def generate_mica(
    csr_path: Path,
    ca_cert_path: Path,
    ca_key_path: Path,
    cert_file: Path | None = None,
    org_name: str = "Example Org Name",
    country_name: str = "AU",
    common_name: str = "IEEE 2030.5 MICA",
    policy_oids: list[ObjectIdentifier] = DEFAULT_MICA_POLICIES,
) -> tuple[Path, Path]:
    """Use a CSR and MICA key pair to generate a SEP2 Certificate"""

    with open(csr_path, "rb") as fh:
        csr_data = fh.read()
    csr = x509.load_pem_x509_csr(csr_data)

    if not cert_file:
        output_dir = csr_path.parent
        output_dir.mkdir(exist_ok=True)
        if csr_path.suffix == "pem":
            cert_name = f"{csr_path.stem}-mica.pem"
        else:
            cert_name = f"{csr_path.stem}.pem"
        cert_file = output_dir / cert_name

    # Load certificate authority
    with open(ca_cert_path, "rb") as fh:
        ca_pem_data = fh.read()
    ca_cert = x509.load_pem_x509_certificate(ca_pem_data)
    with open(ca_key_path, "rb") as fh:
        pem_data = fh.read()
    ca_key = serialization.load_pem_private_key(pem_data, password=None)

    valid_from = datetime.now(tz=tz.UTC)
    valid_to = INDEF_EXPIRY  # as per standard

    policies = [x509.PolicyInformation(oid, None) for oid in policy_oids]

    # Define the Subject Name
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, country_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org_name),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.SERIAL_NUMBER, "1"),
        ]
    )

    # Generate a Subject Key Identifier (SKI)
    ski = csr.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    ski_digest = hashes.Hash(hashes.SHA1(), backend=default_backend())
    ski_digest.update(ski)
    ski_value = ski_digest.finalize()

    issuer_name = ca_cert.subject
    iname = x509.Name(issuer_name)

    cb = x509.CertificateBuilder()

    cb = cb.subject_name(subject)
    cb = cb.issuer_name(iname)
    cb = cb.public_key(csr.public_key())
    cb = cb.serial_number(x509.random_serial_number())
    cb = cb.not_valid_before(valid_from)
    cb = cb.not_valid_after(valid_to)
    cb = cb.add_extension(
        x509.BasicConstraints(ca=True, path_length=0),
        critical=True,
    )
    cb = cb.add_extension(
        x509.KeyUsage(
            key_agreement=False,
            key_cert_sign=True,
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
    cb = cb.add_extension(
        x509.SubjectKeyIdentifier(ski_value),
        critical=False,
    )
    cb = cb.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
            ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
        ),
        critical=False,
    )
    cb = cb.add_extension(
        x509.CertificatePolicies(policies=policies),
        critical=True,
    )
    cert = cb.sign(ca_key, SHA256())

    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    with open(cert_file, "wb") as fh:
        fh.write(cert_pem)
        fh.write(ca_pem_data)  # Append the signing certificate
        log.info("Created MICA %s", cert_file)

    der_file = convert_pem_to_der(cert_file)

    return cert_file, der_file


def generate_device_certificate(
    csr_path: Path,
    ca_cert_path: Path,
    ca_key_path: Path,
    pen: int,
    hardware_serial_number: str,
    cert_file: Path | None = None,
    policy_oids: list[ObjectIdentifier] = DEFAULT_DEV_POLICIES,
    valid_to: datetime | None = None,
) -> Path:
    """Use a CSR and Signing Certificate key pair to generate a SEP2 Certificate"""

    if not cert_file:
        output_dir = csr_path.parent
        cert_name = f"{csr_path.stem}-cert.pem"
        cert_file = output_dir / cert_name

    with open(csr_path, "rb") as fh:
        csr_data = fh.read()
    csr = x509.load_pem_x509_csr(csr_data)
    with open(ca_cert_path, "rb") as fh:
        ca_pem_data = fh.read()
    ca_cert = x509.load_pem_x509_certificate(ca_pem_data)
    with open(ca_key_path, "rb") as fh:
        pem_data = fh.read()
    ca_key = serialization.load_pem_private_key(pem_data, password=None)
    valid_from = datetime.now(tz=tz.UTC)

    if valid_to and valid_to.year != 9999:
        log.warning("Using a valid to year other than 9999 is a deviation from SEP2")
    else:
        valid_to = INDEF_EXPIRY  # as per standard

    policies = [x509.PolicyInformation(oid, None) for oid in policy_oids]

    hardware_type_oid = f"1.3.6.1.4.1.40732.{pen}.1"

    # SAN OtherName encoder
    encoder = asn1.Encoder()
    encoder.start()
    encoder.enter(asn1.Numbers.Sequence)
    encoder.write(str(hardware_type_oid), asn1.Numbers.ObjectIdentifier)
    encoder.write(str(hardware_serial_number), asn1.Numbers.OctetString)
    encoder.leave()
    hw_module_name = encoder.output()
    hw_other_name = x509.OtherName(SEP2_HARDWARE_MODULE_NAME, hw_module_name)

    # Load Subject Alt Names from CSR if they exist
    sans = [hw_other_name]
    try:
        san_oid = ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        san_extension = csr.extensions.get_extension_for_oid(san_oid)
        san = san_extension.value
        log.warning("Specifying a SubjectAlternativeName is a deviation from SEP2")
        sans.extend(san)
    except x509.ExtensionNotFound:
        pass

    # Define the Subject Name
    subject = x509.Name("")

    issuer_name = ca_cert.subject
    iname = x509.Name(issuer_name)

    cb = x509.CertificateBuilder()
    cb = cb.subject_name(subject)
    cb = cb.issuer_name(iname)
    cb = cb.public_key(csr.public_key())
    cb = cb.serial_number(x509.random_serial_number())
    cb = cb.not_valid_before(valid_from)
    cb = cb.not_valid_after(valid_to)
    cb = cb.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    )
    cb = cb.add_extension(
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
    cb = cb.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
            ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
        ),
        critical=False,
    )
    cb = cb.add_extension(
        x509.CertificatePolicies(policies=policies),
        critical=True,
    )
    cb = cb.add_extension(
        x509.SubjectAlternativeName(general_names=sans),
        critical=True,
    )

    cert = cb.sign(ca_key, SHA256())

    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    with open(cert_file, "wb") as fh:
        fh.write(cert_pem)
        # Append the intermediate certificate(s)
        fh.write(ca_pem_data)
        log.info("Created Cert %s", cert_file)

    convert_pem_to_der(cert_file)
    return cert_file
