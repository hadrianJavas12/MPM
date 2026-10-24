;;;; Pure, bounded principal-stress MC return. No MP or input-array mutation.
(in-package :cl-mpm/models/mc-evolution)

(defparameter +plane-pairs+ '((0 1) (0 2) (1 0) (1 2) (2 0) (2 1)))
(defconstant +stress-atol+ 1d-6)
(defconstant +stress-rtol+ 1d-11)
(defconstant +kappa-tol+ 1d-13)
(defconstant +multiplier-tol+ 1d-12)

(defstruct (projection (:constructor %make-projection))
  tau plastic-increment kappa cohesion phi psi max-residual residuals work
  active multipliers iterations root-slope)

(defun dot3 (a b) (loop for i below 3 sum (* (aref a i) (aref b i))))
(defun max-abs3 (a) (loop for i below 3 maximize (abs (aref a i))))
(defun plastic-kappa-increment (b)
  (let ((mean (/ (+ (aref b 0) (aref b 1) (aref b 2)) 3d0)))
    (sqrt (* (/ 2d0 3d0) (loop for i below 3 sum (expt (- (aref b i) mean) 2))))))

(defun plane-vectors (angle)
  (map 'vector (lambda (pair)
                 (let ((out (make-array 3 :initial-element 0d0)) (s (sin angle)))
                   (setf (aref out (first pair)) (+ 1d0 s)
                         (aref out (second pair)) (- s 1d0)) out)) +plane-pairs+))

