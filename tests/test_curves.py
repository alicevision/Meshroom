"""Tests of the curves of the curve editor (meshroom.core.curves)."""
import pytest

from meshroom.core import curves


def test_parseAndSort():
    parsed = curves.parseCurves('{"master": [[1, 1], [0, 0], [0.5, 0.7], ["bad"], [0.5, 0.6]]}')
    assert parsed == {"master": [[0.0, 0.0], [0.5, 0.6], [1.0, 1.0]]}
    assert curves.parseCurves("") == {}
    with pytest.raises(ValueError):
        curves.parseCurves("[1, 2]")


def test_evaluate():
    # No point: identity; one point: constant
    assert curves.evaluate([], 0.3) == 0.3
    assert curves.evaluate([[0.2, 0.7]], 5.0) == 0.7
    # Through the points, straight lines beyond them
    points = [[0, 0], [0.5, 0.8], [1, 1]]
    assert curves.evaluate(points, 0.5) == pytest.approx(0.8)
    assert curves.evaluate(points, 1.0) == pytest.approx(1.0)
    assert curves.evaluate(points, 2.0) == pytest.approx(1.0 + 1.0 * 0.4)
    # Monotone: no overshoot between monotone points
    values = curves.sample([[0, 0], [0.1, 0.9], [1, 1]], 0.0, 1.0, 101)
    assert all(b >= a - 1e-12 for a, b in zip(values, values[1:]))
    assert max(values) <= 1.0 + 1e-12


def test_sample():
    values = curves.sample([[0, 0], [1, 1]], 0.0, 1.0, 5)
    assert values == pytest.approx([0.0, 0.25, 0.5, 0.75, 1.0])
    assert len(curves.sample([], 0.0, 1.0, 1)) == 2
