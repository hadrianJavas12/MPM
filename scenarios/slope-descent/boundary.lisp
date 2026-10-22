(in-package :cl-mpm/scenario/slope-descent)

(defstruct (contact (:constructor make-contact (mp reference-y width))) mp reference-y width)
(defclass tracked-strip (cl-mpm/bc::bc)
  ((contacts :initarg :contacts :accessor strip-contacts)
   (epsilon :initarg :epsilon :reader strip-epsilon)
   (target :initform 0d0 :accessor strip-target)
   (reaction :initform 0d0 :accessor strip-reaction)
   (mapped-reaction :initform 0d0 :accessor strip-mapped-reaction)))

(defun top-point (mp)
  (let ((point (cl-mpm/utils:vector-copy (cl-mpm/particle:mp-position mp))))
    (incf (magicl:tref point 1 0) (* .5d0 (component (cl-mpm/particle::mp-domain-size mp) 1)))
    point))

(defun make-strip (top-row config original-intervals)
  "Rebase every selected original top MP individually after gravity equilibrium.
ORIGINAL-INTERVALS is an EQ table of original x extents, before gravity movement."
  (let* ((left (gethash "patchStart" config)) (right (+ left (gethash "patchLength" config)))
         (contacts
           (loop for mp across top-row
                 for interval = (gethash mp original-intervals)
                 for overlap = (max 0d0 (- (min right (cdr interval)) (max left (car interval))))
                 when (> overlap 0d0)
                   collect (make-contact mp (component (top-point mp) 1) overlap)))
         (pmod (cl-mpm/particle::calculate-p-wave-modulus (gethash "E" config) (gethash "nu" config)))
         (epsilon (/ (* (gethash "penaltyScale" config) pmod) (gethash "meshSize" config))))
    (unless contacts (error "The prescribed strip contains no original top particles."))
    (let ((area (reduce #'+ contacts :key #'contact-width)))
      (unless (< (abs (- area (gethash "patchLength" config))) 1d-8)
        (error "Discrete strip width ~E differs from requested patch ~E." area (- right left))))
    (make-instance 'tracked-strip :index nil :contacts (coerce contacts 'vector) :epsilon epsilon)))

(defmethod cl-mpm/bc::estimate-min-dt-bc (sim (bc tracked-strip))
  (declare (ignore sim))
  (loop for contact across (strip-contacts bc) minimize
    (sqrt (/ (cl-mpm/particle:mp-mass (contact-mp contact))
             (* (strip-epsilon bc) (contact-width contact))))))

(defmethod cl-mpm/bc::calculate-min-dt-bc (sim (bc tracked-strip))
  (cl-mpm/bc::estimate-min-dt-bc sim bc))

(defmethod cl-mpm/bc::apply-sim-bc (sim (bc tracked-strip) dt)
  "Bilateral displacement spring, same predicted-corner force mapping as native penalty.
Force on the soil is signed +Y; reported actuator reaction is its opposite."
  (declare (ignore dt))
  (setf (strip-reaction bc) 0d0 (strip-mapped-reaction bc) 0d0)
  (loop for contact across (strip-contacts bc) do
    (let* ((mp (contact-mp contact)) (point (top-point mp))
           (increment (cl-mpm/penalty::compute-corner-displacement (cl-mpm:sim-mesh sim) point))
           (predicted-y (+ (component point 1) (component increment 1)))
           (target-y (- (contact-reference-y contact) (strip-target bc)))
           (force-y (* (- target-y predicted-y) (strip-epsilon bc) (contact-width contact)))
           (mapped-y 0d0))
      (unless (finite-p force-y) (error "Nonfinite strip spring force."))
      (cl-mpm::iterate-over-neighbours-point-linear
       (cl-mpm:sim-mesh sim) point
       (lambda (mesh node weight grads)
         (declare (ignore mesh grads))
         (when (cl-mpm/mesh:node-active node)
           (incf (magicl:tref (cl-mpm/mesh::node-external-force node) 1 0) (* weight force-y))
           (incf mapped-y (* weight force-y)))))
      (decf (strip-reaction bc) force-y)
      (decf (strip-mapped-reaction bc) mapped-y)))
  (unless (< (abs (- (strip-reaction bc) (strip-mapped-reaction bc)))
             (* 1d-9 (max 1d0 (abs (strip-reaction bc)))))
    (error "Strip particle force and independently accumulated grid force differ.")))

(defun strip-measurements (bc)
  "Return width-weighted actual descent, maximum absolute spring gap and RMS gap."
  (let ((area 0d0) (actual 0d0) (gap2 0d0) (max-gap 0d0))
    (loop for contact across (strip-contacts bc) do
      (let* ((width (contact-width contact))
             (descent (- (contact-reference-y contact) (component (top-point (contact-mp contact)) 1)))
             (gap (- (strip-target bc) descent)))
        (incf area width) (incf actual (* width descent))
        (incf gap2 (* width gap gap)) (setf max-gap (max max-gap (abs gap)))))
    (values (/ actual area) max-gap (sqrt (/ gap2 area)))))
