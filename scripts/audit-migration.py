#!/usr/bin/env python3
"""Generate/check the P0 frozen Git inventory; never move or execute source.

The decisions are conservative target candidates from the architecture spec,
not semantic review. Native ASDF metadata is produced separately by
audit-asdf-metadata.lisp; missing/stale metadata is reported, never invented.

    python scripts/audit-migration.py
    python scripts/audit-migration.py --check
    python scripts/audit-migration.py --self-test
    python scripts/audit-migration.py --capture-baseline --baseline docs/architecture/inventory-next.json

The baseline is intentionally immutable. For a later checkpoint use --baseline
and --output with new paths after explicitly capturing a new Git inventory.
"""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "docs/architecture"
DECISIONS = {"KEEP", "MOVE_CANDIDATE", "SPLIT_REVIEW", "COMPATIBILITY",
             "PRESERVE_EVIDENCE", "OPTIONAL/NOT_LOADED", "BLOCKED", "NEW"}
REQUIRED = {"source_path", "target_path", "decision", "owner", "category",
            "current_asdf_systems", "public_symbols_or_entrypoints",
            "referencing_files_or_callers", "numerical_behavior_change_allowed",
            "required_tests", "evidence", "status", "actual_source_sha256"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")


def tracked_paths():
    return sorted(filter(None, git("ls-files", "-z").split("\0")))


def sha256(path):
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capture_baseline(path):
    if path.exists():
        raise SystemExit("Refusing to overwrite an immutable baseline; select a new --baseline path.")
    paths = tracked_paths()
    status = iter(filter(None, git("status", "--porcelain=v1", "-z", "--untracked-files=all").split("\0")))
    dirty, untracked = [], []
    for item in status:
        if item.startswith("?? "):
            untracked.append(item[3:])
        else:
            row = {"status": item[:2], "path": item[3:]}
            if "R" in item[:2] or "C" in item[:2]:
                row["original_path"] = next(status)
            dirty.append(row)
    value = {"schema_version": 1, "captured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
             "capture_head": git("rev-parse", "HEAD").strip(), "branch": git("branch", "--show-current").strip(),
             "tracked_count": len(paths), "tracked_paths": paths,
             "working_tree_source_sha256": {p: sha256(ROOT / p) for p in paths},
             "dirty_tracked": dirty, "untracked_files": untracked, "untracked_count": len(untracked),
             "scope_note": "git ls-files index capture; untracked paths are separate, ignored outputs/toolchain excluded. Baseline is immutable."}
    save_json(path, value)
    print(json.dumps({"baseline": str(path), "tracked_count": len(paths), "capture_head": value["capture_head"]}))
    return 0


def plan(decision, owner, category, *targets, reason="Architecture specification candidate; source inspection pending"):
    return dict(decision=decision, owner=owner, category=category,
                target_path=targets[0] if len(targets) == 1 else "MULTIPLE:" + ";".join(targets),
                target_candidates=[{"path": p, "rationale": reason} for p in targets],
                classification_basis=reason)


# Explicit mixed-file responsibilities: targets are candidates, not approved splits.
MIXED = {
    "src/particle.lisp": ("engine+materials", "base-particle-and-model-state", "src/core/", "materials/models/"),
    "src/constitutive.lisp": ("materials+engine", "constitutive-and-numerics", "materials/models/", "src/numerics/"),
    "src/cpp.lisp": ("engine+materials", "native-bridge", "src/numerics/native-bridge/", "materials/backends/cpp/"),
    "src/models/plastic.lisp": ("materials", "constitutive-model", "materials/models/plastic/von-mises/", "materials/models/plastic/mohr-coulomb/", "materials/models/plastic/drucker-prager/"),
    "src/models/visco.lisp": ("materials", "constitutive-model", "materials/models/viscoelastic/", "materials/models/viscoplastic/"),
    "src/models/damage.lisp": ("materials+engine", "material-and-generic-damage", "materials/models/", "src/damage/"),
    "src/cl-mpm.lisp": ("engine", "simulation-base", "src/core/", "src/simulation/"),
    "src/core.lisp": ("engine", "simulation-base", "src/core/", "src/simulation/"),
    "src/setup.lisp": ("engine", "setup-and-composition", "src/geometry/", "src/discretization/", "src/boundaries/", "src/simulation/"),
    "src/output.lisp": ("engine", "output", "src/output/"),
    "src/fastmaths.lisp": ("engine", "numerics", "src/numerics/"),
    "src/utils.lisp": ("engine", "numerics", "src/numerics/"),
    "framework/components/materials.lisp": ("materials", "material-factory", "materials/core/", "materials/adapters/"),
    "framework/components/diagnostics.lisp": ("materials+engine", "material-and-generic-diagnostics", "materials/diagnostics/", "src/measurements/"),
    "framework/components/geometry.lisp": ("engine", "geometry-components", "src/geometry/", "src/simulation/components/"),
    "framework/components/specifications.lisp": ("engine", "component-contracts", "src/simulation/components/", "materials/core/"),
    "framework/scenarios/triaxial/material.lisp": ("materials+scenarios", "constructor-and-prestress", "materials/core/", "scenarios/triaxial/initial-conditions.lisp"),
    "framework/scenarios/triaxial/measurements.lisp": ("scenarios+engine", "scenario-and-generic-measurements", "scenarios/triaxial/", "src/measurements/"),
    "framework/scenarios/triaxial/tensors.lisp": ("scenarios+engine", "scenario-and-generic-numerics", "scenarios/triaxial/", "src/numerics/"),
    "framework/scenarios/joss/classes.lisp": ("materials+scenarios", "chalk-state-and-scenario", "materials/models/chalk/", "scenarios/joss/"),
}


def classify(path):
    if path in MIXED:
        owner, category, *targets = MIXED[path]
        return plan("SPLIT_REVIEW", owner, category, *targets)
    p = PurePosixPath(path)
    if path.startswith("src/"):
        if path in {"src/models/elastic.lisp", "src/core/symbolic-derivation.lisp"}:
            return plan("OPTIONAL/NOT_LOADED", "materials" if "/models/" in path else "engine",
                        "unregistered-optional-source", "materials/models/elastic/" if "/models/" in path else "src/numerics/",
                        reason="No direct component membership observed in the native audited ASDF feature set; verify other loaders and preserve current activation state. Source inspection pending")
        if path.startswith("src/models/"):
            family = {"plastic": "plastic", "elastic": "elastic", "concrete": "concrete",
                      "chalk": "chalk", "ice": "ice", "limestone": "limestone",
                      "damage-frictional": "frictional-damage"}.get(p.stem)
            if family:
                return plan("MOVE_CANDIDATE", "materials", "constitutive-model", f"materials/models/{family}/{p.name}")
        if path.startswith("src/damage/"):
            return plan("SPLIT_REVIEW", "engine+materials", "generic-and-model-damage",
                        "src/damage/", "materials/models/*/evolution/", "src/parallel/", "src/output/")
        if path.startswith("src/dynamic-relaxation/"):
            if "/mpi/" in path:
                return plan("SPLIT_REVIEW", "engine", "solver-parallel-extension", "src/parallel/mpi/", "src/solvers/dynamic-relaxation/")
            if "/misc/" in path:
                return plan("SPLIT_REVIEW", "engine", "erosion-solver-extension", "src/boundaries/erosion/", "src/damage/")
            return plan("MOVE_CANDIDATE", "engine", "dynamic-relaxation", "src/solvers/dynamic-relaxation/" + path.split("src/dynamic-relaxation/", 1)[1])
        groups = [("src/mpi/", "src/parallel/", "parallel"), ("src/bc/", "src/boundaries/", "boundary"),
                  ("src/ssa/", "src/formulations/ssa/", "formulation"),
                  ("src/solvers/octree/", "src/formulations/octree/", "formulation-boundary-extension"),
                  ("src/solvers/", "src/solvers/explicit/", "explicit-solver")]
        for prefix, target, category in groups:
            if path.startswith(prefix):
                return plan("MOVE_CANDIDATE", "engine", category, target + path[len(prefix):])
        destinations = {
            "shape-function": "src/discretization/shape-functions/", "domain-update": "src/discretization/domain-update/",
            "splitting": "src/discretization/splitting/", "p2g": "src/transfer/", "g2p": "src/transfer/", "forces": "src/transfer/",
            "linear-solver": "src/solvers/linear-systems/", "symbolic-derivation": "src/numerics/",
            "implicit": "src/solvers/implicit/", "aggregate": "src/stabilization/aggregate/",
            "ghost": "src/discretization/ghost-nodes/", "eigenerosion": "src/damage/eigenerosion/", "mpi": "src/parallel/"}
        if p.stem in destinations:
            return plan("MOVE_CANDIDATE", "engine", "engine-module", destinations[p.stem] + p.name)
        if p.stem in {"mesh", "iterate", "iterate-test", "stress-update", "settings", "errors", "plotter"}:
            return plan("SPLIT_REVIEW", "engine", "engine-responsibility-review", "src/core/", "src/simulation/", "src/numerics/", "src/output/" if p.stem == "plotter" else "src/solvers/")
        return None
    if path.startswith("framework/"):
        if p.suffix == ".asd" or path == "framework/package.lisp":
            return plan("COMPATIBILITY", "compatibility", "asdf-and-package-entrypoint", path,
                        reason="Retain old system/package entrypoints until replacement loaders and all callers pass compatibility gates")
        if p.suffix == ".md":
            return plan("MOVE_CANDIDATE", "documentation", "framework-documentation", "docs/architecture/",
                        reason="Documentation target pending link/source review; retain original until transition")
        if path.startswith("framework/scenarios/"):
            target = path.removeprefix("framework/")
            decision = "COMPATIBILITY" if p.stem == "adapter" else "MOVE_CANDIDATE"
            return plan(decision, "scenarios", "scenario-procedure", target)
        if path.startswith("framework/config/"):
            return plan("MOVE_CANDIDATE", "engine", "simulation-config", path.replace("framework/config/", "src/simulation/config/", 1))
        if path == "framework/materials/chalk.lisp":
            return plan("MOVE_CANDIDATE", "materials", "chalk-state-evolution", "materials/models/chalk/" + p.name)
        if path == "framework/simulation.lisp":
            return plan("MOVE_CANDIDATE", "engine", "simulation-orchestration", "src/simulation/")
        if path == "framework/output/plotting.lisp":
            return plan("SPLIT_REVIEW", "engine+scripts", "runtime-or-analysis-plotting", "src/output/plotting/", "scripts/plotting/")
        return None
    if path.startswith("cases/"):
        scenario = "benchmarks" if p.stem == "joss-collapse" else "triaxial" if p.stem.startswith("triaxial") else "cliff"
        return plan("MOVE_CANDIDATE", "cases", "execution-recipe", f"cases/{scenario}/{p.name}")
    root = p.parts[0]
    policies = {
        "deps": ("KEEP", "third-party", "vendored-dependency"),
        "libs": ("KEEP", "native-libraries", "native-source-binary-or-build"),
        "docs": ("PRESERVE_EVIDENCE" if path.startswith(("docs/evidence/", "docs/archive/")) else "KEEP", "documentation", "evidence-or-documentation"),
        "research": ("PRESERVE_EVIDENCE", "research", "research-input-report-provenance"),
        "movies": ("PRESERVE_EVIDENCE", "historical-media", "historical-media"),
        "example_data": ("PRESERVE_EVIDENCE", "reference-data", "original-reference-data"),
        "examples": ("KEEP", "legacy-examples", "legacy-example"),
        "tutorial": ("KEEP", "legacy-tutorial", "legacy-tutorial"),
        "analysis_scripts": ("KEEP", "historical-analysis", "historical-analysis"),
        "calibration": ("COMPATIBILITY", "legacy-calibration", "calibration-entrypoint-or-config"),
        "studio": ("COMPATIBILITY", "studio", "existing-ui-compatibility"),
        "windows": ("KEEP", "windows-runtime", "windows-launcher-or-build"),
        "tests": ("KEEP", "tests", "existing-test-or-fixture"),
        "scripts": ("KEEP", "scripts", "audit-cli-or-automation"),
        "wiki-vault": ("KEEP", "knowledge-vault", "wiki-or-vault-instructions"),
        "config": ("KEEP", "repository", "repository-configuration"),
        ".agents": ("KEEP", "agent-instructions", "agent-skill"),
        ".github": ("KEEP", "ci", "ci-configuration"),
    }
    if root in policies:
        decision, owner, category = policies[root]
        return plan(decision, owner, category, path, reason="Preserve existing path and bytes in P0; no deletion or relocation authorized by this inventory")
    if len(p.parts) == 1 and (p.suffix == ".asd" or path in {".gitattributes", ".gitconfig", ".gitignore", "README.md", "AGENTS.md", "CLAUDE.md"}):
        return plan("COMPATIBILITY" if p.suffix == ".asd" else "KEEP", "repository", "asdf-entrypoint" if p.suffix == ".asd" else "repository-policy", path,
                    reason="Preserve repository policy, existing system names and compatibility entrypoints")
    return None


def read_text(path):
    # Large binary media and non-UTF8 files have no lexical reference scan.
    try:
        if path.stat().st_size > 5 * 1024 * 1024:
            return None
        value = path.read_text(encoding="utf-8-sig")
        return None if "\0" in value else value
    except (OSError, UnicodeError):
        return None


def literal_references(paths):
    """Exact tracked-path mentions only; this is deliberately not a call graph."""
    path_set = set(paths)
    roots = sorted({p.split("/")[0] for p in paths if "/" in p}, key=len, reverse=True)
    pattern = re.compile(r"(?<![\w./-])(?:" + "|".join(re.escape(r) for r in roots) + r")[/\\][A-Za-z0-9_.@+~/\\-]+")
    quoted = re.compile(r'[`"\']([^`"\'\r\n]+)[`"\']')
    refs = defaultdict(list)
    skipped = []
    for caller in paths:
        text = read_text(ROOT / caller)
        if text is None:
            skipped.append(caller)
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            candidates = {m.group(0).replace("\\", "/") for m in pattern.finditer(line)}
            for match in quoted.finditer(line):
                literal = match.group(1).replace("\\", "/")
                if "/" not in literal and not PurePosixPath(literal).suffix:
                    continue
                # Resolve only existing exact paths; no basename or symbol inference.
                candidates.add(literal)
                relative = PurePosixPath(caller).parent / literal
                candidates.add(posixpath.normpath(str(relative)))
            for target in sorted(candidates & path_set):
                if target != caller:
                    refs[target].append({"file": caller, "line": line_no, "kind": "literal-path-mention", "context": line.strip()[:300]})
    return refs, skipped


def asdf_members(metadata):
    membership = defaultdict(set)
    declarations = defaultdict(list)
    for system in metadata.get("systems", []):
        declarations[system["source_asd"]].append(system["name"])
        def walk(node):
            children = node.get("children", [])
            if children:
                for child in children:
                    walk(child)
            elif node.get("path", "").endswith(".lisp"):
                membership[node["path"]].add(system["name"])
        walk(system["component_tree"])
    return membership, declarations


def lexical_package_exports(text):
    """Read literal DEFPACKAGE/:EXPORT declarations, without a Lisp reader/eval.

    Reader conditionals are deliberately not evaluated. Computed names, package
    renaming, EXPORT calls and escaped |symbol| syntax are outside this scan.
    """
    tokens = []
    index, line = 0, 1
    while index < len(text):
        char = text[index]
        if char.isspace():
            line += char == "\n"
            index += 1
        elif char == ";":
            index = text.find("\n", index)
            if index < 0:
                break
        elif text.startswith("#|", index):
            depth = 1
            index += 2
            while index < len(text) and depth:
                if text.startswith("#|", index):
                    depth += 1
                    index += 2
                elif text.startswith("|#", index):
                    depth -= 1
                    index += 2
                else:
                    line += text[index] == "\n"
                    index += 1
        elif text.startswith("#\\", index):
            index += 2
            if index < len(text):
                index += 1
                while index < len(text) and not text[index].isspace() and text[index] not in "()":
                    index += 1
        elif char in "()":
            tokens.append((char, line))
            index += 1
        elif char == '"':
            start, start_line = index, line
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                elif text[index] == '"':
                    index += 1
                    break
                else:
                    line += text[index] == "\n"
                    index += 1
            tokens.append((text[start:index], start_line))
        else:
            start = index
            while index < len(text) and not text[index].isspace() and text[index] not in '();"':
                index += 1
            tokens.append((text[start:index], line))

    def name(value):
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1] if "\\" not in value else None
        value = value.removeprefix("#:").removeprefix(":")
        return value if value and not any(c in value for c in "|()'#") else None

    exports = []
    for i in range(len(tokens) - 2):
        if tokens[i][0] != "(" or tokens[i + 1][0].lower().split(":")[-1] != "defpackage":
            continue
        package = name(tokens[i + 2][0])
        if package is None:
            continue
        depth, cursor = 1, i + 3
        while cursor < len(tokens) and depth:
            token, token_line = tokens[cursor]
            if token == "(" and depth == 1 and cursor + 1 < len(tokens) and tokens[cursor + 1][0].lower() == ":export":
                entry = cursor + 2
                while entry < len(tokens) and tokens[entry][0] not in {"(", ")"}:
                    exported = name(tokens[entry][0])
                    if exported is not None:
                        exports.append({"symbol": package + ":" + exported, "line": tokens[entry][1],
                                        "kind": "lexical-defpackage-export", "runtime_visibility": "UNVERIFIED"})
                    entry += 1
            depth += (token == "(") - (token == ")")
            cursor += 1
    return exports


