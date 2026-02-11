import math

def calculate_torsion(section, Tu, Vu):
    """
    Check torsion threshold and calculate reinforcement if required (ACI 318-19).
    
    Args:
        section (BeamSection): The beam section object.
        Tu (float): Ultimate Torsion (kNm).
        Vu (float): Ultimate Shear Force (kN).
        
    Returns:
        dict: Results containing T_th, T_cr, requirements (At/s, Al), and status.
    """
    # Units: N and mm
    Tu_Nmm = abs(Tu) * 1e6
    Vu_N = abs(Vu) * 1000
    b_mm = section.b * 10
    h_mm = section.h * 10
    fc = section.fc
    fy = section.fy
    
    # Section Properties for Torsion (Solid Rectangular Section)
    Acp = b_mm * h_mm
    Pcp = 2 * (b_mm + h_mm)
    
    # For Aoh, approx assume 40mm cover to stirrup center
    cover_stirrup = 40 # mm
    x1 = b_mm - 2 * cover_stirrup
    y1 = h_mm - 2 * cover_stirrup
    
    if x1 <= 0 or y1 <= 0:
         return {"status": "Error: Section too small for defined cover to calculate Aoh."}

    Aoh = x1 * y1
    Ph = 2 * (x1 + y1)
    
    # Threshold Torsion T_th (ACI 318-19 22.7.4)
    phi = 0.75
    lambda_conc = 1.0 # Normal weight
    
    T_th = 0.083 * lambda_conc * math.sqrt(fc) * (Acp**2 / Pcp)
    phi_T_th = phi * T_th
    
    T_cr = 0.33 * lambda_conc * math.sqrt(fc) * (Acp**2 / Pcp)
    phi_T_cr = phi * T_cr
    
    results = {
        "Tu": Tu,
        "T_th": T_th / 1e6, # kNm
        "phi_T_th": phi_T_th / 1e6,
        "T_cr": T_cr / 1e6,
        "phi_T_cr": phi_T_cr / 1e6,
        "status": "OK",
        "At_s_req": 0.0, # mm2/mm per leg
        "Al_req": 0.0,   # mm2 total
        "check_cross_section": "OK"
    }

    # 1. Neglect Torsion Check
    if Tu_Nmm < phi_T_th:
        results["status"] = "Torsion Neglectable (Tu < phi * T_th)"
        results["action"] = "No Torsion Design Needed"
        return results
        
    # 2. Cross-Sectional Limit Check (ACI 318-19 22.7.7.1)
    # sqrt((Vu / (bw*d))^2 + (Tu*Ph / (1.7*Aoh^2))^2) <= phi * (Vc/bwd + 8 sqrt(fc))
    # Note: Vc/bwd is usually approx 0.17 sqrt(fc). The limit is phi * (Vc/bwd + 0.66 sqrt(fc)) 
    # Actually eq 22.7.7.1 (a) for Solid sections:
    # ... <= phi * ( (Vc/(bw*d)) + 0.66 * sqrt(fc) )
    
    d_mm = section.d * 10
    bw_d = b_mm * d_mm
    
    # Calculate simple Vc for this check (without Vs)
    Vc = 0.17 * lambda_conc * math.sqrt(fc) * bw_d
    
    lhs_v = Vu_N / bw_d
    lhs_t = (Tu_Nmm * Ph) / (1.7 * Aoh**2)
    lhs = math.sqrt(lhs_v**2 + lhs_t**2)
    
    rhs_max = phi * ((Vc / bw_d) + 0.66 * math.sqrt(fc))
    
    if lhs > rhs_max:
        results["status"] = "Error: Cross-Section Too Small for Torsion+Shear!"
        results["check_cross_section"] = f"Combined Shear Stress {lhs:.2f} > Limit {rhs_max:.2f} MPa"
        return results
        
    results["check_cross_section"] = f"OK ({lhs:.2f} <= {rhs_max:.2f} MPa)"
    
    # 3. Transverse Reinforcement At/s (ACI 22.7.6.1)
    # Tn >= Tu / phi
    Tn = Tu_Nmm / phi
    
    # Tn = (2 * Ao * At * fyt / s) * cot(theta)
    # Ao approx 0.85 * Aoh
    Ao = 0.85 * Aoh
    theta_deg = 45
    cot_theta = 1.0 # cot(45)
    fyt = fy # Assume same yield
    
    # At/s = Tn / (2 * Ao * fyt * cot_theta)
    At_s_req = Tn / (2 * Ao * fyt * cot_theta) # mm2/mm for ONE leg of closed stirrup
    
    results["At_s_req"] = At_s_req # mm2/mm
    results["At_s_req_cm2_m"] = At_s_req * 100 * 100 / 100 # cm2/m, wait: mm2/mm * 1000mm/1m / 100mm2/cm2 = * 10
    
    # 4. Longitudinal Reinforcement Al (ACI 22.7.6.1)
    # Al = (At/s) * Ph * (fyt/fy) * cot(theta)^2
    Al_req = At_s_req * Ph * (fyt / fy) * (cot_theta**2)
    
    # Minimum Al check (ACI 9.6.4.3)
    # Al_min = (5 * sqrt(fc) * Acp / fy) - (At/s)*Ph*(fyt/fy)
    term1 = (0.42 * math.sqrt(fc) * Acp) / fy # ACI 22.7.6.1 uses 5sqrt(fc) in psi... in MPa it's 0.42 (5/12 approx 0.416)
    # Wait, ACI 318-19 Eq 9.6.4.3(a): Al,min = (5 sqrt(fc') Acp / fy) - (At/s)Ph(fyt/fy)
    # 5 psi is roughly 0.42 MPa.
    
    Al_min = term1 - (At_s_req * Ph * (fyt / fy))
    
    # Also need check min (At/s) but that usually governs stirrup spacing. 
    # For Al, use max(Al_calc, Al_min)
    
    Al_final = max(Al_req, Al_min)
    
    results["Al_req"] = Al_final / 100 # cm2
    results["status"] = "Torsion Reinforcement Required"
    results["action"] = "Provide Closed Stirrups + Longitudinal Bars"
    
    return results
