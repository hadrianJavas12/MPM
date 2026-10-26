;;;; Optional material transfer only; geometry/MPM execution lives elsewhere.
(defpackage :cl-mpm/scenario/urmi-damage40/transfer
  (:use :cl)
  (:local-nicknames (:mc :cl-mpm/models/mc-evolution)
                    (:usd :cl-mpm/models/urmi-strength-damage))
  (:export #:elastic-strain-from-stress #:particle-signature
           #:prepare-transfer #:commit-transfer #:transfer! #:transfer-batch
           #:transfer-batch-candidates #:transfer-batch-records))
(in-package :cl-mpm/scenario/urmi-damage40/transfer)