def public_entries(path, declarations):
    text = read_text(ROOT / path) if path.endswith((".lisp", ".asd")) else None
    exports = lexical_package_exports(text) if text is not None else []
    return (["ASDF system:" + name for name in declarations.get(path, [])]
            + [row["symbol"] for row in exports]), exports


def validated_approvals(path, baseline):
    document = load_json(path) if path.exists() else {}
    approved, errors = {}, []
    for item in document.get("approvals", []):
        source = item.get("source_path")
        problem = []
        if source in approved:
            problem.append("duplicate approval source")
        if source not in baseline["tracked_paths"]:
            problem.append("source not in frozen capture")
        if not isinstance(source, str) or sha256(ROOT / source) != item.get("source_sha256_before"):
            problem.append("current source does not match reviewed pre-extraction hash")
        if item.get("numerical_behavior_change_allowed") is not False:
            problem.append("numerical behavior must remain forbidden")
        if item.get("phase") != "P1" or item.get("decision") != "APPROVED_EXTRACTION_NOT_EXECUTED":
            problem.append("unsupported phase/approval state")
        reports = item.get("review_evidence", [])
        if not reports or any(not (ROOT / report).is_file() for report in reports):
            problem.append("missing review report")
        targets = item.get("targets", [])
        if not targets:
            problem.append("missing exact targets")
        for target in targets:
            target_path = target.get("path", "")
            forms = target.get("forms")
            if (not isinstance(target_path, str) or not target_path.endswith(".lisp") or "*" in target_path
                    or "\\" in target_path or ":" in target_path
                    or ".." in PurePosixPath(target_path).parts or PurePosixPath(target_path).is_absolute()
                    or not isinstance(forms, list) or not forms
                    or any(not isinstance(form, str) or not form.strip() for form in forms)
                    or not target.get("reason")):
                problem.append("target must name an exact relative Lisp path and reviewed form group/reason")
        if problem:
            errors.append({"source_path": source, "errors": problem})
        else:
            approved[source] = item
    return approved, errors


