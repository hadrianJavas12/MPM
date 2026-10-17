;;;; Focused native contracts and two-update spatial MC smoke. No scientific validation.
;;;; windows\cl-mpm.cmd tests\material-diagnostics.lisp [fresh-output-directory]
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)
(in-package :cl-mpm/framework)

(defvar *diagnostic-checks* 0)
(defclass test-material-diagnostics (elastic-material-diagnostics)
  ((fields :initarg :fields :reader test-diagnostic-fields)))
(defmethod diagnostics-fields ((adapter test-material-diagnostics)) (test-diagnostic-fields adapter))
(defun diagnostic-check (name function)
  (funcall function) (incf *diagnostic-checks*) (format t "~&PASS: ~A~%" name))
(defun diagnostic-error-p (function)
  (handler-case (progn (funcall function) nil) (error () t)))
(defun diagnostic-close (actual expected)
  (assert (< (abs (- actual expected)) (* 1d-10 (max 1d0 (abs expected))))))
(defun diagnostic-case (material &optional (mode "mpm"))
  (let ((parameters (make-hash-table :test 'equal)))
    (setf (gethash "mode" parameters) mode)
    (make-simulation :scenario :triaxial :material material
     :geometry (make-geometry :rectangle :width 0.02d0 :height 0.04d0)
     :boundary (make-boundary :confinement :cell-pressure 50d3)
     :loading (make-loading :compression :target-strain 1d-8 :duration 1d-6 :ramp-duration 0d0)
     :solver (make-solver :explicit :mesh-size 0.01d0 :mps-per-cell 2 :workers 1
                         :frames 2 :max-updates 3)
     :parameters parameters)))
(defun diagnostic-build (material &optional diagnostics)
  (let* ((case (diagnostic-case material)) (config (compile-scenario :triaxial case))
         (resolved (resolve-material material config
                    '((:youngs-modulus "youngsModulusPa" 5d6)
                      (:poisson-ratio "poissonRatio" 0.49d0)
                      (:density "densityKgM3" 1800d0)
                      (:undrained-strength "undrainedStrengthPa" 25d3)
                      (:plasticity "enablePlasticity" t)))))
    (cl-mpm/calibration/triaxial:setup config :particle-factory (make-particle-factory resolved)
                                     :diagnostics (or diagnostics (material-diagnostics resolved)))))
(defun diagnostic-mc ()
  (make-material :native :particle-class 'cl-mpm/particle::particle-mc
   :youngs-modulus 20d6 :poisson-ratio 0.2d0 :density 1800d0
   :initargs (list :phi (/ pi 6d0) :psi 0d0 :c 6d3 :softening 0d0)))

(cl-mpm/utils:set-workers 1)
(let* ((directory (uiop:ensure-directory-pathname
                   (or (first (cl-user::cl-mpm-script-args))
                       (cl-user::cl-mpm-path
                        (format nil "output/material-contract-2026-10-16/contracts-~D/" (get-universal-time))))))
       (mc (diagnostic-mc)) (adapter (material-diagnostics mc))
       (mc-sim (diagnostic-build mc adapter)) (mp (aref (cl-mpm:sim-mps mc-sim) 0))
       (vm (make-material :von-mises)) (vm-sim (diagnostic-build vm))
       (vm-fields (copy-tree (cl-mpm::sim-output-list-scalar vm-sim))))
  (when (probe-file directory) (error "Use a fresh test output directory: ~A" directory))
  (diagnostic-check "MC is native particle-mc without VM inheritance; VM remains classified correctly"
   (lambda ()
     (assert (typep mp 'cl-mpm/particle::particle-mc))
     (assert (not (typep mp 'cl-mpm/particle::particle-vm)))
     (assert (typep (material-diagnostics vm) 'vm-material-diagnostics))
     (assert (typep (material-diagnostics (make-material :elastic)) 'vm-material-diagnostics))
     (assert (string= (first (diagnostics-modes adapter)) "mpm"))
     (multiple-value-bind (plastic yield) (diagnostics-legacy-values adapter mp)
       (assert (and (null plastic) (null yield))))))
  (diagnostic-check "Signed MC residual uses J*Cauchy, independent of stored trial f"
   (lambda ()
     (let* ((stress (cl-mpm/particle:mp-stress mp))
            (f (cl-mpm/particle:mp-deformation-gradient mp))
            (k 3d0) (sigc (* 12d3 (sqrt 3d0))))
       (setf (cl-mpm/particle::mp-yield-func mp) 987654d0)
       (dotimes (axis 3) (setf (cl-mpm/utils:varef stress axis) -50d3))
       (diagnostic-close (mc-kirchhoff-yield-residual mp) (- (* (- k 1d0) -50d3) sigc))
       (setf (magicl:tref f 0 0) 1.2d0
             (cl-mpm/utils:varef stress 0) -10d3
             (cl-mpm/utils:varef stress 1) -60d3
             (cl-mpm/utils:varef stress 2) -20d3)
       (diagnostic-close (mc-kirchhoff-yield-residual mp) (- (* 1.2d0 (- (* k -10d3) -60d3)) sigc))
       ;; An on-surface state and its yielded trial have distinct diagnostics.
       (setf (magicl:tref f 0 0) 1d0
             (cl-mpm/utils:varef stress 0) -50d3
             (cl-mpm/utils:varef stress 2) -50d3
             (cl-mpm/utils:varef stress 1) (- (+ (* k 50d3) sigc)))
       (diagnostic-close (mc-kirchhoff-yield-residual mp) 0d0)
       (assert (= (cl-mpm/particle::mp-yield-func mp) 987654d0)))))
  (diagnostic-check "MC output is local; VM scalar field names and functions remain unchanged"
   (lambda ()
     (let ((names (mapcar #'first (cl-mpm::sim-output-list-scalar mc-sim))))
       (assert (not (member "yield-function" names :test #'string=)))
       (assert (not (member "plastic-strain" names :test #'string=)))
       (assert (member "mc-yield-residual-kirchhoff-pa" names :test #'string=)))
     (configure-material-output adapter mc-sim)
     (assert (= (count "mc-yield-residual-kirchhoff-pa" (cl-mpm::sim-output-list-scalar mc-sim)
                       :key #'first :test #'string=) 1))
     (assert (equal vm-fields (cl-mpm::sim-output-list-scalar vm-sim)))))
  (diagnostic-check "Invalid MC strength, zero-friction return map and wrong adapter reject"
   (lambda ()
     (setf (cl-mpm/particle::mp-c mp) -1d0)
     (assert (diagnostic-error-p (lambda () (validate-material-state adapter mp))))
     (setf (cl-mpm/particle::mp-c mp) 6d3 (cl-mpm/particle::mp-phi mp) 0d0)
     (assert (diagnostic-error-p (lambda () (validate-material-state adapter mp))))
     (setf (cl-mpm/particle::mp-phi mp) (/ pi 6d0))
     (assert (diagnostic-error-p
              (lambda () (validate-material-diagnostics (material-diagnostics vm) (vector mp) "mpm"))))
     (assert (diagnostic-error-p
              (lambda () (validate-material-diagnostics
                           (make-instance 'elastic-material-diagnostics) (vector mp) "mpm"))))))
  (diagnostic-check "Custom diagnostic descriptors reject duplicate/reserved names and invalid metadata without output mutation"
   (lambda ()
     (let ((field (list "custom-state" "1" :mean #'cl-mpm/particle:mp-mass "test read-only state")))
       (dolist (fields (list (list field field)
                            (list (list "mass" "kg" :mean #'cl-mpm/particle:mp-mass "reserved"))
                            (list (list "size_x" "m" :max #'cl-mpm/particle:mp-mass "reserved vector component"))
                            (list (list "custom" nil :mean #'cl-mpm/particle:mp-mass "invalid unit"))
                            (list (list "custom" "1" :unknown #'cl-mpm/particle:mp-mass "invalid reducer"))
                            (list (list "custom" "1" :mean :missing-diagnostic-accessor "invalid accessor"))))
         (let ((bad (make-instance 'test-material-diagnostics :fields fields)))
           (assert (diagnostic-error-p (lambda () (configure-material-output bad vm-sim))))
           (assert (equal vm-fields (cl-mpm::sim-output-list-scalar vm-sim))))))))
  (diagnostic-check "Non-VM homogeneous/controls and unsupported DP reject before output"
   (lambda ()
     (dolist (mode '("homogeneous" "controls"))
       (assert (diagnostic-error-p (lambda () (compile-scenario :triaxial (diagnostic-case mc mode))))))
     (assert (diagnostic-error-p
              (lambda () (material-diagnostics
                           (make-material :native :particle-class 'cl-mpm/particle::particle-dp)))))
     (assert (diagnostic-error-p
              (lambda () (compile-scenario :triaxial
                           (diagnostic-case (make-material :native :particle-class 'cl-mpm/particle::particle-vm-hardening)
                                            "homogeneous")))))
     (let ((config (make-hash-table :test 'equal)))
       (setf (gethash "mode" config) "controls")
       (assert (diagnostic-error-p
                (lambda () (cl-mpm/calibration/triaxial:run-config
                             config directory :particle-factory (lambda (&rest args) (declare (ignore args))
                                                                 (error "Factory must not run"))))))
       (assert (not (probe-file directory))))))
  (diagnostic-check "Native linear elastic material has generic measurements and no invented plastic state"
   (lambda ()
     (let* ((elastic (make-material :native :particle-class 'cl-mpm/particle::particle-elastic
                      :youngs-modulus 20d6 :poisson-ratio 0.2d0))
            (sim (diagnostic-build elastic))
            (cl-mpm/calibration/triaxial::*material-diagnostics* (material-diagnostics elastic)))
       (let ((stats (cl-mpm/calibration/triaxial::stats sim)))
         (assert (and (null (ninth stats)) (null (nth 10 stats)))))
       (cl-mpm/calibration/triaxial::validate-particles
        sim (reduce #'+ (cl-mpm:sim-mps sim) :key #'cl-mpm/particle:mp-mass)))))
  (diagnostic-check "Bare native VM with valid history initargs is spatial-only; known VM constructors retain affine modes"
   (lambda ()
     (let* ((native (make-material :native :particle-class 'cl-mpm/particle::particle-vm
                     :initargs (list :rho 50d3 :rho-r 25d3 :softening 2d0)))
            (sim (diagnostic-build native))
            (particle (aref (cl-mpm:sim-mps sim) 0)))
       (assert (eq (class-name (class-of particle)) 'cl-mpm/particle::particle-vm))
       (diagnostic-close (cl-mpm/particle::mp-softening particle) 2d0)
       (diagnostic-close (cl-mpm/particle::mp-rho-r particle) 25d3)
       (assert (equal (diagnostics-modes (material-diagnostics native)) '("mpm")))
       (assert (diagnostic-error-p
                (lambda () (compile-scenario :triaxial (diagnostic-case native "homogeneous")))))
       (dolist (kind '(:von-mises :elastic))
         (assert (member "homogeneous" (diagnostics-modes (material-diagnostics (make-material kind)))
                         :test #'string=))))))
  (diagnostic-check "Bounded native spatial MC runs and exports blank VM diagnostics plus named MC state"
   (lambda ()
     (let* ((case (diagnostic-case (diagnostic-mc)))
            (config (compile-scenario :triaxial case)))
       ;; Exactly two updates at the native elastic CFL, without changing the solver.
       (let* ((sim (diagnostic-build (simulation-material case)))
              (dt (* (gethash "timeStepScale" config 0.25d0) (cl-mpm/setup:estimate-elastic-dt sim))))
         (setf (gethash "loadingDurationS" config) (* 2d0 dt)))
       (execute-scenario :triaxial case config directory)
       (let* ((manifest (with-open-file (stream (merge-pathnames "manifest.json" directory)) (yason:parse stream)))
              (csv (uiop:read-file-lines (merge-pathnames "stress-strain.csv" directory)))
              (first-row (uiop:split-string (second csv) :separator ","))
              (vtk (uiop:read-file-string (merge-pathnames "particles_0000.vtk" directory) :external-format :latin-1)))
         (assert (= (gethash "updates" manifest) 2))
         (assert (search "particle-mc" (gethash "nativeModel" manifest)))
         (assert (equal (gethash "unavailableCsvFields" manifest) '("plastic_strain" "max_yield_excess")))
         (assert (= (length first-row) 19))
         (assert (and (string= (nth 12 first-row) "") (string= (nth 14 first-row) "")))
         (assert (search "mc-yield-residual-kirchhoff-pa" vtk))
         (assert (not (search "yield-function" vtk)))
         (assert (probe-file (merge-pathnames "material-diagnostics.csv" directory)))))))
  (format t "~&MATERIAL DIAGNOSTICS CONTRACTS: ~D passed; evidence ~A~%" *diagnostic-checks* directory))
(uiop:quit 0)
