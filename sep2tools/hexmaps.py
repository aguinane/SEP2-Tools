def get_role_flag(
    is_mirror=0, is_premise=0, is_pev=0, is_der=0, is_revenue=0, is_dc=0, is_submeter=0
) -> tuple[str, str]:
    """
    RoleFlagsType object (HexBinary16)
    Specifies the roles that apply to a usage point.
    Bit 0—isMirror—SHALL be set if the server is not the measurement device
    Bit 1—isPremisesAggregationPoint—SHALL be set if the UsagePoint is the
        point of delivery for a premises
    Bit 2—isPEV—SHALL be set if the usage applies to an electric vehicle
    Bit 3—isDER—SHALL be set if the usage applies to a distributed energy resource,
        capable of delivering
    power to the grid
    Bit 4—isRevenueQuality—SHALL be set if usage was measured by a device certified
        as revenue quality
    Bit 5—isDC—SHALL be set if the usage point measures direct current
    Bit 6—isSubmeter—SHALL be set if the usage point is not a premises aggregation point
    Bit 7 to 15—Reserved
    """

    a = is_mirror
    b = is_premise
    c = is_pev
    d = is_der
    e = is_revenue
    f = is_dc
    g = is_submeter

    binary_str = f"000000000{g}{f}{e}{d}{c}{b}{a}"
    val = int(binary_str, 2)
    hex_str = str(hex(val))[2:].zfill(4).upper()
    return binary_str, hex_str


def get_quality_flag(
    valid=0, manual=0, estimate=0, interpolated=0, questionable=0, derived=0, future=0
) -> tuple[str, str]:
    """
    qualityFlags (HexBinary16)
    Bit 0 - valid: data that has gone through all required validation
    checks and either passed them all or has been verified
    Bit 1 - manually edited: Replaced or approved by a human
    Bit 2 - estimated using reference day: data value was replaced
    by a machine computed value based on analysis of historical
    data using the same type of measurement.
    Bit 3 - estimated using linear interpolation: data value was
    computed using linear interpolation based on the readings
    before and after it
    Bit 4 - questionable: data that has failed one or more checks
    Bit 5 - derived: data that has been calculated (using logic or
    mathematical operations), not necessarily measured directly
    Bit 6 - projected (forecast): data that has been calculated as a
    projection or forecast of future reading
    """

    a = valid
    b = manual
    c = estimate
    d = interpolated
    e = questionable
    f = derived
    g = future

    binary_str = f"000000000{g}{f}{e}{d}{c}{b}{a}"
    val = int(binary_str, 2)
    hex_str = str(hex(val))[2:].zfill(4).upper()
    return binary_str, hex_str


def get_connect_status(
    connected=0, available=0, operating=0, test=0, fault=0
) -> tuple[str, str]:
    """
    ConnectStatusType object (HexBinary8)
    0 = Connected
    1 = Available
    2 = Operating
    3 = Test
    4 = Fault/Error
    """

    a = connected
    b = available
    c = operating
    d = test
    e = fault

    binary_str = f"000{e}{d}{c}{b}{a}"
    val = int(binary_str, 2)
    hex_str = str(hex(val))[2:].zfill(2).upper()
    return binary_str, hex_str


