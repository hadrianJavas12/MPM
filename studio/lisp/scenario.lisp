;;;; scenario.lisp — parameterised chalk cliff collapse.
;;;;
;;;; Geometry (2D, metres):
;;;;
;;;;      |<-- shelf-length -->|<---- runout (2 x height) ---->|
;;;;      +--------------------+                                 ^
;;;;      |      chalk         |\  <- face: cliffSlope/undercut  | shelfHeight
;;;;      |                    |_] <- optional toe notch         v
;;;;      +--------------------+---------------------------------+  ^
;;;;      |              soil / base layer                       |  | soilBoundary
;;;;      +------------------------------------------------------+  v
;;;;
;;;; Material model, solver flags and boundary conditions follow
;;;; SETUP-TEST-COLUMN in examples/chalk/chalk.lisp; here every physical
;;;; parameter comes from the config instead of being hardcoded.

(in-package :cl-mpm-studio)

(defparameter *runout-aspect* 2d0
  "Length of the empty runout region, as a multiple of the cliff height.")

(defparameter *mass-scale* 1d4
  "Mass scaling factor (quasi-static acceleration), as in the upstream example.")

(defun deg->rad (deg) (* deg (/ pi 180d0)))

(defun make-chalk-mps (config block-size h)
  "Material points filling BLOCK-SIZE with particle-chalk-delayed."
  (let* ((mps-per-cell (param config "mpsPerCell"))
         (friction (param config "frictionAngle"))
         (counts (mapcar (lambda (s) (max 1 (round (* s mps-per-cell) h))) block-size)))
    (cl-mpm/setup::make-mps-from-list
     (cl-mpm/setup::make-block-mps-list
      (list 0d0 0d0)
      block-size
      counts
      (param config "density")
      'cl-mpm/particle::particle-chalk-delayed
      :E (param config "E")
      :nu (param config "nu")
      :enable-plasticity (param config "enablePlasticity")
      :friction-angle friction
      :phi (deg->rad friction)
      :psi (deg->rad (param config "dilatancyAngle"))
      :c (param config "cohesion")
      :initiation-stress (param config "initiationStress")
      :delay-time (param config "delayTime")
      :ductility (param config "ductility")
      :critical-damage 1d0
      :damage-domain-rate 0.5d0
      :local-length (param config "nonlocalLength")
      :local-length-damaged 1d-9
      :gravity -9.8d0
      :gravity-axis (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0))))))

