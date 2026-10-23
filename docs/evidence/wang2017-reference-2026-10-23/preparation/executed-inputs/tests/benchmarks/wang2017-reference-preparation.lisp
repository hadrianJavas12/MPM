;;;; Export the actual paper-speed Wang Soil1 case inputs without stepping MPM.
;;;; windows\cl-mpm.cmd tests\benchmarks\wang2017-reference-preparation.lisp FRESH.json
;;;; This gate constructs native material objects; it is not scientific validation.
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)

(defpackage :cl-mpm/tests/wang2017-reference-preparation
  (:use :cl))
(in-package :cl-mpm/tests/wang2017-reference-preparation)

(defparameter *controls-count* 0)
(defparameter *control-labels* nil)

(defun record-object (&rest entries)
  (let ((object (make-hash-table :test 'equal)))
    (loop for (key value) on entries by #'cddr
          do (setf (gethash key object) value))
    object))

(defun reference-close (actual expected)
  (assert (and (realp actual)
               (<= (abs (- actual expected))
                   (* 1d-12 (max 1d0 (abs expected)))))))

(defmacro preparation-check (label &body forms)
  `(progn
     ,@forms
     (incf *controls-count*)
     (push ,label *control-labels*)
     (format t "~&PASS: ~A~%" ,label)))

(defun load-reference-case (path)
  ;; Both trusted recipes assign the same special variable. Keep their objects
  ;; separate and do not replace a simulation belonging to the calling session.
  (let ((cl-mpm/framework:*simulation* nil))
    (load path)
    (or cl-mpm/framework:*simulation*
        (error "Wang recipe did not declare a simulation: ~A" path))))

(defun inspect-reference-case (case label target duration)
  (let* ((config (cl-mpm/scenario/slope-descent:compile-configuration case))
         (material (cl-mpm/framework:simulation-material case))
         (particle-class (cl-mpm/framework:material-particle-class material))
         (args (cl-mpm/framework:material-particle-initargs material))
         ;; The actual factory initargs reach the native constructor. No stress
         ;; update, particle-to-grid mapping, settling or solver call is made.
         (particle (apply #'make-instance particle-class args))
         (law (cl-mpm/models/mc-evolution:particle-evolution-law particle))
         (samples nil))
    (preparation-check (format nil "~A: actual native Soil1 elasticity and perfect Cauchy MC" label)
      (assert (eq (cl-mpm/framework:simulation-scenario case) :slope-descent))
      (assert (eq (class-name (class-of particle))
                  'cl-mpm/models/mc-evolution:particle-mc-evolution))
      (assert (cl-mpm/particle::mp-enable-plasticity particle))
      (assert (eq (cl-mpm/models/mc-evolution:evolution-law-variant law) :perfect))
      (assert (eq (cl-mpm/models/mc-evolution:evolution-law-stress-measure law) :cauchy))
      (reference-close (cl-mpm/particle::mp-E particle) 20d6)
      (reference-close (cl-mpm/particle::mp-nu particle) .25d0)
      (reference-close (gethash "E" config) (cl-mpm/particle::mp-E particle))
      (reference-close (gethash "nu" config) (cl-mpm/particle::mp-nu particle))
      (reference-close (* (gethash "density" config) (- (gethash "gravity" config))) 20d3))
    (preparation-check (format nil "~A: actual law values retain Soil1 strength at multiple histories" label)
      (dolist (kappa '(0d0 .001d0 .02d0 1d0 10d0))
        (multiple-value-bind (cohesion phi psi)
            (cl-mpm/models/mc-evolution:law-values law kappa)
          (reference-close cohesion 30d3)
          (reference-close phi (* 35d0 (/ pi 180d0)))
          (reference-close psi 0d0)
          (push (record-object "kappa" kappa "cohesionPa" cohesion
                               "frictionDeg" (* phi (/ 180d0 pi))
                               "dilationDeg" (* psi (/ 180d0 pi)))
                samples))))
    (preparation-check (format nil "~A: paper-speed trajectory and declared geometry inputs" label)
      (reference-close (gethash "velocity" config) 1d-4)
      (reference-close (gethash "targetDisplacement" config) target)
      (reference-close (gethash "duration" config) duration)
      (reference-close (/ target (gethash "velocity" config)) duration)
      (reference-close (gethash "width" config) 20d0)
      (reference-close (gethash "baseHeight" config) 5d0)
      (reference-close (gethash "slope" config) 60d0)
      (reference-close (gethash "crestLength" config) 10d0)
      (reference-close (gethash "patchStart" config) 7d0)
      (reference-close (gethash "patchLength" config) 3d0)
      (reference-close (+ (gethash "patchStart" config) (gethash "patchLength" config)) 10d0)
      ;; This checks the declared assumption, not a dimension supplied by Fig.2.
      (reference-close (gethash "height" config) 10d0))
    (multiple-value-bind (cohesion phi psi)
        (cl-mpm/models/mc-evolution:law-values law 0d0)
      (values config
              (record-object
               "particleClass" (format nil "~A:~A"
                                       (package-name (symbol-package particle-class))
                                       (symbol-name particle-class))
               "lawKind" (string-downcase
                           (symbol-name (cl-mpm/models/mc-evolution:evolution-law-variant law)))
               "stressMeasure" (string-downcase
                                 (symbol-name (cl-mpm/models/mc-evolution:evolution-law-stress-measure law)))
               "plasticityEnabled" (if (cl-mpm/particle::mp-enable-plasticity particle)
                                        t 'yason:false)
               "youngsModulusPa" (cl-mpm/particle::mp-E particle)
               "poissonRatio" (cl-mpm/particle::mp-nu particle)
               "densityKgPerM3" (gethash "density" config)
               "unitWeightNPerM3" (* (gethash "density" config) (- (gethash "gravity" config)))
               "cohesionPa" cohesion "frictionDeg" (* phi (/ 180d0 pi))
               "dilationDeg" (* psi (/ 180d0 pi))
               "lawSamples" (coerce (nreverse samples) 'vector))))))

(let* ((arguments (cl-user::cl-mpm-script-args))
       (output-path (and (= (length arguments) 1) (pathname (first arguments))))
       (full-path (cl-user::cl-mpm-path "cases/benchmarks/wang2017-soil1.lisp"))
       (pilot-path (cl-user::cl-mpm-path "cases/benchmarks/wang2017-soil1-pilot.lisp")))
  (unless (and output-path (pathname-name output-path)
               (string-equal (or (pathname-type output-path) "") "json"))
    (error "Supply exactly one fresh output JSON path: windows\\cl-mpm.cmd tests\\benchmarks\\wang2017-reference-preparation.lisp FRESH.json"))
  (when (probe-file output-path)
    (error "Reference-preparation JSON must not already exist: ~A" output-path))
  (multiple-value-bind (full-config full-material)
      (inspect-reference-case (load-reference-case full-path) "Full case" .1d0 1000d0)
    (multiple-value-bind (pilot-config pilot-material)
        (inspect-reference-case (load-reference-case pilot-path) "Pilot case" 1d-4 1d0)
      (preparation-check "Full and pilot compiled configurations differ only in target, duration and frame count"
        (assert (= (hash-table-count full-config) (hash-table-count pilot-config)))
        (let ((changed nil))
          (maphash (lambda (key value)
                     (multiple-value-bind (pilot-value present-p) (gethash key pilot-config)
                       (assert present-p)
                       (unless (equalp value pilot-value) (push key changed))))
                   full-config)
          (assert (equal (sort changed #'string<) '("duration" "frames" "targetDisplacement")))))
      (ensure-directories-exist output-path)
      (with-open-file (stream output-path :direction :output :if-exists :error
                                         :if-does-not-exist :create)
        (yason:encode
         (record-object
          "passed" t "controlsCount" *controls-count*
          "controlLabels" (coerce (reverse *control-labels*) 'vector)
          "scope" "Actual native material construction and compilation of existing reference-speed cases; no simulation updates or scientific validation"
          "scientificallyValidated" 'yason:false
          "physicalUpdatesExecuted" 0 "settlingUpdatesExecuted" 0
          "nativeParticlesConstructed" 2
          "fullCase" (namestring full-path) "pilotCase" (namestring pilot-path)
          "fullConfig" full-config "pilotConfig" pilot-config
          "fullMaterial" full-material "pilotMaterial" pilot-material
          "assumptionsAndMethod"
          (record-object
           "reliefHeightM" 10d0 "reliefHeightIsPaperValue" 'yason:false
           "reliefHeightProvenance" "Explicit 10 m assumption; Figure 2 does not dimension relief"
           "solver" "Existing explicit USF MPM, not the paper FEM local arc-length method"
           "bottomConstraint" "Existing implementation fixes bottom x/y; paper equivalence is not asserted"
           "crestControl" "Existing bilateral tracked-strip displacement penalty with finite compliance; exact prescribed displacement is not asserted"
           "boundaryAndLoadingFidelityVerified" 'yason:false))
         stream)))))
(format t "~&WANG2017 REFERENCE PREPARATION: ~D controls passed; no physical updates executed.~%"
        *controls-count*)
(uiop:quit 0)
