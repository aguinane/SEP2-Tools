from pathlib import Path

from sep2tools.cert_create import convert_pem_to_der
from sep2tools.cert_id import get_der_certificate_lfdi, get_pem_certificate_lfdi

EXAMPLE_CERT = Path("certs/example_cert.pem")


def test_example_cert_lfdi():
    """Test the LFDI calculation"""

    lfdi1 = get_pem_certificate_lfdi(EXAMPLE_CERT)
    der = convert_pem_to_der(EXAMPLE_CERT)
    lfdi2 = get_der_certificate_lfdi(der)
    assert lfdi1 == lfdi2
