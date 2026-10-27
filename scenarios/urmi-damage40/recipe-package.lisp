;;;; Owned experiment; the original cliff/gravity recipes remain unchanged.
(defpackage :cl-mpm/scenario/urmi-damage40
  (:use :cl)
  (:local-nicknames (:fw :cl-mpm/framework) (:gs :cl-mpm/scenario/gravity-slope)
                    (:mc :cl-mpm/models/mc-evolution)
                    (:usd :cl-mpm/models/urmi-strength-damage)
                    (:tr :cl-mpm/scenario/urmi-damage40/transfer))
  (:export #:compile-configuration #:build-slope #:run #:surface-height
           #:capture-reference #:rebind-reference-after-transfer #:save-state
           #:force-measures #:kinetic-measures #:urmi-damage40-sim))
(in-package :cl-mpm/scenario/urmi-damage40)
(defun obj (&rest pairs) (apply #'gs::json-object pairs))
(defun value (config key) (or (gethash key config) (error "Missing owned parameter ~A" key)))
(defun component (matrix index) (magicl:tref matrix index 0))
(defun write-json (path record) (gs::write-json path record))