def overlay_approval(record, approval):
    targets = approval["targets"]
    record.update(target_path=targets[0]["path"] if len(targets) == 1 else "MULTIPLE:" + ";".join(t["path"] for t in targets),
                  target_candidates=[{"path": t["path"], "rationale": t["reason"], "top_level_forms": t["forms"]} for t in targets],
                  semantic_review="REVIEWED_FOR_P1_EXTRACTION_ONLY", status="APPROVED_EXTRACTION_NOT_EXECUTED",
                  evidence="Reviewed source hash and exact target/form groups in MIGRATION_APPROVALS.json; review reports: " + ", ".join(approval["review_evidence"]) + ". Extraction and native/regression tests NOT_RUN.",
                  migration_approval=approval, test_status="NOT_RUN")


def delta_records(paths, output, approvals, declarations):
    approved_targets = {target["path"] for approval in approvals.values() for target in approval["targets"]}
    records = []
    for path in paths:
        classification = classify(path)
        if classification is None and path in approved_targets:
            classification = plan("KEEP", "materials" if path.startswith("materials/") else "engine",
                                  "reviewed-P1-target", path, reason="Exact target in validated P1 extraction plan; implementation validation pending")
        classification = classification or plan("BLOCKED", "UNCLASSIFIED", "UNCLASSIFIED", path, reason="New tracked source has no owner classification; block migration")
        entries, lexical = public_entries(path, declarations)
        is_self = (ROOT / path).resolve() == output
        records.append({"source_path": path, **classification, "decision": "NEW", "planned_decision": classification["decision"],
                        "public_symbols_or_entrypoints": entries, "lexical_export_declarations": lexical,
                        "numerical_behavior_change_allowed": False, "semantic_review": "PENDING",
                        "status": "NEW_TRACKED_PATH_CLASSIFIED_PENDING_REVIEW", "required_tests": required_tests(path, classification["category"]),
                        "actual_source_sha256": None if is_self else sha256(ROOT / path),
                        "hash_status": "SELF_REFERENTIAL_MANIFEST_EXCLUDED" if is_self else "SHA256_WORKING_TREE_BYTES",
                        "evidence": "Separate live-index delta, excluded from immutable 884-path capture. Owner/category classification is not semantic approval."})
    return records


