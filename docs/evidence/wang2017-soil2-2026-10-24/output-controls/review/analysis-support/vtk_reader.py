"""Read-only, non-interpolated Wang2017 saved-output comparison. No solver calls."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return [{key: float(value.lower().replace("d", "e")) for key, value in row.items()}
                for row in csv.DictReader(stream)]


def vtk(path):
    data, offset = path.read_bytes(), 0

    def line():
        nonlocal offset
        end = data.index(b"\n", offset)
        result = data[offset:end].decode("ascii").rstrip("\r")
        offset = end + 1
        return result

    def array(count):
        nonlocal offset
        if offset + count * 8 > len(data):
            raise ValueError("Truncated VTK array")
        result = np.frombuffer(data, dtype=">f8", count=count, offset=offset).astype(float)
        offset += count * 8
        if line() != "" or not np.isfinite(result).all():
            raise ValueError("Nonfinite or malformed VTK array")
        return result

    if not line().startswith("# vtk DataFile Version"):
        raise ValueError("Missing VTK signature")
    line()
    if line() != "BINARY" or line() != "DATASET UNSTRUCTURED_GRID":
        raise ValueError("Unsupported VTK layout")
    header = line().split()
    if header[0] != "POINTS" or header[2] != "double":
        raise ValueError("Unsupported coordinates")
    count = int(header[1])
    points = array(3 * count).reshape(count, 3)
    if line() != f"POINT_DATA {count}":
        raise ValueError("Point count mismatch")
    fields = {}
    while offset < len(data):
        text = line()
        if not text:
            continue
        header = text.split()
        if header[0] != "SCALARS" or header[2] != "double" or line() != "LOOKUP_TABLE default":
            raise ValueError("Unsupported scalar layout")
        fields[header[1]] = array(count)
    ids = fields["unique-id"]
    if len(np.unique(ids)) != count or not (ids == np.floor(ids)).all():
        raise ValueError("Invalid particle IDs")
    order = np.argsort(ids)
    return points[order], {key: value[order] for key, value in fields.items()}


