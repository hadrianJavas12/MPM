;;;; Existing declarations extracted without numerical changes.
(in-package :cl-mpm/framework)

(defclass geometry (component) ())

(defclass boundary (component) ())

(defclass loading (component) ())

(defclass solver (component) ())

(defun make-geometry (kind &rest options)
  (make-component 'geometry kind options
                  (ecase kind
                    (:rectangle '(:width :height :filter))
                    (:cylinder '(:diameter :height :filter))
                    (:slope '(:width :height :crest-length :slope :base-height))
                    ((:cliff :joss) '(:height :shelf-aspect :slope :base-height
                                     :notch-height :notch-depth)))))

(defun make-boundary (kind &rest options)
  (make-component 'boundary kind options
                  (ecase kind (:confinement '(:cell-pressure :penalty-scale)) (:rollers nil))))

(defun make-loading (kind &rest options)
  (make-component 'loading kind options
                  (ecase kind
                    (:compression '(:target-strain :duration :ramp-duration))
                    (:prescribed-descent '(:velocity :target-displacement :patch-start :patch-length))
                    (:crest-pusher '(:velocity :travel :patch-start :patch-length :penalty-scale))
                    (:gravity nil))))

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
