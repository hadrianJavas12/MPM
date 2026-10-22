---
title: Wang 2017 user reference inputs 2026-10-22
type: source
tags: [wang2017, slope, reference, provenance]
sources: ["C:/Users/ASUS/Downloads/101007s11629_016_3951_1.pdf"]
updated: 2026-10-22
---

# Wang 2017 user reference inputs — 2026-10-22

Immutable factual source snapshot. Wang, Rong, Sun and Wang (2017), *Stability analysis of slope in strain-softening soils using local arc-length solution scheme*, Journal of Mountain Science 14(1), 175–187; DOI 10.1007/s11629-016-3951-1.

User PDF: 2,400,321 bytes; SHA-256 `181875666f93c21291175a830ec1d5030d5b128c081e6d7983a605cbc019919b`. The full PDF remains outside the repository. Extracted text PDF pages 5–6 and rendered PDF page 5 were inspected for this record.

Printed p.179 Table 1 Soil#1: unit weight 20 kN/m³, E 20 MPa, nu 0.25, c 30 kPa, phi 35°, psi 0°, elastic-perfectly plastic. Soil#2: c 30→15 kPa over paper kps 0→0.02; phi remains 35°.

Figure 2: width 20 m, crest 7 m before 3 m loaded patch, 5 m base, slope 60°, descent speed 1e-4 m/s. No numerical slope-relief height is labelled. Section 2 uses gravity initialization followed by displacement/strain reset and crest descent; Figure 3 (printed p.180) compares Soil#1 FEM force–displacement curves. The paper's local arc-length method is distinct from a penalty-driven MPM approximation.

Mutable implementation and evidence status belong in [[wang2017-prescribed-descent]].
