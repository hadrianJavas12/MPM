;;;; Temporary historical source-path compatibility; actual owners are outside framework.
(in-package :cl-user)
(let ((root (merge-pathnames "../../../"
              (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("scenarios/cliff/run.lisp"))
    (load (merge-pathnames relative root))))