def required_tests(path, category):
    if path.startswith(("src/", "framework/", "libs/", "cases/")):
        return ["ASDF/package/loader compatibility before any move", "focused native engine/material contracts relevant to changed forms", "unchanged frozen-source numerical regressions and CSV/VTK checks if source is moved/split; NOT_RUN in P0"]
    if path.startswith(("studio/", "windows/", "calibration/")) or path.endswith(".asd"):
        return ["existing entrypoint/loader compatibility before change", "studio npm run check and npm test if Node/Studio is affected; NOT_RUN in P0"]
    return ["preserve bytes and provenance; exact-path/link audit before any future change"]


def completeness(paths, records):
    counts = Counter(r.get("source_path") for r in records)
    expected = set(paths)
    missing = sorted(expected - counts.keys())
    extra = sorted(counts.keys() - expected)
    duplicate = sorted(p for p, n in counts.items() if n != 1)
    invalid = []
    unclassified = []
    for row in records:
        path = row.get("source_path")
        if row.get("category") == "UNCLASSIFIED":
            unclassified.append(path)
        digest = row.get("actual_source_sha256")
        if (REQUIRED - row.keys() or row.get("decision") not in DECISIONS
                or row.get("numerical_behavior_change_allowed") is not False
                or not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None):
            invalid.append(path)
    return {"expected_count": len(paths), "record_count": len(records), "unique_count": len(counts),
            "missing_paths": missing, "extra_paths": extra, "duplicate_paths": duplicate,
            "invalid_records": invalid, "UNCLASSIFIED": sorted(unclassified),
            "complete_exactly_once": not (missing or extra or duplicate or invalid or len(records) != len(paths))}


