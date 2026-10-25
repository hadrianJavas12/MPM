;;;; Pure perfect/Cauchy/psi0 return with a separately declared g_A=p mode.
(in-package :cl-mpm/models/mc-composite-apex)

(defstruct (apex-projection (:include mc:projection)
                           (:constructor %make-apex-projection))
  (branch :hydrostatic-apex) (apex-multiplier 0d0))

(defun %checked-material-parameters (e nu law old-kappa)
  "Reject unsupported inputs before elastic moduli or apex divisions.
The existing :PERFECT law evaluates its tables at coordinate zero, so this
scope has constant strength even when its otherwise unused table has entries."
  (unless (and (mc::finite-real-p e) (> e 0d0)
               (mc::finite-real-p nu) (< -1d0 nu 0.5d0)
               (mc::finite-real-p old-kappa) (>= old-kappa 0d0)
               (typep law 'mc:evolution-law)
               (eq (mc:evolution-law-variant law) :perfect)
               (eq (mc:evolution-law-stress-measure law) :cauchy)
               (mc::finite-real-p (mc:evolution-law-psi law))
               (= (mc:evolution-law-psi law) 0d0))
    (mc::integration-fail "Composite apex requires finite elasticity/history and perfect Cauchy psi0 law"))
  (multiple-value-bind (c phi psi) (mc:law-values law 0d0)
    (unless (and (mc::finite-real-p c) (>= c 0d0)
                 (mc::finite-real-p phi) (< 0d0 phi (/ pi 2d0))
                 (mc::finite-real-p psi) (= psi 0d0))
      (mc::integration-fail "Composite apex requires finite nonnegative cohesion and 0<phi<pi/2"))
    (values c phi psi)))

(defun %nonnegative-shear-representation (deviator)
  "Represent d=sum lambda_ij(e_i-e_j) by nonnegative transfers.
Positive/negative parts are temporary bookkeeping; the actual deviatoric and
full plastic increments are never altered. Their reconstruction is checked
in stress units before accepting the candidate."
  (let ((positive (map 'vector (lambda (x) (if (> x 0d0) x 0d0)) deviator))
        (negative (map 'vector (lambda (x) (if (< x 0d0) (- x) 0d0)) deviator))
        (multipliers (make-array 6 :initial-element 0d0)))
    (dotimes (i 3)
      (dotimes (j 3)
        (unless (= i j)
          (let ((amount (min (aref positive i) (aref negative j))))
            (setf (aref multipliers (mc::plane-pair-index i j)) amount)
            (decf (aref positive i) amount)
            (decf (aref negative j) amount)))))
    multipliers))

(defun %analytic-apex (trial shear bulk j c phi old-kappa pressure mean tolerance)
  (let* ((deviator (map 'vector (lambda (x) (/ (- x mean) (* 2d0 shear))) trial))
         ;; grad(g_A)=I/3, therefore q is both lambda_A and plastic volume.
         (q (/ (- mean pressure) bulk))
         (plastic (map 'vector (lambda (x) (+ x (/ q 3d0))) deviator))
         (tau (make-array 3 :initial-element pressure)))
    (unless (and (every #'mc::finite-real-p deviator)
                 (every #'mc::finite-real-p plastic)
                 (mc::finite-real-p q) (>= q 0d0))
      (mc::integration-fail "Nonfinite or negative composite apex flow"))
    (let* ((multipliers (%nonnegative-shear-representation deviator))
           (shear-flow (make-array 3 :initial-element 0d0))
           (returned (map 'vector #'- trial (mc::d-times plastic shear bulk)))
           (offset (* 2d0 j c (cos phi)))
           (residuals (map 'vector (lambda (normal) (- (mc::dot3 normal tau) offset))
                           (mc::plane-vectors phi)))
           (increment (mc::plastic-kappa-increment plastic))
           (work (mc::dot3 tau plastic))
           (work-tolerance (* tolerance (max 1d-12 (mc::max-abs3 plastic))))
           (energy-release (+ (* shear (mc::dot3 deviator deviator))
                              (* pressure q) (* 0.5d0 bulk q q)))
           (result (%make-apex-projection
                    :tau tau :plastic-increment plastic :kappa (+ old-kappa increment)
                    :cohesion c :phi phi :psi 0d0 :residuals residuals
                    :max-residual (reduce #'max residuals) :work work
                    :active (loop for i below 6 collect i)
                    :multipliers multipliers :iterations 1
                    :branch :hydrostatic-apex :apex-multiplier q)))
      (loop for (i j-axis) in mc:+plane-pairs+ for multiplier across multipliers do
        (incf (aref shear-flow i) multiplier)
        (decf (aref shear-flow j-axis) multiplier))
      (unless (and (mc::admissible-candidate-p result 0d0 tolerance)
                   (every (lambda (x) (>= x 0d0)) multipliers)
                   (<= (* 2d0 shear (mc::max-abs3 (map 'vector #'- shear-flow deviator))) tolerance)
                   (<= (mc::max-abs3 (map 'vector #'- returned tau)) tolerance)
                   (<= (* bulk (abs (- (reduce #'+ plastic) q))) tolerance)
                   (<= (abs (- work (* pressure q))) work-tolerance)
                   (mc::finite-real-p energy-release)
                   (>= (- energy-release work) (- work-tolerance)))
        (mc::integration-fail "Composite apex compliance, flow, yield or work identity failed"))
      result)))

(defun project-principal-with-apex (trial e nu j law old-kappa)
  "Opt-in perfect/Cauchy/psi0 shear plus volumetric g_A=p at hydrostatic apex.
Preserve the old elastic screen and its stress tolerance exactly. Above the
cap by more than tol/(2sin(phi)), summed yield inequalities exclude every
regular psi0 return even at that tolerance. Only that disjoint domain uses
the analytic apex. Delegate equality, cap band and all other states to the
unchanged strict projector, preserving its rejection/ambiguity behavior.
There is no exception fallback, stress clamp or strength/history replacement."
  (unless (and (typep trial 'sequence) (= (length trial) 3)
               (every #'mc::finite-real-p trial)
               (mc::finite-real-p j) (> j 0d0))
    (mc::integration-fail "Invalid finite composite apex principal trial or Jacobian"))
  (multiple-value-bind (c phi psi) (%checked-material-parameters e nu law old-kappa)
    (declare (ignore psi))
    (let* ((raw (map 'vector (lambda (x) (float x 1d0)) trial))
           (tolerance (+ mc::+stress-atol+
                         (* mc::+stress-rtol+ (max 1d0 (mc::max-abs3 raw)))))
           (offset (* 2d0 j c (cos phi)))
           (residuals (map 'vector (lambda (normal) (- (mc::dot3 normal raw) offset))
                           (mc::plane-vectors phi))))
      (when (<= (reduce #'max residuals) tolerance)
        (return-from project-principal-with-apex
          (mc:project-principal trial e nu j law old-kappa)))
      (let* ((mean (/ (reduce #'+ raw) 3d0))
             (pressure (/ (* j c (cos phi)) (sin phi)))
             (allowance (/ tolerance (* 2d0 (sin phi)))))
        (unless (and (mc::finite-real-p mean) (mc::finite-real-p pressure)
                     (mc::finite-real-p allowance))
          (mc::integration-fail "Nonfinite composite apex stress bound"))
        (if (> (- mean pressure) allowance)
            (%analytic-apex raw (/ e (* 2d0 (+ 1d0 nu)))
                            (/ e (* 3d0 (- 1d0 (* 2d0 nu))))
                            j c phi old-kappa pressure mean tolerance)
            (mc:project-principal trial e nu j law old-kappa))))))
