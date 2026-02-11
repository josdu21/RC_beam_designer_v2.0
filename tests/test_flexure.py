import pytest
from src.models.section import BeamSection
from src.models.flexure import calculate_flexure


@pytest.fixture
def standard_section():
    return BeamSection(b=30, h=50, fc=28, fy=420, cover=4)


class TestFlexure:
    def test_basic_positive_moment(self, standard_section):
        res = calculate_flexure(standard_section, 100)
        assert res['status'] == 'OK'
        assert res['As_calc'] > 0
        assert res['As_design'] >= res['As_min']
        assert res['phi'] == pytest.approx(0.9, abs=0.01)

    def test_zero_moment(self, standard_section):
        res = calculate_flexure(standard_section, 0)
        assert 'Min Steel' in res['status']
        assert res['As_calc'] == 0.0
        assert res['As_design'] > 0

    def test_overloaded_section(self, standard_section):
        res = calculate_flexure(standard_section, 1000)
        assert 'Error' in res['status']
        assert res['As_calc'] == 0.0
        assert res['As_design'] == 0.0

    def test_negative_moment_uses_abs(self, standard_section):
        res_pos = calculate_flexure(standard_section, 100)
        res_neg = calculate_flexure(standard_section, -100)
        assert res_pos['As_calc'] == pytest.approx(res_neg['As_calc'], rel=1e-6)

    def test_all_keys_present_on_success(self, standard_section):
        res = calculate_flexure(standard_section, 100)
        expected_keys = {'As_calc', 'As_min', 'As_design', 'rho', 'phi', 'epsilon_t', 'status', 'c', 'a'}
        assert expected_keys == set(res.keys())

    def test_all_keys_present_on_error(self, standard_section):
        res = calculate_flexure(standard_section, 1000)
        expected_keys = {'As_calc', 'As_min', 'As_design', 'rho', 'phi', 'epsilon_t', 'status', 'c', 'a'}
        assert expected_keys == set(res.keys())

    def test_hand_calc_validation(self):
        """Validate against known: 30x50cm, fc=28, fy=420, Mu=150kNm -> As ~9-10 cm2."""
        section = BeamSection(30, 50, 28, 420, 4)
        res = calculate_flexure(section, 150)
        assert 8.0 < res['As_design'] < 11.0

    @pytest.mark.parametrize("fc", [21, 28, 35, 42, 55, 70])
    def test_various_concrete_strengths(self, fc):
        section = BeamSection(30, 50, fc, 420, 4)
        res = calculate_flexure(section, 100)
        assert res['As_calc'] > 0

    @pytest.mark.parametrize("fy", [280, 420, 500])
    def test_various_steel_grades(self, fy):
        section = BeamSection(30, 50, 28, fy, 4)
        res = calculate_flexure(section, 100)
        assert res['As_calc'] > 0

    def test_higher_fc_gives_less_steel(self):
        s1 = BeamSection(30, 50, 21, 420, 4)
        s2 = BeamSection(30, 50, 42, 420, 4)
        r1 = calculate_flexure(s1, 100)
        r2 = calculate_flexure(s2, 100)
        assert r1['As_calc'] > r2['As_calc']

    def test_higher_fy_gives_less_steel(self):
        s1 = BeamSection(30, 50, 28, 280, 4)
        s2 = BeamSection(30, 50, 28, 500, 4)
        r1 = calculate_flexure(s1, 100)
        r2 = calculate_flexure(s2, 100)
        assert r1['As_calc'] > r2['As_calc']
