# Windows native unilateral-pusher pilot

Source ec285c05956c1b6fd592428869fba826b7430dd9. Actual native run completed
2026-10-22 23:27 WIB, 1 s / 11 states / 915 MPs; native and audit/render exits0.
The driver moves downward0.005 m/s; material and geometry retain the gravity
case assumptions. Initial compression is followed by sampled complete release:
at0.1s reaction3.616kN/m, while each saved0.2–1.0s state has0active/6unloaded
contacts and zero driver reaction. Final tracked soil-patch settlement10.078mm
exceeds the5mm driver command; maximum particle speed is0.052089m/s.

This verifies sampled dynamic loading/release with free soil motion. It does not
establish a landslide, laboratory calibration or general surface-contact validity.
The unamplified particle view shows small distributed creep without a detached
mass/run-out. Saved intervals do not prove zero load at every intermediate step
and do not provide integrated actuator work. No full120s pusher run was started.

Raw VTK/CSV plus executed review support are in native-output.tar.gz; exact
captured sources and runtime provenance are retained separately. review.json,
loading-history.csv and contact-diagnostics.png expose the measured contact
behavior. evidence-manifest.json records artifact hashes.
