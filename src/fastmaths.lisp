;;;; Legacy source path; normal ASDF loads the engine owner directly.
(load (merge-pathnames "numerics/fastmaths.lisp" (uiop:pathname-directory-pathname *load-truename*)))
