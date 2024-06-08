from sep2tools.ids import generate_mrid, proxy_device_lfdi

EXAMPLE_PEN = 1234
EXAMPLE_CPID = "NMI0001234"


def test_proxy_lfdi():
    """Test the LFDI used by a proxy"""
    lfdi = proxy_device_lfdi(EXAMPLE_PEN, EXAMPLE_CPID)
    assert lfdi == "B538-D994-2C7B-5B83-1AED-81A1-FEC4-6B3D-0000-1234"

    lfdi = proxy_device_lfdi(EXAMPLE_PEN, EXAMPLE_CPID, group=False)
    assert lfdi == "B538D9942C7B5B831AED81A1FEC46B3D00001234"


def test_mrid_generation():
    """Test the LFDI used by a proxy"""

    mrid1 = generate_mrid(EXAMPLE_PEN)
    assert mrid1[-9:] == "0000-1234"
    mrid2 = generate_mrid(EXAMPLE_PEN)
    assert mrid2[-9:] == "0000-1234"

    assert mrid1 != mrid2

    mrid3 = generate_mrid(EXAMPLE_PEN, group=False)
    assert mrid3[-8:] == "00001234"
