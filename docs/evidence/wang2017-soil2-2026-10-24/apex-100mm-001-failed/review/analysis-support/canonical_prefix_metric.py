import numpy as np

def metric(a, b, atol, rtol):
    difference = np.abs(a - b)
    tolerance = atol + rtol * np.abs(a)
    baseline_scale = float(np.max(np.abs(a), initial=0))
    max_difference = float(difference.max(initial=0))
    global_tolerance = atol + rtol * baseline_scale
    return {"max_abs_difference": float(difference.max(initial=0)),
            "rms_difference": float(np.sqrt(np.mean(difference ** 2))),
            "max_scaled_difference": float(np.max(difference / np.maximum(tolerance, np.finfo(float).tiny), initial=0)),
            "mismatched_values": int(np.count_nonzero(difference > tolerance)),
            "pass": bool(np.all(difference <= tolerance)),
            "global_linf_diagnostic": {
                "basis": "max absolute difference / max absolute baseline value for this entire saved field; does not replace pointwise pass",
                "baseline_linf": baseline_scale,
                "relative_linf_difference": (max_difference / baseline_scale
                                             if baseline_scale else (0.0 if not max_difference else None)),
                "tolerance": global_tolerance,
                "pass": max_difference <= global_tolerance}}

