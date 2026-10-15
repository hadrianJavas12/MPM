;;;; Compatibility import of the shared, headless configuration module.
(in-package :cl-mpm-studio)
(eval-when (:compile-toplevel :load-toplevel :execute)
  ;; Contract tests compile this file without loading the native engine/system.
  (unless (and (find-package :cl-mpm/framework/config)
               (fboundp (find-symbol "LOAD-CONFIG" :cl-mpm/framework/config)))
    (let ((base (merge-pathnames "../../framework/config/"
                 (uiop:pathname-directory-pathname
                   (or *compile-file-truename* *load-truename*)))))
      (load (merge-pathnames "package.lisp" base))
      (load (merge-pathnames "parameters.lisp" base))))
  (dolist (name '("*SCHEMA-PATH*" "READ-JSON-FILE" "SCHEMA" "EXACT-REAL"
                  "DECIMAL-INPUT" "COERCE-PARAM" "LOAD-CONFIG" "PARAM" "DESCRIBE-CONFIG"))
    (shadowing-import (find-symbol name :cl-mpm/framework/config) :cl-mpm-studio))
  (export (list (find-symbol "LOAD-CONFIG" :cl-mpm-studio)
                (find-symbol "PARAM" :cl-mpm-studio)
                (find-symbol "*SCHEMA-PATH*" :cl-mpm-studio)) :cl-mpm-studio))
(setf *schema-path*
      (merge-pathnames "../schema.json" (asdf:system-source-directory "cl-mpm-studio")))
