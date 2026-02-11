from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.models import flexure, shear, torsion
from src.models.design_inputs import DesignInputs
from src.models.section import BeamSection
from src.models.torsion_distribution import distribute_torsion_longitudinal_reinf


@dataclass
class ReportBundle:
    flexure_pos: Any
    flexure_neg: Any
    shear_res: Any
    torsion_res: Any
    torsion_dist: Any
    warnings: list[str]
    governing_criteria: list[dict[str, str]]

    def export_payload(self) -> dict[str, Any]:
        return {
            "flexure_pos": self.flexure_pos.to_dict(),
            "flexure_neg": self.flexure_neg.to_dict(),
            "shear": self.shear_res.to_dict(),
            "torsion": self.torsion_res.to_dict(),
            "torsion_distribution": self.torsion_dist.to_dict(),
            "warnings": self.warnings,
            "governing_criteria": self.governing_criteria,
        }


def build_design_report(section: BeamSection, design_inputs: DesignInputs) -> ReportBundle:
    res_flex_pos = flexure.calculate_flexure(section, design_inputs.mu_pos)
    res_flex_neg = flexure.calculate_flexure(section, design_inputs.mu_neg)
    stirrup_diameter = 0.95 if design_inputs.stirrup_bar.startswith("#3") else 1.27
    res_shear = shear.calculate_shear(section, design_inputs.vu, design_inputs.n_legs, stirrup_diameter)
    res_tors = torsion.calculate_torsion(section, design_inputs.tu, design_inputs.vu_torsion)
    dist = distribute_torsion_longitudinal_reinf(
        al_total=res_tors.Al_req,
        b_cm=section.b,
        h_cm=section.h,
        cover_cm=section.cover,
        n_bars=design_inputs.n_bars_torsion,
    )

    warnings: list[str] = []
    for item in (res_flex_pos, res_flex_neg, res_shear, res_tors):
        if item.status_code in {"warning", "error"}:
            warnings.append(item.status)

    governing = [
        {"mecanismo": "Flexión (+)", "criterio_aci": "ACI 318-19 Sec. 22.2 / Tabla 9.6.1.2", "estado": res_flex_pos.status},
        {"mecanismo": "Flexión (-)", "criterio_aci": "ACI 318-19 Sec. 22.2 / Tabla 9.6.1.2", "estado": res_flex_neg.status},
        {"mecanismo": "Cortante", "criterio_aci": "ACI 318-19 Sec. 22.5 / Tabla 9.7.6.2.2", "estado": res_shear.status},
        {"mecanismo": "Torsión", "criterio_aci": "ACI 318-19 Sec. 22.7 / Eq. 9.6.4.3(a)", "estado": res_tors.status},
    ]

    return ReportBundle(
        flexure_pos=res_flex_pos,
        flexure_neg=res_flex_neg,
        shear_res=res_shear,
        torsion_res=res_tors,
        torsion_dist=dist,
        warnings=warnings,
        governing_criteria=governing,
    )
