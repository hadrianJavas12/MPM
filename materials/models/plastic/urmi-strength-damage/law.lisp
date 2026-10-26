;;;; New continuous S1 adaptation approved in constitutive-plan.md.
;;;; Not literal Urmi Eq2 and not its dissipated-energy calibration.
(in-package :cl-mpm/models/urmi-strength-damage)
(defconstant +peak-strength-pa+ 40500d0)
(defconstant +transition-strength-pa+ 3847.5d0)
(defconstant +remolded-strength-pa+ 1000d0)
(defconstant +shear-modulus-pa+ 4050000d0)
(defconstant +youngs-modulus-pa+ 11745000d0)
(defconstant +poisson-ratio+ .45d0)
(defconstant +gamma-peak+ .01d0)
(defconstant +gamma-transition+ 1.8d0)
(defconstant +gamma-remolded+ 9.477d0)
(defconstant +beta+ 105d0)
(defconstant +table-tolerance-pa+ 101.25d0)
(defconstant +maximum-segments+ 64)

(defun reference-strength (s)
  "Cauchy cohesion at postpeak TOTAL DSS engineering shear increment S."
  (unless (and (mc::finite-real-p s) (>= s 0d0))
    (mc::integration-fail "Postpeak DSS increment must be finite and nonnegative" s))
  (let ((sr (- +gamma-transition+ +gamma-peak+))
        (send (- +gamma-remolded+ +gamma-peak+)))
    (cond ((zerop s) +peak-strength-pa+)
          ((>= s send) +remolded-strength-pa+)
          ((>= s sr)
           (- +transition-strength-pa+
              (* (- +transition-strength-pa+ +remolded-strength-pa+)
                 (/ (- s sr) (- send sr)))))
          (t (+ +transition-strength-pa+
                (* (- +peak-strength-pa+ +transition-strength-pa+)
                   (/ (- (exp (* (- +beta+) s)) (exp (* (- +beta+) sr)))
                      (- 1d0 (exp (* (- +beta+) sr))))))))))

(defun reference-node (s)
  "Fresh (s,kappa,cohesion) node; q=s+(sup-c)/G, kappa=q/sqrt(3)."
  (let ((c (reference-strength s)))
    (list (float s 1d0)
          (/ (+ s (/ (- +peak-strength-pa+ c) +shear-modulus-pa+)) (sqrt 3d0)) c)))

(defun %curvature-bound (left right)
  "Maximum d2c/dkappa2 on one exponential interval, including its stationary A."
  (let* ((sr (- +gamma-transition+ +gamma-peak+))
         (scale (/ (- +peak-strength-pa+ +transition-strength-pa+)
                   (- 1d0 (exp (* (- +beta+) sr)))))
         (ahi (* scale (exp (* (- +beta+) left))))
         (alo (* scale (exp (* (- +beta+) right))))
         (critical (/ +shear-modulus-pa+ (* 2d0 +beta+))))
    (flet ((curvature (a)
             (/ (* 3d0 +beta+ +beta+ a)
                (expt (+ 1d0 (/ (* +beta+ a) +shear-modulus-pa+)) 3))))
      (max (curvature alo) (curvature ahi)
           (if (<= alo critical ahi) (curvature critical) 0d0)))))

(defun %interval (left right)
  (let ((dk (- (second (reference-node right)) (second (reference-node left)))))
    ;; The analytic bound concerns exact real expressions. A fixed rounding
    ;; allowance is reported in addition; it is not a projector tolerance.
    (list left right (+ (* (%curvature-bound left right) dk dk .125d0) 1d-7))))

