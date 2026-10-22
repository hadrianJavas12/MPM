;;;; Free slope under sustained self-weight; no commanded displacement history.
(defpackage :cl-mpm/scenario/slope-creep
  (:use :cl)
  (:import-from :cl-mpm/scenario/slope-descent
                #:finite-p #:component #:matrix-finite-p #:json-object #:write-json
                #:stable-dt #:free-residual #:make-slope)
  (:export #:compile-configuration #:run))

