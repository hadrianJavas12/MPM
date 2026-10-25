;;;; Read-only diagnostics for the explicitly selected perfect composite model.
(in-package :cl-mpm/framework)

(defclass mc-composite-apex-material-diagnostics (mc-evolution-material-diagnostics) ())

(defmethod specialized-material-diagnostics
    ((particle-class (eql 'cl-mpm/models/mc-composite-apex:particle-mc-composite-apex))
     (material material))
  (declare (ignore particle-class material))
  (make-instance 'mc-composite-apex-material-diagnostics))

(defmethod diagnostics-particle-type ((adapter mc-composite-apex-material-diagnostics))
  'cl-mpm/models/mc-composite-apex:particle-mc-composite-apex)

(defmethod diagnostics-conventions ((adapter mc-composite-apex-material-diagnostics))
  (append
   (call-next-method)
   (list "materialVariant" "perfect-mc-composite-apex"
         "apexConvention"
         "Explicit additional gA=p flow at pA=J*c*cot(phi); constant perfect Cauchy strength and regular psi0. Positive apex plastic volume changes the constitutive response; not strict MC at all states or a fracture model."
         "apexCapBandPolicy"
         "Preserve the old elastic screen. Analytic apex only when mean excess exceeds the EXISTING stressTolerance/(2*sin(phi)); equality and the entire remaining band delegate unchanged strict projection, including rejection."
         "apexMultiplierConvention"
         "Separate lambdaA is the last accepted apex return's plastic volume multiplier, retained in its owned derived projection; a post-commit current-minus-committed zero does not mean no accumulated flow.")))

(defmethod diagnostics-fields ((adapter mc-composite-apex-material-diagnostics))
  (append
   (call-next-method)
   (list
    (list "mc-apex-active-last" "1" :max
          (lambda (particle)
            (if (typep (cl-mpm/models/mc-evolution:particle-last-projection particle)
                       'cl-mpm/models/mc-composite-apex:apex-projection)
                1d0 0d0))
          "One when the last accepted principal return used the declared volumetric apex mode")
    (list "mc-apex-lambda-last" "1" :max
          #'cl-mpm/models/mc-composite-apex:particle-last-apex-multiplier
          "Separate last-return apex multiplier lambdaA; not a current-minus-committed difference"))))
