---
title: Joss Bay user reference inputs 2026-10-14
type: source
tags: [joss-bay, reference, paper, video]
sources: ["D:/model/Referensi/1-s2.0-S0266352X25005579-main.pdf", "D:/model/Referensi/video.mp4", examples/chalk/joss.lisp]
updated: 2026-10-14
---

# Joss Bay user reference inputs - 2026-10-14

Immutable input/provenance snapshot. The user supplied a paper and video, then
clarified that numerical identity is unnecessary, declined a dataset requirement,
and requested work from the existing `examples/chalk/joss.lisp`. The intended
target is cliff geometry, cracking, collapse and run-out similar to the references.

PDF: Sutcliffe et al., *Modelling cliff collapse and run-out with the material
point method*, Computers and Geotechnics189(2026)107608,
DOI10.1016/j.compgeo.2025.107608. Original absolute path is listed above;
24pages,4,010,130bytes. SHA256:
`0D5F49FDDDE5E88F59FB9996F16B2BD1E05D0A453FAC27B1EA184BC6EA0193F5`.

Video: original path listed above,377,835bytes, H.2641280x720,30fps,184frames,
playback duration6.133333s. SHA256:
`96C053F1F411E884CD5FB4BA1230311581C279EECBDE29F656012225C395CF26`.
Playback time is not simulation time; rendered title times require explicit
reading. This record does not assert which published figure variant the video uses.

Relevant paper evidence: Fig.12/section6.1 describe15.5m cliff,1m base,78degree
lower slope and assumed45degree0.5m notch; Table5 includes E100MPa while prose
states1GPa. Eq.(44/57) and the75.6 plastic oversize support a1GPa candidate,
but do not establish an erratum. Section6.2/Algorithm1 distinguish equilibrium,
accelerated crack growth, unscaled collapse and settling. Section6.3 acknowledges
numerical versus field cutback/run-out differences. Complete audited notes are
in `output/reference-reproduction-2026-10-14/paper-spec.md`; mutable current
implementation/results belong in [[joss-reference-reproduction]].
