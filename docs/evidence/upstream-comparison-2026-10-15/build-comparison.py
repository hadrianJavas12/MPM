"""Rebuild the Git-only upstream comparison; no tests or simulations are run."""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
UPSTREAM = "d8e65543c55634b54b9d8edf2a6bcf6082415bdc"
FORK = "f7fb2a3322eabf483b3d6cedd2c090b356ca01ca"


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.quotepath=false", *args], cwd=ROOT
    ).decode("utf-8").replace("\r\n", "\n")


def write(name: str, value: str) -> None:
    (OUT / name).write_text(value, encoding="utf-8", newline="\n")


def write_json(name: str, value: object) -> None:
    write(name, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def tree(ref: str) -> dict[str, dict[str, str]]:
    result = {}
    for entry in git("ls-tree", "-r", ref).splitlines():
        info, path = entry.split("\t", 1)
        mode, obj_type, oid = info.split(" ")
        result[path] = {"mode": mode, "type": obj_type, "gitBlob": oid}
    return result


def category(path: str) -> str:
    if path.startswith("deps/"):
        return "vendored-dependencies"
    if path.startswith("studio/"):
        return "studio-controller"
    if path.startswith("windows/") or path == "libs/kirchoff.dll":
        return "windows-runtime"
    if path.startswith("src/") or path == "cl-mpm.asd":
        return "engine-output-and-platform-adapter"
    if path.startswith("examples/"):
        return "upstream-example-compatibility"
    if path.startswith("scripts/"):
        return "verification-and-rendering-scripts"
    if path.startswith("docs/evidence/"):
        return "retained-experimental-evidence"
    if path.startswith("docs/") or path == "README.md":
        return "project-documentation"
    if path.startswith("wiki-vault/"):
        return "knowledge-vault"
    return "repository-governance-and-ci"


def main() -> None:
    before, after = tree(UPSTREAM), tree(FORK)
    changed = []
    for line in git("diff", "--no-renames", "--numstat", UPSTREAM, FORK).splitlines():
        added, deleted, path = line.split("\t", 2)
        status = "A" if path not in before else "D" if path not in after else "M"
        changed.append({
            "path": path,
            "status": status,
            "category": category(path),
            "binary": added == "-",
            "addedLines": None if added == "-" else int(added),
            "deletedLines": None if deleted == "-" else int(deleted),
            "upstreamBlob": before.get(path, {}).get("gitBlob"),
            "forkBlob": after.get(path, {}).get("gitBlob"),
        })
    summaries = defaultdict(lambda: {
        "files": 0, "statuses": Counter(), "binaryFiles": 0,
        "addedTextLines": 0, "deletedTextLines": 0,
    })
    for item in changed:
        record = summaries[item["category"]]
        record["files"] += 1
        record["statuses"][item["status"]] += 1
        record["binaryFiles"] += int(item["binary"])
        record["addedTextLines"] += item["addedLines"] or 0
        record["deletedTextLines"] += item["deletedLines"] or 0
    preserved = []
    for prefix in ["src/", "src/core/", "src/models/", "src/damage/", "src/dynamic-relaxation/", "examples/", "libs/"]:
        paths = [p for p in before if p.startswith(prefix)]
        preserved.append({
            "prefix": prefix, "upstreamFiles": len(paths),
            "identicalBlobsAtSamePath": sum(before[p] == after.get(p) for p in paths),
            "modifiedOriginalPaths": [p for p in paths if p in after and before[p] != after[p]],
            "removedOriginalPaths": [p for p in paths if p not in after],
            "addedPaths": [p for p in after if p.startswith(prefix) and p not in before],
        })
    proof_paths = [
        "src/core.lisp", "src/core/stress-update.lisp", "src/core/domain-update.lisp",
        "src/aggregate.lisp", "src/models/chalk.lisp", "src/damage/damage.lisp",
        "src/damage/solver.lisp", "examples/chalk/joss.lisp", "libs/src/constitutive.h",
    ]
    proofs = [{"path": p, "upstream": before.get(p), "fork": after.get(p),
               "byteIdenticalInGit": p in before and before[p] == after.get(p)}
              for p in proof_paths]
    provenance = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "comparisonKind": "fixed-commit tree comparison; working tree changes excluded",
        "upstream": {"repository": "https://github.com/samjvsutcliffe/cl-mpm.git", "commit": UPSTREAM,
                     "refFetchedByParent": "refs/remotes/upstream-audit/main",
                     "metadata": git("show", "-s", "--format=%H%n%aI%n%cI%n%s", UPSTREAM).splitlines()},
        "fork": {"repository": "https://github.com/hadrianJavas12/MPM.git", "commit": FORK,
                 "metadata": git("show", "-s", "--format=%H%n%aI%n%cI%n%s", FORK).splitlines()},
        "mergeBase": git("merge-base", UPSTREAM, FORK).strip(),
        "ancestryCountsUpstreamOnlyForkOnly": [int(v) for v in git("rev-list", "--left-right", "--count", f"{UPSTREAM}...{FORK}").split()],
        "originalTreeFiles": len(before), "forkTreeFiles": len(after),
        "unchangedOriginalFiles": sum(v == after.get(p) for p, v in before.items()),
        "changedFiles": len(changed), "statuses": dict(Counter(i["status"] for i in changed)),
        "binaryFiles": sum(i["binary"] for i in changed),
        "addedTextLines": sum(i["addedLines"] or 0 for i in changed),
        "deletedTextLines": sum(i["deletedLines"] or 0 for i in changed),
        "categoryRule": "first matching rule in build-comparison.py; each changed path belongs to exactly one category",
        "categories": dict(summaries), "preservedPrefixes": preserved,
        "selectedIdentityProofs": proofs,
        "exclusions": ["new task changes after f7fb2a3", "untracked files", "git-ignored output and toolchain", "separate modular preset branch / draft PR #6"],
        "executionScope": "Git metadata and file hashes only. This script does not run Node tests, SBCL, or simulations.",
    }
    write_json("comparison.json", provenance)
    write_json("changed-files.json", changed)
    for name, options in [
        ("name-status.tsv", ["--name-status", "--no-renames"]),
        ("numstat.tsv", ["--numstat", "--no-renames"]),
        ("diff-stat.txt", ["--stat", "--no-renames"]),
        ("diff-summary.txt", ["--shortstat", "--no-renames"]),
    ]:
        write(name, git("diff", *options, UPSTREAM, FORK))
    write("modified-original-source.patch", git("diff", "--no-ext-diff", UPSTREAM, FORK, "--",
          "cl-mpm.asd", "examples/chalk/chalk.lisp", "src/output.lisp"))
    write("upstream-README.md", git("show", f"{UPSTREAM}:README.md"))
    evidence_paths = [
        "output/windows-verification-2026-10-14/output-parity.json",
        "output/windows-verification-2026-10-14/config-parity.json",
        "docs/evidence/joss-collapse-2026-10-15/validation/validation-summary.json",
        "docs/evidence/joss-collapse-2026-10-15/accepted/final-shape-comparison.json",
        "docs/evidence/scientific-audit-2026-10-15/forensic-artifacts-summary.json",
        "docs/evidence/scientific-audit-2026-10-15/forensic-visual-audit.json",
        "docs/evidence/scientific-audit-2026-10-15/fresh-replay-audit.json",
        "output/calibration-development-2026-10-15/live-github-status.json",
    ]
    retained = []
    for path in evidence_paths:
        src = ROOT / path
        if not src.is_file():
            retained.append({"source": path, "presentAtBuild": False})
            continue
        data = src.read_bytes()
        target = f"source-{src.name}"
        (OUT / target).write_bytes(data)
        retained.append({"source": path, "retainedAs": target, "presentAtBuild": True,
                         "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_json("retained-source-index.json", retained)
    files = [{"path": p.name, "bytes": p.stat().st_size,
              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"]
    write_json("manifest.json", {"algorithm": "SHA-256", "files": files})
    print(json.dumps({k: provenance[k] for k in ["changedFiles", "statuses", "binaryFiles", "addedTextLines", "deletedTextLines", "categories", "preservedPrefixes"]}, indent=2))


if __name__ == "__main__":
    main()
