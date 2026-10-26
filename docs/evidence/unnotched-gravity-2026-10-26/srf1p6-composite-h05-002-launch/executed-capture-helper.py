"""SOURCE ONLY / NOT_RUN: fresh repaired h0.5 attempt002 profile.

Restore directly to D:/MPM/.tmp/capture-gravity-composite-h05-repair-launch.py.
Reuse immutable attempt001 preparation/capture functions; never launch/query/test.
Root reviews the committed profile and closed gates before any preparation/run.
"""
import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
SUPPORT = ROOT / "research/notes/unnotched-landslide-2026-10-24/support"
ORIGINAL_HELPER = ROOT / ".tmp/capture-gravity-composite-h05-launch.py"
RAW = ROOT / "output/mc-composite-apex-2026-10-26"
OLD_FINE = RAW / "srf1p6-composite-h05-001"
GATE = RAW / "fine-repair-controls-001"
INDEX = ROOT / "docs/evidence/mc-composite-apex-2026-10-26/composite-apex-repair-gates-001/artifact-index.json"
DIAGNOSTICS = "source/materials/models/plastic/mc-composite-apex/diagnostics.lisp"
CHANGED = {"source/cl-mpm.asd", "source/materials/models/plastic/mc-composite-apex/package.lisp",
           "source/materials/models/plastic/mc-composite-apex/projection.lisp"}
GATES = ("stable-math-001", "stable-regression-001", "capture-controls-001", "fine-repair-controls-001")
CAPTURE_GROUPS = {"helper-preserves-condition-and-owns-json-tree",
    "synthetic-analytic-rejection-captures-named-checks", "optional-in-memory-and-json-replay",
    "strict-and-optional-replay-variant-firewall", "base-and-detailed-capture-failures-preserve-original-error",
    "native-rejection-preserves-complete-state-and-external-strain",
    "successful-return-does-not-build-diagnostic", "delegated-strict-condition-is-untouched"}
REPAIR = dict(previousRun=str(OLD_FINE), previousStatus="FAILED_NATIVE",
    previousLastSavedTimeS=5.2, previousSavedStates=53,
    actualFailedTrialCapsuleAvailable=False, actualFailedTrialReplayed=False,
    rationale="Synthetic false-work-rejection class demonstrated; symmetric pair-difference deviator is algebraically equal. Original mean/q/branch/law/checks/tolerances retained; optional failure-only owned diagnostics added.",
    changes=sorted(CHANGED), addedSource=DIAGNOSTICS,
    physicalInputsChanged=False, identicalRestart=False, restartFromSavedState=False,
    initialState="Fresh original zero-stress/zero-velocity initial state, same6s/SRF1.6/h0.5",
    failureCauseLimit="Missing actual failed trial/predicate remains unavailable; synthetic witness is not actual cause proof.",
    trajectoryLimit="New evaluation can round apex fields differently; no identity with the old5.2s trajectory is promised.",
    stopRule="One fresh repaired attempt; no SRF/grid/duration/strength/psi/tolerance escalation; registered observers and physical limits remain.")


