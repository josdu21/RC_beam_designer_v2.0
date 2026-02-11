
class BeamSection:
    def __init__(self, b, h, fc, fy, cover):
        """
        Initialize the BeamSection with material and geometric properties.
        
        Args:
            b (float): Width of the beam (cm)
            h (float): Total height of the beam (cm)
            fc (float): Concrete compressive strength (MPa)
            fy (float): Steel yield strength (MPa)
            cover (float): Concrete cover to centroid of reinforcement (cm)
        """
        self.b = b
        self.h = h
        self.fc = fc
        self.fy = fy
        self.cover = cover
        self.d = h - cover
        
        # Beta1 calculation (ACI 318-19 Table 22.2.2.4.3)
        if fc <= 28:
            self.beta1 = 0.85
        elif fc < 55:
            self.beta1 = 0.85 - 0.05 * (fc - 28) / 7
        else:
            self.beta1 = 0.65
