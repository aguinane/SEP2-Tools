from pathlib import Path

from sep2tools.cert_create import (
    convert_pem_to_der,
    generate_device_certificate,
    generate_key,
    generate_serca,
)
from sep2tools.cert_id import (
    get_certificate_lfdi,
)
from sep2tools.cert_validate import validate_certificate

EXAMPLE_PEN = 1234
EXAMPLE_SERNO = "A1234"


def test_key_creation():
    """Create Private Key and CSR"""

    key, csr = generate_key()

    with open(key) as fh:
        lines = fh.readlines()
        assert lines[0] == "-----BEGIN PRIVATE KEY-----\n"

    with open(csr) as fh:
        lines = fh.readlines()
        assert lines[0] == "-----BEGIN CERTIFICATE REQUEST-----\n"

    key.unlink()  # Delete to cleanup
    csr.unlink()  # Delete to cleanup


def test_key_creation_with_dns():
    """Create Private Key and CSR"""

    key, csr = generate_key(hostnames=["www.example.com"])

    with open(key) as fh:
        lines = fh.readlines()
        assert lines[0] == "-----BEGIN PRIVATE KEY-----\n"

    with open(csr) as fh:
        lines = fh.readlines()
        assert lines[0] == "-----BEGIN CERTIFICATE REQUEST-----\n"

    key.unlink()  # Delete to cleanup
    csr.unlink()  # Delete to cleanup


def test_example_cert_lfdi():
    """Test the LFDI calculation"""

    folder = Path(".")

    key_fp = folder / "test-serca.key"
    generate_key(key_fp, generate_csr=False)

    serca_fp = folder / "test-serca.pem"
    _, serca_der_fp = generate_serca(key_fp, serca_fp)

    dev_fp = folder / "test-dev.key"
    _, csr_fp = generate_key(key_fp, generate_csr=True)

    dev_fp = folder / "test-device.pem"

    generate_device_certificate(
        csr_fp,
        serca_fp,
        key_fp,
        pen=EXAMPLE_PEN,
        hardware_serial_number=EXAMPLE_SERNO,
        cert_file=dev_fp,
    )

    assert validate_certificate(dev_fp)

    dev_der_fp = convert_pem_to_der(dev_fp)

    lfdi1 = get_certificate_lfdi(dev_fp)
    lfdi2 = get_certificate_lfdi(dev_der_fp)
    assert lfdi1 == lfdi2

    # Delete files that were created
    key_fp.unlink()
    serca_fp.unlink()
    serca_der_fp.unlink()
    dev_fp.unlink()
    csr_fp.unlink()
    dev_der_fp.unlink()