def generate(args):
    baseline = load_json(args.baseline)
    paths = baseline["tracked_paths"]
    metadata = load_json(args.asdf_metadata) if args.asdf_metadata.exists() else {}
    membership, declarations = asdf_members(metadata)
    approvals, approval_errors = validated_approvals(args.approvals, baseline)
    current = set(tracked_paths())
    new_paths = sorted(current - set(paths))
    removed_paths = sorted(set(paths) - current)
    excluded_manifests = {str(p.relative_to(ROOT)).replace("\\", "/") for p in (args.output, args.baseline, args.asdf_metadata)}
    references, skipped = literal_references(sorted((set(paths) | current) - excluded_manifests))
    records = []
    hashes_changed = []
    for path in paths:
        classification = classify(path) or plan("BLOCKED", "UNCLASSIFIED", "UNCLASSIFIED", path, reason="No classification rule; review before migration")
        digest = sha256(ROOT / path)
        if digest != baseline["working_tree_source_sha256"].get(path):
            hashes_changed.append(path)
        systems = sorted(membership[path])
        entries, lexical = public_entries(path, declarations)
        record = {"source_path": path, **classification, "current_asdf_systems": systems,
                  "public_symbols_or_entrypoints": entries, "lexical_export_declarations": lexical,
                  "referencing_files_or_callers": references[path], "numerical_behavior_change_allowed": False,
                  "required_tests": required_tests(path, classification["category"]),
                  "evidence": "Path classification only; source inspection pending. Actual ASDF definition registration where listed; literal path mentions are not verified dynamic callers.",
                  "status": "NOT_STARTED" if classification["decision"] in {"MOVE_CANDIDATE", "SPLIT_REVIEW", "BLOCKED"} else "PRESERVE_PENDING_VERIFICATION",
                  "actual_source_sha256": digest, "baseline_source_sha256": baseline["working_tree_source_sha256"].get(path),
                  "capture_head": baseline["capture_head"], "semantic_review": "PENDING",
                  "asdf_membership_evidence": "native registration; not proof of load" if systems else "no component membership observed in audited native definition metadata; not proof of disuse"}
        for name in systems:
            source_asd = next(system["source_asd"] for system in metadata["systems"] if system["name"] == name)
            record["referencing_files_or_callers"].append({"file": source_asd, "kind": "native-ASDF-component-registration", "system": name})
        if path in approvals:
            overlay_approval(record, approvals[path])
        records.append(record)
    coverage = completeness(paths, records)
    active_roots = {"src", "materials", "framework", "cases", "studio", "windows", "calibration", "scripts", "tests", "libs"}
    active_paths = {p for p in paths if p.split("/")[0] in active_roots or ("/" not in p and p.endswith(".asd"))}
    coverage["active_path_definition"] = "All captured paths under src/materials/framework/cases/studio/windows/calibration/scripts/tests/libs, plus root ASD files; conservative path-based migration gate, not runtime reachability"
    coverage["active_path_count"] = len(active_paths)
    coverage["UNCLASSIFIED_active"] = sorted(active_paths & set(coverage["UNCLASSIFIED"]))
    delta = delta_records(new_paths, args.output, approvals, declarations)
    delta_unknown = sorted(r["source_path"] for r in delta if r["category"] == "UNCLASSIFIED")
    delta_unknown_active = sorted(p for p in delta_unknown if p.split("/")[0] in active_roots or p.endswith(".asd"))
    warnings = ["P0 inventory is not semantic review, move approval, runtime loading proof, numerical equivalence or scientific validation.",
                "All proposed moves/splits require per-form ownership review and the stated compatibility/regression gates before mutation."]
    if coverage["UNCLASSIFIED"]:
        warnings.append("BLOCK bulk migration: UNCLASSIFIED paths remain, including any active paths named in UNCLASSIFIED_active.")
    if new_paths or removed_paths:
        warnings.append("Tracked paths differ from frozen capture; separate NEW delta records classify additions; checkpoint/review delta before any future migration.")
    if delta_unknown or approval_errors:
        warnings.append("BLOCK dependent migration: unknown delta classifications or invalid/stale P1 approvals remain.")
    if hashes_changed:
        warnings.append("Working-tree bytes changed after baseline capture; consult changed_since_baseline.")
    if not metadata or metadata.get("errors"):
        warnings.append("Native ASDF metadata missing or incomplete; do not infer loaders/dependencies.")
    result = {"schema_version": 1, "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "capture_head": baseline["capture_head"], "capture_branch": baseline["branch"],
              "baseline": str(args.baseline.relative_to(ROOT)), "tracked_count_at_capture": len(paths),
              "dirty_tracked_at_capture": baseline["dirty_tracked"], "untracked_files_at_capture": baseline["untracked_files"],
              "completeness": coverage, "root_counts": dict(sorted(Counter(p.split("/")[0] for p in paths).items())),
              "current_tracked_delta": {"new_paths_requiring_NEW_register": [], "new_paths_classified_NEW": new_paths, "removed_paths": removed_paths,
                                        "UNCLASSIFIED": delta_unknown, "UNCLASSIFIED_active": delta_unknown_active,
                                        "records": delta, "self_hash_policy": "The output manifest alone has no in-manifest source hash; hash it externally after generation. All other delta paths are hashed."},
              "changed_since_baseline": hashes_changed, "decision_counts": dict(sorted(Counter(r["decision"] for r in records).items())),
              "semantic_review_pending_count": sum(r["semantic_review"] == "PENDING" for r in records),
              "reviewed_P1_source_count": len(approvals), "migration_ready": False, "warnings": warnings,
              "approval_input": {"file": str(args.approvals.relative_to(ROOT)), "sha256": sha256(args.approvals), "validation_errors": approval_errors,
                                 "review_report_sha256": {p: sha256(ROOT / p) for item in approvals.values() for p in item["review_evidence"]}},
              "asdf_metadata": {"file": str(args.asdf_metadata.relative_to(ROOT)), "sha256": sha256(args.asdf_metadata),
                                "mode": metadata.get("mode", "MISSING"), "system_count": len(metadata.get("systems", [])),
                                "errors": metadata.get("errors", []), "definition_source_sha256": {p: sha256(ROOT / p) for p in metadata.get("definitions_requested", [])},
                                "registered_components_missing_from_capture": sorted(set(membership) - set(paths))},
              "limitations": ["current_asdf_systems lists direct registered component ownership only. Dependencies/order are in asdf-metadata.json; transitive ownership is not assigned to every dependency caller.",
                              "Native Windows feature set only. Conditional MPI/non-Windows branches and ASDF connections not activated by this feature set may be absent; no operation plan/source system was loaded.",
                              "Public-symbol entries include actual ASDF system entrypoints and literal DEFPACKAGE/:EXPORT declarations with source lines. Lexical declarations do not prove runtime export availability; reader conditionals/discards and quoted code are not evaluated, computed EXPORT/package aliases/escaped symbol syntax are not resolved. Class/method ownership remains a separate semantic audit.",
                              "References are exact literal tracked-path mentions or actual ASDF registrations, including documentation/comment mentions; dynamic paths, symbol calls, generated paths and ambiguous short paths are not inferred.",
                              "Lexical path scan skips files larger than 5 MiB, binary/NUL and non-UTF8 files; hashes still cover their full bytes.",
                              "This matrix covers the immutable capture, not ignored outputs/toolchain or untracked files. Recheck live index delta after checkpoint.",
                              "target_candidates are provisional except the two hash-validated P1 approval overlays, which name reviewed exact targets/forms. Approval is not extraction execution, native tests, regression PASS or permission for bulk migration."],
              "lexical_reference_scan_skipped": skipped, "reference_scan_generated_manifests_excluded": sorted(excluded_manifests), "records": records}
    if args.output.exists():
        previous = load_json(args.output)
        if ({k: v for k, v in previous.items() if k != "generated_at_utc"}
                == {k: v for k, v in result.items() if k != "generated_at_utc"}):
            result["generated_at_utc"] = previous["generated_at_utc"]
    save_json(args.output, result)
    print(json.dumps({"output": str(args.output), "head": baseline["capture_head"], "coverage": coverage,
                      "decision_counts": result["decision_counts"], "native_asdf_systems": len(metadata.get("systems", [])),
                      "changed_since_baseline": hashes_changed, "reviewed_P1_sources": len(approvals), "approval_errors": approval_errors,
                      "NEW_delta_count": len(delta), "UNCLASSIFIED_delta_active": delta_unknown_active, "migration_ready": False}, indent=2))
    return 0 if coverage["complete_exactly_once"] and not coverage["UNCLASSIFIED"] and not delta_unknown and not approval_errors else 2


