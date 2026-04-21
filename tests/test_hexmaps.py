from sep2tools.hexmaps import (
    get_connect_status,
    get_doe_modes_supported,
    get_modes_supported,
    get_quality_flag,
    get_role_flag,
)


def test_role_flags():
    """Test the role flag mappings"""

    # Site Reading
    _binval, hexval = get_role_flag(is_mirror=1, is_premise=1)
    assert hexval == "0003"

    # DER Reading
    _binval, hexval = get_role_flag(is_mirror=1, is_der=1, is_submeter=1)
    assert hexval == "0049"


def test_quality_flags():
    """Test the quality mappings"""

    # Valid
    _binval, hexval = get_quality_flag(valid=1)
    assert hexval == "0001"

    # Questionable
    _binval, hexval = get_quality_flag(questionable=1)
    assert hexval == "0010"


def test_connect_status():
    """Test the connect status mappings"""

    # Connected
    _binval, hexval = get_connect_status(connected=1, available=1, operating=1)
    assert hexval == "07"

    # Offline
    _binval, hexval = get_connect_status(connected=0, available=0, operating=0)
    assert hexval == "00"

    # Fault
    _binval, hexval = get_connect_status(connected=1, fault=1)
    assert hexval == "11"


def test_modes_supported():
    """Test the modes supported mappings"""

    modes = ["opModMaxLimW"]
    _binval, hexval = get_modes_supported(modes=modes)
    assert hexval == "00100000"

    modes = ["opModEnergize", "opConnect"]
    _binval, hexval = get_modes_supported(modes=modes)
    assert hexval == "00000008"


def test_doe_modes_supported():
    """Test the modes supported mappings"""

    modes = ["opModExpLimW"]
    _binval, hexval = get_doe_modes_supported(modes=modes)
    assert hexval == "00000001"

    modes = ["opModExpLimW", "opModImpLimW", "opModGenLimW", "opModLoadLimW"]
    _binval, hexval = get_doe_modes_supported(modes=modes)
    assert hexval == "0000000F"
