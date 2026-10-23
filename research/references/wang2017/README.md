# Wang et al. (2017) reference provenance

[Source record](source.json): Wang, Rong, Sun and Wang, *Stability analysis of slope in strain-softening soils using local arc-length solution scheme*, Journal of Mountain Science 14(1), 175–187, [DOI](https://doi.org/10.1007/s11629-016-3951-1).

The original user-supplied PDF was recorded at `C:/Users/ASUS/Downloads/101007s11629_016_3951_1.pdf`; SHA-256 is `181875666f93c21291175a830ec1d5030d5b128c081e6d7983a605cbc019919b` (2,400,321 bytes). That path was missing on2026-10-23. No full copyrighted PDF is committed. The original source record remains unchanged; the [MPM preparation contract](mpm-reference-contract.json) records the newer public author-upload source and unresolved inputs.

Table 1 and Figure 2 are on printed page 179 (PDF page 5); Figure 3, the Soil#1 force–displacement comparison, is on printed page 180 (PDF page 6). Text extraction covers these pages; the page-179 render was also visually checked. Values are transcribed reference inputs, not experimental calibration.

Figure 2 gives width 20 m, crest segments 7 m + 3 m loaded patch, base 5 m and slope 60°. It gives no numerical slope-relief height. The proposed 10 m relief is an explicit implementation assumption. Soil#1 is perfectly plastic; Soil#2 softening parameters are recorded for future work, with no implementation claimed here.

See [benchmark scope and Windows commands](../../../docs/benchmarks/WANG2017_SLOPE_DESCENT.md). A one-second native pilot has completed; full reference-curve comparison remains **NOT_RUN**. No curve was digitized or fitted.

Latest user decision on2026-10-23: keep MPM and follow paper physical inputs.
Use [the current preparation guide](../../../docs/benchmarks/WANG2017_MPM_PREPARATION.md)
and `scripts/prepare-wang2017.ps1` for an actual native input audit without a
solver run. Soil1/Figure3 and Soil2/Figure4 are separate material cases; the
paper kps coordinate needs an explicit adapter before Soil2 is executable.

Boundary clarification: the support symbols in Figure 2 do not enumerate every
constrained DOF in the text. The initial source record's "bottom vertical rollers"
is a diagram interpretation, not a quoted boundary specification. The pilot
explicitly fixes bottom x/y and side x, leaves top free, and constrains the loaded
strip by finite displacement springs. Bottom tangential fixity is an additional
implementation assumption to resolve before quantitative reproduction.
