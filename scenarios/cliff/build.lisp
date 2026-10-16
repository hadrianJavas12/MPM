;;;; Ordinary chalk material points and scenario assembly.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun make-cliff-sim (config &key
                                (particle-type 'cl-mpm/particle::particle-chalk-delayed)
                                particle-factory geometry-filter custom-validator)
  "Build the cliff case with per-run component functions.
PARTICLE-FACTORY, when supplied, receives (CONFIG BLOCK-SIZE H) and returns
the native material-point vector. GEOMETRY-FILTER receives
(SIM CONFIG SHELF-LENGTH SOIL) and replaces the default face/notch cuts.
The trusted custom-model adapter may supply PARTICLE-TYPE/CUSTOM-VALIDATOR."
  (when (eq (param config "constitutiveModel") :custom)
    (unless custom-validator
      (error "Custom material requires an explicit trusted adapter/validator."))
    (funcall custom-validator))
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
    (setf (cl-mpm:sim-mps sim)
          (if particle-factory
              (funcall particle-factory config block-size h)
              (make-chalk-mps config block-size h :particle-type particle-type)))
    (configure-solver sim config h)
    (loop for mp across (cl-mpm:sim-mps sim)
          do (setf (cl-mpm/particle::mp-split-depth mp) 0))
    (if geometry-filter
        (funcall geometry-filter sim config shelf-length soil)
        (progn
          (cut-cliff-face sim config shelf-length soil)
          (cut-toe-notch sim config shelf-length soil)))
    sim))
