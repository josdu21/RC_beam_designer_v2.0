"""ACI 318-19 coefficients and constants (SI / MPa units)."""

# Concrete type factor
LAMBDA_NWC = 1.0  # Normal weight concrete

# Shear (ACI 318-19 Section 22.5)
VC_COEFF = 0.17             # Simplified Vc: 0.17 * lambda * sqrt(fc) * bw * d
VS_MAX_COEFF = 0.66         # Max Vs: 0.66 * sqrt(fc) * bw * d
VS_HALF_COEFF = 0.33        # Spacing transition threshold: 0.33 * sqrt(fc) * bw * d
AV_MIN_COEFF_1 = 0.062      # Av,min: 0.062 * sqrt(fc) * bw * s / fy
AV_MIN_COEFF_2 = 0.35       # Av,min: 0.35 * bw * s / fy

# Flexure (ACI 318-19 Section 22.2)
PHI_TENSION = 0.9            # Tension-controlled phi
PHI_COMPRESSION = 0.65       # Compression-controlled phi
EPSILON_T_TENSION = 0.005    # Tension-controlled strain limit
EPSILON_T_COMPRESSION = 0.002  # Compression-controlled strain limit
EPSILON_CU = 0.003           # Ultimate concrete strain
WHITNEY_COEFF = 0.85         # Whitney stress block factor
MIN_RHO_COEFF_1 = 0.25      # 0.25 * sqrt(fc) / fy
MIN_RHO_COEFF_2 = 1.4       # 1.4 / fy

# Torsion (ACI 318-19 Section 22.7)
T_TH_COEFF = 0.083          # Threshold torsion: 0.083 * lambda * sqrt(fc) * Acp^2/Pcp
T_CR_COEFF = 0.33            # Cracking torsion: 0.33 * lambda * sqrt(fc) * Acp^2/Pcp
CROSS_SECTION_COEFF = 0.66   # Cross-section limit: 0.66 * sqrt(fc)
TORSION_STRESS_COEFF = 1.7   # Torsion stress denominator: 1.7 * Aoh^2
AO_FACTOR = 0.85             # Ao = 0.85 * Aoh
AL_MIN_COEFF = 0.42          # 5/12 for MPa units (ACI Eq 9.6.4.3)

# Phi factors
PHI_SHEAR = 0.75
PHI_TORSION = 0.75

# Spacing limits (mm)
S_MAX_NORMAL = 600           # d/2 or 600 mm
S_MAX_HEAVY = 300            # d/4 or 300 mm

# Beta1 thresholds (MPa)
BETA1_HIGH = 0.85
BETA1_LOW = 0.65
FC_BETA1_UPPER = 28.0        # fc threshold for beta1 = 0.85
FC_BETA1_LOWER = 55.0        # fc threshold for beta1 = 0.65
