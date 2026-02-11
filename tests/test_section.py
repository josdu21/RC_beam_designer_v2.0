import pytest
from src.models.section import BeamSection


class TestBeamSection:
    def test_valid_creation(self):
        s = BeamSection(30, 50, 28, 420, 4)
        assert s.b == 30
        assert s.h == 50
        assert s.d == 46
        assert s.fc == 28
        assert s.fy == 420
        assert s.cover == 4

    def test_beta1_low_fc(self):
        s = BeamSection(30, 50, 21, 420, 4)
        assert s.beta1 == 0.85

    def test_beta1_medium_fc(self):
        s = BeamSection(30, 50, 40, 420, 4)
        assert 0.65 < s.beta1 < 0.85

    def test_beta1_high_fc(self):
        s = BeamSection(30, 50, 60, 420, 4)
        assert s.beta1 == 0.65

    def test_cover_equals_height_raises(self):
        with pytest.raises(ValueError, match="Cover"):
            BeamSection(30, 50, 28, 420, 50)

    def test_cover_exceeds_height_raises(self):
        with pytest.raises(ValueError, match="Cover"):
            BeamSection(30, 50, 28, 420, 60)

    def test_negative_width_raises(self):
        with pytest.raises(ValueError, match="positive"):
            BeamSection(-10, 50, 28, 420, 4)

    def test_negative_height_raises(self):
        with pytest.raises(ValueError, match="positive"):
            BeamSection(30, -50, 28, 420, 4)

    def test_zero_fc_raises(self):
        with pytest.raises(ValueError, match="positive"):
            BeamSection(30, 50, 0, 420, 4)

    def test_negative_fy_raises(self):
        with pytest.raises(ValueError, match="positive"):
            BeamSection(30, 50, 28, -420, 4)
