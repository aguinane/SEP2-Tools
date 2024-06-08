from pathlib import Path

from sep2tools.cert_create import generate_key_and_csr

CERT_DIR = Path("certs")
CERT_DIR.mkdir(exist_ok=True)
EXAMPLE_PEN = 1234


def test_key_creation():
    """Create Private Key and CSR"""

    key, csr = generate_key_and_csr(CERT_DIR / "key.pem", CERT_DIR / "csr.pem")

    with open(key) as fh:
        lines = fh.readlines()
        assert lines[0] == "-----BEGIN PRIVATE KEY-----\n"

    with open(csr) as fh:
        lines = fh.readlines()
        assert lines[0] == "-----BEGIN CERTIFICATE REQUEST-----\n"

    key.unlink()  # Delete to cleanup
    csr.unlink()  # Delete to cleanup
