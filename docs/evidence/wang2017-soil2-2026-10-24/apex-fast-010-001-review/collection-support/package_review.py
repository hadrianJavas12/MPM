"""Package authored review only; never copy paper pages/text/PDF or rerun analysis."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/"output/wang2017-soil2-2026-10-24"
PHYSICAL=BASE/"apex-fast-010-001-review"
TECHNICAL=BASE/"apex-next-study-001"
DEST=ROOT/"docs/evidence/wang2017-soil2-2026-10-24/apex-fast-010-001-review"


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))


def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    data=source.read_bytes();shutil.copyfile(source,target)
    assert target.read_bytes()==data
    return {"source":str(source.relative_to(ROOT)),"destination":str(target.relative_to(DEST)),
            "bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}


def main():
    report=read(PHYSICAL/"completed-apex-physical-review.json")
    assert report["nativeComplete"] and report["nativeExitCode"]==0
    assert report["scientificValidation"] is False and report["nativeSavedOutput"]["loadingFrames"]==61
    input_hashes=read(PHYSICAL/"review-input-hashes.json")
    for name,expected in input_hashes["analysisSources"].items():
        assert sha(PHYSICAL/"analysis-support"/name)==expected
    for record in read(TECHNICAL/"SHA256SUMS.json"):
        source=TECHNICAL/record["path"]
        assert source.stat().st_size==record["bytes"] and sha(source)==record["sha256"]
    source_proof=read(TECHNICAL/"source-proof.json")
    for entry in source_proof["files"]:
        path=ROOT/entry["path"]
        assert path.stat().st_size==entry["bytes"] and sha(path)==entry["sha256"]
    original=(TECHNICAL/"next-study-review.md").read_bytes()
    text=original.decode("utf-8")
    bad="\u00e2\u20ac\u201c"
    assert text.count(bad)==5 and text.count("\u2013")==0
    editorial=text.replace(bad,"\u2013").encode("utf-8")
    assert editorial.decode("utf-8").replace("\u2013",bad).encode("utf-8")==original
    video_proof=BASE/"apex-100mm-inputs-001/completed-video-decode.json"
    decode=read(video_proof)
    assert decode["exitCode"]==0 and decode["logBytes"]==0
    assert (BASE/"apex-100mm-inputs-001/completed-video-decode.log").stat().st_size==0
    assert sha(ROOT/decode["video"])==decode["sha256"].lower()
    DEST.parent.mkdir(parents=True,exist_ok=True);DEST.mkdir(exist_ok=False)
    (DEST/".gitattributes").write_text("* -text -whitespace\n*.png binary\n",encoding="utf-8")
    copied=[]
    for source in sorted(PHYSICAL.rglob("*")):
        if source.is_file() and "__pycache__" not in source.parts:
            copied.append(copy(source,DEST/"physical-review"/source.relative_to(PHYSICAL)))
    for name in ("next-study-review.md","source-proof.json","SHA256SUMS.json"):
        copied.append(copy(TECHNICAL/name,DEST/"technical"/"original"/name))
    copied.append(copy(TECHNICAL/"source-proof.json",DEST/"technical/source-proof.json"))
    editorial_path=DEST/"technical/next-study-review.md"
    editorial_path.write_bytes(editorial)
    normalization={"scope":"Editorial encoding correction only; original authored report bytes retained separately. No reference facts/recommendations changed.",
        "originalPath":"original/next-study-review.md","originalSha256":hashlib.sha256(original).hexdigest(),
        "editorialPath":"next-study-review.md","editorialSha256":hashlib.sha256(editorial).hexdigest(),
        "replacementCount":5,"originalSequenceCodepoints":["U+00E2","U+20AC","U+201C"],"replacementCodepoint":"U+2013",
        "originalBytes":len(original),"editorialBytes":len(editorial),
        "allOtherBytesPreserved":True,"inverseReplacementExactlyRestoresOriginalBytes":True}
    (DEST/"technical/editorial-normalization.json").write_text(json.dumps(normalization,indent=2)+"\n",encoding="utf-8")
    for name in ("completed-video-decode.json","completed-video-decode.log"):
        copied.append(copy(BASE/"apex-100mm-inputs-001"/name,DEST/"media-qa"/name))
    copied.append(copy(Path(__file__),DEST/"collection-support/package_review.py"))
    packet={"scope":"Authored physical/technical review and media-decode proof only; no native raw/source archive duplicated",
            "scientificValidation":False,"landslideValidation":False,
            "nativeCompletionEvidence":"../apex-fast-010-001-completed/README.md",
            "completedNativeEvidenceIndex":{"path":"docs/evidence/wang2017-soil2-2026-10-24/apex-fast-010-001-completed/evidence-manifest.json",
                                             "sha256":sha(ROOT/"docs/evidence/wang2017-soil2-2026-10-24/apex-fast-010-001-completed/evidence-manifest.json")},
            "copiedFilesVerifiedByteForByte":copied,
            "copyrightedSourcePolicy":"Only source-proof filenames/byte counts/SHA256 and authored reference facts are retained. No complete paper text, page render or PDF is copied into this packet.",
            "threeExistingPrimaryArtifactHashesRechecked":source_proof["files"],
            "analysisExecution":"The already-completed saved-data review was copied; no analysis, test, renderer, solver, replay or decode was rerun for collection",
            "editorialChange":normalization,
            "noNewArchives":"Files are copied directly and individually verified; no archive or raw native output duplication is necessary"}
    (DEST/"packet-source-proof.json").write_text(json.dumps(packet,indent=2)+"\n",encoding="utf-8")
    (DEST/"README.md").write_text(
      "# Completed apex experiment: authored physical review and next-study audit\n\n"
      "This packet contains the already-completed saved-data analysis, its exact Python sources/input hashes/results and diagnostic figure, plus the separate technical next-study review. "
      "The physical run completed6s/60mm with native exit0. This does not establish coherent landslide, paper agreement, quasistatic response or numerical/experimental validation. "
      "The original native raw/source/media evidence remains in [the completed-run packet](../apex-fast-010-001-completed/README.md); it is not duplicated here.\n\n"
      "See [physical review](physical-review/completed-apex-physical-review.json) and [diagnostic figure](physical-review/physical-diagnostics.png). "
      "The review distinguishes actual sampled apex activation from cumulative event counts, accumulated plastic-volume strain from geometric volume, and local high/upward velocity from coherent moving mass. "
      "No free above-base mass crossed the original toe, and the reaction remained increasing through60mm.\n\n"
      "The [technical review](technical/next-study-review.md) recommends a gated same-model/same-rate100mm continuation as a further experiment; the Soil2 paper endpoint remains unverified. "
      "Five visible mojibake en-dash sequences were corrected ONLY in this editorial copy. The original report, its original hash index and unchanged source-proof are retained under technical/original/. "
      "technical/editorial-normalization.json records both hashes and verifies that reversing those five replacements exactly restores every original byte. No reference fact or recommendation was changed.\n\n"
      "Only three existing primary-artifact filenames/byte counts/hashes and authored facts are retained as source proof. Full paper text, page renders and PDF are not copied. "
      "Root independently inspected the primary pages and native viewports; the collector did not repeat that work. The two copied full-video-decode proof files are existing exit0 verification, not a new decode/render or physics check.\n\n"
      "All direct copies were verified byte-for-byte and indexed with SHA-256. No tests, solver, renderer, replay, analysis or decode were rerun during collection. "
      "No production files, raw reference sources or existing evidence were modified.\n",encoding="utf-8")
    assert (TECHNICAL/"next-study-review.md").read_bytes()==original
    entries=[{"path":p.relative_to(DEST).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(DEST.rglob("*")) if p.is_file()]
    (DEST/"evidence-manifest.json").write_text(json.dumps({"scope":"Authored review; scientific landslide PASS not claimed","entries":entries},indent=2)+"\n",encoding="utf-8")
    assert all(sha(DEST/e["path"])==e["sha256"] for e in entries)
    print(json.dumps({"verifiedArtifacts":len(entries),"directCopiesVerified":len(copied),"editorialReplacements":5,
                      "copyrightedFullSourcesCopied":0,"newArchives":0,"destination":str(DEST)}))


if __name__=="__main__":main()
