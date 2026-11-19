import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from channel import retention_points  # noqa: E402


def test_half_quarter_and_early_drop():
    curve = [(k / 100, r) for k, r in enumerate([1.0, 0.95, 0.70, 0.66, 0.6, 0.55, 0.52, 0.49] + [0.4] * 20 + [0.2] * 73)]
    line = retention_points(curve, 600)
    assert "half the viewers gone by 0:42" in line
    assert "three quarters by 2:48" in line
    assert "steepest early drop at 0:12" in line
