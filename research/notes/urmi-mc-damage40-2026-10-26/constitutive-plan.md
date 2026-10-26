# Approved optional MC strength damage: source preparation only

26-27 October 2026. Root and independent math review approve the corrected
total-DSS mapping below for an explicitly new optional point module. Source
implementation is authorized; FIRST frozen native point execution remains
pending root review. No MPM is authorized by this material task.

Use an explicitly **Urmi-inspired S1 adaptation**, not literal paper Eq2.
The retained primary PDF pp2-3,6-7 prescribes undrained phi0 MC/Tresca with
cohesion softening, not a damage variable or stiffness degradation. Literal
Eq2 at total gamma_p=.01 gives about16kPa rather than40.5kPa. Connecting that
point to the peak at the same total strain makes DSS consistency singular;
do not introduce a sample gap to conceal this unresolved paper origin.

Corrected continuous alternative for math review: s=gamma_total-gamma_p is
postpeak TOTAL DSS engineering shear increment, s_R=gamma_R-gamma_p.
For 0<=s<=s_R use

    c(s) = suR + (sup-suR)*(exp(-beta*s)-exp(-beta*s_R))
                             /(1-exp(-beta*s_R)).

Then use the linear TOTAL-gamma tail from (gamma_R,suR) to (gamma_r,sur),
and clamp at sur. Map each parameterized node with elastic unloading:

    q(s) = s + (sup-c(s))/G; kappa=q/sqrt(3).

Thus q_R=gamma_R-suR/G and q_r=gamma_r-sur/G because gamma_p=sup/G.
q equals monotonic DSS plastic engineering shear only; using sqrt(3)*kappa
in general MPM is an explicitly declared equivalent-invariant adaptation.
Nodes are evaluated in s and mapped to (kappa,c); no inverse solve is needed.
Peak/endpoints are exact and the law is C0. Alpha remains paper metadata but
cancels from peak normalization; this is NOT literal Eq2 or recalibration.
The former direct exponential in q is rejected: its initial softening slope
exceeded the axisymmetric Tresca-edge unloading stiffness. Here
dc/dq=-.95025G/(1+.95025) approximately -.487245G, below the .866025G
edge bound in magnitude. With Cauchy cohesion the Kirchhoff consistency uses
J*dc/dq: the edge comparison is only positive near J1 (initially J<about1.777),
not arbitrary positive J. DSS monotonicity alone is not a general return proof.
S1 inputs: sup40500Pa, suR3847.5Pa, sur1000Pa, G4.05MPa, nu_u=.45,
E_u=11.745MPa, gamma_p=.01, gamma_R=1.8, gamma_r=9.477, alpha=.95,
beta105 (paper calibration at h=.5m). Normalization/origin/history changes mean
this adaptation has not inherited the paper's dissipated-energy calibration.
Retain those values without strength/SRF tuning. Drained c3700Pa/phi30.6deg/nu=.33;
using the same G gives declared
derived E_d=10.773MPa. Stable drained initialization and transfer are separate
future recipe work, not implemented by this material task.

Construct an existing evolution-law with phi=psi=0 and cohesion su(kappa),
using deterministic curvature-bounded subdivision: absolute interpolation
error <=.0025*sup=101.25Pa, <=64 total segments, including linear tail.
For the exponential branch define A=(sup-suR)*exp(-beta*s)/(1-exp(-beta*s_R)).
Then d2c/dkappa2=3*beta^2*A/(1+beta*A/G)^3. On each s interval obtain an
upper bound by maximizing this expression at its endpoints and the stationary
value A=G/(2*beta), if inside the interval. This is the chain-rule correction
c''(s)/(1-c'(s)/G)^3, times3 for kappa. Chord error is bounded by
M*(delta-kappa)^2/8. The linear tail remains linear after mapping and is exact.
Exceeding the segment budget fails explicitly without changing beta/tolerance.
Publish actual bound/count; no runtime fitting or repeated table construction.

The owned factory validates tables/finite origin and uses the existing internal
law struct constructor with actual peak-kappa=origin, including0. The ordinary
public law constructor still rejects peak0. The ordinary diagnostic replay
helper does not support this zero-peak extension. Root additionally authorizes
an owned exact-law/schema principal-input replay factory and one explicitly
SYNTHETIC serialized replay control before FIRST point execution. It must reject
tampered law/schema inputs before projector entry and never claim a whole-MPM
restart or an actual failure replay. Shared baseline replay remains untouched.

Optional particle subclass reuses unchanged MC projector, native Hencky/
Kirchhoff return and accepted-step kappa transaction. D_s=1-su/sup is derived
from accepted cohesion (Dmax=1-1000/40500), not independently evolved state.
Any owned parameter slots join particle-transaction-slots using copy-supported
scalars/lists. No new stiffness, fracture energy, tensile cap or Joss behavior.
Point controls will cover endpoints, monotonicity, bounded table error, real
MC face and both edge returns including two-equal-principal small-excess trials
and all six permutations at current J.8/1/1.2/1.7, work/history and rollback.
Large-J outcomes may be accepted distant roots or original strict rejections;
neither is forced or a uniqueness proof. Strict multiple-root rejection remains
unchanged. No MPM or old suites; defaults stay intact.
