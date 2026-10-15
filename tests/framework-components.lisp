;;;; Native construction contracts, not solver regression or scientific validation.
;;;; windows\cl-mpm.cmd tests\framework-components.lisp
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)
(in-package :cl-mpm/framework)

(defvar *component-checks* 0)
(defvar *component-failures* nil)

(defun component-check (name thunk)
  (incf *component-checks*)
  (handler-case (progn (funcall thunk) (format t "~&PASS: ~A~%" name))
    (error (condition)
      (push (format nil "~A: ~A" name condition) *component-failures*)
      (format t "~&FAIL: ~A: ~A~%" name condition))))

(defun component-error-p (thunk)
  (handler-case (progn (funcall thunk) nil) (error () t)))

(defun component-close (actual expected)
  (assert (<= (abs (- actual expected)) (* 1d-11 (max 1d0 (abs expected))))
          () "Expected ~A, got ~A" expected actual))

(defun component-hash-equal (left right)
  (and (= (hash-table-count left) (hash-table-count right))
       (loop for key being the hash-keys of left using (hash-value value)
             always (multiple-value-bind (other present) (gethash key right)
                      (and present (equalp value other))))))

(defun component-triaxial (material geometry &optional parameters)
  (make-simulation :scenario :triaxial :material material :geometry geometry
                   :boundary (make-boundary :confinement :cell-pressure 50d3)
                   :loading (make-loading :compression :target-strain 0.1d0)
                   :solver (make-solver :explicit :mesh-size 0.01d0 :mps-per-cell 1)
                   :parameters parameters))

(defun component-build (case)
  "Construct the native particles only; never enter the timestep loop."
  (let* ((config (compile-scenario :triaxial case))
         (resolved (resolve-material
                    (simulation-material case) config
                    '((:youngs-modulus "youngsModulusPa" 5d6)
                      (:poisson-ratio "poissonRatio" 0.49d0)
                      (:density "densityKgM3" 1800d0)
                      (:undrained-strength "undrainedStrengthPa" 25d3)
                      (:plasticity "enablePlasticity" t)))))
    (cl-mpm/calibration/triaxial:setup
     config :particle-factory (make-particle-factory resolved)
     :geometry-filter (geometry-filter (simulation-geometry case)))))

(cl-mpm/utils:set-workers 1)
(setf *component-checks* 0 *component-failures* nil)

(component-check
 "Framework loads independently without the Studio package"
 (lambda () (assert (null (find-package :cl-mpm-studio)))))

