import re


def validate_greek_afm(value: str | None) -> bool:
    """Validate Greek AFM format and Modulo 11 checksum."""

    if value is None:
        return False

    afm = str(value).strip()

    if not re.fullmatch(r"[0-9]{9}", afm):
        return False

    weighted_sum = sum(
        int(afm[i]) * (2 ** (8 - i))
        for i in range(8)
    )

    check_digit = (weighted_sum % 11) % 10

    return check_digit == int(afm[-1])