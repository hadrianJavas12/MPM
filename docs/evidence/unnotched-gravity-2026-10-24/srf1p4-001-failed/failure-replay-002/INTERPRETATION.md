# Actual gravity-slope perfect-MC ambiguity: diagnostic interpretation

24 October 2026. Native replay002 exited0. The retained production capsule was
replayed **once**, with zero MPM updates. Temporary observation wrappers returned
the unchanged production predicate results and were restored afterward.

The six MC source modules and mapped DLL match the actual failed run byte for
byte. All283 frozen files match before and after execution. Capsule SHA256:
`d0fa089970adf81178ca486f00423d53e0dffa98ba963823e822037e6e5f15bb`.
Harness001 stopped at a package-lock collision before capsule parsing or any
projection call; its source and error log remain retained. Helper renaming was
the only repair before002. There was one actual projection call across attempts.

## Observed cause

The face return, active plane1 `(0,2)` in sorted principal coordinates, has a
positive multiplier1.0037301356154057e-7, all six yield residuals nonpositive,
positive work0.004073913767104577Pa, and history residual-7.01449e-22.

The second accepted candidate, upper edge planes1 and3, requires
lambda3=-7.313031007122379e-13. Production's fixed absolute multiplier allowance
1e-12 accepts this negative flow multiplier. Its elastic stress effect is
5.625408467017215e-5Pa, **32.4237 times** the existing stress residual tolerance
1.734967079821152e-6Pa. Positive total plastic work and small complementarity
products do not remedy the negative-multiplier KKT violation.

The two stresses differ by5.6254088121932e-5Pa, exceeding the existing dedup
distance2.7759473277138433e-5Pa. Kappa differs only1.0623390662707448e-13, within
its dedup allowance1e-10. Production therefore retains two roots and correctly
raises its ambiguity error given those inconsistent acceptance allowances.

## Analytical check for this particular perfect law and state

For perfect plasticity, c, phi and psi do not vary with kappa. Each nonsingular
active-set problem is a linear system `A lambda = n*t_trial - 2*J*c*cos(phi)`,
where `A_ab = n_a dot D*m_b`. Kappa follows explicitly as
`old_kappa + sqrt(2/3)*norm(dev(sum(lambda*m)))`; it creates no extra stress root.

Here psi0 gives `m_1=(1,0,-1)` and `m_3=(0,1,-1)`. With `s=sin(phi)` the upper
edge matrix is `2G * [[2,1-s],[1-s,2]]`. Its eigenvalues
`2G*(3-s)` and `2G*(1+s)` are strictly positive for the declared angle. Let the
face solve be lambda1=rhs1/(4G). The second face residual f3 is negative
(-9.67547603067942e-5Pa), so the edge solution requires
`lambda3 = f3 / (A33 - A31*A13/A11) < 0`. That edge is outside its admissible
active cone. The other canonical edge also has a negative multiplier
(-3.245406889949329e-4); all three-plane psi0 flow matrices have rank at most2
and are singular. Independent direct arithmetic over all six canonical bases
is saved in analytical-active-set.json. Thus this state has one admissible
face return under the model's exact nonnegative multiplier conditions.

This is not a global uniqueness theorem for arbitrary nonassociated or
softening models, and it does not justify selecting among genuinely distinct
positive-multiplier nonlinear roots.

## Recommended repair and verification, not yet implemented here

Keep the current stress/history/dedup tolerances and the ambiguity rejection.
Tighten the negative-multiplier acceptance according to its elastic stress
effect: each negative lambda should satisfy
`abs(lambda_i) * norm_inf(D*m_i) <= stress_tolerance`, in addition to the current
absolute bound. For psi0, the resulting allowance is
`stress_tolerance/(2G)=2.2554572037674974e-14`, which rejects the spurious edge
without changing the valid face or any physical inputs. Computing this bound
requires explicit elasticity context, not an assumed E or a dimensionally
unrelated fixed multiplier tolerance.

Alternatively a documented active-set method can remove an inactive/negative
constraint and recompute the lower-dimensional return, while retaining full
KKT checks. Do not clamp the negative multiplier and retain the old edge stress,
prefer the first root, increase the stress dedup radius, or change psi/strength.

Relevant controls should cover the captured face/edge boundary, exact edge
states, scale changes in E and stress units, permutations, nonzero dilation,
and genuine multiple-root rejection, followed by existing MC regressions.
Whole-MPM rollback is NOT_EXECUTED by this pure capsule; it lacks full state.
The full failed simulation remains negative evidence and was not restarted.
