#!/usr/bin/env python3
"""Initialize E and a triaxial strength scale from a declared CSV source.

This script does not execute a constitutive model, generate a forward curve,
or calibrate/validate the native MPM solver. All calculations use the input rows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


STRAIN_HEADER = "axial_strain_pct"
STRESS_HEADER = "deviatoric_stress_kpa"
SOURCE_KINDS = ("user_data", "actual_simulation", "synthetic")


def read_curve(path: Path, strain_column: str = STRAIN_HEADER) -> list[tuple[float, float]]:
    """Read a monotonic compression curve with explicit percent/kPa headers."""
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise ValueError("CSV contains duplicate column headers")
        if strain_column not in headers or STRESS_HEADER not in headers:
            raise ValueError(
                f"CSV requires unit-bearing headers {strain_column!r} and {STRESS_HEADER!r}"
            )
        for line_number, record in enumerate(reader, start=2):
            if None in record:
                raise ValueError(f"CSV line {line_number}: too many columns")
            try:
                strain = float(record[strain_column])
                stress = float(record[STRESS_HEADER])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"CSV line {line_number}: strain and stress must be numeric"
                ) from error
            if not math.isfinite(strain) or not math.isfinite(stress):
                raise ValueError(f"CSV line {line_number}: non-finite strain or stress")
            if not 0 <= strain < 100:
                raise ValueError(
                    f"CSV line {line_number}: engineering compression strain must be in [0, 100) percent"
                )
            if rows and strain < rows[-1][0]:
                raise ValueError(
                    f"CSV line {line_number}: strain decreases; select the monotonic loading branch first"
                )
            rows.append((strain, stress))
    if not rows:
        raise ValueError("CSV has no data rows")
    return rows


def regression(points: list[tuple[float, float]]) -> dict:
    """Regress q in Pa against engineering strain as a fraction, with intercept."""
    x = [strain / 100 for strain, _ in points]
    y = [stress * 1000 for _, stress in points]
    mean_x = statistics.fmean(x)
    mean_y = statistics.fmean(y)
    xx = sum((value - mean_x) ** 2 for value in x)
    if xx <= 0:
        raise ValueError("regression needs distinct strain values")
    slope = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / xx
    intercept = mean_y - slope * mean_x
    residuals = [yi - (intercept + slope * xi) for xi, yi in zip(x, y)]
    sse = sum(value ** 2 for value in residuals)
    sst = sum((value - mean_y) ** 2 for value in y)
    r_squared = 1 - sse / sst if sst > 0 else None
    if not all(math.isfinite(value) for value in (slope, intercept, sse, sst)):
        raise ValueError("regression overflow; check the input units and magnitudes")
    return {
        "slope_pa_per_unit_strain": slope,
        "intercept_kpa": intercept / 1000,
        "r_squared": r_squared,
        "rmse_kpa": math.sqrt(sse / len(points)) / 1000,
    }


def estimate(
    path: Path,
    *,
    source_kind: str = "user_data",
    strain_column: str = STRAIN_HEADER,
    elastic_max_strain_pct: float = 0.4,
    strength_start_strain_pct: float = 5.0,
) -> dict:
    if source_kind not in SOURCE_KINDS:
        raise ValueError(f"source kind must be one of {', '.join(SOURCE_KINDS)}")
    if not isinstance(strain_column, str) or not strain_column.endswith("_pct"):
        raise ValueError("strain column must have a percent unit header ending in '_pct'")
    if not (
        math.isfinite(elastic_max_strain_pct)
        and math.isfinite(strength_start_strain_pct)
        and 0 < elastic_max_strain_pct < strength_start_strain_pct < 100
    ):
        raise ValueError("require 0 < elastic maximum < strength start < 100 percent")
    rows = read_curve(path, strain_column)
    elastic = [point for point in rows if point[0] <= elastic_max_strain_pct + 1e-12]
    late = [point for point in rows if point[0] >= strength_start_strain_pct - 1e-12]
    for label, points in (("elastic", elastic), ("late-strength", late)):
        if len(points) < 3 or len({point[0] for point in points}) < 3:
            raise ValueError(f"{label} window needs at least 3 distinct strain samples")
    elastic_fit = regression(elastic)
    youngs_modulus = elastic_fit["slope_pa_per_unit_strain"]
    if youngs_modulus <= 0:
        raise ValueError("elastic regression slope must be positive; check window, signs and units")
    late_stresses = [stress for _, stress in late]
    median_q = statistics.median(late_stresses)
    if median_q <= 0:
        raise ValueError("late-strength median q must be positive; check window and sign convention")
    su = median_q * 1000 / 2
    rho = math.sqrt(8 / 3) * su
    if not all(math.isfinite(value) for value in (youngs_modulus, su, rho)):
        raise ValueError("parameter overflow; check the input units and magnitudes")
    return {
        "status": "parameter_initialization_only",
        "laboratory_calibration": False,
        "scientific_validation": False,
        "native_forward_optimization": False,
        "source": {
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "kind": source_kind,
            "provenance": "declared_by_caller_not_independently_verified",
            "row_count": len(rows),
            "strain_column": strain_column,
            "stress_column": STRESS_HEADER,
        },
        "conventions": {
            "strain": "engineering axial compression positive, percent",
            "stress": "axial minus radial compression stress, kPa",
        },
        "parameters": {
            "youngsModulusPa": youngs_modulus,
            "undrainedStrengthPa": su,
            "nativeVmRhoPa": rho,
        },
        "elastic_regression": {
            "method": "ordinary least squares with intercept; q [Pa] versus strain [fraction]",
            "maximum_requested_strain_pct": elastic_max_strain_pct,
            "used_strain_range_pct": [elastic[0][0], elastic[-1][0]],
            "point_count": len(elastic),
            "distinct_strain_count": len({point[0] for point in elastic}),
            **elastic_fit,
        },
        "late_strength": {
            "method": "su initializer = median late q / 2; native rho = sqrt(8/3)*su",
            "minimum_requested_strain_pct": strength_start_strain_pct,
            "used_strain_range_pct": [late[0][0], late[-1][0]],
            "point_count": len(late),
            "distinct_strain_count": len({point[0] for point in late}),
            "median_q_kpa": median_q,
            "q_range_kpa": [min(late_stresses), max(late_stresses)],
            "median_absolute_deviation_kpa": statistics.median(
                abs(value - median_q) for value in late_stresses
            ),
            "plateau_verified": False,
        },
        "limitations": [
            "No native constitutive/MPM forward solve or parameter optimization was performed.",
            "A late stress median does not establish yield or a plateau; inspect the curve and test protocol.",
            "The small-strain constant-lateral-stress E relation is an initializer, not an exact finite-strain MPM fit.",
            "VM rho is a Kirchhoff stress scale; Cauchy yield differs by 1/J when J is not one.",
            "No Poisson ratio, pore pressure, permeability, consolidation history or damage parameters are identified.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path, help="input curve with percent/kPa headers")
    parser.add_argument("--output", required=True, type=Path, help="parameter-initialization JSON")
    parser.add_argument("--source-kind", choices=SOURCE_KINDS, default="user_data")
    parser.add_argument(
        "--strain-column", default=STRAIN_HEADER,
        help="engineering strain column in percent (header must end in _pct)",
    )
    parser.add_argument("--elastic-max-strain-pct", type=float, default=0.4)
    parser.add_argument("--strength-start-strain-pct", type=float, default=5.0)
    args = parser.parse_args()
    try:
        if args.csv.resolve() == args.output.resolve():
            raise ValueError("output must differ from the input CSV")
        result = estimate(
            args.csv,
            source_kind=args.source_kind,
            strain_column=args.strain_column,
            elastic_max_strain_pct=args.elastic_max_strain_pct,
            strength_start_strain_pct=args.strength_start_strain_pct,
        )
        encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    except (OSError, ValueError, OverflowError) as error:
        parser.exit(2, f"error: {error}\n")
    print(f"Parameter initialization only; no laboratory/native calibration: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
