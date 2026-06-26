from collections.abc import Iterable


CONF_ID_NAMES = {
    0: "Default",
    1: "VZW",
    2: "TMO",
    3: "ATT",
    4: "SPRINT",
    5: "USC",
    6: "DISH",
    7: "ROGERS",
    8: "TELUS",
    9: "BELL",
    10: "FREEDOM",
    11: "VIDEOTRON",
    12: "RAKUTEN",
    13: "DCM",
    14: "SBM",
    15: "KDDI",
    16: "DT_DE",
    17: "VF_DE",
    18: "O2_DE",
    19: "VF_UK",
    20: "EE",
    21: "O2_UK",
    22: "3_UK",
    23: "VF_IE",
    24: "ORANGE_FR",
    25: "BOUYGUES",
    26: "SFR",
    27: "FREE_FR",
    28: "MOVISTAR_ES",
    29: "VF_ES",
    30: "ORANGE_ES",
    33: "DT_PL",
    34: "VF_IT",
    35: "TIM_IT",
    36: "WINDTRE",
    37: "VF_TR",
    38: "VF_RO",
    39: "TELSTRA",
    40: "OPTUS",
    41: "VHA",
    42: "TWM",
    43: "FET",
    44: "CHT",
    45: "SINGTEL",
    46: "STARHUB",
    47: "M1",
    50: "TEST_LAB",
    51: "CSPIRE",
    52: "CELLCOM",
    53: "T_STAR",
    54: "RJIO",
    55: "VF_CZ",
    56: "3_IE",
    57: "VODA_IDEA",
    58: "VF_IN",
    59: "AIRTEL",
    60: "EU_COMMON",
    61: "GOOGLE_COMCAST_",
    62: "EU_GENERIC_3CA",
    63: "APAC_COMMON",
    64: "EU_COMMON1",
    65: "1_1_DE",
    66: "TEST_FIELD_NA",
    67: "TEST_FIELD_ROW",
    68: "TELIA_NO",
    69: "TELIA_SE",
    70: "TELIA_DK",
    71: "FIRSTNET",
    72: "IN_GEN",
    73: "IN_GEN2",
    74: "TELENOR_NO",
    75: "KPN_NL",
    76: "TMO_NL",
    77: "VF_NL",
    78: "CA_COMMON",
    79: "SASKTEL",
    80: "ORANGE_BE",
    81: "NA_COMMON",
    82: "MX_COMMON",
    83: "MY_COMMON",
    84: "VZWPRIVATE_US",
}


def conf_ids_to_masks(
    conf_ids: Iterable[int],
    include_bit_zero: bool = False,
) -> tuple[int, int]:
    """
    Convert conf_id values into the two protobuf bitmasks.

    conf_id 0 is treated as implicit by default and therefore does not set
    bit 0. Pass include_bit_zero=True only when working with a file format
    that explicitly uses that bit.
    """
    low_mask = 0
    high_mask = 0

    for raw_conf_id in conf_ids:
        conf_id = int(raw_conf_id)

        if not 0 <= conf_id <= 95:
            raise ValueError(
                f"conf_id must be between 0 and 95: {conf_id}"
            )

        if conf_id == 0 and not include_bit_zero:
            continue

        if conf_id <= 63:
            low_mask |= 1 << conf_id
        else:
            high_mask |= 1 << (conf_id - 64)

    return low_mask, high_mask


def masks_to_conf_ids(
    low_mask: int,
    high_mask: int,
    include_bit_zero: bool = False,
) -> set[int]:
    """Decode the two protobuf masks back into a set of conf_id values."""
    if not 0 <= low_mask <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("Conf ID 1 must fit in uint64")

    if not 0 <= high_mask <= 0xFFFFFFFF:
        raise ValueError("Conf ID 2 must fit in uint32")

    start_id = 0 if include_bit_zero else 1

    result = {
        conf_id
        for conf_id in range(start_id, 64)
        if low_mask & (1 << conf_id)
    }

    result.update(
        conf_id
        for conf_id in range(64, 96)
        if high_mask & (1 << (conf_id - 64))
    )

    return result
