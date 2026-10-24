;;;; Separate model: six psi=0 shear modes plus g_A=p at hydrostatic apex only.
;;;; This is an explicit constitutive extension, not a repair to strict MC.
(in-package :cl-mpm/models/wang2017-apex)

(defun %nonnegative-shear-representation (deviator)
  "Canonical nonnegative transfers for d=sum lambda_ij(e_i-e_j).
All six MC planes coincide at the apex. This representation proves flow
admissibility only; it does not select between distinct stress/history roots."
  (let ((positive (map 'vector (lambda (x) (max 0d0 x)) deviator))
        (negative (map 'vector (lambda (x) (max 0d0 (- x))) deviator))
        (multipliers (make-array 6 :initial-element 0d0)))
    (dotimes (i 3)
      (dotimes (j 3)
        (unless (= i j)
          (let ((amount (min (aref positive i) (aref negative j))))
            (setf (aref multipliers (mc-evolution::plane-pair-index i j)) amount)
            (decf (aref positive i) amount)
            (decf (aref negative j) amount)))))
    multipliers))

(defun %apex-candidate (context)
  "At most one coupled apex candidate; NIL means its q is negative/inadmissible.
Use the same captured rotated Ep, Q and J as every regular candidate."
  (let* ((trial (getf context :sorted)) (g (getf context :shear))
         (bulk (getf context :bulk)) (j (getf context :jacobian))
         (basis (getf context :basis)) (old (getf context :history))
         (tol (getf context :tolerance)) (law (getf context :law))
         (mean (/ (reduce #'+ trial) 3d0))
         (dev (map 'vector (lambda (x) (/ (- x mean) (* 2d0 g))) trial))
         (dev-fixed (point::fixed-increment dev basis))
         (dev-next (paper:advance-history old dev-fixed))
         (kps (paper:history-kps dev-next)))
    (multiple-value-bind (c phi psi) (mc-evolution:law-values law kps)
      (let* ((pressure (/ (* j c (cos phi)) (sin phi)))
             ;; q=lambda_A because gradient(p)=I/3; no sign clamp.
             (q (/ (- mean pressure) bulk)))
        (unless (and (mc-evolution::finite-real-p q) (>= q 0d0))
          (return-from %apex-candidate nil))
        (let* ((plastic (map 'vector (lambda (x) (+ x (/ q 3d0))) dev))
               (fixed (point::fixed-increment plastic basis))
               (next (paper:advance-history old fixed))
               (history-residual (- kps (paper:history-kps next)))
               (tau (make-array 3 :initial-element pressure))
               (residuals (map 'vector
                              (lambda (n) (- (mc-evolution::dot3 n tau)
                                             (* 2d0 j c (cos phi))))
                              (mc-evolution::plane-vectors phi)))
               (multipliers (%nonnegative-shear-representation dev))
               (shear-flow (make-array 3 :initial-element 0d0))
               (compliance (map 'vector #'- trial
                                (mc-evolution::d-times plastic g bulk)))
               (work (mc-evolution::dot3 tau plastic))
               (work-tolerance (* 8d0 tol (max 1d-12 (mc-evolution::max-abs3 plastic))))
               (energy-release (+ (* g (mc-evolution::dot3 dev dev))
                                  (* pressure q) (* .5d0 bulk q q)))
               (candidate (mc-evolution::%make-projection
                           :tau tau :plastic-increment plastic :kappa kps
                           :cohesion c :phi phi :psi psi
                           :max-residual (reduce #'max residuals) :residuals residuals
                           :work work :active '(0 1 2 3 4 5)
                           :multipliers multipliers :iterations 1)))
          (loop for (i j) in mc-evolution::+plane-pairs+
                for multiplier across multipliers do
                  (incf (aref shear-flow i) multiplier)
                  (decf (aref shear-flow j) multiplier))
          ;; Physical shear convention is used throughout: no engineering-shear
          ;; factor in Ep, Q diag(delta) Q^T or its Frobenius norm.
          (when (and (mc-evolution::admissible-candidate-p candidate history-residual tol)
                     (<= (mc-evolution::max-abs3 (map 'vector #'- shear-flow dev)) 1d-13)
                     (<= (mc-evolution::max-abs3 (map 'vector #'- compliance tau)) (* 8d0 tol))
                     (<= (abs (- (reduce #'+ plastic) q)) 1d-13)
                     (<= (abs (- work (* pressure q))) work-tolerance)
                     (mc-evolution::finite-real-p energy-release)
                     (>= (- energy-release work) (- work-tolerance)))
            (list candidate next fixed history-residual :hydrostatic-apex q)))))))

(defun %same-physical-root-p (a b tolerance)
  "Deduplicate the same state, not distinct shear-multiplier representations."
  (and (mc-evolution::same-projection-p (first a) (first b) tolerance)
       (<= (mc-evolution::max-abs3
            (map 'vector #'- (mc-evolution:projection-plastic-increment (first a))
                             (mc-evolution:projection-plastic-increment (first b)))) 1d-13)
       (every (lambda (x y) (<= (abs (- x y)) 1d-13))
              (paper:history-tensor (second a)) (paper:history-tensor (second b)))))

(defun %root-summary (root)
  (let ((projection (first root)))
    (list :branch (fifth root) :kps (mc-evolution:projection-kappa projection)
          :tau (coerce (mc-evolution:projection-tau projection) 'list)
          :plastic-increment (coerce (mc-evolution:projection-plastic-increment projection) 'list)
          :apex-multiplier (or (sixth root) 0d0))))

(defun project-paper-principal-with-apex (trial e nu j history basis)
  "Opt-in composite flow: enumerate ALL strict roots and the hydrostatic apex.
Keep the legacy elastic screen. Reject absent/multiple physical roots; do not
select an apex to force failure or apply an exception-triggered stress clamp.
The native adapter separately rejects history decrease outside monotonic scope."
  (multiple-value-bind (roots context) (point::%collect-paper-candidates trial e nu j history basis)
    (when (getf context :elastic)
      (return-from project-paper-principal-with-apex (getf context :elastic)))
    (let ((apex (%apex-candidate context)))
      (incf (getf context :evaluations))
      (when (and apex (not (some (lambda (root)
                                  (%same-physical-root-p root apex (getf context :tolerance))) roots)))
        (push apex roots)))
    (unless roots
      (mc-evolution::integration-fail
       "No admissible signed-tensor Soil2 composite-apex solution"
       :trial (coerce (getf context :raw) 'list) :old-kps (getf context :old-kps)
       :evaluations (getf context :evaluations)))
    (when (rest roots)
      (mc-evolution::integration-fail
       "Multiple distinct signed-tensor Soil2 composite-apex roots; continuation is undefined"
       (mapcar #'%root-summary roots)))
    (point::%projection-from-root (first roots) context)))