def check(args):
    baseline, matrix = load_json(args.baseline), load_json(args.output)
    coverage = completeness(baseline["tracked_paths"], matrix["records"])
    stale = [r["source_path"] for r in matrix["records"] if sha256(ROOT / r["source_path"]) != r["actual_source_sha256"]]
    delta = sorted(set(tracked_paths()) ^ set(baseline["tracked_paths"]))
    metadata_stale = sha256(args.asdf_metadata) != matrix["asdf_metadata"]["sha256"]
    definitions_stale = [p for p, h in matrix["asdf_metadata"]["definition_source_sha256"].items() if sha256(ROOT / p) != h]
    metadata_missing_or_failed = not matrix["asdf_metadata"]["system_count"] or bool(matrix["asdf_metadata"]["errors"])
    provenance_mismatch = matrix["capture_head"] != baseline["capture_head"]
    approvals, approval_errors = validated_approvals(args.approvals, baseline)
    approval_stale = sha256(args.approvals) != matrix["approval_input"]["sha256"]
    review_reports_stale = [p for p, h in matrix["approval_input"]["review_report_sha256"].items() if sha256(ROOT / p) != h]
    delta_rows = matrix["current_tracked_delta"]["records"]
    new_current = set(tracked_paths()) - set(baseline["tracked_paths"])
    delta_paths = [r["source_path"] for r in delta_rows]
    delta_registration_complete = set(delta_paths) == new_current and len(delta_paths) == len(set(delta_paths))
    delta_stale = [r["source_path"] for r in delta_rows if r["hash_status"] != "SELF_REFERENTIAL_MANIFEST_EXCLUDED" and sha256(ROOT / r["source_path"]) != r["actual_source_sha256"]]
    delta_unknown = [r["source_path"] for r in delta_rows if r["category"] == "UNCLASSIFIED"]
    valid = (coverage["complete_exactly_once"] and not coverage["UNCLASSIFIED"] and not stale
             and not metadata_stale and not definitions_stale and not metadata_missing_or_failed and not provenance_mismatch
             and not approval_stale and not approval_errors and not review_reports_stale
             and delta_registration_complete and not delta_stale and not delta_unknown)
    print(json.dumps({"frozen_capture_valid": valid, "coverage": coverage, "stale_source_hashes": stale,
                      "stale_asdf_metadata": metadata_stale, "stale_asdf_definitions": definitions_stale,
                      "metadata_missing_or_failed": metadata_missing_or_failed, "capture_head_mismatch": provenance_mismatch,
                      "live_index_delta_requires_classification_before_moves": delta,
                      "NEW_delta_registration_complete": delta_registration_complete, "UNCLASSIFIED_delta": delta_unknown,
                      "stale_delta_hashes": delta_stale, "stale_approval_input": approval_stale,
                      "stale_review_reports": review_reports_stale, "approval_errors": approval_errors,
                      "semantic_review_pending": matrix["semantic_review_pending_count"], "migration_ready": False}, indent=2))
    return 0 if valid else 2


