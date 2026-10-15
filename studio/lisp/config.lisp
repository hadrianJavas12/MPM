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
  ;; Keep the old symbols: callers may already have read/compiled references.
  (dolist (name '("READ-JSON-FILE" "EXACT-REAL" "DECIMAL-INPUT" "COERCE-PARAM"
                  "PARAM" "DESCRIBE-CONFIG"))
    (setf (fdefinition (intern name :cl-mpm-studio))
          (fdefinition (find-symbol name :cl-mpm/framework/config)))))
(defparameter *schema-path*
  (merge-pathnames "../schema.json" (asdf:system-source-directory "cl-mpm-studio")))
(defun schema ()
  (let ((cl-mpm/framework/config:*schema-path* *schema-path*))
    (cl-mpm/framework/config:schema)))
(defun load-config (&optional path)
  (let ((cl-mpm/framework/config:*schema-path* *schema-path*))
    (cl-mpm/framework/config:load-config path)))
