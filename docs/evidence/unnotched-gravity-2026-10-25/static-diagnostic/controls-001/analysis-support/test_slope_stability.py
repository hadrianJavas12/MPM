"""Independent equilibrium/scale/sign controls; no MPM or family search."""
from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.analysis.slope_stability import Circle, RejectedCircle, make_slices, solve_bishop

PROFILE = [(0., 10.), (12., 10.), (32., 0.)]


class BishopControls(unittest.TestCase):
    def setUp(self):
        self.circle = Circle(2., 28., .8)

    def test_phi_zero_independent_circle_moment(self):
        # Exact cohesive arc length; independent Gauss integration of the
        # continuous weight moment, split at the ground-profile corner.
        a, b, rho = 2., 28., .8
        cx, cy = (a+b)/2 + rho*8, 6 + rho*(b-a)
        radius = math.hypot(b-a, -8)*math.sqrt(.25+rho*rho)
        points, weights = np.polynomial.legendre.leggauss(96)
        driving = 0.
        for left, right in ((a, 12.), (12., b)):
            x = (left+right)/2 + (right-left)/2*points
            ground = np.where(x <= 12, 10., (32-x)/2)
            arc = cy - np.sqrt(radius**2-(x-cx)**2)
            driving += (right-left)/2*np.dot(weights, 20000*(ground-arc)*(cx-x)/radius)
        length = radius*(math.asin((b-cx)/radius)-math.asin((a-cx)/radius))
        expected = 10000*length/driving
        result = solve_bishop(make_slices(self.circle, PROFILE, 0., 2000, 20000), 10000, 0.)
        self.assertAlmostEqual(result["formalFactor"], expected, delta=1e-5)

    def test_strength_reduction_identity_and_negative_normals(self):
        slices = make_slices(self.circle, PROFILE, 0., 800, 20000)
        tangent = math.tan(math.radians(20))
        first = solve_bishop(slices, 10000, tangent)
        second = solve_bishop(slices, 10000/1.4, tangent/1.4)
        self.assertAlmostEqual(second["formalFactor"], first["formalFactor"]/1.4, delta=3e-10)
        self.assertGreater(first["negativeNormalCount"], 0)
        self.assertLess(first["minimumNormalStressPa"], 0)
        self.assertFalse(first["physicalAdmissibility"])

    def test_length_and_force_unit_similarity(self):
        tangent = math.tan(math.radians(20))
        first = solve_bishop(make_slices(self.circle, PROFILE, 0., 400, 20000), 10000, tangent)
        scale = 7
        scaled = Circle(self.circle.entry*scale, self.circle.exit*scale, self.circle.rho)
        profile = [(x*scale, y*scale) for x, y in PROFILE]
        second = solve_bishop(make_slices(scaled, profile, 0., 400, 20000/scale), 10000, tangent)
        third = solve_bishop(make_slices(self.circle, PROFILE, 0., 400, 20), 10, tangent)
        for result in (second, third):
            self.assertAlmostEqual(first["formalFactor"], result["formalFactor"], delta=3e-10)

    def test_geometry_and_driving_rejections(self):
        for circle in (Circle(-1, 28, .8), Circle(2, 28, .25), Circle(0, 32, .05)):
            with self.assertRaises(RejectedCircle):
                make_slices(circle, PROFILE, 0., 100, 20000)
        slices = make_slices(self.circle, PROFILE, 0., 400, 20000)
        self.assertGreater(slices.sine[0], 0)
        self.assertLess(slices.sine[-1], 0)
        zero_drive = replace(slices, weights=np.array([10., 10.]),
                             sine=np.array([-.5, .5]), cosine=np.array([math.sqrt(.75)]*2))
        with self.assertRaisesRegex(RejectedCircle, "NO_DRIVING"):
            solve_bishop(zero_drive, 10000, .3)

    def test_valid_vertical_tangent_at_arc_endpoint(self):
        # Crest P=(12,10), Q=(12.5,9.75), rho=.25 gives C=(12.3125,10).
        # The left endpoint has exactly zero circle radicand; midpoint bases
        # still have positive cos(alpha), so the geometry must be retained.
        slices = make_slices(Circle(12., 12.5, .25), PROFILE, 0., 200, 20000)
        self.assertEqual(slices.geometry["centerY"], 10.)
        self.assertAlmostEqual(slices.geometry["radius"], .3125)
        self.assertTrue((slices.cosine > 0).all())


if __name__ == "__main__":
    unittest.main()
