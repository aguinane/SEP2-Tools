from sep2tools.cert_id import get_lfdi, get_sfdi

EXAMPLE_FINGERPRINT = (
    "3E4F-45AB-31ED-FE5B-67E3-43E5-E456-2E31-984E-23E5-349E-2AD7-4567-2ED1-45EE-213A"
)


def test_lfdi():
    """Test the LFDI calculation"""
    lfdi = get_lfdi(EXAMPLE_FINGERPRINT)
    assert lfdi == "3E4F-45AB-31ED-FE5B-67E3-43E5-E456-2E31-984E-23E5"

    lfdi = get_lfdi(EXAMPLE_FINGERPRINT, group=False)
    assert lfdi == "3E4F45AB31EDFE5B67E343E5E4562E31984E23E5"


def test_sfdi():
    """Test the SFDI calculation"""

    sfdi = get_sfdi(EXAMPLE_FINGERPRINT, group=False)
    assert sfdi == "167261211391"

    sfdi = get_sfdi(EXAMPLE_FINGERPRINT)
    assert sfdi == "167-261-211-391"

    # Ensure checksum is valid
    digits = list(map(int, sfdi.replace("-", "")))
    assert sum(digits) % 10 == 0

    # Should also work if you pass the LFDI
    lfdi = get_lfdi(EXAMPLE_FINGERPRINT)
    sfdi = get_sfdi(lfdi)
    assert sfdi == "167-261-211-391"
