;;; CL-MPM Self-Contained Workspace Initialization
(in-package :cl-user)

;; 1. Load Quicklisp directly from workspace
(let ((ql-setup #P"D:/MPM/quicklisp/setup.lisp"))
  (when (probe-file ql-setup)
    (load ql-setup)))

(require :asdf)
(ql:quickload :cffi :silent t)

;; 2. Register DLL and CFFI search directories
(let ((cffi-fld (find-symbol "*FOREIGN-LIBRARY-DIRECTORIES*" :cffi)))
  (when cffi-fld
    (pushnew #P"D:/MPM/openblas/bin/" (symbol-value cffi-fld))
    (pushnew #P"D:/MPM/" (symbol-value cffi-fld))
    (pushnew #P"D:/MPM/libs/" (symbol-value cffi-fld))))

;; 3. Register ASDF systems in workspace
(pushnew #P"D:/MPM/" asdf:*central-registry*)
(pushnew #P"D:/MPM/deps/magicl/" asdf:*central-registry*)
(pushnew #P"D:/MPM/deps/vgplot/" asdf:*central-registry*)

;; 4. Define fallback dummy package for serial CL-MPM/MPI
(unless (find-package :cl-mpm/mpi)
  (let ((pkg (make-package :cl-mpm/mpi :use '(:cl))))
    (export (intern "MPI-SUM" pkg) pkg)
    (export (intern "MPM-SIM-MPI" pkg) pkg)))
(defclass cl-mpm/mpi:mpm-sim-mpi () ())
(defun cl-mpm/mpi:mpi-sum (x) x)

;; 5. Define fallback for swank.live
(unless (find-package :swank.live)
  (let ((pkg (make-package :swank.live :use '(:cl))))
    (export (intern "UPDATE-SWANK" pkg) pkg)))
(defun swank.live:update-swank () nil)

