# CL-MPM Studio: Geometry and notch controls

The Studio 2D chalk-cliff scenario lives in `studio/lisp/scenario.lisp`. Geometry is
constructed from material points and removed by signed predicates through
`cl-mpm/setup:remove-sdf`. The **Geometry Preview** in Studio is an
independent sampled 2D representation in `studio/public/geometry.js`.
It is **not** a solver result, damage plot, mesh-convergence test, or VTK output.

## Coordinates and cliff face

- `x = 0` is the left edge of the domain, `y = 0` the bottom.
- `soilBoundary` is the base-layer thickness. That layer is not cut by a notch.
- `shelfHeight` is the height **above** the base layer.
- `shelfLength = shelfHeight * shelfAspect`.
- The toe reference point is `(shelfLength, soilBoundary)`.
- `cliffSlope = 90` is a vertical face. Values below 90 tilt the top back.
- `undercut` is **face overhang**, not the notch angle. The older setting
  retains its original meaning for backwards compatibility.

The face in the Lisp scenario is the plane through the toe with normal
`(cos(theta), sin(theta))`, where
`theta = radians(90 - cliffSlope - undercut)`.
The preview uses the equivalent equation
`faceX(y) = shelfLength - (y-soilBoundary)*tan(theta)`.

## Toe notch

The notch height `notchHeight = 0` disables notch removal. The active
height range is `soilBoundary < y < soilBoundary + notchHeight`.
A `notchDepth = 0` means `depth = 1.5 * notchHeight`, preserving the old
automatic-depth rule.

Three styles are available:

| notchShape | Description |
| --- | --- |
| `rectangle` | Legacy, centred at the toe and extending inward by `depth` |
| `ellipse` | Ellipse centred on the toe, radii `(depth, height/2)` |
| `triangle` | Wedge with a vertical mouth at the toe and an inward point at `depth` |

For triangular notches, `notchTipFraction` (0.15 to 0.85) places the tip
vertically within the notch. At 0.5 the tip is halfway up; lower/higher
values shift it down/up. Other notch styles ignore this parameter.

The clipping is applied **after** removal of the inclined cliff face.
Accordingly, high overhang angles and unusual face/notch combinations
may produce disconnected geometry; visually inspect the preview and
initial VTK before running expensive simulations.

## Preview limits and validation

- The preview samples a fixed grid; thin slits may disappear due to sampling.
- The solver removes **material points**, not a polygonal continuum; if a
  notch is smaller than the material point spacing or background mesh size,
  its discretised shape may differ from the preview.
- A physically meaningful run requires geometry checks, appropriate
  boundary conditions, stable timestep selection, material calibration,
  and mesh convergence checks. No numerical validation is implied.
- The Studio runner still uses its simplified timestep loop, not the
  multi-phase Joss Bay procedure from the published paper.

## Tests

Run `cd studio && npm run check && npm test` with Node.js 22.
The tests verify geometry predicates, numeric boundaries, and basic Studio
HTTP behaviour. They do **not** invoke SBCL, gnuplot, or the MPM solver.
