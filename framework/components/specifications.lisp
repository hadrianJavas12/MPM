;;;; Declarative components. All public dimensions/loads use SI; strain is a fraction.
(in-package :cl-mpm/framework)

(defclass component ()
  ((kind :initarg :kind :reader component-kind)
   (options :initarg :options :reader component-options)))
(defclass material (component) ())
(defclass geometry (component) ())
(defclass boundary (component) ())
(defclass loading (component) ())
(defclass solver (component) ())

(defun option (component key &optional default)
  (getf (component-options component) key default))

(defun make-component (class kind options allowed)
  (unless (and (keywordp kind) (evenp (length options)))
    (error "A component needs a keyword kind and keyword/value options."))
  (loop for tail on options by #'cddr for key = (first tail)
        unless (member key allowed) do (error "Unknown ~A option ~S" class key))
  (let ((keys (loop for tail on options by #'cddr collect (first tail))))
    (unless (= (length keys) (length (remove-duplicates keys)))
      (error "Duplicate component option in ~S" options)))
  (make-instance class :kind kind :options (copy-list options)))

(defun make-material (kind &rest options)
  "Existing native material adapter; :NATIVE accepts a dedicated particle class."
  (make-component 'material kind options
                  (ecase kind
                    ((:von-mises :elastic) '(:youngs-modulus :poisson-ratio :density
                                            :undrained-strength :plasticity))
                    ((:chalk :joss) '(:youngs-modulus :poisson-ratio :density :plasticity))
                    (:native '(:youngs-modulus :poisson-ratio :density :undrained-strength
                               :plasticity :particle-class :initargs)))))
(defun make-geometry (kind &rest options)
  (make-component 'geometry kind options
                  (ecase kind
                    (:rectangle '(:width :height :filter))
                    (:cylinder '(:diameter :height :filter))
                    ((:cliff :joss) '(:height :shelf-aspect :slope :base-height
                                     :notch-height :notch-depth)))))
(defun make-boundary (kind &rest options)
  (make-component 'boundary kind options
                  (ecase kind (:confinement '(:cell-pressure :penalty-scale)) (:rollers nil))))
(defun make-loading (kind &rest options)
  (make-component 'loading kind options
                  (ecase kind (:compression '(:target-strain :duration :ramp-duration)) (:gravity nil))))
(defun make-solver (kind &rest options)
  (make-component 'solver kind options
                  (ecase kind
                    (:explicit '(:mesh-size :mps-per-cell :workers :time-step-scale :frames
                                 :max-updates :damping))
                    (:staged '(:mesh-size :mps-per-cell :workers :time-step-scale :frames
                               :simulation-time)))))

(defclass simulation ()
  ((scenario :initarg :scenario :reader simulation-scenario)
   (material :initarg :material :reader simulation-material)
   (geometry :initarg :geometry :reader simulation-geometry)
   (boundary :initarg :boundary :reader simulation-boundary)
   (loading :initarg :loading :reader simulation-loading)
   (solver :initarg :solver :reader simulation-solver)
   (parameters :initarg :parameters :reader simulation-parameters)))

(defun make-simulation (&key scenario material geometry boundary loading solver parameters)
  "Compose a case. PARAMETERS is copied; component options never mutate it."
  (unless (keywordp scenario) (error "SCENARIO must be a keyword."))
  (loop for value in (list material geometry boundary loading solver)
        for type in '(material geometry boundary loading solver)
        unless (typep value type) do (error "Expected ~A component, got ~S" type value))
  (when (and parameters (not (hash-table-p parameters)))
    (error "PARAMETERS must be a hash table of backend-specific settings."))
  (make-instance 'simulation :scenario scenario :material material :geometry geometry
                 :boundary boundary :loading loading :solver solver
                 :parameters (if parameters (alexandria:copy-hash-table parameters)
                                 (make-hash-table :test 'equal))))

(defvar *simulation* nil "Dynamically bound by run-case.lisp while loading a trusted case file.")