class IntegrityTests(unittest.TestCase):
    def record(self, path):
        return {**{key: [] for key in REQUIRED}, "source_path": path, "decision": "KEEP",
                "category": "preserved", "numerical_behavior_change_allowed": False,
                "actual_source_sha256": "0" * 64}

    def test_exact_capture(self):
        self.assertTrue(completeness(["a", "b"], [self.record("b"), self.record("a")])["complete_exactly_once"])

    def test_duplicate_cannot_mask_missing(self):
        result = completeness(["a", "b"], [self.record("a"), self.record("a")])
        self.assertFalse(result["complete_exactly_once"])
        self.assertEqual(result["duplicate_paths"], ["a"])
        self.assertEqual(result["missing_paths"], ["b"])

    def test_untracked_cannot_replace_tracked(self):
        result = completeness(["a"], [self.record("local-only")])
        self.assertEqual(result["extra_paths"], ["local-only"])
        self.assertFalse(result["complete_exactly_once"])

    def test_numerical_change_rejected(self):
        row = self.record("a")
        row["numerical_behavior_change_allowed"] = True
        self.assertFalse(completeness(["a"], [row])["complete_exactly_once"])

    def test_missing_schema_rejected(self):
        row = self.record("a")
        del row["actual_source_sha256"]
        self.assertFalse(completeness(["a"], [row])["complete_exactly_once"])

    def test_missing_source_hash_rejected(self):
        row = self.record("a")
        row["actual_source_sha256"] = None
        self.assertFalse(completeness(["a"], [row])["complete_exactly_once"])

    def test_unknown_source_is_blocked(self):
        self.assertIsNone(classify("src/unreviewed-new-model.lisp"))
        self.assertEqual(classify("deps/magicl/LICENSE.txt")["decision"], "KEEP")
        self.assertEqual(classify("src/models/plastic.lisp")["decision"], "SPLIT_REVIEW")

    def approval_fixture(self, root):
        source, report = root / "framework/source.lisp", root / "docs/review.md"
        source.parent.mkdir(parents=True)
        report.parent.mkdir(parents=True)
        source.write_text("(defclass component () ())\n", encoding="utf-8")
        report.write_text("Reviewed fixture only.\n", encoding="utf-8")
        approval = {"source_path": "framework/source.lisp", "source_sha256_before": sha256(source),
                    "phase": "P1", "decision": "APPROVED_EXTRACTION_NOT_EXECUTED",
                    "review_evidence": ["docs/review.md"], "numerical_behavior_change_allowed": False,
                    "targets": [{"path": "materials/core/fixture.lisp", "forms": ["component"], "reason": "fixture group"}]}
        return root / "approval.json", {"approvals": [approval]}, {"tracked_paths": ["framework/source.lisp"]}

    def test_lexical_exports_exclude_comments_and_never_claim_runtime(self):
        text = ('; (defpackage :comment (:export #:wrong))\n'
                '#| (defpackage :block (:export #:wrong)) #| nested |# |#\n'
                '(defpackage :sample (:export #:yes "mixedCase"))\n'
                '#+unverified-feature (defpackage :conditional (:export #:candidate))\n')
        rows = lexical_package_exports(text)
        self.assertEqual([r["symbol"] for r in rows], ["sample:yes", "sample:mixedCase", "conditional:candidate"])
        self.assertTrue(all(r["runtime_visibility"] == "UNVERIFIED" and r["kind"] == "lexical-defpackage-export" for r in rows))

    def test_stale_approval_hash_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, value, baseline = self.approval_fixture(root)
            save_json(path, value)
            (root / "framework/source.lisp").write_text("(defclass changed () ())\n", encoding="utf-8")
            with mock.patch.dict(globals(), {"ROOT": root}):
                approved, errors = validated_approvals(path, baseline)
            self.assertFalse(approved)
            self.assertIn("current source does not match reviewed pre-extraction hash", errors[0]["errors"])

    def test_duplicate_approval_source_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, value, baseline = self.approval_fixture(root)
            value["approvals"].append(dict(value["approvals"][0]))
            save_json(path, value)
            with mock.patch.dict(globals(), {"ROOT": root}):
                _, errors = validated_approvals(path, baseline)
            self.assertIn("duplicate approval source", errors[0]["errors"])

    def test_invalid_target_paths_rejected(self):
        for target in ("../escape.lisp", "/absolute.lisp", "C:/absolute.lisp", "materials/*.lisp", "materials\\ambiguous.lisp"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                path, value, baseline = self.approval_fixture(root)
                value["approvals"][0]["targets"][0]["path"] = target
                save_json(path, value)
                with mock.patch.dict(globals(), {"ROOT": root}):
                    approved, errors = validated_approvals(path, baseline)
                self.assertFalse(approved)
                self.assertTrue(any("exact relative Lisp path" in message for message in errors[0]["errors"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline", type=Path, default=ARCH / "inventory-baseline.json")
    parser.add_argument("--output", type=Path, default=ARCH / "FILE_MIGRATION_MATRIX.json")
    parser.add_argument("--asdf-metadata", type=Path, default=ARCH / "asdf-metadata.json")
    parser.add_argument("--approvals", type=Path, default=ARCH / "MIGRATION_APPROVALS.json", help="optional hash-bound, source-specific P1 review overlays")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--capture-baseline", action="store_true", help="capture to a NEW baseline path; never overwrite")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IntegrityTests)).wasSuccessful() else 2
    for key in ("baseline", "output", "asdf_metadata", "approvals"):
        value = getattr(args, key)
        setattr(args, key, value.resolve() if value.is_absolute() else (ROOT / value).resolve())
    if args.capture_baseline:
        return capture_baseline(args.baseline)
    return check(args) if args.check else generate(args)


if __name__ == "__main__":
    sys.exit(main())
