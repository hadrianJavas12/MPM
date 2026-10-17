;;;; P4/E standalone loader and legacy material adapter controls; no MPM updates.
;;;; windows\cl-mpm.cmd tests\p4-standalone-triaxial-compat.lisp
(in-package :cl-user)
(ql:quickload '(:cl-mpm :cl-mpm/setup :cl-mpm/output :cl-mpm/penalty :yason) :silent t)
(assert (null (find-package :cl-mpm/framework)))
(load (cl-mpm-path "calibration/triaxial.lisp"))

(in-package :cl-mpm/calibration/triaxial)
(let ((checks 0) (config (make-hash-table :test 'equal)))
  (assert (null (find-package :cl-mpm/framework)))
  (dolist (symbol '(main run-config setup run-controls homogeneous-step
                    material-initargs initialize-prestress
                    legacy-vm-stats-values legacy-copy-homogeneous-state))
    (assert (fboundp symbol)))
  (incf checks)
  (format t "~&PASS: Historical standalone calibration loads complete material/scenario owners without the public framework.~%")
  (setf (gethash "spatialDimensions" config) 2
        (gethash "mpsPerCell" config) 2
        (gethash "workers" config) 1)
  (let* ((before (alexandria:copy-hash-table config))
         (sim (setup config)) (particles (cl-mpm:sim-mps sim))
         (first (aref particles 0)) (second (aref particles 1)))
    (assert (= (hash-table-count before) (hash-table-count config)))
    (maphash (lambda (key value) (assert (equal value (gethash key config)))) before)
    (assert (zerop (cl-mpm::sim-time sim)))
    (assert (every (lambda (mp) (typep mp 'cl-mpm/particle::particle-vm)) particles))
    (multiple-value-bind (plastic residual)
        (legacy-vm-stats-values first (cl-mpm/particle:mp-stress first))
      ;; Isotropic prestress has no deviator and starts without plastic history.
      (assert (zerop plastic))
      (assert (= residual -1d0)))
    (incf checks)
    (format t "~&PASS: Standalone initial state/config remain intact; private VM diagnostics preserve the hydrostatic limit.~%")
    (let ((position (cl-mpm/utils::vector-copy (cl-mpm/particle:mp-position second)))
          (deformation (cl-mpm/particle:mp-deformation-gradient first)))
      (setf (cl-mpm/particle::mp-strain-plastic-vm first) 0.002d0
            (component (cl-mpm/particle:mp-stress first) 0) -60000d0)
      (legacy-copy-homogeneous-state second first deformation)
      (assert (= (cl-mpm/particle::mp-strain-plastic-vm second) 0.002d0))
      (assert (= (component (cl-mpm/particle:mp-stress second) 0) -60000d0))
      (setf (component (cl-mpm/particle:mp-stress first) 0) -70000d0)
      (assert (= (component (cl-mpm/particle:mp-stress second) 0) -60000d0))
      (dotimes (axis 3)
        (assert (= (component position axis) (component (cl-mpm/particle:mp-position second) axis))))
      (assert (zerop (cl-mpm::sim-time sim))))
    (incf checks)
    (format t "~&PASS: Legacy homogeneous material-state copy is independent and does not move particles or advance time.~%"))
  (format t "~&P4 STANDALONE TRIAXIAL: ~D passed; no MPM update executed.~%" checks))
(uiop:quit 0)
