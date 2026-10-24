;;;; Optional Soil2 native adapter. Corotation is an explicit MPM approximation.
(defpackage :cl-mpm/models/wang2017-native
  (:use :cl)
  (:local-nicknames (:paper :cl-mpm/models/wang2017)
                    (:point :cl-mpm/models/wang2017-point))
  (:export #:particle-wang2017-soil2 #:make-soil2-law #:soil2-law-p
           #:particle-paper-tensor #:particle-paper-tensor-committed
           #:particle-paper-kps #:particle-paper-cohesion
           #:particle-history-decrease-p #:particle-rotation
           #:particle-last-paper-diagnostic #:particle-legacy-j2
           #:proper-polar-rotation #:transport-paper-tensor
           #:snapshot-particle #:restore-particle #:copy-particle-state
           #:replay-native-diagnostic #:project-native-point
           #:project-point-variant #:native-material-variant))
(in-package :cl-mpm/models/wang2017-native)
