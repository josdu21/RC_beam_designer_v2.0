"""Unit conversion helpers. Internal calculations use N and mm."""


def cm_to_mm(val_cm: float) -> float:
    """Convert centimeters to millimeters."""
    return val_cm * 10


def kNm_to_Nmm(val_kNm: float) -> float:
    """Convert kN-m to N-mm (absolute value)."""
    return abs(val_kNm) * 1e6


def kN_to_N(val_kN: float) -> float:
    """Convert kN to N (absolute value)."""
    return abs(val_kN) * 1000


def mm2_to_cm2(val_mm2: float) -> float:
    """Convert mm^2 to cm^2."""
    return val_mm2 / 100


def mm_to_cm(val_mm: float) -> float:
    """Convert mm to cm."""
    return val_mm / 10


def N_to_kN(val_N: float) -> float:
    """Convert N to kN."""
    return val_N / 1000


def Nmm_to_kNm(val_Nmm: float) -> float:
    """Convert N-mm to kN-m."""
    return val_Nmm / 1e6
