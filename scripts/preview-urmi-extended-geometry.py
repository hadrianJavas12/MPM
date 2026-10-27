"""Plot the approved geometry proposal only; no native MPM or material update."""
from pathlib import Path
import hashlib
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "research/notes/urmi-mc-damage40-2026-10-26/geometry-preview-extended-left-base8.json"
OUTPUT = ROOT / "docs/benchmarks/previews/urmi-left12-base8"


def record(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def polygon(left, right, crest, toe, height, depth):
    return [[left, -depth], [right, -depth], [right, 0], [toe, 0], [crest, height], [left, height]]


def particles(config, shift_x, depth):
    h, ppc = config["meshSize"], config["mpsPerCell"]
    nx = round(config["domainWidth"] / h) * ppc
    ny = round((depth + config["height"]) / h) * ppc
    x, y = np.meshgrid((np.arange(nx) + .5) * config["domainWidth"] / nx,
                       (np.arange(ny) + .5) * (depth + config["height"]) / ny)
    top = depth + np.maximum(0, config["height"] - math.tan(math.radians(config["slope"])) * np.maximum(0, x - config["crestLength"]))
    mask = y <= top
    return np.column_stack((x[mask] - shift_x, y[mask] - depth))


def main():
    proposal = json.loads(PROPOSAL.read_text())
    original_path = ROOT / proposal["sourceConfiguration"]
    original = json.loads(original_path.read_text(encoding="utf-8-sig"))
    extension, depth = proposal["leftExtensionM"], proposal["foundationThicknessM"]
    assert extension == 12 and depth == 8 and original["baseHeight"] == 4
    assert original["slope"] == 40 and original["height"] == 10
    new = dict(original)
    new.update(crestLength=original["crestLength"] + extension, baseHeight=depth,
               domainWidth=original["domainWidth"] + extension,
               domainHeight=original["domainHeight"] + depth - original["baseHeight"])
    crest, height, right = original["crestLength"], original["height"], original["domainWidth"]
    toe = crest + height / math.tan(math.radians(original["slope"]))
    old_polygon = polygon(0, right, crest, toe, height, original["baseHeight"])
    new_polygon = polygon(-extension, right, crest, toe, height, depth)
    old_points, new_points = particles(original, 0, original["baseHeight"]), particles(new, extension, depth)
    old_set = set(map(tuple, old_points))
    added = np.array([tuple(p) not in old_set for p in new_points])
    assert len(old_points) == 105 and len(new_points) == 219 and added.sum() == 114
    assert old_set <= set(map(tuple, new_points))
    assert math.isclose(math.degrees(math.atan2(height, toe - crest)), 40)
    OUTPUT.mkdir(parents=True, exist_ok=False)
    (OUTPUT / ".gitattributes").write_text("** -text\n", encoding="utf-8")
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    for sampling in (False, True):
        fig, ax = plt.subplots(figsize=(14, 6.8), constrained_layout=True)
        ax.add_patch(Polygon(new_polygon, facecolor="#e6cd9e", edgecolor="#43392b", lw=2, label="Geometri baru"))
        ax.add_patch(Rectangle((-extension, -depth), extension, height + depth, color="#89c7df", alpha=.55, label="Tambahan tanah"))
        ax.add_patch(Rectangle((0, -depth), right, depth - original["baseHeight"], color="#89c7df", alpha=.55))
        ax.add_patch(Polygon(old_polygon, fill=False, edgecolor="#9a592c", lw=2, ls=(0, (5, 3)), label="Batas tanah lama"))
        ax.axhline(0, color="#555", lw=.8, ls=":")
        if sampling:
            ax.scatter(new_points[~added, 0], new_points[~added, 1], s=17, color="#66503d", zorder=4, label="105 titik lama")
            ax.scatter(new_points[added, 0], new_points[added, 1], s=21, color="#086c94", zorder=4, label="114 titik tambahan")
        ax.annotate("", xy=(-extension, 12), xytext=(0, 12), arrowprops={"arrowstyle": "<->", "color": "#086c94", "lw": 1.5})
        ax.text(-extension / 2, 12.6, "+12 m ke kiri", ha="center", color="#086c94", weight="bold")
        ax.annotate("", xy=(right + 3, 0), xytext=(right + 3, -depth), arrowprops={"arrowstyle": "<->", "lw": 1.5})
        ax.text(right + 3.6, -depth / 2, "8 m", rotation=90, va="center", weight="bold")
        ax.text(43, -2.4, "Lapisan bawah lama: 4 m", color="#7c4a24", ha="center")
        ax.text(35, -6.5, "Tambahan ketebalan: 4 m", color="#075b7c", ha="center")
        ax.annotate("", xy=(28, 0), xytext=(28, height), arrowprops={"arrowstyle": "<->", "lw": 1.2})
        ax.text(29, height / 2, "Tinggi lereng 10 m", va="center")
        ax.text((crest + toe) / 2 + 1, height / 2 + .6, "40°", rotation=-40, fontsize=14, weight="bold")
        ax.plot([crest, toe], [height, 0], "o", color="#43392b", ms=4)
        ax.annotate("", xy=(-extension, -10), xytext=(right, -10), arrowprops={"arrowstyle": "<->", "color": "#555"})
        ax.text((right - extension) / 2, -11.1, "Lebar keseluruhan 72 m", ha="center")
        ax.set(xlim=(-16, 68), ylim=(-12, 17), xlabel="x (m) — memakai patokan posisi model lama", ylabel="Elevasi (m) — kaki lereng = 0")
        ax.set_aspect("equal", adjustable="box")
        ax.set_xticks([-12, 0, 12, 24, 36, 48, 60])
        ax.set_yticks([-8, -4, 0, 4, 8, 12, 16])
        ax.grid(alpha=.13)
        title = "Preview susunan partikel: 105 → 219 titik" if sampling else "Preview geometri: kiri diperpanjang +12 m, lapisan bawah menjadi 8 m"
        ax.set_title(title + "\nSudut 40° dan tinggi 10 m tetap • belum menjalankan simulasi", pad=18, weight="bold")
        ax.legend(loc="upper right", frameon=True, fontsize=9, ncol=1)
        fig.text(.5, .01, "Warna hanya membedakan tambahan geometri; material tanah MC sama. Bukan hasil deformasi atau damage.", ha="center", fontsize=9, color="#555")
        fig.savefig(OUTPUT / ("particle-preview.png" if sampling else "geometry-preview.png"), dpi=150)
        plt.close(fig)
    area = lambda c: c["domainWidth"] * c["baseHeight"] + c["crestLength"] * height + .5 * height * (toe - crest)
    summary = {"status": "PREVIEW_ONLY_NO_SOLVER", "inputSources": [record(PROPOSAL), record(original_path), record(Path(__file__))],
               "oldWorldPolygon": old_polygon, "newWorldPolygon": new_polygon,
               "oldParticleCount": len(old_points), "newParticleCount": len(new_points), "addedParticles": int(added.sum()),
               "oldAreaM2": area(original), "newAreaM2": area(new), "previewConfigurationNotExecutable": new,
               "newWorldParticlePoints": new_points.tolist(),
               "futureImplementationNote": "Positive engine coordinates require x+12,y+8; new crestLength24/base8/domain72x24. Runtime geometry checks/metadata/cohort need coherent changes; this preview does not alter the actual case.",
               "unchangedOriginalPhysicalCohortInNewCoordinates": "x>14m and y>10m",
               "nativeCalls": 0, "mpmUpdates": 0, "outputs": [record(OUTPUT / "geometry-preview.png"), record(OUTPUT / "particle-preview.png")]}
    (OUTPUT / "preview-summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "oldParticles": len(old_points), "newParticles": len(new_points), "output": str(OUTPUT)}))


if __name__ == "__main__":
    main()
