import math

def calculate_shear(section, Vu, n_legs=2, stirrup_diameter=0.95):
    """
    Calculate shear reinforcement (stirrups) for a given ultimate shear force.
    ACI 318-19 Simplified Method.
    
    Args:
        section (BeamSection): The beam section object.
        Vu (float): Ultimate Shear Force (kN).
        n_legs (int): Number of legs for stirrups (usually 2).
        stirrup_diameter (float): Diameter of stirrup bar (cm) (e.g., 0.95 for #3).
        
    Returns:
        dict: Results containing Vc, Vs, s_req, s_max, and status.
    """
    # Convert units to N and mm
    Vu_N = abs(Vu) * 1000
    b_mm = section.b * 10
    d_mm = section.d * 10
    fc = section.fc
    fy = section.fy
    
    # Concrete Shear Capacity Vc (Simplified: 0.17 * lambda * sqrt(fc) * bw * d)
    # Lambda = 1.0 for normal weight concrete
    Vc = 0.17 * 1.0 * math.sqrt(fc) * b_mm * d_mm
    phi = 0.75
    
    phi_Vc = phi * Vc
    
    # Area of stirrup bar (mm2) -> pi * (d/2)^2
    Av_bar = math.pi * ((stirrup_diameter * 10) / 2)**2
    Av = n_legs * Av_bar
    
    status = "OK"
    s_req = None
    
    # Check if stirrups are required
    # Required if Vu > 0.5 * phi * Vc
    if Vu_N <= 0.5 * phi_Vc:
        status = "No Shear Reinforcement Required (Vu < 0.5 * phi * Vc)"
        return {
            "Vc": Vc / 1000, # kN
            "phi_Vc": phi_Vc / 1000,
            "Vs_req": 0,
            "s_req": None,
            "s_max": d_mm / 20, # cm
            "status": status,
            "Av": Av
        }
    
    # Calculate required Vs
    # Vu <= phi * (Vc + Vs)  =>  Vs >= (Vu/phi) - Vc
    Vs_req = (Vu_N / phi) - Vc
    
    # Check max Vs (ACI 318 limits Vs <= 0.66 * sqrt(fc) * bw * d)
    Vs_max = 0.66 * math.sqrt(fc) * b_mm * d_mm
    
    if Vs_req > Vs_max:
        return {
            "Vc": Vc / 1000, "phi_Vc": phi_Vc / 1000, "Vs_req": Vs_req / 1000,
            "s_req": None, "s_max": None,
            "status": "Error: Section Dimensions too small for Shear (Vs > Vs_max). Increase Dimensions.",
            "Av": Av
        }
        
    # Calculate spacing s
    # Vs = Av * fyt * d / s  =>  s = Av * fyt * d / Vs
    # Using fyt = fy for simplicity
    if Vs_req <= 0:
        # Minimum reinforcement governs
        # Av_min = 0.062 * sqrt(fc) * bw * s / fyt  >=  0.35 * bw * s / fyt
        # s_max for min reinf logic... we'll just report Min Reinf Needed
        s_calc = 9999 # Large number
    else:
        s_calc = (Av * fy * d_mm) / Vs_req
        
    # Max spacing limits (ACI 318 Table 9.7.6.2.2)
    if Vs_req <= 0.33 * math.sqrt(fc) * b_mm * d_mm:
        s_max_limit = min(d_mm / 2, 600)
    else:
        s_max_limit = min(d_mm / 4, 300)
        
    # Apply Min Shear Reinforcement check if Vu > 0.5 phi Vc
    # Av_min >= 0.062 sqrt(fc) bw s / fy
    # s <= Av * fy / (0.062 sqrt(fc) bw)
    s_min_1 = (Av * fy) / (0.062 * math.sqrt(fc) * b_mm)
    s_min_2 = (Av * fy) / (0.35 * b_mm)
    s_max_min_reinf = min(s_min_1, s_min_2)
    
    s_final = min(s_calc, s_max_limit, s_max_min_reinf)
    
    return {
        "Vc": Vc / 1000, # kN
        "phi_Vc": phi_Vc / 1000,
        "Vs_req": max(0, Vs_req) / 1000,
        "s_req": s_final / 10, # cm
        "s_max": s_max_limit / 10,
        "status": "Add Stirrups" if Vs_req > 0 else "Minimum Stirrups Required",
        "Av": Av,
        "Av_bar_cm2": Av_bar / 100
    }