def get_modes_supported(modes: list[str]) -> tuple[str, str]:
    """DERControlType object (HexBinary32)
    Control modes supported by the DER. Bit positions SHALL be defined as follows:
    0 = Charge mode
    1 = Discharge mode
    2 = opModConnect (connect/disconnect—implies galvanic isolation)
    3 = opModEnergize (energize/de-energize)
    4 = opModFixedPFAbsorbW (fixed power factor setpoint when absorbing active power)
    5 = opModFixedPFInjectW (fixed power factor setpoint when injecting active power)
    6 = opModFixedVar (reactive power setpoint)
    7 = opModFixedW (charge/discharge setpoint)
    8 = opModFreqDroop (Frequency-Watt Parameterized mode)
    9 = opModFreqWatt (Frequency-Watt Curve mode)
    10 = opModHFRTMayTrip (High Frequency Ride-Through, May Trip mode)
    11 = opModHFRTMustTrip (High Frequency Ride-Through, Must Trip mode)
    12 = opModHVRTMayTrip (High Voltage Ride-Through, May Trip mode)
    13 = opModHVRTMomentaryCessation (HV Ride-Through, Momentary Cessation mode)
    14 = opModHVRTMustTrip (High Voltage Ride-Through, Must Trip mode)
    15 = opModLFRTMayTrip (Low Frequency Ride-Through, May Trip mode)
    16 = opModLFRTMustTrip (Low Frequency Ride-Through, Must Trip mode)
    17 = opModLVRTMayTrip (Low Voltage Ride-Through, May Trip mode)
    18 = opModLVRTMomentaryCessation (LV Ride-Through, Momentary Cessation mode)
    19 = opModLVRTMustTrip (Low Voltage Ride-Through, Must Trip mode)
    20 = opModMaxLimW (maximum active power)
    21 = opModTargetVar (target reactive power)
    22 = opModTargetW (target active power)
    23 = opModVoltVar (Volt-Var mode)
    24 = opModVoltWatt (Volt-Watt mode)
    25 = opModWattPF (Watt-Powerfactor mode)
    26 = opModWattVar (Watt-Var mode)
    """

    a = 1 if "Charge mode" in modes else 0
    b = 1 if "Discharge mode" in modes else 0
    c = 1 if "opModConnect" in modes else 0
    d = 1 if "opModEnergize" in modes else 0
    e = 1 if "opModFixedPFAbsorbW" in modes else 0
    f = 1 if "opModFixedPFInjectW" in modes else 0
    g = 1 if "opModFixedVar" in modes else 0
    h = 1 if "opModFixedW" in modes else 0
    i = 1 if "opModFreqDroop" in modes else 0
    j = 1 if "opModFreqWatt" in modes else 0
    k = 1 if "opModHFRTMayTrip" in modes else 0
    l = 1 if "opModHFRTMustTrip" in modes else 0  # noqa: E741
    m = 1 if "opModHVRTMayTrip" in modes else 0
    n = 1 if "opModHVRTMomentaryCessation" in modes else 0
    o = 1 if "opModHVRTMustTrip" in modes else 0
    p = 1 if "opModLFRTMayTrip" in modes else 0
    q = 1 if "opModLFRTMustTrip" in modes else 0
    r = 1 if "opModLVRTMayTrip" in modes else 0
    s = 1 if "opModLVRTMomentaryCessation" in modes else 0
    t = 1 if "opModLVRTMustTrip" in modes else 0
    u = 1 if "opModMaxLimW" in modes else 0
    v = 1 if "opModTargetVar" in modes else 0
    w = 1 if "opModTargetW" in modes else 0
    x = 1 if "opModVoltVar" in modes else 0
    y = 1 if "opModVoltWatt" in modes else 0
    z = 1 if "opModWattPF" in modes else 0
    aa = 1 if "opModWattVar" in modes else 0

    binary_str = f"00000{aa}{z}{y}{x}{w}{v}{u}{t}{s}{r}{q}"
    binary_str += f"{p}{o}{n}{m}{l}{k}{j}{i}{h}{g}{f}{e}{d}{c}{b}{a}"
    val = int(binary_str, 2)
    hex_str = str(hex(val))[2:].zfill(8).upper()
    return binary_str, hex_str


def get_doe_modes_supported(modes: list[str]) -> tuple[str, str]:
    """DERControlType object (HexBinary32)
    Control modes supported by the DER. Bit positions SHALL be defined as follows:
    0 = opModExpLimW
    1 = opModImpLimW
    2 = opModGenLimW
    3 = opModLoadLimW
    """
    a = 1 if "opModExpLimW" in modes else 0
    b = 1 if "opModImpLimW" in modes else 0
    c = 1 if "opModGenLimW" in modes else 0
    d = 1 if "opModLoadLimW" in modes else 0

    binary_str = f"000000000000{d}{c}{b}{a}"
    val = int(binary_str, 2)
    hex_str = str(hex(val))[2:].zfill(8).upper()
    return binary_str, hex_str
