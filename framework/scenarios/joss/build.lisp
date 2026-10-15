;;;; Assemble the dedicated reference scenario.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun make-joss-reference-sim (config &key (aggregate t))
  (let* ((h (param config "meshSize"))
         (height (param config "shelfHeight"))
         (base (param config "soilBoundary"))
         (length (* height (+ (param config "shelfAspect") (param config "runoutAspect"))))
         (mps (param config "mpsPerCell"))
         (size (list length (+ height base)))
         (counts (mapcar (lambda (extent) (max 1 (round (* extent mps) h))) size))
         (cells (list (ceiling length h) (ceiling (+ height base (* 5d0 h)) h)))
         (damage-angle (param config "damageFrictionAngle"))
         (initiation (cl-mpm/damage::mohr-coloumb-coheasion-to-tensile
                       (param config "damageCohesion") damage-angle))
         ;; Eq. (44) uses k=1; the helper's default k=2 is a different estimate.
         (ductility (cl-mpm/damage::estimate-ductility-jirsek2004
                      (param config "fractureEnergy") (param config "nonlocalLength")
                      initiation (param config "E") 1d0))
         ;; The raw reference class remains available for bounded comparisons.
         (sim (cl-mpm/setup::make-block h cells :sim-type
                (if aggregate 'joss-reference-aggregate-sim 'joss-reference-sim))))
    (unless (and (> initiation 0d0) (> ductility 1d0)
                 (<= 0d0 (param config "upperVerticalHeight") height))
      (error "Invalid reference damage/geometry parameters (initiation=~A, ductility=~A)" initiation ductility))
    (setf (cl-mpm:sim-mps sim)
          (make-joss-chalk-mps config size counts damage-angle initiation ductility))
    (reference-clip-geometry sim config)
    (unless (plusp (length (cl-mpm:sim-mps sim))) (error "Reference geometry removed all particles"))
    ;; Material tag survives later motion/splitting; the beach remains elastic.
    (loop for mp across (cl-mpm:sim-mps sim) do
      (setf (cl-mpm/particle::mp-index mp)
            (if (<= (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1) base) 1 0)))
    (setf (cl-mpm:sim-gravity sim) -9.8d0
          (cl-mpm::sim-enable-damage sim) nil
          (cl-mpm::sim-nonlocal-damage sim) t
          (cl-mpm/damage::sim-enable-length-localisation sim) t
          (cl-mpm::sim-enable-fbar sim) t
          (cl-mpm::sim-velocity-algorithm sim) :BLEND
          (cl-mpm::sim-mass-scale sim) 1d0
          (cl-mpm::sim-mass-filter sim) 0d0
          (cl-mpm::sim-max-split-depth sim) (param config "geometryRefinement")
          (cl-mpm:sim-allow-mp-split sim) t)
    (setf (cl-mpm:sim-bcs sim)
          (cl-mpm/bc::make-outside-bc-varfix (cl-mpm:sim-mesh sim)
            '(0 nil 0) '(0 nil 0) '(nil nil 0) '(0 0 0) '(nil nil 0) '(nil nil 0)))
    (cl-mpm/setup::initialise-stress-self-weight-vardatum
     sim (lambda (position) (reference-surface-height config (cl-mpm/utils:varef position 0))))
    (setf (cl-mpm:sim-dt sim)
          (cl-mpm/setup:estimate-elastic-dt sim :dt-scale (param config "timeStepScale")))
    sim))
