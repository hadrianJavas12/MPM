;;;; Legacy source path; normal ASDF loads the engine owner directly.
(load (merge-pathnames "../solvers/linear-systems.lisp" (uiop:pathname-directory-pathname *load-truename*)))
