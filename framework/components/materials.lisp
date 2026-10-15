;;;; Material extension contract: native class plus its constructor arguments.
;;;; No constitutive equation is reimplemented by these adapters.
(in-package :cl-mpm/framework)

(defgeneric material-particle-class (material))
(defgeneric material-particle-initargs (material))

(defun material-value (material key default)
  "Explicit metadata must agree with matching native constitutive initargs."
  (let* ((marker (gensym)) (given (option material key marker))
         (native-key (case key (:youngs-modulus :E) (:poisson-ratio :nu)
                           (:undrained-strength :rho) (:plasticity :enable-plasticity)))
         (native (if (and native-key (eq (component-kind material) :native))
                     (getf (option material :initargs) native-key marker) marker)))
    (when (and (eq key :undrained-strength) (not (eq native marker)))
      (setf native (/ native (sqrt (/ 8d0 3d0)))))
    (when (and (not (eq given marker)) (not (eq native marker))
               (not (or (eql given native)
                        (and (numberp given) (numberp native)
                             (<= (abs (- given native)) (* 1d-12 (max 1d0 (abs given))))))))
      (error "Material metadata ~S disagrees with native ~S" key native-key))
    (cond ((not (eq given marker)) given) ((not (eq native marker)) native) (t default))))

(defun resolve-material (material config mappings)
  "Make a run-local material, inheriting omitted options from this case only."
  (let ((options (copy-list (component-options material))))
    (dolist (mapping mappings)
      (destructuring-bind (key config-key default) mapping
        (setf (getf options key) (material-value material key (gethash config-key config default)))))
    (make-instance 'material :kind (component-kind material) :options options)))

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
      (:native
       (let ((args (copy-list (option material :initargs))))
         (setf (getf args :E) (material-value material :youngs-modulus e)
               (getf args :nu) (material-value material :poisson-ratio nu))
         args))
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
