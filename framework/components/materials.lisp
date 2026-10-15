;;;; Material extension contract: native class plus its constructor arguments.
;;;; No constitutive equation is reimplemented by these adapters.
(in-package :cl-mpm/framework)

(defgeneric material-particle-class (material))
(defgeneric material-particle-initargs (material))

(defmethod material-particle-class ((material material))
  (ecase (component-kind material)
    ((:von-mises :elastic) 'cl-mpm/particle::particle-vm)
    (:chalk 'cl-mpm/particle::particle-chalk-delayed)
    (:joss 'cl-mpm/framework/cliff::joss-reference-chalk)
    (:native (or (option material :particle-class)
                 (error ":NATIVE material requires :PARTICLE-CLASS")))))

(defmethod material-particle-initargs ((material material))
  (let ((e (option material :youngs-modulus 5d6))
        (nu (option material :poisson-ratio 0.49d0)))
    (case (component-kind material)
      ((:von-mises :elastic)
       (let ((rho (* (sqrt (/ 8d0 3d0))
                     (option material :undrained-strength 25d3))))
         (list :E e :nu nu :rho rho :rho-r rho :softening 0d0
               :enable-plasticity (and (not (eq (component-kind material) :elastic))
                                       (option material :plasticity t)))))
      (:native (copy-list (option material :initargs)))
      (otherwise (error "~A uses the dedicated chalk builder; it is not a VM factory."
                         (component-kind material))))))

(defun make-particle-factory (material)
  "Return a run-local builder matching the triaxial geometry-builder contract."
  (lambda (config origin size counts clip-function)
    (declare (ignore config))
    (apply #'cl-mpm/setup:make-block-mps
           origin size counts (option material :density 1800d0)
           (material-particle-class material)
           (append (material-particle-initargs material)
                   (list :clip-func clip-function)))))
