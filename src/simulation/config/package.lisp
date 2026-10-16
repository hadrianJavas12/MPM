(defpackage :cl-mpm/framework/config
  (:use :cl)
  (:export #:*schema-path* #:read-json-file #:schema #:exact-real #:decimal-input
           #:coerce-param #:load-config #:param #:describe-config))
