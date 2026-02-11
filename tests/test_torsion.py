import pytest
from src.models.section import BeamSection
from src.models.torsion import calculate_torsion


@pytest.fixture
def standard_section():
    return BeamSection(b=30, h=50, fc=28, fy=420, cover=4)


class TestTorsion:
    def test_negligible_torsion(self, standard_section):
        res = calculate_torsion(standard_section, Tu=1.0, Vu=10.0)
        assert "Neglectable" in res['status']
        assert res['At_s_req'] == 0.0
        assert res['Al_req'] == 0.0

    def test_significant_torsion(self, standard_section):
        res = calculate_torsion(standard_section, Tu=20.0, Vu=50.0)
        assert "Required" in res['status']
        assert res['At_s_req'] > 0
        assert res['Al_req'] > 0

    def test_cross_section_failure(self, standard_section):
        res = calculate_torsion(standard_section, Tu=100.0, Vu=500.0)
        assert "Too Small" in res['status'] or "Error" in res['status']

    def test_all_keys_on_negligible(self, standard_section):
        res = calculate_torsion(standard_section, Tu=1.0, Vu=10.0)
        expected = {'Tu', 'T_th', 'phi_T_th', 'T_cr', 'phi_T_cr', 'status',
                    'At_s_req', 'At_s_req_cm2_m', 'Al_req', 'check_cross_section', 'action'}
        assert expected == set(res.keys())

    def test_all_keys_on_required(self, standard_section):
        res = calculate_torsion(standard_section, Tu=20.0, Vu=50.0)
        expected = {'Tu', 'T_th', 'phi_T_th', 'T_cr', 'phi_T_cr', 'status',
                    'At_s_req', 'At_s_req_cm2_m', 'Al_req', 'check_cross_section', 'action'}
        assert expected == set(res.keys())

    def test_all_keys_on_error(self, standard_section):
        res = calculate_torsion(standard_section, Tu=100.0, Vu=500.0)
        expected = {'Tu', 'T_th', 'phi_T_th', 'T_cr', 'phi_T_cr', 'status',
                    'At_s_req', 'At_s_req_cm2_m', 'Al_req', 'check_cross_section', 'action'}
        assert expected == set(res.keys())

    def test_section_too_small_for_cover(self):
        """Section where cover is almost as big as the section."""
        section = BeamSection(b=10, h=15, fc=28, fy=420, cover=8)
        res = calculate_torsion(section, Tu=10.0, Vu=10.0)
        assert "Error" in res['status']

    def test_custom_cover_affects_results(self):
        """Different cover should give different torsion results."""
        s1 = BeamSection(30, 50, 28, 420, 3)
        s2 = BeamSection(30, 50, 28, 420, 5)
        r1 = calculate_torsion(s1, Tu=20.0, Vu=50.0)
        r2 = calculate_torsion(s2, Tu=20.0, Vu=50.0)
        # Larger cover reduces Aoh, increasing At/s requirement
        if "Required" in r1['status'] and "Required" in r2['status']:
            assert r2['At_s_req'] > r1['At_s_req']

    def test_at_s_cm2_m_conversion(self, standard_section):
        """Verify At_s_req_cm2_m = At_s_req * 10."""
        res = calculate_torsion(standard_section, Tu=20.0, Vu=50.0)
        if res['At_s_req'] > 0:
            assert res['At_s_req_cm2_m'] == pytest.approx(res['At_s_req'] * 10, rel=1e-6)

    def test_zero_torsion_is_negligible(self, standard_section):
        res = calculate_torsion(standard_section, Tu=0.0, Vu=50.0)
        assert "Neglectable" in res['status']

    @pytest.mark.parametrize("fc", [21, 28, 35, 55])
    def test_various_concrete_strengths(self, fc):
        section = BeamSection(30, 50, fc, 420, 4)
        res = calculate_torsion(section, Tu=20.0, Vu=50.0)
        assert 'status' in res
        assert res['T_th'] > 0
