from sep2tools.cert_create import generate_key

EXAMPLE_PEN = 1234


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
