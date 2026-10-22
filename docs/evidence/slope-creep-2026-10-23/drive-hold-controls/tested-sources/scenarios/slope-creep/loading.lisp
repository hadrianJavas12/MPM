;;;; Moving, compression-only crest driver. This boundary never prescribes MP velocity.
(in-package :cl-mpm/scenario/slope-creep)

(defclass one-way-pusher (cl-mpm/scenario/slope-descent::tracked-strip)
  ((patch-left :initarg :patch-left :reader pusher-patch-left)
   (patch-right :initarg :patch-right :reader pusher-patch-right)
   (active-count :initform 0 :accessor pusher-active-count)
   (separated-count :initform 0 :accessor pusher-separated-count)
   (max-compression-gap :initform 0d0 :accessor pusher-max-compression-gap)
   (max-separation-gap :initform 0d0 :accessor pusher-max-separation-gap)
   (accumulated-command-work :initform 0d0 :accessor pusher-command-work)))

(defun pusher-target-at-time (config time)
  "Commanded driver descent; optional travel stops the driver, never the soil."
  (let ((velocity (gethash "pusherVelocity" config)))
    (unless (and (finite-p time) (>= time 0d0)
                 (finite-p velocity) (> velocity 0d0))
      (error "Pusher command requires finite nonnegative time and positive velocity."))
    (multiple-value-bind (travel supplied-p) (gethash "pusherTravelM" config)
      (when (and supplied-p (not (and (finite-p travel) (> travel 0d0))))
        (error "Pusher travel must be finite and positive when supplied."))
      (let ((target (* velocity time)))
        (unless (finite-p target) (error "Nonfinite pusher command."))
        (if supplied-p (min target travel) target)))))

(defun accumulate-pusher-command-work (bc old-target)
  "Right-end rectangle sum of reaction times driver descent, in J/m.
Call once after each native update. This is a command-work diagnostic, not
a closed energy budget or a modification of particle/material state."
  (let ((target (cl-mpm/scenario/slope-descent:strip-target bc))
        (reaction (cl-mpm/scenario/slope-descent:strip-reaction bc)))
    (unless (and (finite-p old-target) (>= old-target 0d0)
                 (finite-p target) (>= target old-target)
                 (finite-p reaction) (>= reaction 0d0))
      (error "Pusher work requires nonnegative reaction and nondecreasing command."))
    (let ((work (+ (pusher-command-work bc) (* reaction (- target old-target)))))
      (unless (finite-p work) (error "Nonfinite accumulated pusher command work."))
      (setf (pusher-command-work bc) work))))

