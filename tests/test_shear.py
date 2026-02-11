import pytest

from src.models.section import BeamSection
from src.models.shear import calculate_shear


@pytest.fixture
def standard_section():
    return BeamSection(b=30, h=50, fc=28, fy=420, cover=4)


class TestShear:
    def test_no_stirrups_needed(self, standard_section):
        res = calculate_shear(standard_section, Vu=5)
        assert "No Shear" in res['status']
        assert res['Vs_req'] == 0
        assert res['s_req'] is None

    def test_stirrups_required(self, standard_section):
        res = calculate_shear(standard_section, Vu=100)
        assert res['Vs_req'] > 0
        assert res['s_req'] is not None
        assert res['s_req'] > 0

    def test_section_too_small(self, standard_section):
        res = calculate_shear(standard_section, Vu=1000)
        assert "Error" in res['status']
        assert res['s_req'] is None

    def test_all_keys_present(self, standard_section):
        res = calculate_shear(standard_section, 100)
        expected = {'Vc', 'phi_Vc', 'Vs_req', 's_req', 's_max', 'status', 'status_code', 'Av', 'Av_bar_cm2', 'trace'}
        assert expected == set(res.keys())

    def test_all_keys_on_no_stirrups(self, standard_section):
        res = calculate_shear(standard_section, 5)
        expected = {'Vc', 'phi_Vc', 'Vs_req', 's_req', 's_max', 'status', 'status_code', 'Av', 'Av_bar_cm2', 'trace'}
        assert expected == set(res.keys())

    def test_negative_vu_uses_abs(self, standard_section):
        r1 = calculate_shear(standard_section, 100)
        r2 = calculate_shear(standard_section, -100)
        assert r1['Vs_req'] == pytest.approx(r2['Vs_req'], rel=1e-6)

    def test_more_legs_reduces_spacing(self, standard_section):
        r2 = calculate_shear(standard_section, 100, n_legs=2)
        r4 = calculate_shear(standard_section, 100, n_legs=4)
        # More legs -> same Vs but more Av -> larger spacing
        if r2['s_req'] and r4['s_req']:
            assert r4['s_req'] >= r2['s_req']

    def test_larger_bar_reduces_spacing_need(self, standard_section):
        r_small = calculate_shear(standard_section, 100, stirrup_diameter=0.95)  # #3
        r_large = calculate_shear(standard_section, 100, stirrup_diameter=1.27)  # #4
        if r_small['s_req'] and r_large['s_req']:
            assert r_large['s_req'] >= r_small['s_req']

    @pytest.mark.parametrize("Vu", [20, 50, 80, 120, 200])
    def test_various_shear_forces(self, standard_section, Vu):
        res = calculate_shear(standard_section, Vu)
        assert res['Vc'] > 0
        assert 'status' in res

    def test_status_code_and_trace_present(self, standard_section):
        res = calculate_shear(standard_section, -100)
        assert res['status_code'] in {'ok', 'warning', 'error'}
        assert isinstance(res['trace'], list)
        assert len(res['trace']) >= 1
