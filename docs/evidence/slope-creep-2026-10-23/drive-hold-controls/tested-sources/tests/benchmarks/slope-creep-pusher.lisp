;;;; Native small-mesh boundary controls only: no gravity or simulation timesteps.
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)
(in-package :cl-mpm/scenario/slope-creep)

(defvar *pusher-checks* 0)
(defmacro pusher-check (label &body body)
  `(progn ,@body (incf *pusher-checks*) (format t "~&PASS: ~A~%" ,label)))
(defun pusher-close (actual expected)
  (assert (< (abs (- actual expected)) (* 1d-10 (max 1d0 (abs expected))))))
(defun pusher-native-state (sim)
  (map 'vector
       (lambda (mp)
         (mapcar (lambda (matrix) (copy-seq (cl-mpm/utils:fast-storage matrix)))
                 (list (cl-mpm/particle:mp-position mp) (cl-mpm/particle:mp-velocity mp)
                       (cl-mpm/particle:mp-stress mp) (cl-mpm/particle:mp-strain mp)
                       (cl-mpm/particle::mp-deformation-gradient mp))))
       (cl-mpm:sim-mps sim)))
(defun prepare-pusher-grid (sim)
  (cl-mpm:iterate-over-nodes (cl-mpm:sim-mesh sim)
    (lambda (node)
      (setf (cl-mpm/mesh:node-active node) t)
      (cl-mpm/fastmaths:fast-zero (cl-mpm/mesh::node-external-force node))
      (cl-mpm/fastmaths:fast-zero (cl-mpm/mesh::node-displacment node)))))
(defun pusher-grid-force (sim)
  (let ((sum 0d0))
    (cl-mpm:iterate-over-nodes (cl-mpm:sim-mesh sim)
      (lambda (node) (incf sum (component (cl-mpm/mesh::node-external-force node) 1))))
    sum))

(cl-mpm/utils:set-workers 1)
(pusher-check "Analytic compression, touching and downward separation obey one-way law"
  (pusher-close (one-way-force 1d0 1.1d0 1000d0 2d0) -200d0)
  (pusher-close (one-way-force 1d0 1d0 1000d0 2d0) 0d0)
  (pusher-close (one-way-force 1d0 .9d0 1000d0 2d0) 0d0)
  (assert (handler-case (progn (one-way-force 1d0 1d0 -1d0 1d0) nil) (error () t))))

(let* ((config (json-object "E" 5d6 "nu" .3d0 "density" 1800d0 "gravity" -9.80665d0
                            "meshSize" 1d0 "width" 8d0 "height" 2d0 "baseHeight" 2d0
                            "crestLength" 3d0 "slope" 60d0 "mpsPerCell" 2
                            "patchStart" 1d0 "patchLength" 1d0 "penaltyScale" 5d0
                            "velocity" .005d0))
       (material (cl-mpm/framework:make-material :von-mises :youngs-modulus 5d6
                                                :poisson-ratio .3d0 :density 1800d0)))
  (multiple-value-bind (sim top-row) (make-slope material config)
    (let* ((intervals (capture-crest-intervals top-row))
           (bc (make-pusher top-row config intervals))
           (contacts (cl-mpm/scenario/slope-descent:strip-contacts bc))
           (epsilon (cl-mpm/scenario/slope-descent::strip-epsilon bc)))
      (prepare-pusher-grid sim)
      (pusher-check "Unilateral subclass inherits a positive conservative penalty timestep"
        (let ((dt (cl-mpm/bc::estimate-min-dt-bc sim bc)))
          (assert (and (finite-p dt) (> dt 0d0)))
          (pusher-close (cl-mpm/bc::calculate-min-dt-bc sim bc) dt)))
      (pusher-check "Exact native touching produces no force or material/kinematic mutation"
        (let ((before (pusher-native-state sim)))
          (cl-mpm/bc::apply-sim-bc sim bc 1d-4)
          (assert (equalp before (pusher-native-state sim)))
          (pusher-close (third (pusher-observations bc)) 0d0)
          (pusher-close (pusher-grid-force sim) 0d0)
          (assert (= (sixth (pusher-observations bc)) (length contacts)))))
      (pusher-check "Native compressive reaction equals analytic and independent nodal sums"
        (set-pusher-target bc .001d0)
        (let ((before (pusher-native-state sim)))
          (cl-mpm/bc::apply-sim-bc sim bc 1d-4)
          (assert (equalp before (pusher-native-state sim))))
        (let ((observations (pusher-observations bc)))
          (pusher-close (third observations) (* epsilon (gethash "patchLength" config) .001d0))
          (pusher-close (fourth observations) (third observations))
          (pusher-close (pusher-grid-force sim) (- (third observations)))
          (assert (= (fifth observations) (length contacts)))
          (pusher-close (seventh observations) .001d0)))
      (pusher-check "Soil descending at 0.02m/s can outrun the 0.005m/s driver and separate"
        (loop for contact across contacts do
          (let ((mp (cl-mpm/scenario/slope-descent:contact-mp contact)))
            (decf (magicl:tref (cl-mpm/particle:mp-position mp) 1 0) .004d0)
            (setf (magicl:tref (cl-mpm/particle:mp-velocity mp) 1 0) -.02d0)))
        (set-pusher-target bc (* .2d0 (gethash "velocity" config)))
        (prepare-pusher-grid sim)
        (let ((before (pusher-native-state sim)))
          (cl-mpm/bc::apply-sim-bc sim bc 1d-4)
          (assert (equalp before (pusher-native-state sim))))
        (let ((observations (pusher-observations bc)))
          (pusher-close (third observations) 0d0)
          (pusher-close (pusher-grid-force sim) 0d0)
          (assert (zerop (fifth observations)))
          (assert (= (sixth observations) (length contacts)))
          (pusher-close (eighth observations) .003d0))
        (loop for contact across contacts do
          (pusher-close (component (cl-mpm/particle:mp-velocity
                                   (cl-mpm/scenario/slope-descent:contact-mp contact)) 1) -.02d0)))
      (pusher-check "Tracked particles leaving the fixed x patch release even in compression"
        (loop for contact across contacts do
          (let ((mp (cl-mpm/scenario/slope-descent:contact-mp contact)))
            (incf (magicl:tref (cl-mpm/particle:mp-position mp) 1 0) .004d0)
            (incf (magicl:tref (cl-mpm/particle:mp-position mp) 0 0) 2d0)))
        (prepare-pusher-grid sim)
        (cl-mpm/bc::apply-sim-bc sim bc 1d-4)
        (pusher-close (third (pusher-observations bc)) 0d0)
        (pusher-close (pusher-grid-force sim) 0d0)
        (assert (= (sixth (pusher-observations bc)) (length contacts)))))))

(format t "~&SLOPE CREEP PUSHER CONTROLS: ~D passed; no physical updates executed.~%" *pusher-checks*)
(uiop:quit 0)
