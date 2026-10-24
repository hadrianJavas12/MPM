;;;; Opt-in composite apex extension; the strict Soil2 model stays separate.
(defpackage :cl-mpm/models/wang2017-apex
  (:use :cl)
  (:local-nicknames (:paper :cl-mpm/models/wang2017)
                    (:point :cl-mpm/models/wang2017-point)
                    (:native :cl-mpm/models/wang2017-native))
  (:import-from :cl-mpm/models/wang2017-point #:paper-projection-apex-multiplier)
  (:export #:project-paper-principal-with-apex #:paper-projection-apex-multiplier
           #:particle-wang2017-soil2-apex #:make-soil2-apex-law
           #:particle-wang2017-soil2-apex-residual #:make-soil2-apex-residual-law))
(in-package :cl-mpm/models/wang2017-apex)