(defun d-times (b shear bulk)
  (let ((trace (+ (aref b 0) (aref b 1) (aref b 2))))
    (map 'vector (lambda (v) (+ (* 2d0 shear v) (* (- bulk (* (/ 2d0 3d0) shear)) trace))) b)))

(defun solve-small (matrix right)
  "Pivoted solve, sizes 1..3. Singular active bases are rejected, not regularized."
  (let* ((n (length right)) (a (make-array (list n (1+ n)) :initial-element 0d0))
         (scale (loop for row across matrix maximize (loop for v across row maximize (abs v)))))
    (when (= scale 0d0) (return-from solve-small nil))
    (dotimes (i n)
      (dotimes (j n) (setf (aref a i j) (aref (aref matrix i) j)))
      (setf (aref a i n) (aref right i)))
    (dotimes (column n)
      (let ((pivot column))
        (loop for i from (1+ column) below n do
          (when (> (abs (aref a i column)) (abs (aref a pivot column))) (setf pivot i)))
        (when (<= (abs (aref a pivot column)) (* 1d-12 scale))
          (return-from solve-small nil))
        (unless (= pivot column)
          (dotimes (j (1+ n)) (rotatef (aref a column j) (aref a pivot j))))
        (let ((divisor (aref a column column)))
          (loop for j from column to n do (setf (aref a column j) (/ (aref a column j) divisor))))
        (dotimes (i n)
          (unless (= i column)
            (let ((factor (aref a i column)))
              (loop for j from column to n do
                (decf (aref a i j) (* factor (aref a column j)))))))))
    (let ((answer (make-array n)))
      (dotimes (i n) (setf (aref answer i) (aref a i n))) answer)))

(defparameter +active-bases+
  '((1)
    (0 1)
    (1 3)
    (0 1 4)
    (1 3 4)
    (0 3 4)))

(defun plane-pair-index (i k)
  (position (list i k) +plane-pairs+ :test #'equal))

(defun sort-trial-permutation (trial)
  "Return permutation vector #(p0 p1 p2) such that trial[p0] >= trial[p1] >= trial[p2]."
  (let ((indices (list 0 1 2)))
    (coerce (stable-sort indices (lambda (a b) (> (aref trial a) (aref trial b)))) 'vector)))

(defun unpermute-projection (proj perm)
  "Map a projection computed in sorted principal frame back to the caller's axis order."
  (let* ((tau (make-array 3 :element-type 'double-float :initial-element 0d0))
         (b (make-array 3 :element-type 'double-float :initial-element 0d0))
         (res (make-array 6 :element-type 'double-float :initial-element 0d0))
         (mult (make-array 6 :element-type 'double-float :initial-element 0d0))
         (plane-map (make-array 6 :element-type 'fixnum :initial-element 0)))
    (dotimes (i 3)
      (let ((orig-i (aref perm i)))
        (setf (aref tau orig-i) (aref (projection-tau proj) i)
              (aref b orig-i) (aref (projection-plastic-increment proj) i))))
    (loop for (i k) in +plane-pairs+
          for sorted-idx from 0
          for orig-idx = (plane-pair-index (aref perm i) (aref perm k)) do
            (setf (aref plane-map sorted-idx) orig-idx
                  (aref res orig-idx) (aref (projection-residuals proj) sorted-idx)
                  (aref mult orig-idx) (aref (projection-multipliers proj) sorted-idx)))
    (%make-projection :tau tau
                      :plastic-increment b
                      :kappa (projection-kappa proj)
                      :cohesion (projection-cohesion proj)
                      :phi (projection-phi proj)
                      :psi (projection-psi proj)
                      :max-residual (projection-max-residual proj)
                      :residuals res
                      :work (projection-work proj)
                      :active (mapcar (lambda (a) (aref plane-map a)) (projection-active proj))
                      :multipliers mult
                      :iterations (projection-iterations proj)
                      :root-slope (projection-root-slope proj))))

(defun fixed-kappa-candidate (trial shear bulk j law old-kappa kappa active)
  (multiple-value-bind (c phi psi) (law-values law kappa)
    (let* ((normals (plane-vectors phi)) (flows (plane-vectors psi))
           (eta (if (eq (evolution-law-stress-measure law) :cauchy) j 1d0))
           (strength (* 2d0 eta c (cos phi))) (count (length active))
           (matrix (make-array count)) (rhs (make-array count)))
      (loop for a in active for row from 0 do
        (setf (aref matrix row) (make-array count)
              (aref rhs row) (- (dot3 (aref normals a) trial) strength))
        (loop for b in active for column from 0 do
          (setf (aref (aref matrix row) column)
                (dot3 (aref normals a) (d-times (aref flows b) shear bulk)))))
      (let ((local (solve-small matrix rhs)))
        (unless (and local (every #'finite-real-p local))
          (return-from fixed-kappa-candidate (values nil nil)))
        (let ((multipliers (make-array 6 :initial-element 0d0))
              (b (make-array 3 :initial-element 0d0)))
          (loop for index in active for value across local do
            (setf (aref multipliers index) value)
            (dotimes (axis 3) (incf (aref b axis) (* value (aref (aref flows index) axis)))))
          (let* ((db (d-times b shear bulk))
                 (tau (map 'vector #'- trial db))
                 (residuals (map 'vector (lambda (n) (- (dot3 n tau) strength)) normals))
                 (candidate (%make-projection :tau tau :plastic-increment b :kappa kappa
                              :cohesion c :phi phi :psi psi :multipliers multipliers
                              :active (copy-list active) :residuals residuals
                              :max-residual (reduce #'max residuals) :work (dot3 tau b))))
            (values candidate (- kappa old-kappa (plastic-kappa-increment b)))))))))

(defstruct (kappa-frame (:constructor %make-kappa-frame))
  kappa flows rhs g)

(defun build-kappa-frame (trial shear bulk j law kappa)
  (multiple-value-bind (c phi psi) (law-values law kappa)
    (let* ((normals (plane-vectors phi))
           (flows (plane-vectors psi))
           (dflows (map 'vector (lambda (f) (d-times f shear bulk)) flows))
           (eta (if (eq (evolution-law-stress-measure law) :cauchy) j 1d0))
           (strength (* 2d0 eta c (cos phi)))
           (rhs (make-array 6 :element-type 'double-float :initial-element 0d0))
           (g (make-array '(6 6) :element-type 'double-float :initial-element 0d0)))
      (dotimes (a 6)
        (setf (aref rhs a) (- (dot3 (aref normals a) trial) strength))
        (dotimes (b 6)
          (setf (aref g a b) (dot3 (aref normals a) (aref dflows b)))))
      (%make-kappa-frame :kappa kappa :flows flows :rhs rhs :g g))))

(defun eval-frame-active (frame old-kappa active)
  "Evaluate (values residual local-multipliers) for ACTIVE using a precomputed KAPPA-FRAME."
  (let* ((kappa (kappa-frame-kappa frame))
         (flows (kappa-frame-flows frame))
         (rhs6 (kappa-frame-rhs frame))
         (g6 (kappa-frame-g frame))
         (count (length active)))
    (let ((local
            (cond
              ((= count 1)
               (let* ((a0 (first active))
                      (g00 (aref g6 a0 a0))
                      (r0 (aref rhs6 a0)))
                 (when (> (abs g00) 1d-12)
                   (vector (/ r0 g00)))))
              ((= count 2)
               (let* ((a0 (first active))
                      (a1 (second active))
                      (g00 (aref g6 a0 a0))
                      (g01 (aref g6 a0 a1))
                      (g10 (aref g6 a1 a0))
                      (g11 (aref g6 a1 a1))
                      (scale (max (abs g00) (abs g01) (abs g10) (abs g11)))
                      (det (- (* g00 g11) (* g01 g10))))
                 (when (and (> scale 0d0) (> (abs det) (* 1d-12 scale scale)))
                   (let ((r0 (aref rhs6 a0))
                         (r1 (aref rhs6 a1)))
                     (vector (/ (- (* r0 g11) (* g01 r1)) det)
                             (/ (- (* g00 r1) (* r0 g10)) det))))))
              (t
               (let ((matrix (make-array count))
                     (rhs (make-array count)))
                 (loop for a in active for row from 0 do
                   (setf (aref matrix row) (make-array count)
                         (aref rhs row) (aref rhs6 a))
                   (loop for b in active for column from 0 do
                     (setf (aref (aref matrix row) column) (aref g6 a b))))
                 (solve-small matrix rhs))))))
      (unless (and local (every #'finite-real-p local))
        (return-from eval-frame-active (values nil nil)))
      (let ((b0 0d0) (b1 0d0) (b2 0d0))
        (loop for index in active for value across local
              for f = (aref flows index) do
          (incf b0 (* value (aref f 0)))
          (incf b1 (* value (aref f 1)))
          (incf b2 (* value (aref f 2))))
        (let* ((mean (/ (+ b0 b1 b2) 3d0))
               (dk (sqrt (* (/ 2d0 3d0)
                            (+ (expt (- b0 mean) 2)
                               (expt (- b1 mean) 2)
                               (expt (- b2 mean) 2))))))
          (values (- kappa old-kappa dk) local))))))

(defun fixed-kappa-residual-and-local (trial shear bulk j law old-kappa kappa active)
  "Lightweight residual/multiplier check used for bracket scanning and bisection."
  (eval-frame-active (build-kappa-frame trial shear bulk j law kappa) old-kappa active))

(defun negative-multiplier-backward-error (candidate shear bulk)
  "Conservative backward stress error (Pa) from negative flow multipliers.
An absolute strain-like multiplier allowance alone can admit a resolvably
negative KKT multiplier at high stiffness. Sum absolute negative contributions
to both principal stress and every yield plane, without cancellation, clamping
or changing the candidate. This additional check belongs only to the generic
MC-evolution PROJECT-PRINCIPAL return, whose complete flow is D*g. Wang point
and composite-apex models retain their separately gated acceptance behavior.
Call only after the shared candidate finite-value validation."
  (when (every (lambda (multiplier) (>= multiplier 0d0))
               (projection-multipliers candidate))
    (return-from negative-multiplier-backward-error 0d0))
  (unless (and (finite-real-p shear) (> shear 0d0)
               (finite-real-p bulk) (> bulk 0d0))
    (integration-fail "Finite positive elastic moduli required for multiplier stress error"))
  (let ((normals (plane-vectors (projection-phi candidate)))
        (flows (plane-vectors (projection-psi candidate))))
    (loop for multiplier across (projection-multipliers candidate)
          for flow across flows
          when (< multiplier 0d0)
            sum (let* ((dflow (d-times flow shear bulk))
                       (scale (max (max-abs3 dflow)
                                   (loop for normal across normals
                                         maximize (abs (dot3 normal dflow))))))
                  (* (- multiplier) scale)) into error-pa
          finally (return (float error-pa 1d0)))))

(defun admissible-candidate-p (candidate residual stress-tolerance)
  (and candidate (finite-real-p residual)
       (every #'finite-real-p
              (list (projection-kappa candidate) (projection-cohesion candidate)
                    (projection-phi candidate) (projection-psi candidate)
                    (projection-work candidate) (projection-max-residual candidate)))
       (every #'finite-real-p (projection-plastic-increment candidate))
       (every #'finite-real-p (projection-residuals candidate))
       (every #'finite-real-p (projection-multipliers candidate))
       (<= (abs residual) (* +kappa-tol+ (max 1d0 (projection-kappa candidate))))
       (every #'finite-real-p (projection-tau candidate))
       (let ((tau (projection-tau candidate)))
         (and (>= (aref tau 0) (- (aref tau 1) stress-tolerance))
              (>= (aref tau 1) (- (aref tau 2) stress-tolerance))))
       (every (lambda (x) (>= x (- +multiplier-tol+))) (projection-multipliers candidate))
       (<= (projection-max-residual candidate) stress-tolerance)
       (every (lambda (index) (<= (abs (aref (projection-residuals candidate) index)) stress-tolerance))
              (projection-active candidate))
       (>= (projection-work candidate)
           (- (* stress-tolerance (max 1d-12 (max-abs3 (projection-plastic-increment candidate))))))))

(defun bisect-coupled-root-fast (eval-res eval-full left lr right rr)
  (unless (and lr rr) (return-from bisect-coupled-root-fast nil))
  (when (<= (abs lr) 1d-15) (return-from bisect-coupled-root-fast (nth-value 0 (funcall eval-full left))))
  (when (<= (abs rr) 1d-15) (return-from bisect-coupled-root-fast (nth-value 0 (funcall eval-full right))))
  (unless (< (* lr rr) 0d0) (return-from bisect-coupled-root-fast nil))
  (let ((illinois-l lr)
        (illinois-r rr)
        (last-side 0))
    (loop for iter below 60 do
      (let* ((span (- right left))
             (secant (if (> (abs (- illinois-r illinois-l)) 1d-30)
                         (- left (* illinois-l (/ span (- illinois-r illinois-l))))
                         (* 0.5d0 (+ left right))))
             (margin (* 0.05d0 span))
             (middle (if (and (< (mod iter 3) 2)
                              (> secant (+ left margin))
                              (< secant (- right margin)))
                         secant
                         (* 0.5d0 (+ left right)))))
        (multiple-value-bind (residual local) (funcall eval-res middle)
          (unless (and residual local) (return-from bisect-coupled-root-fast nil))
          (when (or (<= (abs residual) 1d-15) (<= (abs (- right left)) 1d-15)
                    (= middle left) (= middle right))
            (return-from bisect-coupled-root-fast (nth-value 0 (funcall eval-full middle))))
          (if (< (* lr residual) 0d0)
              (progn
                (setf right middle rr residual illinois-r residual)
                (when (= last-side -1) (setf illinois-l (* 0.5d0 illinois-l)))
                (setf last-side -1))
              (progn
                (setf left middle lr residual illinois-l residual)
                (when (= last-side 1) (setf illinois-r (* 0.5d0 illinois-r)))
                (setf last-side 1)))))))
  (nth-value 0 (funcall eval-full (* 0.5d0 (+ left right)))))

(defun same-projection-p (a b stress-tolerance)
  (and (<= (max-abs3 (map 'vector #'- (projection-tau a) (projection-tau b)))
           (* 16d0 stress-tolerance))
       (<= (abs (- (projection-kappa a) (projection-kappa b))) 1d-10)))

(defun bracket-may-have-nonnegative-multipliers-p (local-left local-right)
  "On a linear segment of a table, if the same multiplier component is strictly
negative at both bracket endpoints, no nonnegative multiplier root exists inside."
  (and local-left local-right
       (loop for i below (length local-left)
             always (or (>= (aref local-left i) (- +multiplier-tol+))
                        (>= (aref local-right i) (- +multiplier-tol+))))))

(defun project-principal (trial e nu j law old-kappa)
  "Bounded pure return. Root isolation is sampled per table branch.
Final residual/complementarity are strict; global nonlinear uniqueness is not proved."
  (unless (and (typep law 'evolution-law) (= (length trial) 3)
               (every #'finite-real-p trial) (finite-real-p e) (> e 0d0)
               (finite-real-p nu) (< -1d0 nu 0.5d0)
               (finite-real-p j) (> j 0d0)
               (finite-real-p old-kappa) (>= old-kappa 0d0))
    (%principal-integration-fail "Invalid finite principal return input"
                                 trial e nu j law old-kappa trial e nu j old-kappa))
  (let* ((raw-trial (map 'vector (lambda (x) (float x 1d0)) trial))
         (perm (sort-trial-permutation raw-trial))
         (sorted-trial (vector (aref raw-trial (aref perm 0))
                               (aref raw-trial (aref perm 1))
                               (aref raw-trial (aref perm 2))))
         (shear (/ e (* 2d0 (+ 1d0 nu)))) (bulk (/ e (* 3d0 (- 1d0 (* 2d0 nu)))))
         (stress-tolerance (+ +stress-atol+ (* +stress-rtol+ (max 1d0 (max-abs3 sorted-trial)))))
         (roots nil) (evaluations 0)
         (breaks (sort (remove-duplicates
                       (cons old-kappa (remove-if (lambda (x) (< x old-kappa)) (law-breakpoints law)))
                       :test #'=) #'<)))
    (multiple-value-bind (c phi psi) (law-values law old-kappa)
      (let* ((eta (if (eq (evolution-law-stress-measure law) :cauchy) j 1d0))
             (strength (* 2d0 eta c (cos phi)))
             (residuals (map 'vector (lambda (n) (- (dot3 n raw-trial) strength)) (plane-vectors phi))))
        (when (<= (reduce #'max residuals) stress-tolerance)
          (return-from project-principal
            (%make-projection :tau (copy-seq raw-trial) :plastic-increment (vector 0d0 0d0 0d0)
                              :kappa old-kappa :cohesion c :phi phi :psi psi
                              :max-residual (reduce #'max residuals) :residuals residuals :work 0d0
                              :active nil :multipliers (make-array 6 :initial-element 0d0) :iterations 0)))))
    ;; Precompute shared 6-plane frames across each branch segment once in canonical Weyl chamber.
    (let* ((tail (car (last breaks)))
           (tail-frame (build-kappa-frame sorted-trial shear bulk j law tail))
           (segment-frames
             (loop for (left right) on breaks while right
                   collect (let ((frames (make-array 9)))
                             (dotimes (s 9)
                               (let ((coord (+ left (* (/ (float s 1d0) 8d0) (- right left)))))
                                 (setf (aref frames s)
                                       (build-kappa-frame sorted-trial shear bulk j law coord))))
                             frames))))
      (dolist (active +active-bases+)
        (flet ((evaluate-full (coordinate)
                 (incf evaluations)
                 (fixed-kappa-candidate sorted-trial shear bulk j law old-kappa coordinate active))
               (evaluate-res (coordinate)
                 (incf evaluations)
                 (fixed-kappa-residual-and-local sorted-trial shear bulk j law old-kappa coordinate active)))
          (labels ((consider (candidate)
                     (when candidate
                       (multiple-value-bind (checked residual) (evaluate-full (projection-kappa candidate))
                         (when (and (admissible-candidate-p checked residual stress-tolerance)
                                    (<= (negative-multiplier-backward-error checked shear bulk)
                                        stress-tolerance))
                           (unless (some (lambda (old) (same-projection-p old checked stress-tolerance)) roots)
                             (push checked roots)))))))
            ;; Constant-tail root is explicit; there is no arbitrary kappa search cap.
            (incf evaluations)
            (multiple-value-bind (res-tail local-tail) (eval-frame-active tail-frame old-kappa active)
              (when (and res-tail local-tail
                         (every (lambda (x) (>= x (- +multiplier-tol+))) local-tail))
                (let ((coordinate (- tail res-tail)))
                  (when (>= coordinate tail)
                    (consider (nth-value 0 (evaluate-full coordinate)))))))
            ;; Each finite table branch is independently scanned.
            (dolist (frames segment-frames)
              (let* ((f0 (aref frames 0))
                     (previous (kappa-frame-kappa f0)))
                (incf evaluations)
                (multiple-value-bind (prev-res prev-local) (eval-frame-active f0 old-kappa active)
                  (when (and prev-res prev-local (<= (abs prev-res) 1d-15)
                             (every (lambda (x) (>= x (- +multiplier-tol+))) prev-local))
                    (consider (nth-value 0 (evaluate-full previous))))
                  (loop for sample from 1 to 8
                        for frame = (aref frames sample)
                        for coordinate = (kappa-frame-kappa frame) do
                          (incf evaluations)
                          (multiple-value-bind (curr-res curr-local) (eval-frame-active frame old-kappa active)
                            (when (and curr-res curr-local (<= (abs curr-res) 1d-15)
                                       (every (lambda (x) (>= x (- +multiplier-tol+))) curr-local))
                              (consider (nth-value 0 (evaluate-full coordinate))))
                            (when (and prev-res curr-res (< (* prev-res curr-res) 0d0)
                                       (bracket-may-have-nonnegative-multipliers-p prev-local curr-local))
                              (consider (bisect-coupled-root-fast
                                         #'evaluate-res #'evaluate-full
                                         previous prev-res coordinate curr-res)))
                            (setf previous coordinate
                                  prev-res curr-res
                                  prev-local curr-local))))))))))
    (unless roots
      (%principal-integration-fail "No admissible coupled active-set solution; no apex clamp or strength floor applied"
                                   raw-trial e nu j law old-kappa
                                   :trial (coerce raw-trial 'list) :old-kappa old-kappa :evaluations evaluations))
    (when (rest roots)
      (%principal-integration-fail "Multiple distinct admissible coupled roots; subdivision/continuation is not implemented"
                                   raw-trial e nu j law old-kappa
                                   (mapcar (lambda (r) (list (projection-kappa r) (coerce (projection-tau r) 'list))) roots)))
    (let ((answer (unpermute-projection (first roots) perm)))
      (setf (projection-iterations answer) evaluations)
      answer)))
