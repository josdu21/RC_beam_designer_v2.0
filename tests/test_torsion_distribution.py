from src.models.torsion_distribution import distribute_torsion_longitudinal_reinf


def test_distribution_zero_area():
    dist = distribute_torsion_longitudinal_reinf(0.0, 30, 50, 4, 6)
    assert dist.al_total == 0.0
    assert dist.al_bottom == 0.0
    assert dist.al_top == 0.0
    assert dist.al_side_each == 0.0


def test_distribution_conserves_total_area():
    dist = distribute_torsion_longitudinal_reinf(6.0, 30, 50, 4, 8)
    total = dist.al_bottom + dist.al_top + 2 * dist.al_side_each
    assert abs(total - 6.0) < 1e-9
    assert dist.n_bars >= 4
