;;;; Historical source-path compatibility; ASDF loads the new owner directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("materials/adapters/native.lisp"))
    (load (merge-pathnames relative root))))