def load_profile():
    if ORIGINAL_HELPER.read_bytes() != (SUPPORT / "capture-composite-h05-launch.py.txt").read_bytes():
        raise RuntimeError("Original h05 helper differs from its immutable archive")
    staged = RAW / "srf1p6-composite-h05-002-launch-preparation/helper-source-checkpoint/capture-composite-h05-launch.py.txt"
    if staged.exists() and ORIGINAL_HELPER.read_bytes() != staged.read_bytes():
        raise RuntimeError("Original imported h05 helper changed after preparation")
    spec = importlib.util.spec_from_file_location("_immutable_h05_attempt001", ORIGINAL_HELPER)
    profile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profile)
    # Change only this imported module's profile values, never historical files.
    profile.SHARED_ARCHIVES["capture-composite-h05-launch.py.txt"] = ORIGINAL_HELPER
    profile.SHARED_ARCHIVES["capture-composite-h05-repair-launch.py.txt"] = SELF
    profile.__file__ = str(SELF)
    profile.NAME = "srf1p6-composite-h05-002"
    profile.RUN = RAW / profile.NAME
    profile.STAGE = RAW / (profile.NAME + "-launch-preparation")
    profile.PACKET = ROOT / "docs/evidence/unnotched-gravity-2026-10-26" / (profile.NAME + "-launch")
    profile.NATIVE_GATE, profile.NATIVE_INDEX = GATE, INDEX
    profile.FROZEN_ANALYSIS += ("docs/benchmarks/COMPOSITE_APEX_ROUNDOFF_REPAIR.md",
        "tests/materials/mc-composite-apex-stable-math.protocol.json")
    profile.FROZEN_ANALYSIS += tuple(key.removeprefix("source/") for key in sorted(CHANGED | {DIAGNOSTICS}))
    original_frozen_sources = profile.frozen_sources
    def including_diagnostic_load(run, reviewer, h, require):
        rows, proof = original_frozen_sources(run, reviewer, h, require)
        if DIAGNOSTICS in rows:
            actions = h.read_json(run / "source-provenance.json")["verifiedAsdfActions"]
            loaded = {Path(a["source"]).resolve() for a in actions if a.get("firstParty")
                      and a.get("operation") == "load-op" and a.get("event") == "performing"}
            require((run / DIAGNOSTICS).resolve() in loaded, "Actual repaired native diagnostics not loaded")
        return rows, proof
    profile.frozen_sources = including_diagnostic_load
    profile.matching_members = matching_members
    profile.gate_profile = lambda args, commit, base, h, reviewer: gate_profile(profile, args, commit, base, h, reviewer)
    return profile


def matching_members(left, right, require, *, right_only=()):
    """New gate/full must match exactly; old/new may have only declared repair."""
    require(set(right_only) <= set(right), "Missing declared gate-only inputs")
    right_keys = set(right) - set(right_only)
    difference = set(left) ^ right_keys
    require(difference in (set(), {DIAGNOSTICS}), "Unexpected source member delta")
    require(not right_only or not difference, "New full source set must match new fine gate exactly")
    ignored = {"source/case.lisp", "source/config/git-commit-version.txt"}
    if difference:
        ignored |= CHANGED  # The repaired side is independently bound to actual new gates.
    for key in (set(left) & right_keys) - ignored:
        require((left[key]["bytes"], left[key]["sha256"]) == (right[key]["bytes"], right[key]["sha256"]),
                "Undeclared source/input change: " + key)
    return len((set(left) & right_keys) - ignored)


