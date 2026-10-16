;;;; Historical source-path compatibility; ASDF loads owner files directly.
(in-package :cl-user)
(let ((root (merge-pathnames "../" (uiop:pathname-directory-pathname *load-truename*))))
  (dolist (relative '("src/numerics/native-bridge/cpp.lisp" "materials/backends/cpp/legacy-transaction.lisp"))
    (load (merge-pathnames relative root))))
