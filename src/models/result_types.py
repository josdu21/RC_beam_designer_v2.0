from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class TraceCheck:
    code_ref: str
    formula_id: str
    inputs: dict[str, float]
    value: float
    units: str
    status: str
    note: str = ""


@dataclass
class ResultBase:
    status: str
    status_code: str
    trace: list[TraceCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def keys(self):
        return self.to_dict().keys()

    def items(self):
        return self.to_dict().items()

    def values(self):
        return self.to_dict().values()

    def __iter__(self) -> Iterator[str]:
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())


@dataclass
class FlexureResult(ResultBase):
    As_calc: float = 0.0
    As_min: float = 0.0
    As_design: float = 0.0
    rho: float = 0.0
    phi: float = 0.0
    epsilon_t: float = 0.0
    c: float = 0.0
    a: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "As_calc": self.As_calc,
            "As_min": self.As_min,
            "As_design": self.As_design,
            "rho": self.rho,
            "phi": self.phi,
            "epsilon_t": self.epsilon_t,
            "status": self.status,
            "status_code": self.status_code,
            "c": self.c,
            "a": self.a,
            "trace": [t.__dict__ for t in self.trace],
        }


@dataclass
class ShearResult(ResultBase):
    Vc: float = 0.0
    phi_Vc: float = 0.0
    Vs_req: float = 0.0
    s_req: float | None = None
    s_max: float | None = None
    Av: float = 0.0
    Av_bar_cm2: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "Vc": self.Vc,
            "phi_Vc": self.phi_Vc,
            "Vs_req": self.Vs_req,
            "s_req": self.s_req,
            "s_max": self.s_max,
            "status": self.status,
            "status_code": self.status_code,
            "Av": self.Av,
            "Av_bar_cm2": self.Av_bar_cm2,
            "trace": [t.__dict__ for t in self.trace],
        }


@dataclass
class TorsionResult(ResultBase):
    Tu: float = 0.0
    T_th: float = 0.0
    phi_T_th: float = 0.0
    T_cr: float = 0.0
    phi_T_cr: float = 0.0
    At_s_req: float = 0.0
    At_s_req_cm2_m: float = 0.0
    Al_req: float = 0.0
    check_cross_section: str = "OK"
    action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "Tu": self.Tu,
            "T_th": self.T_th,
            "phi_T_th": self.phi_T_th,
            "T_cr": self.T_cr,
            "phi_T_cr": self.phi_T_cr,
            "status": self.status,
            "status_code": self.status_code,
            "At_s_req": self.At_s_req,
            "At_s_req_cm2_m": self.At_s_req_cm2_m,
            "Al_req": self.Al_req,
            "check_cross_section": self.check_cross_section,
            "action": self.action,
            "trace": [t.__dict__ for t in self.trace],
        }
