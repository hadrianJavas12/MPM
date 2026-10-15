;;;; Trusted custom-model loading and the Studio-specific CLOS contract.
(in-package :cl-mpm-studio)

(defclass studio-custom-chalk (cl-mpm/particle::particle-chalk-delayed) ()
  (:documentation "Extension point for a user-authored constitutive model."))

(defun custom-model-method ()
  (find-method #'cl-mpm/particle:constitutive-model '()
               (list (find-class 'studio-custom-chalk) (find-class 't) (find-class 't))
               nil))

(defun ensure-custom-model ()
  "Require the exact primary method; inherited Chalk or auxiliary methods do not qualify."
  (or (custom-model-method)
      (error "Custom file must define a primary constitutive-model (studio-custom-chalk strain dt).")))

(defun load-custom-model (path)
  "Load an explicitly selected trusted file. This executes unrestricted OS-user code."
  (unless (and path (probe-file path)) (error "Missing custom-model.lisp source file."))
  ;; A REPL may have loaded an earlier model. It cannot satisfy this file's contract.
  (let ((old-method (custom-model-method)))
    (when old-method (remove-method #'cl-mpm/particle:constitutive-model old-method)))
  (format t "~&Loading USER-SUPPLIED Lisp: ~A~%" (namestring path))
  (finish-output)
  (handler-case
      (progn (load path) (ensure-custom-model))
    (error (e)
      (let ((partial-method (custom-model-method)))
        (when partial-method (remove-method #'cl-mpm/particle:constitutive-model partial-method)))
      (error "Custom model could not be loaded: ~A" e)))
  (format t "~&Custom constitutive model installed.~%")
  (finish-output))

(defmethod cl-mpm/particle:constitutive-model :around
    ((mp studio-custom-chalk) strain dt)
  "Fail before the core's unchecked copies if a custom law returns invalid stress."
  (declare (optimize (safety 3) (debug 1)))
  (let ((stress (call-next-method)))
    (unless (and (typep stress 'magicl:matrix/double-float)
                 (equal (magicl:shape stress) '(6 1)))
      (error "Custom constitutive-model must return a 6 x 1 double-float Kirchhoff stress matrix."))
    (loop for value across (cl-mpm/utils::fast-storage stress)
          unless (and (typep value 'double-float)
                      (not (sb-ext:float-nan-p value))
                      (not (sb-ext:float-infinity-p value)))
            do (error "Custom constitutive-model returned non-finite stress."))
    stress))
