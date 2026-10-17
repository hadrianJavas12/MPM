;;;; Existing declarations extracted without numerical changes.
(in-package :cl-mpm/framework)

(defclass material (component) ())

(defun make-material (kind &rest options)
  "Existing native material adapter; :NATIVE accepts a dedicated particle class."
  (make-component 'material kind options
                  (ecase kind
                    ((:von-mises :elastic) '(:youngs-modulus :poisson-ratio :density
                                            :undrained-strength :plasticity))
                    ((:chalk :joss) '(:youngs-modulus :poisson-ratio :density :plasticity))
                    ((:mc-h :mc-hs) '(:youngs-modulus :poisson-ratio :density :plasticity
                                      :evolution-law :kappa :initargs))
                    (:native '(:youngs-modulus :poisson-ratio :density :undrained-strength
                               :plasticity :particle-class :initargs)))))