(defun capture-crest-intervals (top-row)
  "Capture original tributary x intervals before gravity moves the crest MPs."
  (let ((intervals (make-hash-table :test 'eq)))
    (loop for mp across top-row do
      (let ((x (component (cl-mpm/particle:mp-position mp) 0))
            (half (* .5d0 (component (cl-mpm/particle::mp-domain-size mp) 0))))
        (unless (and (finite-p x) (finite-p half) (> half 0d0))
          (error "Invalid original crest particle interval."))
        (setf (gethash mp intervals) (cons (- x half) (+ x half)))))
    intervals))

(defun make-pusher (top-row config original-intervals)
  "Rebase tracked original contacts after gravity, retaining their individual profile.
The fixed x patch releases tracked top points leaving it. This is not general
rigid surface contact: newly exposed or entering particles are not discovered."
  (let* ((strip (cl-mpm/scenario/slope-descent:make-strip top-row config original-intervals))
         (left (gethash "patchStart" config))
         (right (+ left (gethash "patchLength" config))))
    (make-instance 'one-way-pusher :index nil
                   :contacts (cl-mpm/scenario/slope-descent:strip-contacts strip)
                   :epsilon (cl-mpm/scenario/slope-descent::strip-epsilon strip)
                   :patch-left left :patch-right right)))

(defun one-way-force (target-y predicted-y epsilon width)
  "Signed soil force Y: compression negative; separation cannot pull the soil.
The unilateral MIN is the contact law, not clipping of output or particle motion."
  (unless (and (every #'finite-p (list target-y predicted-y epsilon width))
               (> epsilon 0d0) (> width 0d0))
    (error "One-way contact requires finite coordinates and positive stiffness/width."))
  (let ((force (min 0d0 (* (- target-y predicted-y) epsilon width))))
    (unless (finite-p force) (error "Nonfinite one-way contact force."))
    force))

(defun set-pusher-target (bc settlement)
  "Move the driver; particle position, velocity and material state remain free."
  (unless (and (finite-p settlement) (>= settlement 0d0))
    (error "Pusher settlement must be finite and nonnegative."))
  (setf (cl-mpm/scenario/slope-descent:strip-target bc) settlement))

;; The inherited TRACKED-STRIP penalty timestep remains a conservative bound,
;; including while open. The original bilateral class and methods are untouched.
(defmethod cl-mpm/bc::apply-sim-bc (sim (bc one-way-pusher) dt)
  (declare (ignore dt))
  (setf (cl-mpm/scenario/slope-descent:strip-reaction bc) 0d0
        (cl-mpm/scenario/slope-descent:strip-mapped-reaction bc) 0d0
        (pusher-active-count bc) 0 (pusher-separated-count bc) 0
        (pusher-max-compression-gap bc) 0d0 (pusher-max-separation-gap bc) 0d0)
  (loop for contact across (cl-mpm/scenario/slope-descent:strip-contacts bc) do
    (let* ((mp (cl-mpm/scenario/slope-descent:contact-mp contact))
           (point (cl-mpm/scenario/slope-descent::top-point mp))
           (increment (cl-mpm/penalty::compute-corner-displacement (cl-mpm:sim-mesh sim) point))
           (predicted-y (+ (component point 1) (component increment 1)))
           (target-y (- (cl-mpm/scenario/slope-descent:contact-reference-y contact)
                        (cl-mpm/scenario/slope-descent:strip-target bc)))
           (inside (<= (pusher-patch-left bc) (component point 0) (pusher-patch-right bc)))
           (gap (- predicted-y target-y))
           (force-y (if inside
                        (one-way-force target-y predicted-y
                                       (cl-mpm/scenario/slope-descent::strip-epsilon bc)
                                       (cl-mpm/scenario/slope-descent:contact-width contact))
                        0d0))
           (mapped-y 0d0))
      (unless (and (finite-p predicted-y) (finite-p gap))
        (error "Nonfinite one-way pusher contact geometry."))
      (if (< force-y 0d0) (incf (pusher-active-count bc)) (incf (pusher-separated-count bc)))
      ;; These gaps and counts belong to precisely the predicted geometry used
      ;; for this force evaluation. A lateral release has no compression load.
      (when inside
        (setf (pusher-max-compression-gap bc) (max (pusher-max-compression-gap bc) gap 0d0)))
      (setf (pusher-max-separation-gap bc) (max (pusher-max-separation-gap bc) (- gap) 0d0))
      (cl-mpm::iterate-over-neighbours-point-linear
       (cl-mpm:sim-mesh sim) point
       (lambda (mesh node weight grads)
         (declare (ignore mesh grads))
         (when (cl-mpm/mesh:node-active node)
           (incf (magicl:tref (cl-mpm/mesh::node-external-force node) 1 0) (* weight force-y))
           (incf mapped-y (* weight force-y)))))
      (decf (cl-mpm/scenario/slope-descent:strip-reaction bc) force-y)
      (decf (cl-mpm/scenario/slope-descent:strip-mapped-reaction bc) mapped-y)))
  (unless (< (abs (- (cl-mpm/scenario/slope-descent:strip-reaction bc)
                     (cl-mpm/scenario/slope-descent:strip-mapped-reaction bc)))
             (* 1d-9 (max 1d0 (abs (cl-mpm/scenario/slope-descent:strip-reaction bc)))))
    (error "Pusher particle force and independently accumulated grid force differ.")))

(defun pusher-observations (bc)
  "Return command, current weighted settlement, upward reaction, mapped reaction,
active count, unloaded count (including exact touching), max compression gap,
max separation gap, accumulated command-work rectangle diagnostic (J/m).
Counts/gaps/reactions are from the last predicted contact
evaluation; measured settlement uses the current MP geometry after the update."
  (list (cl-mpm/scenario/slope-descent:strip-target bc)
        (nth-value 0 (cl-mpm/scenario/slope-descent:strip-measurements bc))
        (cl-mpm/scenario/slope-descent:strip-reaction bc)
        (cl-mpm/scenario/slope-descent:strip-mapped-reaction bc)
        (pusher-active-count bc) (pusher-separated-count bc)
        (pusher-max-compression-gap bc) (pusher-max-separation-gap bc)
        (pusher-command-work bc)))
