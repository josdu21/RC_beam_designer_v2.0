import os
import sys
import unittest

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import flexure, shear, torsion
from src.models.section import BeamSection


class TestModularBeam(unittest.TestCase):
    def setUp(self):
        self.section = BeamSection(b=30, h=50, fc=28, fy=420, cover=4)

    def test_flexure(self):
        res = flexure.calculate_flexure(self.section, Mu=100)
        self.assertEqual(res['status'], 'OK')
        self.assertGreater(res['As_calc'], 0)

    def test_shear(self):
        # Vu = 100 kN significantly higher than Vc approx 40kN
        res = shear.calculate_shear(self.section, Vu=100)
        self.assertTrue(res['Vs_req'] > 0)
        self.assertIsNotNone(res['s_req'])

    def test_torsion_logic(self):
        # Case 1: Negligible Torsion
        res = torsion.calculate_torsion(self.section, Tu=1.0, Vu=10.0)
        self.assertIn("Neglectable", res['status'])
        
        # Case 2: Significant Torsion
        # Tu = 20 kNm, Vu = 50 kN
        res_large = torsion.calculate_torsion(self.section, Tu=20.0, Vu=50.0)
        self.assertIn("Required", res_large['status'])
        self.assertGreater(res_large['At_s_req'], 0)
        self.assertGreater(res_large['Al_req'], 0)
        
        # Case 3: Cross Section Failure (Huge forces)
        res_fail = torsion.calculate_torsion(self.section, Tu=100.0, Vu=500.0)
        self.assertIn("Too Small", res_fail['status'])

if __name__ == '__main__':
    unittest.main()