def gate_profile(profile, args, commit, base, h, reviewer):
    require = base.require
    require(args.native_gate.resolve() == GATE.resolve() and args.gate_index.resolve() == INDEX.resolve()
            and INDEX.is_file(), "NOT_READY: exact cohesive repair-gate packet required")
    index = profile.committed_index(INDEX, commit, base, h)
    fine_rows, proof = profile.frozen_sources(GATE, reviewer, h, require)
    production = {key: (row["bytes"], row["sha256"]) for key, row in fine_rows.items() if base.numerical_member(key)}
    results = {}
    for name in GATES:
        run, saved = RAW / name, index.parent / "gates" / name
        require((saved / "exit.json").is_file(), "NOT_READY: " + name + " exit/packet absent")
        require(h.read_json(saved / "exit.json")["exitCode"] == 0, "NOT_READY: gate native exit failed")
        profile.same_bytes(run / "result.json", saved / "result.json", require)
        result = h.read_json(saved / "result.json")
        require(result.get("passed") is True and not result.get("failedGroups", [])
                and not result.get("failures", []), "NOT_READY: gate groups/checks failed")
        results[name] = result
        # Source counts differ by each fixture's inputs; compare actual maps.
        manifest = h.read_json(run / "source/source-manifest.json")["files"]
        rows = {r["path"]: r for r in manifest}
        require(len(rows) == len(manifest) > 0, "Empty/duplicate gate source set")
        profile.same_bytes(run / "source/source-manifest.json", saved / "source-manifest-index.json", require)
        require({key: (r["bytes"], r["sha256"]) for key, r in rows.items() if base.numerical_member(key)} == production,
                "Gate numerical source set/bytes differ from repaired fine gate")
        for phase in ("before", "after"):
            profile.same_bytes(run / f"source-proof-{phase}.json", saved / f"source-proof-{phase}.json", require)
            observed = h.read_json(saved / f"source-proof-{phase}.json")["files"]
            require(len(observed) == len(rows) and {r["path"]: r["sha256"] for r in observed}
                    == {key: r["sha256"] for key, r in rows.items()}, "Gate before/after proof differs")
        after = "source-provenance.json" if name in ("stable-math-001", "fine-repair-controls-001") else "source-provenance-after.json"
        profile.same_bytes(run / after, saved / after, require)
        provenance = h.read_json(saved / after)
        require(provenance["sourceSnapshotExactLoadedBytes"] is True
                and provenance["copiedByteEqualityBeforeLoad"] is True
                and provenance["nativeBackend"] == result["nativeBackend"], "Gate runtime/DLL provenance differs")
        loaded = {Path(a["source"]).resolve() for a in provenance["verifiedAsdfActions"]
                  if a.get("firstParty") and a.get("operation") == "load-op" and a.get("event") == "performing"}
        require((run / DIAGNOSTICS).resolve() in loaded, "Repaired optional diagnostics not loaded")
    stable, regression, capture, fine = (results[name] for name in GATES)
    require(stable["explicitProductionProjectorCalls"] == 33 and stable["physicalUpdateAttempts"] == 0
            and stable["actualFailedTrialReplayCalls"] == stable["nativeConstitutiveCalls"]
                == stable["oldControlsCalled"] == stable["unchangedOldProjectorCalls"] == 0
            and len(stable["cases"]) == 33
            and all(case["passed"] for case in stable["cases"]), "NOT_READY: stable33 controls incomplete")
    require(len(regression["passedGroups"]) == len(set(regression["passedGroups"])) == 15
            and regression["explicitNewPureProjectorCalls"] == 38 and regression["nativeConstitutiveCalls"] == 10
            and regression["explicitStrictComparatorCalls"] == 6
            and regression["physicalUpdateAttempts"] == regression["oldOriginalFailureReplayCalls"] == 0,
            "NOT_READY: relevant15 regression incomplete")
    require(set(capture["passedGroups"]) == set(capture["plannedGroups"]) == CAPTURE_GROUPS
            and len(capture["passedGroups"]) == len(capture["plannedGroups"]) == 8
            and capture["physicalUpdateAttempts"] == capture["originalFineFailureReplayCalls"] == 0
            and capture["optionalProjectorCalls"] == 7 and capture["nativeConstitutiveCalls"] == 2
            and capture["explicitHelperOnlyFailures"] == 6 and capture["optionalReplayAttempts"] == 9
            and capture["optionalReplayProjectorCalls"] == 2
            and capture["strictReplaySchemaRejectionAttempts"] == capture["syntheticStrictDelegateCalls"] == 1,
            "NOT_READY: eight capture groups incomplete")
    require(set(fine["passedGroups"]) == set(fine["selectedGroups"]) == profile.EXPECTED_GROUPS
            and len(fine["passedGroups"]) == len(fine["selectedGroups"]) == 4
            and fine.get("failure") is None
            and all(fine.get(k) == v for k, v in profile.EXPECTED_GATE.items())
            and all(fine["observations"].get(k) == v for k, v in profile.EXPECTED_OBSERVATIONS.items()),
            "NOT_READY: repaired fine four groups/counters incomplete")
    require(Path(fine["observations"]["observationsDirectory"]).resolve() == (GATE / "observations").resolve(),
            "Repaired result observation path differs")
    for key, row in fine_rows.items():
        if base.numerical_member(key):
            actual = h.record(Path(row["originalPath"]))
            require((actual["bytes"], actual["sha256"]) == production[key], "Workspace repaired source changed")
    old_rows, _ = profile.frozen_sources(OLD_FINE, reviewer, h, require)
    require(set(fine_rows) - set(profile.GATE_INPUTS) == set(old_rows) | {DIAGNOSTICS}, "Unexpected old/new source set")
    actual_changed = {key for key in set(old_rows) & set(fine_rows)
                      if (old_rows[key]["bytes"], old_rows[key]["sha256"]) != (fine_rows[key]["bytes"], fine_rows[key]["sha256"])}
    require(actual_changed - {"source/case.lisp", "source/config/git-commit-version.txt"} == CHANGED,
            "Repair differs beyond exact optional ASDF/package/projection/added diagnostics")
    for relative, current in profile.GATE_INPUTS.items():
        profile.same_bytes(current, GATE / relative, require)
    profile.same_bytes(profile.CASE, OLD_FINE / "source/case.lisp", require)
    original_stage = RAW / (OLD_FINE.name + "-launch-preparation")
    for name in profile.FROZEN_ANALYSIS[:4]:
        profile.same_bytes(ROOT / name, original_stage / "analysis" / Path(name).name, require)
    profile.same_bytes(profile.CONTRACT, original_stage / "protocol" / profile.CONTRACT.name, require)
    profile.same_bytes(profile.PAIR_CONTRACT, original_stage / "protocol" / profile.PAIR_CONTRACT.name, require)
    tiny = h.read_json(GATE / "observations/manifest.json")
    require(tiny["complete"] is True and tiny["updates"] == 2 and tiny["savedFrames"] == 3
            and tiny["particleCount"] == 3520, "Tiny actual manifest differs")
    expected = dict(tiny["config"], duration=6, gravityRampDuration=2, frames=61, maxUpdates=60000)
    require({k: tiny["config"][k] for k in ("duration", "gravityRampDuration", "frames", "maxUpdates")}
            == dict(duration=2e-5, gravityRampDuration=1e-5, frames=3, maxUpdates=2), "Unexpected tiny overrides")
    require(expected == h.read_json(OLD_FINE / "manifest.json")["config"], "Repaired full physical config changed")
    contract = h.read_json(profile.CONTRACT)
    require(contract["numerics"]["durationS"] == 6 and contract["numerics"]["frames"] == 61
            and h.read_json(profile.PAIR_CONTRACT)["runtime"]["wallBudgetHours"] == 3, "Wrong registered bound")
    for record in (tiny, expected):
        require(record["materialVariant"] == profile.VARIANT and record["materialClass"] == profile.PARTICLE_CLASS,
                "Repaired material metadata changed")
    comparison = GATE / "original-output-byte-comparison.json"
    report = h.read_json(comparison)
    require(report["status"] == "PASS" and len(report["comparedFiles"]) == 5
            and {row["relative"] for row in report["comparedFiles"]} == {"history.csv", "particles.csv",
                "vtk/particles_0000.vtk", "vtk/particles_0001.vtk", "vtk/particles_0002.vtk"}
            and all(row["bytesIdentical"] is True for row in report["comparedFiles"]), "Bounded byte closure absent")
    # Cohesive packet must carry the exact first root comparison, wherever indexed.
    require(any(row["sha256"] == h.record(comparison)["sha256"] for row in h.read_json(index)["artifacts"]),
            "First comparison is not bound to committed gate packet")
    return expected, dict(nativeGate=str(GATE), nativeSourceFiles=len(fine_rows), nativeRuntimeProof=proof,
        nativeGateArtifactIndex=h.record(index), gates=list(GATES), freshRepairAttempt=REPAIR,
        repairedNumericalSources=production, actualNativeCounters=profile.EXPECTED_GATE,
        actualObservations=fine["observations"], onlyFullPhysicalDeltaFromPreviousAttempt="none",
        boundedOutputByteComparison=h.record(comparison), expectedSourceMemberDelta=list(profile.GATE_INPUTS))


def main():
    profile = load_profile()
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--capture", action="store_true")
    parser.add_argument("--checkpoint")
    parser.add_argument("--gate-index", type=Path, default=INDEX)
    parser.add_argument("--native-gate", type=Path, default=GATE)
    args = parser.parse_args()
    base = profile.base_definitions()
    h = base.helpers()
    write_json = h.write_json
    def with_repair_identity(path, value):
        if path.name in ("prelaunch-snapshot.json", "summary.json"):
            value = dict(value, freshRepairAttempt=REPAIR)
        write_json(path, value)
    h.write_json = with_repair_identity
    if args.prepare:
        profile.prepare(args, base, h)
    else:
        profile.capture(base, h)


if __name__ == "__main__":
    main()
