;;;; Compatibility entry: the native scenario is split into explicit modules.
;;;; Standalone LOAD and the Windows launcher retain the historical MAIN API.
(in-package :cl-user)
(let ((directory (merge-pathnames "../framework/scenarios/triaxial/"
                                  (make-pathname :name nil :type nil :defaults *load-truename*))))
  (dolist (name '("package" "config" "tensors" "material" "geometry" "boundaries" "measurements" "mpm" "homogeneous" "controls" "runner"))
    (load (merge-pathnames (concatenate 'string name ".lisp") directory))))
