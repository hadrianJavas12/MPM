;;;; Explicit model diagnostics: volumetric apex flow is an added convention.
(in-package :cl-mpm/framework)

(defclass wang2017-apex-material-diagnostics (wang2017-material-diagnostics) ())
(defclass wang2017-apex-residual-material-diagnostics (wang2017-apex-material-diagnostics) ())

(defmethod specialized-material-diagnostics
    ((particle-class (eql 'cl-mpm/models/wang2017-apex:particle-wang2017-soil2-apex))
     (material material))
  (declare (ignore particle-class material))
  (make-instance 'wang2017-apex-material-diagnostics))

(defmethod specialized-material-diagnostics
    ((particle-class (eql 'cl-mpm/models/wang2017-apex:particle-wang2017-soil2-apex-residual))
     (material material))
  (declare (ignore particle-class material))
  (make-instance 'wang2017-apex-residual-material-diagnostics))

(defmethod diagnostics-particle-type ((adapter wang2017-apex-residual-material-diagnostics))
  'cl-mpm/models/wang2017-apex:particle-wang2017-soil2-apex-residual)

(defmethod diagnostics-conventions ((adapter wang2017-apex-residual-material-diagnostics))
  (append
   (loop for (key value) on (call-next-method) by #'cddr
         unless (member key '("materialVariant" "historyConvention") :test #'string=)
           append (list key value))
   (list "materialVariant" "composite-apex-residual"
         "historyConvention"
         "Literal tensor-derived kps may decrease beyond1e-13 only when old and new are both on the exactly constant residual tail and all law values remain exactly equal. No max-history clamp or strength recovery is added; original monotonic-scope rejection remains elsewhere.")))

(defmethod diagnostics-particle-type ((adapter wang2017-apex-material-diagnostics))
  'cl-mpm/models/wang2017-apex:particle-wang2017-soil2-apex)

(defmethod diagnostics-conventions ((adapter wang2017-apex-material-diagnostics))
  (append (call-next-method)
          (list "materialVariant" "composite-apex"
                "apexConvention"
                "Additional hydrostatic apex mode fA=p-J*c(kps)*cot(phi), gA=p. Regular shear has psi=0; apex can add positive plastic volume. This is an explicit model extension, not pure-shear psi0 or a uniquely specified Wang law. All candidate branches remain subject to admissibility and ambiguity rejection.")))

(defmethod diagnostics-fields ((adapter wang2017-apex-material-diagnostics))
  (append
   (call-next-method)
   (list
    (list "wang-apex-active" "1" :max
          (lambda (particle)
            (if (eq (getf (cl-mpm/models/wang2017-native:particle-last-paper-diagnostic particle) :branch)
                    :hydrostatic-apex) 1d0 0d0))
          "Last accepted return uses the explicitly added volumetric apex mode")
    (list "wang-plastic-volume" "1" :mean
          #'cl-mpm/models/mc-evolution:particle-plastic-volume
          "Accumulated plastic volumetric strain; regular psi0 shear is trace-free")
    (list "wang-plastic-volume-increment" "1" :mean
          (lambda (particle)
            (- (cl-mpm/models/mc-evolution:particle-plastic-volume particle)
               (cl-mpm/models/mc-evolution:particle-plastic-volume-committed particle)))
          "Accepted trial plastic-volume increment, without clipping roundoff")
    (list "wang-Ep-trace" "1" :mean
          (lambda (particle)
            (let ((tensor (cl-mpm/models/wang2017-native:particle-paper-tensor particle)))
              (+ (aref tensor 0) (aref tensor 1) (aref tensor 2))))
          "Independent trace of the actual transported signed plastic tensor"))))
