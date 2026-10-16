;;;; Native triaxial scenario: controls.lisp
(in-package :cl-mpm/calibration/triaxial)

(defun run-controls (config directory)
  "Analytical constitutive checks and native3D hydrostatic equilibrium control."
  (let ((results (make-hash-table :test 'equal))
        (p (num config "cellPressurePa" 50d3))
        (e (num config "youngsModulusPa" 5d6))
        (su (num config "undrainedStrengthPa" 25d3)))
    (setf (gethash "enablePlasticity" config) nil)
    (let* ((sim (setup config)) (mp (aref (cl-mpm:sim-mps sim) 0))
           (strain 1d-6))
      (homogeneous-step mp (log (- 1d0 strain)) p)
      (let* ((q (q-of (cl-mpm/particle:mp-stress mp)))
             (relative (abs (- (/ q (* e strain)) 1d0))))
        (assert (< relative 1d-4) () "Native elastic tangent differs from E: ~E" relative)
        (setf (gethash "elasticTangentRelativeError" results) relative)))
    (setf (gethash "enablePlasticity" config) t)
    (let* ((sim (setup config)) (mp (aref (cl-mpm:sim-mps sim) 0))
           (previous-log 0d0) (max-pressure-error 0d0))
      (dotimes (index 100)
        (let ((next-log (log (- 1d0 (* 0.05d0 (/ (1+ index) 100d0))))))
          (homogeneous-step mp (- next-log previous-log) p)
          (setf previous-log next-log)
          (setf max-pressure-error
                (max max-pressure-error
                     (abs (+ p (component (cl-mpm/particle:mp-stress mp) 0)))))))
      (let* ((q-tau (* (j-of mp) (qj2-of (cl-mpm/particle:mp-stress mp))))
             (relative (abs (- (/ q-tau (* 2d0 su)) 1d0))))
        (assert (< relative 1d-7) () "Native Kirchhoff yield radius mismatch ~E" relative)
        (assert (< max-pressure-error 1d-5))
        (setf (gethash "plasticYieldRelativeError" results) relative
              (gethash "lateralStressControlMaxErrorPa" results) max-pressure-error
              (gethash "finalPlasticStrain" results) (cl-mpm/particle::mp-strain-plastic-vm mp)
              (gethash "finalJHomogeneous" results) (j-of mp))))
    (let* ((sim (setup config))
           (mass (reduce #'+ (cl-mpm:sim-mps sim) :key #'cl-mpm/particle:mp-mass))
           (positions (loop for mp across (cl-mpm:sim-mps sim)
                            collect (cl-mpm/utils:vector-copy (cl-mpm/particle:mp-position mp)))))
      (setf (cl-mpm:sim-dt sim) (* 0.25d0 (cl-mpm/setup:estimate-elastic-dt sim)))
      (cl-mpm:add-bcs-force-list sim
                               (vector (make-instance 'isotropic-pressure :index nil :pressure p)))
      (dotimes (index 20) (cl-mpm:update-sim sim))
      (validate-particles sim mass)
      (let ((max-displacement 0d0) (max-q 0d0) (max-volume-f-error 0d0))
        (loop for mp across (cl-mpm:sim-mps sim) for original in positions do
          (dotimes (axis 3)
            (setf max-displacement (max max-displacement
                                        (abs (- (component (cl-mpm/particle:mp-position mp) axis)
                                                (component original axis))))))
          (setf max-q (max max-q (qj2-of (cl-mpm/particle:mp-stress mp)))
                max-volume-f-error (max max-volume-f-error
                                        (abs (- (/ (cl-mpm/particle:mp-volume mp)
                                                   (cl-mpm/particle::mp-volume-0 mp))
                                                (j-of mp))))))
        (assert (< max-displacement 1d-12))
        (assert (< max-q 1d-6))
        (assert (< max-volume-f-error 1d-12))
        (setf (gethash "hydrostatic3DUpdates" results) 20
              (gethash "hydrostatic3DParticles" results) (length (cl-mpm:sim-mps sim))
              (gethash "hydrostaticMaxDisplacementM" results) max-displacement
              (gethash "hydrostaticMaxDeviatoricStressPa" results) max-q
              (gethash "hydrostaticMaxVolumeFRelativeError" results) max-volume-f-error)))
    (setf (gethash "passed" results) t
          (gethash "scope" results) "analytical elastic tangent, native Kirchhoff VM yield, constant Cauchy lateral stress, native3D hydrostatic pressure balance; not scientific validation")
    (json-file (merge-pathnames "controls.json" directory) results)
    (format t "~&TRIAXIAL NATIVE CONTROLS PASSED~%")
    results))
