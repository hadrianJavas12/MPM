;;;; windows/init.lisp — bootstrap for running CL-MPM on native Windows.
;;;;
;;;; Load this before anything else, e.g.
;;;;   sbcl --dynamic-space-size 4000 --no-userinit --load windows/init.lisp --load my-script.lisp
;;;; or from ~/.sbclrc:  (load "D:/path/to/cl-mpm/windows/init.lisp")
;;;;
;;;; Every path is derived from the location of this file, so the checkout can
;;;; live anywhere.  It:
;;;;   1. loads Quicklisp (toolchain/quicklisp, falling back to ~/quicklisp),
;;;;   2. registers the project, the vendored deps and the studio with ASDF,
;;;;   3. tells CFFI where OpenBLAS and the optional kirchoff.dll live,
;;;;   4. exposes CL-USER::*CL-MPM-ROOT* and CL-USER::CL-MPM-PATH.

(in-package :cl-user)

(defvar *cl-mpm-root*
  (merge-pathnames "../" (make-pathname :name nil :type nil
                                        :defaults (or *load-truename* *default-pathname-defaults*)))
  "Root directory of the CL-MPM checkout.")

(setf *cl-mpm-root* (truename *cl-mpm-root*))

(defun cl-mpm-path (relative)
  "Resolve RELATIVE (a string such as \"output/run/\") against the project root."
  (merge-pathnames relative *cl-mpm-root*))

(defun cl-mpm-script-args ()
  "Arguments given after the script name by windows\\cl-mpm.cmd.
The launcher passes them after --end-toplevel-options; SBCL strips its own
options (and that marker), so they are simply the rest of argv."
  (let ((argv (rest sb-ext:*posix-argv*)))
    (or (rest (member "--end-toplevel-options" argv :test #'string=))
        argv)))

;;; 1. Quicklisp -------------------------------------------------------------

#-quicklisp
(let ((candidates (list (cl-mpm-path "toolchain/quicklisp/setup.lisp")
                        (merge-pathnames "quicklisp/setup.lisp" (user-homedir-pathname)))))
  (let ((setup (find-if #'probe-file candidates)))
    (if setup
        (load setup)
        (error "Quicklisp not found. Run windows\\setup.ps1 first (looked in ~{~A~^, ~})."
               candidates))))

(require :asdf)

;;; 2. ASDF registry ---------------------------------------------------------

(dolist (dir '("" "materials/" "deps/magicl/" "deps/vgplot/" "deps/swank.live/" "studio/lisp/"))
  (pushnew (cl-mpm-path dir) asdf:*central-registry* :test #'equal))

;;; 3. Native libraries ------------------------------------------------------

(funcall (intern "QUICKLOAD" :ql) :cffi :silent t)

(let ((dirs (symbol-value (find-symbol "*FOREIGN-LIBRARY-DIRECTORIES*" :cffi))))
  (dolist (dir (list (cl-mpm-path "toolchain/openblas/bin/")
                     (cl-mpm-path "libs/")))
    (pushnew dir dirs :test #'equal))
  (setf (symbol-value (find-symbol "*FOREIGN-LIBRARY-DIRECTORIES*" :cffi)) dirs))

;; cl-mpm.asd also pushes this, but doing it here keeps the feature visible
;; to scripts that test it before the system definition is loaded.
(pushnew :cl-mpm-no-mpi *features*)