(component-check
 "VM and elastic swap retains geometry, density and native state; changes plasticity"
 (lambda ()
   (let* ((geometry (make-geometry :rectangle :width 0.07d0 :height 0.14d0))
          (vm (component-build (component-triaxial (make-material :von-mises) geometry)))
          (elastic (component-build (component-triaxial (make-material :elastic) geometry))))
     (assert (= (length (cl-mpm:sim-mps vm)) (length (cl-mpm:sim-mps elastic))))
     (assert (plusp (length (cl-mpm:sim-mps vm))))
     (loop for a across (cl-mpm:sim-mps vm) for b across (cl-mpm:sim-mps elastic) do
       (assert (and (typep a 'cl-mpm/particle::particle-vm)
                    (typep b 'cl-mpm/particle::particle-vm)))
       (assert (cl-mpm/particle::mp-enable-plasticity a))
       (assert (null (cl-mpm/particle::mp-enable-plasticity b)))
       (component-close (cl-mpm/particle:mp-mass a) (cl-mpm/particle:mp-mass b))
       (dotimes (d 3)
         (component-close (cl-mpm/utils:varef (cl-mpm/particle:mp-position a) d)
                          (cl-mpm/utils:varef (cl-mpm/particle:mp-position b) d)))))))

(component-check
 "Rectangle/cylinder geometry swap and clipping produce actual native particle positions"
 (lambda ()
   (let* ((material (make-material :elastic))
          (rectangle (component-build
                      (component-triaxial material
                       (make-geometry :rectangle :width 0.07d0 :height 0.14d0))))
          (cylinder (component-build
                     (component-triaxial material
                      (make-geometry :cylinder :diameter 0.07d0 :height 0.14d0))))
          (filtered (component-build
                     (component-triaxial material
                      (make-geometry :rectangle :width 0.07d0 :height 0.14d0
                       :filter (lambda (x y z) (declare (ignore y z)) (< x 0.065d0)))))))
     (assert (< 0 (length (cl-mpm:sim-mps filtered)) (length (cl-mpm:sim-mps rectangle))))
     (loop for mp across (cl-mpm:sim-mps rectangle) do
       (component-close (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 2) 0d0)
       (component-close (magicl:tref (cl-mpm/particle:mp-deformation-gradient mp) 2 2) 1d0))
     (loop for mp across (cl-mpm:sim-mps filtered) do
       (assert (< (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 0) 0.065d0)))
     (assert (plusp (length (cl-mpm:sim-mps cylinder))))
     (loop with center = 0.065d0 with radius = 0.035d0
           for mp across (cl-mpm:sim-mps cylinder)
           for p = (cl-mpm/particle:mp-position mp) do
       (assert (<= (+ (expt (- (cl-mpm/utils:varef p 0) center) 2)
                       (expt (- (cl-mpm/utils:varef p 2) center) 2))
                    (+ (expt radius 2) 1d-14)))))))

(component-check
 "Omitted material options inherit supplied configuration; source config stays unchanged"
 (lambda ()
   (let ((parameters (make-hash-table :test 'equal)))
     (setf (gethash "youngsModulusPa" parameters) 7d6
           (gethash "poissonRatio" parameters) 0.3d0
           (gethash "densityKgM3" parameters) 1900d0
           (gethash "undrainedStrengthPa" parameters) 30d3)
     (let* ((before (alexandria:copy-hash-table parameters))
            (case (component-triaxial
                   (make-material :von-mises)
                   (make-geometry :rectangle :width 0.08d0 :height 0.16d0) parameters))
            (config (compile-scenario :triaxial case))
            (sim (component-build case))
            (mp (aref (cl-mpm:sim-mps sim) 0)))
       (component-close (gethash "youngsModulusPa" config) 7d6)
       (component-close (cl-mpm/particle::mp-E mp) 7d6)
       (component-close (cl-mpm/particle::mp-nu mp) 0.3d0)
       (component-close (gethash "diameterMm" config) 80d0)
       (component-close (gethash "heightMm" config) 160d0)
       (component-close (/ (cl-mpm/particle:mp-mass mp) (cl-mpm/particle:mp-volume mp)) 1900d0)
       (assert (component-hash-equal before parameters))
       (assert (component-hash-equal before (simulation-parameters case)))))))

(component-check
 "Native VM initargs and exported material configuration agree; contradictions reject"
 (lambda ()
   (let* ((rho (* (sqrt (/ 8d0 3d0)) 30d3))
          (geometry (make-geometry :rectangle :width 0.07d0 :height 0.14d0))
          (native (make-material :native :particle-class 'cl-mpm/particle::particle-vm
                   :initargs (list :E 7d6 :nu 0.3d0 :rho rho :rho-r rho :softening 0d0
                                   :enable-plasticity nil)))
          (case (component-triaxial native geometry))
          (config (compile-scenario :triaxial case))
          (sim (component-build case))
          (mp (aref (cl-mpm:sim-mps sim) 0)))
     (component-close (gethash "youngsModulusPa" config) (cl-mpm/particle::mp-E mp))
     (component-close (gethash "poissonRatio" config) (cl-mpm/particle::mp-nu mp))
     (component-close (gethash "undrainedStrengthPa" config) 30d3)
     (assert (null (gethash "enablePlasticity" config)))
     (assert (null (cl-mpm/particle::mp-enable-plasticity mp)))
     (assert (component-error-p
              (lambda ()
                (compile-scenario :triaxial
                 (component-triaxial
                  (make-material :native :particle-class 'cl-mpm/particle::particle-vm
                   :youngs-modulus 5d6 :initargs (list :E 7d6 :nu 0.3d0)) geometry))))))))

(component-check
 "Unknown options and incompatible material/geometry/scenario combinations reject"
 (lambda ()
   (assert (component-error-p (lambda () (make-material :von-mises :misspelled-modulus 5d6))))
   (assert (component-error-p
            (lambda () (validate-simulation
                        (component-triaxial (make-material :chalk) (make-geometry :rectangle))))))
   (assert (component-error-p
            (lambda () (validate-simulation
                        (component-triaxial (make-material :elastic) (make-geometry :cliff))))))
   (assert (component-error-p
            (lambda () (validate-simulation
                        (component-triaxial
                         (make-material :native :particle-class 'cl-mpm/particle::particle-elastic)
                         (make-geometry :rectangle))))))))

(component-check
 "Accepted Joss parameters remain numerically identical through public composition"
 (lambda ()
   (let* ((parameters (read-parameters "studio/reference/joss-bay-accepted-collapse.json" :schema t))
          (before (alexandria:copy-hash-table parameters))
          (case (make-simulation :scenario :joss :parameters parameters
                 :material (make-material :joss) :geometry (make-geometry :joss)
                 :boundary (make-boundary :rollers) :loading (make-loading :gravity)
                 :solver (make-solver :staged)))
          (compiled (compile-scenario :joss case)))
     (assert (component-hash-equal parameters compiled))
     (assert (component-hash-equal parameters before))
     (assert (component-error-p
              (lambda ()
                (validate-simulation
                 (make-simulation :scenario :joss :parameters parameters
                  :material (make-material :elastic) :geometry (make-geometry :joss)
                  :boundary (make-boundary :rollers) :loading (make-loading :gravity)
                  :solver (make-solver :staged)))))))))

(component-check
 "Explicit native plasticity metadata configures the native flag without duplicate initargs"
 (lambda ()
   (let* ((rho (* (sqrt (/ 8d0 3d0)) 25d3))
          (material (make-material :native :particle-class 'cl-mpm/particle::particle-vm
                     :plasticity nil :initargs (list :rho rho :rho-r rho :softening 0d0)))
          (case (component-triaxial material
                 (make-geometry :rectangle :width 0.07d0 :height 0.14d0)))
          (config (compile-scenario :triaxial case))
          (sim (component-build case)))
     (assert (null (gethash "enablePlasticity" config)))
     (assert (null (cl-mpm/particle::mp-enable-plasticity (aref (cl-mpm:sim-mps sim) 0)))))))

(component-check
 "Native VM strength-only metadata supplies bound yield fields without custom initargs"
 (lambda ()
   (let* ((material (make-material :native :particle-class 'cl-mpm/particle::particle-vm
                     :youngs-modulus 7d6 :poisson-ratio 0.3d0 :density 1900d0
                     :undrained-strength 30d3))
          (before (copy-list (component-options material)))
          (case (component-triaxial material
                 (make-geometry :rectangle :width 0.07d0 :height 0.14d0)))
          (sim (component-build case)) (mp (aref (cl-mpm:sim-mps sim) 0)))
     (component-close (cl-mpm/particle::mp-rho mp) (* (sqrt (/ 8d0 3d0)) 30d3))
     (component-close (cl-mpm/particle::mp-rho-r mp) (cl-mpm/particle::mp-rho mp))
     (component-close (cl-mpm/particle::mp-E mp) 7d6)
     (assert (equal before (component-options material))))))

(component-check
 "False config plasticity is inherited; ambiguous or irrelevant component options reject"
 (lambda ()
   (let* ((parameters (make-hash-table :test 'equal))
          (geometry (make-geometry :rectangle :width 0.07d0 :height 0.14d0)))
     (setf (gethash "enablePlasticity" parameters) nil)
     (let* ((case (component-triaxial (make-material :von-mises) geometry parameters))
            (config (compile-scenario :triaxial case)) (sim (component-build case)))
       (assert (null (gethash "enablePlasticity" config)))
       (assert (null (cl-mpm/particle::mp-enable-plasticity (aref (cl-mpm:sim-mps sim) 0))))))
   (assert (component-error-p
            (lambda () (make-material :elastic :youngs-modulus 5d6 :youngs-modulus 7d6))))
   (assert (component-error-p (lambda () (make-geometry :cylinder :width 0.07d0))))
   (assert (component-error-p (lambda () (make-solver :staged :damping 100d0))))))

(format t "~&FRAMEWORK COMPONENT CHECKS: ~D passed, ~D failed; no timesteps executed.~%"
        (- *component-checks* (length *component-failures*)) (length *component-failures*))
(when *component-failures*
  (dolist (failure (reverse *component-failures*)) (format *error-output* "~&~A~%" failure))
  (uiop:quit 1))
(uiop:quit 0)
