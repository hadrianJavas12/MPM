;;;; Paper-coordinate primitives; deliberately not a native particle adapter.
(defpackage :cl-mpm/models/wang2017
  (:use :cl)
  (:export #:paper-kps #:engineering-voigt-to-tensor #:tensor-to-engineering-voigt
           #:paper-history #:make-paper-history #:history-tensor #:history-kps
           #:advance-history #:soil2-cohesion))
(in-package :cl-mpm/models/wang2017)
