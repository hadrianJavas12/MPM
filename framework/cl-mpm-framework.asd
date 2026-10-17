;;;; Temporary ASDF source-path compatibility; canonical metadata is at repository root.
(in-package :cl-user)
(load (merge-pathnames "../cl-mpm-framework.asd"
       (uiop:pathname-directory-pathname *load-truename*)))
