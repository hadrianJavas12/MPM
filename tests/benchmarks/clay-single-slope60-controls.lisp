(in-package :cl-user)
(ql:quickload :cl-mpm-framework/clay-toe-profile :silent t)
(in-package :cl-mpm/scenario/residual-clay-slope)
(let* ((cfg (single-slope-config 60d0))
       (material (fw:make-material :native :youngs-modulus 20d6 :poisson-ratio .2d0 :density 2000d0
                    :particle-class 'particle-clay-toe :initargs (list :evolution-law (make-law cfg) :enable-plasticity t))))
  (assert (not (gethash "upperSlopeDeg" cfg)))
  (loop for x from 0d0 to 72d0 by .125d0 do
    (assert (= (toe-surface cfg x) (u:surface-height cfg x))))
  (cl-mpm/utils:set-workers 1)
  (let* ((sim (build-toe-slope material cfg)) (mps (cl-mpm:sim-mps sim)))
    (assert (= (length mps) 13517))
    (loop for mp across mps for id from 0 do
      (assert (= (cl-mpm/particle::mp-unique-index mp) id))
      (assert (= (mc:particle-kappa mp) 0d0))
      (assert (= (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp)) 1d0)))
    (format t "~&SINGLE SLOPE PASS:577exact matches to original60deg surface,13517nativeinitialMP/IDs/J1/kappa0;0physicalupdates.~%")))
(uiop:quit 0)
