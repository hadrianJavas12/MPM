;;;; Native triaxial scenario: mpm.lisp
(in-package :cl-mpm/calibration/triaxial)

(defun run-mpm (sim config directory offset height)
  (declare (ignore offset))
  (let* ((p (num config "cellPressurePa" 50d3))
         (e (num config "youngsModulusPa" 5d6))
         (nu (num config "poissonRatio" 0.49d0))
         (epsilon (* (num config "penaltyModulusScale" 10)
                     (cl-mpm/particle::calculate-p-wave-modulus e nu)))
         (top (cl-mpm/penalty::make-bc-penalty-displacment
               sim (cl-mpm/utils:vector-from-list '(0d0 1d0 0d0)) epsilon))
         (bottom (cl-mpm/penalty::make-bc-penalty-displacment
                  sim (cl-mpm/utils:vector-from-list '(0d0 -1d0 0d0)) epsilon))
         (duration (num config "loadingDurationS" 0.2d0))
         (ramp (num config "rampDurationS" 0.01d0))
         (target (* 0.01d0 (num config "targetAxialStrainPct" 10)))
         (frames (round (num config "frames" 51)))
         (max-updates (round (num config "maxUpdates" 100000)))
         (initial-mass (reduce #'+ (cl-mpm:sim-mps sim) :key #'cl-mpm/particle:mp-mass))
         (dt (* (num config "timeStepScale" 0.25d0)
                (cl-mpm/setup:estimate-elastic-dt sim)))
         (work 0d0) (last-disp 0d0) (frame 1) (update 0) (data nil))
    (assert (and (> duration 0d0) (<= 0d0 ramp duration) (< 0d0 target 0.3d0)
                 (>= frames 2) (> dt 0d0)))
    (setf (cl-mpm:sim-dt sim) dt)
    (cl-mpm:add-bcs-force-list sim
                             (vector (make-instance 'isotropic-pressure :index nil :pressure p)
                                     top bottom))
    (write-frame sim directory 0 0d0 0d0 0 0d0)
    (format t "~&Native MPM particles=~D dt=~E planned-updates=~D~%"
            (length (cl-mpm:sim-mps sim)) dt (ceiling duration dt))
    (loop while (< (cl-mpm::sim-time sim) duration) do
      (when (>= update max-updates) (error "Bounded update cap reached at t=~E" (cl-mpm::sim-time sim)))
      (let* ((next-time (min duration (+ (cl-mpm::sim-time sim) dt)))
             ;; Smooth velocity startup with analytic normalization; final
             ;; prescribed engineering strain is exactly the requested target.
             (progress (/ (if (< next-time ramp)
                              (* 0.5d0 (/ (expt next-time 2) (max ramp 1d-30)))
                              (- next-time (* 0.5d0 ramp)))
                          (- duration (* 0.5d0 ramp))))
             (disp (* (- height) target progress)))
        (setf (cl-mpm:sim-dt sim) (- next-time (cl-mpm::sim-time sim)))
        (cl-mpm/penalty::bc-set-displacement
         top (cl-mpm/utils:vector-from-list (list 0d0 disp 0d0)))
        (cl-mpm:update-sim sim)
        ;; Additional platen work (cell pressure acts separately on all faces).
        (incf work (* (abs (cl-mpm/penalty::resolve-load top)) (- last-disp disp)))
        (setf last-disp disp)
        (incf update)
        (when (or (>= next-time (* (/ frame (1- frames)) duration))
                  (>= next-time duration))
          (validate-particles sim initial-mass)
          (setf data (write-frame sim directory frame (* 100d0 target progress)
                                  next-time update work))
          (incf frame))))
    (values data update (1- frame))))

;; Coaxial homogeneous material-point forward model for fast constitutive fits.
;; Each lateral strain increment is solved so computed CAUCHY sigma_xx=-p.
;; Visualization is the affine F of that constitutive state, not a spatial solve.
