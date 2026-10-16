"""
Curves edited with the curve editor of the Node Editor (StringParam with the "curves" semantic).

A set of curves is stored as JSON: {"curveName": [[x, y], ...], ...}. A curve goes smoothly through its
points (monotone cubic interpolation, Fritsch-Carlson: no overshoot between two points) and continues in
straight lines beyond its first and last points. A curve without point is the identity, a curve with one
point is constant.
"""
import json
from typing import Dict, List, Sequence


def parseCurves(text: str) -> Dict[str, List[List[float]]]:
    """ The curves stored in a JSON string ({} if empty). Raises ValueError if it is not valid. """
    if not text or not text.strip():
        return {}
    curves = json.loads(text)
    if not isinstance(curves, dict):
        raise ValueError("The curves must be a JSON object {name: [[x, y], ...]}.")
    return {name: sortedPoints(points) for name, points in curves.items()}


def sortedPoints(points) -> List[List[float]]:
    """ The valid points of a curve, sorted by x, one point per x (the last one given). """
    result = {}
    for point in points or []:
        try:
            result[float(point[0])] = float(point[1])
        except (TypeError, ValueError, IndexError):
            continue
    return [[x, result[x]] for x in sorted(result)]


def _slopes(xs: List[float], ys: List[float]) -> List[float]:
    """ Tangents of the monotone cubic interpolation of the points. """
    deltas = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(len(xs) - 1)]
    slopes = [deltas[0]] + [0.0] * (len(xs) - 2) + [deltas[-1]]
    for i in range(1, len(xs) - 1):
        if deltas[i - 1] * deltas[i] <= 0:
            slopes[i] = 0.0
        else:
            # Weighted harmonic mean: keeps the curve monotone between monotone points
            w1 = 2 * (xs[i + 1] - xs[i]) + (xs[i] - xs[i - 1])
            w2 = (xs[i + 1] - xs[i]) + 2 * (xs[i] - xs[i - 1])
            slopes[i] = (w1 + w2) / (w1 / deltas[i - 1] + w2 / deltas[i])
    return slopes


class Curve:
    """ A curve ready to be evaluated many times (see the module documentation). """

    def __init__(self, points: Sequence[Sequence[float]]):
        points = sortedPoints(points)
        self.xs = [p[0] for p in points]
        self.ys = [p[1] for p in points]
        self.slopes = _slopes(self.xs, self.ys) if len(points) >= 2 else []

    def __call__(self, x: float) -> float:
        xs, ys, slopes = self.xs, self.ys, self.slopes
        if not xs:
            return float(x)
        if len(xs) == 1:
            return ys[0]
        if x <= xs[0]:
            return ys[0] + (x - xs[0]) * slopes[0]
        if x >= xs[-1]:
            return ys[-1] + (x - xs[-1]) * slopes[-1]
        # Segment [xs[i], xs[i + 1]] containing x (binary search)
        low, high = 0, len(xs) - 1
        while high - low > 1:
            middle = (low + high) // 2
            if xs[middle] <= x:
                low = middle
            else:
                high = middle
        i = low
        h = xs[i + 1] - xs[i]
        t = (x - xs[i]) / h
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * slopes[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * slopes[i + 1])


def evaluate(points: Sequence[Sequence[float]], x: float) -> float:
    """ The value of a curve at x. """
    return Curve(points)(x)


def sample(points: Sequence[Sequence[float]], x0: float, x1: float, count: int) -> List[float]:
    """ The values of a curve at `count` regular x from x0 to x1 (both included), e.g. to draw it. """
    curve = Curve(points)
    count = max(2, int(count))
    return [curve(x0 + (x1 - x0) * i / (count - 1)) for i in range(count)]
