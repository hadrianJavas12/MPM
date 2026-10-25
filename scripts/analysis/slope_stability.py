"""Dry simplified Bishop on a declared circular family, not MPM validation."""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np


class RejectedCircle(ValueError):
    """A recorded geometric or formal-equilibrium rejection."""


@dataclass(frozen=True)
class Circle:
    entry: float
    exit: float
    rho: float


@dataclass(frozen=True)
class SliceData:
    width: float
    weights: np.ndarray
    sine: np.ndarray
    cosine: np.ndarray
    geometry: dict


def profile_height(x, profile):
    points = np.asarray(profile, dtype=float)
    if (points.ndim != 2 or points.shape[1] != 2 or len(points) < 2
            or not np.isfinite(points).all() or not (np.diff(points[:, 0]) > 0).all()):
        raise ValueError("Profile must contain finite, increasing x/y pairs")
    return np.interp(x, points[:, 0], points[:, 1])


def make_slices(circle, profile, base, count, unit_weight, geometry_tolerance=1e-9):
    """Check the continuous arc at its exact minimum and profile breakpoints."""
    profile_height(0., profile)
    points = np.asarray(profile, dtype=float)
    a, b, rho = circle.entry, circle.exit, circle.rho
    if (not all(math.isfinite(v) for v in (a, b, rho, base, unit_weight, geometry_tolerance))
            or not isinstance(count, int) or count < 2 or unit_weight <= 0 or geometry_tolerance < 0):
        raise ValueError("Invalid finite geometry, slice count or unit weight")
    if a < points[0, 0] or b > points[-1, 0] or a >= b or rho <= 0:
        raise RejectedCircle("ENDPOINT_RANGE_OR_CHORD")
    ya, yb = map(float, profile_height([a, b], profile))
    dx, dy = b - a, yb - ya
    cx, cy = (a + b) / 2 - rho * dy, (ya + yb) / 2 + rho * dx
    radius = math.hypot(dx, dy) * math.sqrt(.25 + rho * rho)
    if cy < max(ya, yb):
        raise RejectedCircle("CENTER_BELOW_ENDPOINT")

    def arc(x):
        radicand = radius * radius - (np.asarray(x) - cx) ** 2
        if not np.isfinite(radicand).all() or (radicand < 0).any():
            raise RejectedCircle("NONREAL_LOWER_ARC")
        return cy - np.sqrt(radicand)

    minimum_x = min(max(cx, a), b)
    minimum_y = float(arc(minimum_x))
    if minimum_y < base - geometry_tolerance:
        raise RejectedCircle("ARC_BELOW_BASE")
    check_x = np.concatenate(([a, b], points[(points[:, 0] > a) & (points[:, 0] < b), 0]))
    # Ground minus lower arc is concave within each linear profile segment;
    # checking segment endpoints therefore checks its continuous minimum.
    if (arc(check_x) > profile_height(check_x, profile) + geometry_tolerance).any():
        raise RejectedCircle("ARC_OUTSIDE_SOIL")
    width = (b - a) / count
    x = a + (np.arange(count) + .5) * width
    bottom = arc(x)
    weights = unit_weight * (profile_height(x, profile) - bottom) * width
    sine = (cx - x) / radius  # positive for a base descending toward the right
    cosine = np.sqrt(1 - sine * sine)
    if not np.isfinite(weights).all() or not (weights > 0).all() or not (cosine > 0).all():
        raise RejectedCircle("NONPOSITIVE_WEIGHT_OR_BASE_COSINE")
    return SliceData(width, weights, sine, cosine,
                     {"centerX": cx, "centerY": cy, "radius": radius,
                      "arcMinimumX": minimum_x, "arcMinimumY": minimum_y,
                      "baseRoundoffDeficitM": max(0., base - minimum_y)})


def solve_bishop(slices, cohesion, tan_phi, tolerance=1e-10, maximum_bisections=100):
    """Unique formal root on the positive m_alpha domain; retain negative N.

    H(F)=sum(A/(F*cos(alpha)+sin(alpha)*tan(phi)))-D is strictly decreasing
    when A>=0, some A>0 and cos(alpha)>0. This is a restricted formal diagnostic;
    horizontal equilibrium and a tension-crack/no-tension model are not solved.
    """
    if (not all(math.isfinite(v) for v in (cohesion, tan_phi, tolerance))
            or cohesion < 0 or tan_phi < 0 or tolerance <= 0 or maximum_bisections < 1):
        raise ValueError("Invalid Bishop strength or root controls")
    w, sine, cosine = slices.weights, slices.sine, slices.cosine
    if (not all(np.isfinite(v).all() for v in (w, sine, cosine))
            or not (w > 0).all() or not (cosine > 0).all()):
        raise RejectedCircle("INVALID_SLICE_DATA")
    driving = float(np.dot(w, sine))
    if driving <= 0:
        raise RejectedCircle("NO_DRIVING_MOMENT")
    resistance = cohesion * slices.width + w * tan_phi
    if not (resistance >= 0).all() or not (resistance > 0).any():
        raise RejectedCircle("NO_NONNEGATIVE_RESISTANCE")
    barrier = max(0., float(np.max(-sine * tan_phi / cosine)))
    low = barrier + 1e-10
    high = barrier + float(np.sum(resistance / cosine)) / driving + 1.

    def residual(factor):
        denominator = factor * cosine + sine * tan_phi
        if not (denominator > 0).all():
            raise RejectedCircle("NONPOSITIVE_M_ALPHA_DOMAIN")
        return float(np.sum(resistance / denominator) - driving)

    if not low > barrier or not high > low or residual(low) <= 0 or residual(high) >= 0:
        raise RejectedCircle("NO_POSITIVE_ROOT_BRACKET_ABOVE_BARRIER")
    iterations = 0
    while high - low > tolerance and iterations < maximum_bisections:
        middle = (low + high) / 2
        if residual(middle) > 0:
            low = middle
        else:
            high = middle
        iterations += 1
    if high - low > tolerance:
        raise RejectedCircle("BISECTION_NOT_CONVERGED")
    factor = (low + high) / 2
    m_alpha = cosine + sine * tan_phi / factor
    if not (m_alpha > 0).all():
        raise RejectedCircle("NONPOSITIVE_M_ALPHA_DOMAIN")
    normal = (w - cohesion * slices.width * (sine / cosine) / factor) / m_alpha
    normal_stress = normal * cosine / slices.width
    if not np.isfinite(normal).all():
        raise RejectedCircle("NONFINITE_BASE_NORMAL")
    return {"formalFactor": factor, "iterations": iterations,
            "factorBracketWidth": high - low, "domainBarrier": barrier,
            "equilibriumResidualNPerM": residual(factor), "drivingNPerM": driving,
            "minimumMAlpha": float(np.min(m_alpha)),
            "negativeNormalCount": int(np.count_nonzero(normal < 0)),
            "minimumNormalForceNPerM": float(np.min(normal)),
            "minimumNormalStressPa": float(np.min(normal_stress)),
            "normalForcesNonnegative": bool((normal >= 0).all()),
            "physicalAdmissibility": False, "scientificallyValidated": False}
