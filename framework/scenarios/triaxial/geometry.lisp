;;;; Native triaxial scenario: geometry.lisp
(in-package :cl-mpm/calibration/triaxial)

(defun setup (config &key particle-factory geometry-filter diagnostics)
  "Build a native cylinder3D or plane-strain rectangle2D, without engine overrides."
  (check-type particle-factory (or null function))
  (check-type geometry-filter (or null function))
  (let* ((h (* 1d-3 (num config "meshSizeMm" 10)))
         (dimensions (round (num config "spatialDimensions" 3)))
         (diameter (* 1d-3 (num config "diameterMm" 70)))
         (height (* 1d-3 (num config "heightMm" 140)))
         (density (num config "densityKgM3" 1800))
         (e (num config "youngsModulusPa" 5d6))
         (nu (num config "poissonRatio" 0.49d0))
         (su (num config "undrainedStrengthPa" 25d3))
         (p (num config "cellPressurePa" 50d3))
         (mps (round (num config "mpsPerCell" 1)))
         (offset (* 3d0 h))
         (center (+ offset (* 0.5d0 diameter))))
    (assert (and (> h 0d0) (> diameter 0d0) (> height 0d0) (> density 0d0)
                 (> e 0d0) (> su 0d0) (>= p 0d0) (< -1d0 nu 0.5d0)
                 (<= 1 mps 3) (member dimensions '(2 3))))
    (let* ((size (if (= dimensions 2) (list diameter height)
                     (list diameter height diameter)))
           (origin (if (= dimensions 2) (list offset offset)
                       (list offset offset offset)))
           (sim (cl-mpm/setup:make-simple-sim
                 h (mapcar (lambda (length) (ceiling (+ length (* 6 h)) h)) size)
                 :args-list (list :enable-fbar nil :enable-damage nil
                                  :ghost-factor nil :enable-split nil)))
           (counts (mapcar (lambda (length) (* (ceiling length h) mps)) size))
           (clip (or geometry-filter
                     (lambda (x y z)
                       (declare (ignore y))
                       (or (= dimensions 2)
                           (<= (+ (expt (- x center) 2) (expt (- z center) 2))
                               (expt (* diameter 0.5d0) 2))))))
           (particles
             (if particle-factory
                 (funcall particle-factory config origin size counts clip)
                 (apply #'cl-mpm/setup:make-block-mps
                        origin size counts density 'cl-mpm/particle::particle-vm
                        :clip-func clip (material-initargs config)))))
      (check-type particles vector)
      (setf particles (remove-if-not
                       (lambda (mp) (typep mp 'cl-mpm/particle:particle)) particles))
      (if diagnostics
          (material-diagnostic-call "VALIDATE-MATERIAL-DIAGNOSTICS" diagnostics particles
                                    (value config "mode" "mpm"))
          (unless (and (plusp (length particles))
                       (every (lambda (mp) (typep mp 'cl-mpm/particle::particle-vm)) particles))
            (error "Non-VM triaxial particles require an explicit compatible diagnostics adapter.")))
      (cl-mpm:add-mps sim particles)
      (initialize-prestress sim config)
      (when diagnostics
        (material-diagnostic-call "CONFIGURE-MATERIAL-OUTPUT" diagnostics sim))
      (setf (cl-mpm:sim-gravity sim) 0d0
            (cl-mpm:sim-enable-fbar sim) nil
            (cl-mpm:sim-enable-damage sim) nil
            (cl-mpm:sim-damping-factor sim) (num config "dampingPerS" 100)
            (cl-mpm::sim-velocity-algorithm sim) :FLIP)
      (cl-mpm/setup::set-mass-filter sim density :proportion 1d-12)
      (values sim offset center height diameter))))
