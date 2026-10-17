# Reference data provenance

These files are numerical-comparison proposals, **not calibration data or
executable, validated physics configurations**. No graph was digitized, no curve
was fitted, and no solver was run to prepare them.

The local source is `Numerical Simulation Residual Soil TRX CU SIGMA ^0
FLAC_290825.pdf`, a 28-page presentation. Its SHA-256 was checked against the
master plan and equals
`acd60b668e3b6ed8c7a7378ae3afd053ca0419f4ed63aecc0031b019495f3979`.
The PDF remains outside the repository. Page numbers are one-based PDF pages,
matching the printed slide numbers.

`source_values.json` stores every page-6 table cell, including missing cells as
`null`. Every value record carries `source_file`, `page`, `model_family`, `units`,
`status`, `origin` and `notes`. A `declared_assumption` cites the plan with a null
page because the markdown plan has no PDF page number. SI-derived entries retain
their source page and state the conversion. Explicit numerical data use
`status=reference_not_calibration` throughout.

The read-only source audit used pypdf text extraction and Poppler page renders.
Pages **3, 6, 7, 11 and 17** were visually inspected. Other pages recorded in the
JSON audit list were inspected through extracted text only. Page-14 historical
confinement values remain labelled as plan transcription, not visual verification.
The actual integrity-test result and file hashes are in `verification.json`.

## Separation of material families

- Page 6 has four independent columns: laboratory-slide values, SANICLAY,
  MC hardening/softening and conventional MC peak. MC-HS cohesion is **0 kPa**;
  the conventional MC peak cohesion **6.04 kPa** must not be substituted.
- Page-17 **Table 4.8** is an independent assumed-clay reference: unit weight
  18.8 kN/m3, peak 7 kPa/20 degrees, residual 2 kPa/13 degrees and nu=0.20.
  The requested `zhan_*` identifiers follow the master plan. Page 25 spells
  the cited study's author as **Zang et al. (2012)**. Attribution to the original
  publication remains unverified; no paper was silently identified or substituted.
- Page-17 **Table 4.1** is separately preserved and unused. Its density 2000
  kg/m3, E=50 MPa and nu=0.3 do not belong to Table 4.8.

## Units and source caveats

Both pairs use the explicitly chosen conversion convention g=9.80665 m/s2:
rho=gamma/g. The residual-soil unit weight is 16830 N/m3, giving approximately
1716.1824 kg/m3; the independent-clay value is 18800 N/m3, giving approximately
1917.0665 kg/m3. This is an SI conversion, not a measured mass density.

The proposed residual-soil specimen is a **3D cylinder**, diameter 0.07 m and
height 0.14 m, at separate confining pressures 100000 and 200000 Pa. The source
shows 2D axisymmetric geometry; it does not demonstrate a plane-strain or 3D
MPM implementation. Page 3 writes a specimen height of 14 cm but its
axisymmetric sketch also has a vertical 7 cm label. The written 14 cm height
specified by the plan is retained, and the sketch inconsistency remains open.

The Table-4.8 stiffness expression remains pressure dependent:
E[Pa]=max(4000000,25*(p'[Pa]+100000)). This is the SI rewriting of
E[kPa]=max(4000,25*(p'[kPa]+100)), not a chosen constant modulus. The source's
water bulk modulus 2e9 has **no printed unit** in Table 4.8; it remains unused.

## Paired evolution proposals and execution gate

The residual-soil pair preserves raw phi=0 degrees at source strain zero and
c=0 Pa. H and HS have identical unscaled prepeak knots (0,0), (0.0068,27.10),
(0.037,33.99). H remains at phi=33.99 degrees after the peak. HS adds
(0.1,27.62) and (0.2,16.34), then clamps at the last value. Angles stay in degrees
until an audited native material interface converts them. Piecewise-linear
interpolation and endpoint clamping are declared reference-law proposals.

No initial prepeak strength or hardening path is supplied for Table 4.8.
The `zhan_*` proposals therefore preserve the common peak endpoint at source
strain 0.05, mark the prepeak path as unresolved, and make no invented initial
strength. H proposes a plateau at 7 kPa/20 degrees; HS proposes softening to
2 kPa/13 degrees at source strain 0.20. M2 must declare a common prepeak law
before these become runnable experiments. Cliff geometry is also pending M5.

All four configurations have `execution.enabled=false`. They do not match or
claim compatibility with an engine execution schema. Internal plastic-strain
mapping, MC corners/apex behavior, the raw zero-strength initial state,
return mapping, boundary/loading and solver settings require later verification.
The generic baseline choice psi=0 for the residual-soil pair is an explicitly
declared assumption, since page 6 does not supply it.

Page 11 reports multiplying FLAC input strain by **20** to adjust a prior trend.
That factor is preserved only as an excluded historical adjustment; the primary
data are unscaled. Page 17 says FLAC plastic shear strain is **one half** of
the cited deviatoric plastic strain. Neither factor is automatically applied to
CL-MPM. Neither total axial strain nor equivalent plastic strain has yet been
shown to equal the source coordinate.

The source includes no raw laboratory time series or uncertainty information.
Calling these cases a true CU reproduction would require a demonstrated
pore-pressure/effective-stress formulation. Slide FoS values are separately
labelled comparison context and are not mandatory MPM targets. The long-term
nine-year example explicitly did not finish before its iteration limit.

## Repeatable data-only check

```powershell
python research/references/test_reference_data.py --write-evidence
```

This uses only the Python standard library and the checked-in JSON files. It
does not require the local PDF and does not rerun the PDF source audit. It checks
provenance, SI conversions, pair identity before peak, endpoint separation,
source-family separation and execution gates. It is not a constitutive or SBCL
test and supplies no scientific validation.
