# Primary MPM literature for an unnotched landslide

Reviewed 2026-10-24. Research only: no solver, production, UI, raw-source, or default-law changes. Live remote read: main `9e97e001c2eaf9be81c7b7e39e32fa87f2d6f64b`; working branch `codex/wang2017-soil2-landslide`.

The three principal papers below demonstrate unnotched numerical slope failure. None establishes scientific validation of this repository's solver. Exact bibliography, parameters, page locations, missing inputs, and source URLs are in [mpm-softening-primary.json](mpm-softening-primary.json).

## Two strongest practical candidates

1. **Wang, Hicks and Vardon (2016), deterministic baseline.** Its explicitly self-weight-triggered short slope, simple cohesion softening, and reported discretisation comparison make it the most economical mechanism benchmark. However, its numerical unit weight is absent from the successfully inspected text: **do not silently import a density from another paper**. The frictional base and Von Mises invariant also require explicit implementation mapping. An MC material at zero friction is Tresca; it is not automatically the paper's Von Mises law. The reported backward retreat is not toe runout. [Final published paper, TU Delft](https://pure.tudelft.nl/ws/files/8514063/jgele.16.00019.pdf).

2. **Yu and Kasama (2024), already unstable deterministic runout subset.** The paper supplies a continuous face, full domain dimensions, unit weight, boundaries, grid, and integration interval, and separates this subset from its strength-reduction study. It is therefore the clearer input contract when avoiding unresolved density. Its Drucker-Prager conversion, dilatancy evolution and smeared-crack regularisation still need reconciliation; merely inserting its cohesion into the current MC material is an adaptation. The published runout values are numerical comparisons, not measured landslide validation. [Journal paper and PDF](https://doi.org/10.2208/journalofjsce.23-15036).

These are candidate *new declared benchmarks*. Neither licenses undisclosed changes to Wang2017 Soil2 strength, loading rate, boundary conditions, or scientific claims. The 2016 paper's norm of the plastic strain tensor is not automatically the current engine's accumulated incremental history; bind the actual curve before using it. A proof of sustained coherent sliding must track moving mass, toe crossing, centroid descent, energy, stress admissibility and mass conservation, beyond successful native termination or a load-reaction drop.

## Third useful primary and scope boundaries

**Remmerswaal, Vardon and Hicks (2025)** is an openly accessible journal example with explicit gravity/crest-load triggering and constitutive/numerical details. It is better used to justify trigger design and geometric failure assessment than as an immediate Windows CPU target. Its published 3D method, random realisations and deletion of points leaving the domain need explicit treatment before any comparison of deposited mass or runout. [Open full text](https://doi.org/10.1007/s11440-025-02542-w).

Two other verified journal references are retained as boundaries, not ready reproduction contracts. **Wang, Vardon and Hicks (2016)** separates an eligible short self-weight slope from an ineligible long slope with a toe cut; do not label the entire paper no-notch. **Zabala and Alonso (2011)** offers field failure-surface evidence for construction-induced brittle foundation failure, but needs coupled flow/deformation and detailed staged loading; it is not a quick mechanical-only implementation. See JSON URLs.

The closely titled 2017 Vardon/Wang/Hicks long-slope studies use a steeper toe-cut segment to represent erosion/cutting and should not be adopted as an unnotched benchmark. Rainfall papers require hydro-mechanical capabilities not demonstrated here.

## Verification limits

Primary journal/repository records and relevant full text were inspected. Yu/Kasama PDF pages 4 and 5 were rendered and visually checked: Fig. 3 is unnotched; Table 1 has E=100 MPa (web text extraction loses zeroes). An attempted additional Wang PDF download timed out; already retrieved web PDF text supplies its facts. No density was inferred from missing text. No Node tests or SBCL runs were performed for this literature-only note.