(defun %build-reference-table (&key (tolerance +table-tolerance-pa+)
                                  (maximum-segments +maximum-segments+))
  "Deterministic largest-error bisection, performed once when this optional module loads."
  (unless (and (mc::finite-real-p tolerance) (> tolerance 1d-7)
               (integerp maximum-segments) (>= maximum-segments 2))
    (mc::integration-fail "Invalid owned table error/segment budget" tolerance maximum-segments))
  (let* ((sr (- +gamma-transition+ +gamma-peak+))
         (send (- +gamma-remolded+ +gamma-peak+))
         (intervals (list (%interval 0d0 sr))))
    (loop for worst = (reduce (lambda (a b) (if (>= (third a) (third b)) a b)) intervals)
          while (> (third worst) tolerance) do
      (when (>= (1+ (length intervals)) maximum-segments)
        (mc::integration-fail "Owned table cannot meet fixed error within segment budget"
                             tolerance maximum-segments (third worst)))
      (let ((mid (* .5d0 (+ (first worst) (second worst)))))
        (setf intervals
              (loop for interval in intervals append
                (if (eq interval worst)
                    (list (%interval (first interval) mid) (%interval mid (second interval)))
                    (list interval))))))
    (let ((nodes (append (list (reference-node 0d0))
                         (mapcar (lambda (interval) (reference-node (second interval))) intervals)
                         (list (reference-node send))))
          (bounds (append (mapcar #'third intervals) (list 1d-7))))
      (list :nodes nodes :bounds bounds :segments (length bounds)
            :maximum-bound (reduce #'max bounds) :rounding-allowance-pa 1d-7))))

;; Private, immutable by contract. Public factories/readers always return copies.
;; Particle initialization translates these cached knots; it never refines them.
(defparameter *reference-table* (%build-reference-table))

(defun make-strength-damage-law (&key (kappa-origin 0d0))
  "Owned checked HS law with real peak at ORIGIN, including zero.
The public baseline constructor's positive-peak contract remains unchanged.
The baseline diagnostic replay helper cannot recreate a zero-peak owned law;
REPLAY-STRENGTH-DAMAGE-DIAGNOSTIC validates/reconstructs this owned extension."
  (unless (and (mc::finite-real-p kappa-origin) (>= kappa-origin 0d0))
    (mc::integration-fail "Owned kappa origin must be finite and nonnegative" kappa-origin))
  (let* ((origin (float kappa-origin 1d0))
         (cohesion (append (when (> origin 0d0) (list (list 0d0 +peak-strength-pa+)))
                           (mapcar (lambda (node) (list (+ origin (second node)) (third node)))
                                   (getf *reference-table* :nodes))))
         (c-table (mc::checked-table cohesion "owned cohesion Pa" (lambda (x) (>= x 0d0))))
         (phi-table (mc::checked-table '((0d0 0d0)) "owned friction degrees" #'zerop)))
    (unless (and (= (caar c-table) 0d0) (= (caar phi-table) 0d0)
                 (= (second (first c-table)) +peak-strength-pa+)
                 (= (second (car (last c-table))) +remolded-strength-pa+))
      (mc::integration-fail "Invalid owned strength table endpoints"))
    (loop for (a b) on c-table while b do
      (unless (>= (second a) (second b)) (mc::integration-fail "Nonmonotone owned cohesion table")))
    (mc::%make-evolution-law
     :variant :hs :points phi-table :cohesion-points c-table :psi 0d0
     :stress-measure :cauchy :peak-kappa origin
     :strain-assumption
     "NEW Urmi-inspired S1 C0 normalized exponential/linear TOTAL-DSS curve mapped by q=s+(sup-c)/G=sqrt(3)*(kappa-origin); general MPM invariant adaptation; not literal Eq2 or energy calibration; strength damage only")))

(defun %owned-diagnostic-table (table)
  (unless (or (listp table) (vectorp table))
    (mc::integration-fail "Owned diagnostic table must be a sequence"))
  (map 'vector
       (lambda (row)
         (unless (and (or (listp row) (vectorp row)) (= (length row) 2)
                      (every #'mc::finite-real-p row))
           (mc::integration-fail "Invalid owned diagnostic table row" row))
         (map 'vector (lambda (value) (float value 1d0)) row)) table))

(defun replay-strength-damage-diagnostic (diagnostic)
  "Validate an exact owned principal-input capsule, then call the unchanged projector once.
This is not a native-MPM restart and does not manufacture missing failure state."
  (unless (and (hash-table-p diagnostic)
               (equal (gethash "schema" diagnostic) "cl-mpm.mc-evolution.principal-failure")
               (eql (gethash "schemaVersion" diagnostic) 1))
    (mc::integration-fail "Unsupported owned principal diagnostic schema"))
  (let* ((field #'mc::%diagnostic-field)
         (record (funcall field diagnostic "law"))
         (origin (funcall field record "peakKappa"))
         (law (make-strength-damage-law :kappa-origin origin))
         (trial (funcall field diagnostic "trialKirchhoffPa"))
         (e (funcall field diagnostic "youngsModulusPa"))
         (nu (funcall field diagnostic "poissonRatio"))
         (j (funcall field diagnostic "deformationJacobian"))
         (old (funcall field diagnostic "oldKappa")))
    (unless (and (equal (funcall field record "variant") "hs")
                 (equal (funcall field record "stressMeasure") "cauchy")
                 (mc::finite-real-p (funcall field record "psi"))
                 (zerop (funcall field record "psi"))
                 (equal (funcall field record "strainAssumption") (mc:evolution-law-strain-assumption law))
                 (equalp (%owned-diagnostic-table (funcall field record "points"))
                         (mc::%diagnostic-table-copy (mc:evolution-law-points law)))
                 (equalp (%owned-diagnostic-table (funcall field record "cohesionPoints"))
                         (mc::%diagnostic-table-copy (mc:evolution-law-cohesion-points law)))
                 (mc::finite-real-p e) (= e +youngs-modulus-pa+)
                 (mc::finite-real-p nu) (= nu +poisson-ratio+)
                 (mc::finite-real-p old) (>= old origin)
                 (or (vectorp trial) (listp trial)) (= (length trial) 3)
                 (every #'mc::finite-real-p trial))
      (mc::integration-fail "Diagnostic is not the exact owned S1 strength-damage law/input"))
    ;; J is deliberately supplied unchanged; the original projector owns its
    ;; positive-finite check and preserves an invalid-J rejection when replayed.
    (mc:project-principal (map 'vector (lambda (value) (float value 1d0)) trial)
                         e nu j law old)))

(defun strength-damage-reference ()
  "Fresh provenance/table record. No returned object aliases production data."
  (let ((record (make-hash-table :test #'equal)))
    (loop for (key value) on
      (list "model" "urmi-inspired-s1-strength-damage-v1"
            "source" "Urmi et al.2024 Engineering Geology340107669, PDFpp2-3/6-7"
            "referencePdfSha256" "3f6aa9f5ba914564df3031aa8d6853ffef91b045a433446126e49316c150785a"
            "adaptation" "C0 normalization/total-to-plastic DSS mapping; no inherited energy calibration"
            "history" "q=sqrt(3)*(kappa-origin), monotonic DSS plastic engineering shear equivalent only"
            "strengthMeaning" "Cauchy MC cohesion; phi=psi=0; D_s=1-c/sup; stiffness unchanged; no fracture damage"
            "peakStrengthPa" +peak-strength-pa+ "transitionStrengthPa" +transition-strength-pa+
            "remoldedStrengthPa" +remolded-strength-pa+
            "damageMaximum" (- 1d0 (/ +remolded-strength-pa+ +peak-strength-pa+))
            "shearModulusPa" +shear-modulus-pa+ "youngsModulusPa" +youngs-modulus-pa+
            "poissonRatio" +poisson-ratio+ "gammaPeak" +gamma-peak+
            "gammaTransition" +gamma-transition+ "gammaRemolded" +gamma-remolded+
            "paperAlphaUnusedAfterNormalization" .95d0 "paperMeshSizeM" .5d0 "beta" +beta+
            "tableTolerancePa" +table-tolerance-pa+ "maximumSegments" +maximum-segments+
            "actualSegments" (getf *reference-table* :segments)
            "maximumErrorBoundPa" (getf *reference-table* :maximum-bound)
            "roundingAllowancePa" (getf *reference-table* :rounding-allowance-pa)
            "currentJQualification" "Cauchy strength uses J in Kirchhoff projection; near-J1 slope analysis is not arbitrary-J uniqueness; strict root rejection retained"
            "replayScope" "Owned exact-law principal-input replay supported; baseline zero-peak replay is incompatible; not a whole-MPM restart")
      by #'cddr do (setf (gethash key record) (mc::%copy-state-value value)))
    (setf (gethash "tableNodes_s_kappa_cPa" record)
          (map 'vector (lambda (node) (coerce (copy-list node) 'vector)) (getf *reference-table* :nodes))
          (gethash "intervalErrorBoundsPa" record) (coerce (copy-list (getf *reference-table* :bounds)) 'vector))
    record))
