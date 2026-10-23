;;;; Wang et al. (2017), Eq. 5-6: norm of a signed accumulated plastic tensor.
;;;; All six-vectors here use xx yy zz yz zx xy, with TRUE tensor shear.
;;;; Components share a fixed frame. No finite-strain transport is implied.
(in-package :cl-mpm/models/wang2017)

(defun checked-tensor (components)
  (unless (and (typep components 'sequence) (= (length components) 6))
    (error "A symmetric tensor requires six components: xx yy zz yz zx xy."))
  (map 'vector
       (lambda (value)
         (unless (handler-case
                     (and (realp value)
                          (<= (- most-positive-double-float) value
                              most-positive-double-float))
                   (arithmetic-error () nil))
           (error "Plastic tensor component must be finite and representable: ~S" value))
         (float value 1d0))
       components))

(defun engineering-voigt-to-tensor (components)
  "Convert engine-order engineering shear gamma to physical tensor shear gamma/2."
  (let ((tensor (checked-tensor components)))
    (loop for i from 3 below 6 do (setf (aref tensor i) (* .5d0 (aref tensor i))))
    tensor))

(defun tensor-to-engineering-voigt (components)
  "Convert physical tensor shear to engineering shear; returns an owned vector."
  (let ((tensor (checked-tensor components)))
    (loop for i from 3 below 6 do (setf (aref tensor i) (* 2d0 (aref tensor i))))
    tensor))

(defun paper-kps (components)
  "sqrt(0.5 * dev(Ep):dev(Ep)), not the sum of norms of plastic increments."
  (let* ((tensor (checked-tensor components))
         (scale (reduce #'max tensor :key #'abs)))
    (when (zerop scale) (return-from paper-kps 0d0))
    ;; Normalize before taking trace/squares: even a large hydrostatic tensor
    ;; must give zero without overflowing its intermediate trace.
    (setf tensor (map 'vector (lambda (x) (/ x scale)) tensor))
    (let* ((mean (/ (+ (aref tensor 0) (aref tensor 1) (aref tensor 2)) 3d0))
         (norm-squared
           (+ (loop for i below 3 sum (expt (- (aref tensor i) mean) 2))
              (* 2d0 (loop for i from 3 below 6 sum (expt (aref tensor i) 2))))))
      (* scale (sqrt (* .5d0 norm-squared))))))

(defstruct (paper-history (:constructor %make-paper-history (tensor))
                          (:copier nil) (:conc-name %history-))
  (tensor #(0d0 0d0 0d0 0d0 0d0 0d0) :read-only t))

(defun make-paper-history (&optional (components #(0d0 0d0 0d0 0d0 0d0 0d0)))
  "Own a copy of signed Ep; this is a coordinate state, not a constitutive update."
  (%make-paper-history (checked-tensor components)))

(defun history-tensor (history)
  "Return an owned copy; callers cannot mutate the retained history."
  (copy-seq (%history-tensor history)))

(defun history-kps (history)
  (paper-kps (%history-tensor history)))

(defun advance-history (history plastic-increment)
  "Return a NEW candidate state in the SAME frame; the old state stays unchanged.
Reversal may reduce kps. No irreversible maximum or healing rule is introduced."
  (let* ((increment (checked-tensor plastic-increment))
         (candidate (map 'vector #'+ (%history-tensor history) increment)))
    (make-paper-history candidate)))
