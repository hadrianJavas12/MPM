;;;; Isolated SMALL-STRAIN, FIXED-FRAME Soil2 material-point prototype.
;;;; Literal signed Ep norm from Wang2017 Eq5-6: reversal can reduce strength
;;;; coordinate and increase cohesion. This is NOT an approved healing rule,
;;;; particle adapter, finite-strain transport, or validated slope material.
(defpackage :cl-mpm/models/wang2017-point
  (:use :cl :cl-mpm/models/wang2017)
  (:export #:project-paper-principal #:paper-projection
           #:paper-projection-tau #:paper-projection-plastic-increment
           #:paper-projection-fixed-increment #:paper-projection-history
           #:paper-projection-kps #:paper-projection-cohesion
           #:paper-projection-phi #:paper-projection-psi
           #:paper-projection-residuals #:paper-projection-max-residual
           #:paper-projection-multipliers #:paper-projection-active
           #:paper-projection-work #:paper-projection-evaluations
           #:paper-projection-history-residual #:paper-projection-branch))
(in-package :cl-mpm/models/wang2017-point)

(defstruct (paper-projection (:constructor %make-paper-projection)
                            (:copier nil) (:conc-name %paper-))
  (native nil :read-only t) (history nil :read-only t)
  (fixed-increment nil :read-only t) (history-residual 0d0 :read-only t)
  (evaluations 0 :read-only t) (branch nil :read-only t))

;; No retained vector or tensor is exposed through the public readers.
(defun paper-projection-tau (p) (copy-seq (mc-evolution:projection-tau (%paper-native p))))
(defun paper-projection-plastic-increment (p)
  (copy-seq (mc-evolution:projection-plastic-increment (%paper-native p))))
(defun paper-projection-fixed-increment (p) (copy-seq (%paper-fixed-increment p)))
(defun paper-projection-history (p) (make-paper-history (history-tensor (%paper-history p))))
(defun paper-projection-kps (p) (history-kps (%paper-history p)))
(defun paper-projection-cohesion (p) (mc-evolution:projection-cohesion (%paper-native p)))
(defun paper-projection-phi (p) (mc-evolution:projection-phi (%paper-native p)))
(defun paper-projection-psi (p) (mc-evolution:projection-psi (%paper-native p)))
(defun paper-projection-residuals (p) (copy-seq (mc-evolution:projection-residuals (%paper-native p))))
(defun paper-projection-max-residual (p) (mc-evolution:projection-max-residual (%paper-native p)))
(defun paper-projection-multipliers (p)
  (copy-seq (mc-evolution:projection-multipliers (%paper-native p))))
(defun paper-projection-active (p) (copy-list (mc-evolution:projection-active (%paper-native p))))
(defun paper-projection-work (p) (mc-evolution:projection-work (%paper-native p)))
(defun paper-projection-evaluations (p) (%paper-evaluations p))
(defun paper-projection-history-residual (p) (%paper-history-residual p))
(defun paper-projection-branch (p) (%paper-branch p))

(defun soil2-point-law ()
  ;; A fresh, private law: callers cannot change the constants during a search.
  (mc-evolution:make-evolution-law
   :variant :hs :points '((0d0 35d0)) :psi 0d0 :stress-measure :cauchy
   :cohesion-points '((0d0 30000d0) (.02d0 15000d0))
   :strain-assumption "Literal Wang2017 Eq5-6 signed Ep tensor norm in one fixed frame; no irreversible maximum or finite-strain transport"))

(defun checked-basis (basis)
  "Own a 3x3 orthonormal Q, whose columns map principal axes into the fixed frame."
  (unless (and (arrayp basis) (equal (array-dimensions basis) '(3 3)))
    (mc-evolution::integration-fail "Principal-to-fixed basis must be a 3x3 array"))
  (let ((q (make-array '(3 3) :element-type 'double-float)))
    (dotimes (i 3) (dotimes (j 3)
      (let ((x (aref basis i j)))
        (unless (mc-evolution::finite-real-p x)
          (mc-evolution::integration-fail "Basis component is not finite" i j))
        (setf (aref q i j) (float x 1d0)))))
    (dotimes (a 3) (dotimes (b 3)
      (unless (<= (abs (- (loop for i below 3 sum (* (aref q i a) (aref q i b)))
                           (if (= a b) 1d0 0d0))) 1d-12)
        (mc-evolution::integration-fail "Principal-to-fixed basis is not orthonormal"))))
    q))

(defun fixed-increment (principal q)
  "Q diag(b) Q^T in xx yy zz yz zx xy order, with physical tensor shear."
  (flet ((entry (i j)
           (loop for a below 3 sum (* (aref q i a) (aref principal a) (aref q j a)))))
    (vector (entry 0 0) (entry 1 1) (entry 2 2)
            (entry 1 2) (entry 2 0) (entry 0 1))))

(defun tensor-dev (tensor)
  (let* ((copy (copy-seq tensor))
         (mean (/ (+ (aref copy 0) (aref copy 1) (aref copy 2)) 3d0)))
    (dotimes (i 3) (decf (aref copy i) mean)) copy))

(defun tensor-dot (a b)
  (+ (loop for i below 3 sum (* (aref a i) (aref b i)))
     (* 2d0 (loop for i from 3 below 6 sum (* (aref a i) (aref b i))))))

(defun real-quadratic-roots (a b c)
  "All real roots, stable q/a and c/q evaluation; second value flags identity 0=0.
Only EXACT zero selects the linear case: a small nonzero a can have two roots."
  (let ((scale (max (abs a) (abs b) (abs c))))
    (when (zerop scale) (return-from real-quadratic-roots (values nil t)))
    (setf a (/ a scale) b (/ b scale) c (/ c scale))
    (when (zerop a)
      (return-from real-quadratic-roots
        (values (unless (zerop b) (list (/ (- c) b))) nil)))
    (let* ((bb (* b b)) (four-ac (* 4d0 a c)) (disc (- bb four-ac)))
      ;; A roundoff-sized negative discriminant represents a repeated root;
      ;; every resulting candidate still passes the UNSQUARED history residual.
      (when (and (< disc 0d0)
                 (>= disc (- (* 32d0 double-float-epsilon (+ bb (abs four-ac))))))
        (setf disc 0d0))
      (when (< disc 0d0) (return-from real-quadratic-roots (values nil nil)))
      (when (zerop disc)
        (return-from real-quadratic-roots (values (list (/ (- b) (* 2d0 a))) nil)))
      (let ((q (* -.5d0 (+ b (float-sign b (sqrt disc))))))
        (values (list (/ q a) (/ c q)) nil)))))

(defun identity-admissible-interval (start end stress-tolerance)
  "Conservative affine feasibility interval for a 0=0 history branch.
Eliminate branches whose multipliers, ordering or yield inequalities cannot hold
anywhere, rather than rejecting a valid solution due to an inadmissible identity.
A surviving identity is rejected: isolated-root continuation is not defined."
  (let ((lo 0d0) (hi .02d0))
    (labels ((restrict (left right)
               ;; The inequality interpolated from LEFT to RIGHT must be >=0.
               (let ((slope (/ (- right left) .02d0)))
                 (cond ((zerop slope) (when (< left 0d0)
                                       (return-from identity-admissible-interval nil)))
                       ((plusp slope) (setf lo (max lo (/ (- left) slope))))
                       (t (setf hi (min hi (/ (- left) slope)))))
                 (when (> lo hi) (return-from identity-admissible-interval nil)))))
      (dotimes (i 6)
        (restrict (+ (aref (mc-evolution:projection-multipliers start) i) mc-evolution::+multiplier-tol+)
                  (+ (aref (mc-evolution:projection-multipliers end) i) mc-evolution::+multiplier-tol+))
        (restrict (- stress-tolerance (aref (mc-evolution:projection-residuals start) i))
                  (- stress-tolerance (aref (mc-evolution:projection-residuals end) i))))
      (dotimes (i 2)
        (restrict (+ stress-tolerance (- (aref (mc-evolution:projection-tau start) i)
                                         (aref (mc-evolution:projection-tau start) (1+ i))))
                  (+ stress-tolerance (- (aref (mc-evolution:projection-tau end) i)
                                         (aref (mc-evolution:projection-tau end) (1+ i))))))
      (dolist (i (mc-evolution:projection-active start))
        (restrict (+ stress-tolerance (aref (mc-evolution:projection-residuals start) i))
                  (+ stress-tolerance (aref (mc-evolution:projection-residuals end) i))))
      (values lo hi))))

(defun project-paper-principal (trial e nu j history basis)
  "Pure coupled Soil2 prototype: Kirchhoff TRIAL, E/nu, positive J, owned HISTORY,
and orthonormal Q mapping trial principal axes into HISTORY's SAME fixed frame.
Stress/flow arrays are returned in the caller's original principal axis order.
Searches the entire [0,.02] branch and constant tail, INCLUDING kps<old kps.
Rejects absent or multiple distinct admissible solutions; no apex/tensile clamp."
  (unless (and (typep trial 'sequence) (= (length trial) 3)
               (every #'mc-evolution::finite-real-p trial)
               (mc-evolution::finite-real-p e) (> e 0d0)
               (mc-evolution::finite-real-p nu) (< -1d0 nu .5d0)
               (mc-evolution::finite-real-p j) (> j 0d0)
               (typep history 'paper-history))
    (mc-evolution::integration-fail "Invalid fixed-frame paper return input"))
  (let* ((q (checked-basis basis))
         (old (make-paper-history (history-tensor history)))
         (raw (map 'vector (lambda (x) (float x 1d0)) trial))
         (perm (mc-evolution::sort-trial-permutation raw))
         (sorted (map 'vector (lambda (i) (aref raw i)) perm))
         (sorted-q (make-array '(3 3) :element-type 'double-float))
         (shear (/ e (* 2d0 (+ 1d0 nu))))
         (bulk (/ e (* 3d0 (- 1d0 (* 2d0 nu)))))
         (tol (+ mc-evolution::+stress-atol+
                 (* mc-evolution::+stress-rtol+ (max 1d0 (mc-evolution::max-abs3 raw)))))
         (law (soil2-point-law)) (old-k (history-kps old))
         (roots nil) (evaluations 0))
    (dotimes (i 3) (dotimes (a 3)
      (setf (aref sorted-q i a) (aref q i (aref perm a)))))
    (multiple-value-bind (c phi psi) (mc-evolution:law-values law old-k)
      (let ((res (map 'vector
                      (lambda (n) (- (mc-evolution::dot3 n raw) (* 2d0 j c (cos phi))))
                      (mc-evolution::plane-vectors phi))))
        (when (<= (reduce #'max res) tol)
          (return-from project-paper-principal
            (%make-paper-projection
             :native (mc-evolution::%make-projection
                      :tau raw :plastic-increment #(0d0 0d0 0d0) :kappa old-k
                      :cohesion c :phi phi :psi psi :max-residual (reduce #'max res)
                      :residuals res :work 0d0 :active nil
                      :multipliers (make-array 6 :initial-element 0d0))
             :history old :fixed-increment (make-array 6 :initial-element 0d0)
             :branch :elastic)))))
    (dolist (active mc-evolution::+active-bases+)
      (labels ((evaluate-at (k)
                 (incf evaluations)
                 ;; Deliberately discard the legacy incremental-J2 residual.
                 (let ((candidate (nth-value 0 (mc-evolution::fixed-kappa-candidate
                                                sorted shear bulk j law 0d0 k active))))
                   (when candidate
                     (let* ((delta (fixed-increment
                                    (mc-evolution:projection-plastic-increment candidate) sorted-q))
                            (next (advance-history old delta)))
                       (values candidate (- k (history-kps next)) next delta)))))
               (consider (k branch)
                 (when (and (mc-evolution::finite-real-p k) (>= k 0d0))
                   (multiple-value-bind (candidate residual next delta) (evaluate-at k)
                     (when (mc-evolution::admissible-candidate-p candidate residual tol)
                       (unless (some (lambda (r) (mc-evolution::same-projection-p
                                                 (first r) candidate tol)) roots)
                         (push (list candidate next delta residual branch) roots)))))))
        (let ((zero (nth-value 0 (evaluate-at 0d0)))
              (end (nth-value 0 (evaluate-at .02d0))))
          (when (and zero end)
            (let* ((delta0 (fixed-increment (mc-evolution:projection-plastic-increment zero) sorted-q))
                   (delta-end (fixed-increment (mc-evolution:projection-plastic-increment end) sorted-q))
                   (a (tensor-dev (map 'vector #'+ (history-tensor old) delta0)))
                   (b (tensor-dev (map 'vector (lambda (x y) (/ (- x y) .02d0)) delta-end delta0)))
                   ;; k^2 = .5 (A+kB):(A+kB), with true shear weights.
                   (qa (- 1d0 (* .5d0 (tensor-dot b b))))
                   (qb (- (tensor-dot a b)))
                   (qc (* -.5d0 (tensor-dot a a))))
              (multiple-value-bind (coordinates identity-p) (real-quadratic-roots qa qb qc)
                (when (and identity-p (identity-admissible-interval zero end tol))
                  (mc-evolution::integration-fail
                   "Potentially admissible paper history continuum; isolated-root continuation is undefined" active))
                (dolist (k coordinates)
                  (when (<= 0d0 k .02d0) (consider k :softening)))))
            ;; Cohesion is constant for k>=.02: b_res is constant too.
            (let* ((delta (fixed-increment (mc-evolution:projection-plastic-increment end) sorted-q))
                   (tail-k (history-kps (advance-history old delta))))
              (when (>= tail-k .02d0) (consider tail-k :residual)))))))
    (unless roots
      (mc-evolution::integration-fail
       "No admissible signed-tensor Soil2 solution; no apex clamp or irreversible maximum applied"
       :trial (coerce raw 'list) :old-kps old-k :evaluations evaluations))
    (when (rest roots)
      (mc-evolution::integration-fail
       "Multiple distinct signed-tensor Soil2 roots; continuation is undefined"
       (mapcar (lambda (r) (list (mc-evolution:projection-kappa (first r))
                                (coerce (mc-evolution:projection-tau (first r)) 'list))) roots)))
    (destructuring-bind (native next delta residual branch) (first roots)
      (%make-paper-projection
       :native (mc-evolution::unpermute-projection native perm)
       :history next :fixed-increment delta :history-residual residual
       :evaluations evaluations :branch branch))))