(defun configure-solver (sim config h)
  "Solver flags, mass scaling, time step and fixed outer boundaries."
  (setf (cl-mpm:sim-allow-mp-split sim) t
        (cl-mpm::sim-enable-damage sim) (param config "enableDamage")
        (cl-mpm::sim-nonlocal-damage sim) t
        (cl-mpm::sim-enable-fbar sim) t
        (cl-mpm::sim-allow-mp-damage-removal sim) nil
        (cl-mpm::sim-mp-damage-removal-instant sim) nil
        (cl-mpm::sim-mass-filter sim) 1d-15
        (cl-mpm::sim-mass-scale sim) *mass-scale*
        (cl-mpm:sim-damping-factor sim) (* 1d-1 *mass-scale*))
  (let ((mp0 (aref (cl-mpm:sim-mps sim) 0)))
    (setf (cl-mpm:sim-dt sim)
          (* h (sqrt *mass-scale*)
             (sqrt (/ (param config "density")
                      (cl-mpm/particle::mp-p-modulus mp0))))))
  ;; Rollers on the sides, fixed base, free top.
  (setf (cl-mpm:sim-bcs sim)
        (cl-mpm/bc::make-outside-bc-var
         (cl-mpm:sim-mesh sim)
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 nil nil)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 nil nil)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 0 nil)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(0 0 nil)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(nil nil 0)))
         (lambda (i) (cl-mpm/bc::make-bc-fixed i '(nil nil 0)))))
  sim)

(defun cut-cliff-face (sim config shelf-length soil)
  "Remove material in front of the (possibly inclined or overhanging) face."
  (let* ((deviation (+ (- (param config "cliffSlope") 90d0) (param config "undercut")))
         (angle (- (deg->rad deviation)))
         (normal (magicl:from-list (list (cos angle) (sin angle)) '(2 1)))
         (toe (magicl:from-list (list shelf-length soil) '(2 1) :type 'double-float)))
    (cl-mpm/setup:remove-sdf
     sim
     (lambda (p)
       (if (> (magicl:tref p 1 0) soil)
           (cl-mpm/setup::plane-point-sdf
            (magicl:from-list (list (magicl:tref p 0 0) (magicl:tref p 1 0)) '(2 1))
            normal toe)
           1d0)))))

(defun cut-toe-notch (sim config shelf-length soil)
  "Remove a rectangular, elliptic or triangular toe notch.
The notch dimensions follow the legacy convention: notchDepth measures
inward from the original face at x=SHELF-LENGTH; 0 means 1.5 x height.
The tip fraction affects triangular notches only."
  (let ((notch-h (param config "notchHeight")))
    (when (> notch-h 1d-2)
      (let* ((depth (param config "notchDepth"))
             (notch-d (if (> depth 1d-2) depth (* 1.5d0 notch-h)))
             (half-h (* 0.5d0 notch-h))
             (centre-y (+ soil half-h))
             (shape (param config "notchShape"))
             (tip-y (+ soil (* notch-h (param config "notchTipFraction"))))
             (sdf (ecase shape
                    (:rectangle
                     (cl-mpm/setup::rectangle-sdf
                      (list shelf-length centre-y) (list notch-d half-h)))
                    (:ellipse
                     (cl-mpm/setup::ellipse-sdf
                      (list shelf-length centre-y 0d0) notch-d half-h))
                    (:triangle
                     ;; REMOVE-SDF uses only the sign of the supplied function.
                     ;; A triangle has a tip at (face-depth, tip-y) and an
                     ;; open vertical edge along the original cliff face.
                     (lambda (p)
                       (let* ((x (magicl:tref p 0 0))
                              (y (magicl:tref p 1 0))
                              (inside-y (and (> y soil) (< y (+ soil notch-h))))
                              (fraction (if inside-y
                                            (if (< y tip-y)
                                                (/ (- y soil) (- tip-y soil))
                                                (/ (- (+ soil notch-h) y)
                                                   (- (+ soil notch-h) tip-y)))
                                            0d0))
                              (left-x (- shelf-length (* notch-d fraction))))
                         (if (and inside-y
                                  (> x left-x) (< x shelf-length))
                             -1d0 1d0)))))))
        (cl-mpm/setup:remove-sdf
         sim
         (lambda (p)
           ;; Do not cut through the underlying soil/foundation layer.
           (if (> (magicl:tref p 1 0) soil)
               (funcall sdf p)
               1d0)))))))
(defun make-cliff-sim (config)
  "Build the cliff-collapse simulation described by CONFIG."
  (let* ((h (param config "meshSize"))
         (height (param config "shelfHeight"))
         (soil (param config "soilBoundary"))
         (shelf-length (* height (param config "shelfAspect")))
         (domain-length (+ shelf-length (* *runout-aspect* height)))
         (block-size (list domain-length (+ height soil)))
         ;; Five spare cells above the cliff top.
         (cells (list (ceiling domain-length h)
                      (ceiling (+ height soil (* 5 h)) h)))
         (sim (cl-mpm/setup::make-block h cells :sim-type 'cl-mpm/damage::mpm-sim-damage)))
    (setf (cl-mpm:sim-mps sim) (make-chalk-mps config block-size h))
    (configure-solver sim config h)
    (loop for mp across (cl-mpm:sim-mps sim)
          do (setf (cl-mpm/particle::mp-split-depth mp) 0))
    (cut-cliff-face sim config shelf-length soil)
    (cut-toe-notch sim config shelf-length soil)
    sim))
