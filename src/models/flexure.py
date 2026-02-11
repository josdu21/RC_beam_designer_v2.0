import math

def calculate_flexure(section, Mu):
    """
    Calculate required reinforcement for a given ultimate moment.
    
    Args:
        section (BeamSection): The beam section object.
        Mu (float): Ultimate Moment (kNm).
        
    Returns:
        dict: Results containing As, phi, Mn, epsilon_t, and status.
    """
    # Convert units: kNm -> N-mm
    Mu_Nmm = abs(Mu) * 1e6
    b_mm = section.b * 10
    d_mm = section.d * 10
    fc = section.fc
    fy = section.fy
    
    # Check minimum reinforcement (ACI 318 Table 9.6.1.2)
    min_rho_1 = 0.25 * math.sqrt(fc) / fy
    min_rho_2 = 1.4 / fy
    As_min = max(min_rho_1, min_rho_2) * b_mm * d_mm
    
    # Check if Mu is negligible
    if Mu_Nmm < 1e-6:
        return {
            "As_calc": 0.0,
            "As_min": As_min / 100,
            "As_design": As_min / 100, # Still recommend min steel usually
            "rho": 0.0,
            "phi": 0.9,
            "epsilon_t": 1.0, # Infinite ductility
            "status": "OK (Min Steel)",
            "c": 0,
            "a": 0
        }

    phi = 0.9
    
    # Quadratic coefficients for: (fy^2 / 1.7fc b) * As^2 - (fy * d) * As + Mu/phi = 0
    term_A = (fy**2) / (1.7 * fc * b_mm)
    term_B = -fy * d_mm
    
    for _ in range(10): 
        term_C = Mu_Nmm / phi
        
        delta = term_B**2 - 4 * term_A * term_C
        
        if delta < 0:
            return {
                "As_calc": None, "As_min": As_min/100, "As_design": None,
                "rho": None, "phi": phi, "epsilon_t": 0,
                "status": "Error: Section Overloaded (Compression Failure)",
                "c": 0, "a": 0
            }
            
        As_req = (-term_B - math.sqrt(delta)) / (2 * term_A)
        
        a = As_req * fy / (0.85 * fc * b_mm)
        c = a / section.beta1
        
        if c <= 0:
            epsilon_t = 1.0; phi = 0.9; break
            
        epsilon_t = 0.003 * (d_mm - c) / c
        
        if epsilon_t >= 0.005:
            new_phi = 0.9
        elif epsilon_t <= 0.002:
            new_phi = 0.65
        else:
            new_phi = 0.65 + 0.25 * (epsilon_t - 0.002) / 0.003
        
        if abs(new_phi - phi) < 0.001:
            phi = new_phi
            break
        phi = new_phi

    status = "OK"
    if epsilon_t < 0.004:
        status = "Warning: Low Ductility (epsilon_t < 0.004)"
    elif epsilon_t < 0.005:
        status = "Transition Zone (epsilon_t < 0.005)"

    return {
        "As_calc": As_req / 100, 
        "As_min": As_min / 100,
        "As_design": max(As_req, As_min) / 100,
        "rho": As_req / (b_mm * d_mm),
        "phi": phi,
        "epsilon_t": epsilon_t,
        "status": status,
        "c": c / 10,
        "a": a / 10
    }
