;;; Runner script for cl-mpm on Native Windows
(in-package :cl-user)

(require :asdf)

;; 1. Configure CFFI library path to locate OpenBLAS (BLAS and LAPACK) and kirchoff.dll
(ql:quickload :cffi :silent t)
(pushnew #P"D:/MPM/openblas/bin/" cffi:*foreign-library-directories*)
(pushnew #P"D:/MPM/" cffi:*foreign-library-directories*)
(pushnew #P"D:/MPM/libs/" cffi:*foreign-library-directories*)

;; 2. Register local packages: cl-mpm, magicl, vgplot
(pushnew #P"D:/MPM/" asdf:*central-registry*)
(pushnew #P"D:/MPM/deps/magicl/" asdf:*central-registry*)
(pushnew #P"D:/MPM/deps/vgplot/" asdf:*central-registry*)

(format t "~%========================================~%")
(format t "Loading cl-mpm on Windows...~%")
(format t "========================================~%")

(ql:quickload :asdf-system-connections :silent t)
(ql:quickload :cl-mpm)
(ql:quickload :cl-mpm/setup)

(format t "~%========================================~%")
(format t "Running 2D Elastic Squish Verification Sim...~%")
(format t "========================================~%")

;; Setup workers
(cl-mpm/utils:set-workers 4)

;; Create a simulation of 10x10 nodes 1x1 meter wide
(defparameter *sim*
  (cl-mpm/setup::make-simple-sim
   0.1d0
   (list 10 10)))

;; Create a block of elastic material points 0.5x0.5 meters across
(cl-mpm:add-mps
 *sim*
 (cl-mpm/setup::make-block-mps
  (list 0d0 0d0)
  (list 0.5d0 0.5d0)
  (list 10 10)
  1000d0
  'cl-mpm/particle::particle-elastic
  :E 1d5
  :nu 0.35d0))

(setf (cl-mpm:sim-gravity *sim*) -9.8d0)
(setf (cl-mpm:sim-damping-factor *sim*) 10d0)
(setf (cl-mpm:sim-dt *sim*) (cl-mpm/setup:estimate-elastic-dt *sim*))

(format t "Estimated dt: ~F~%" (cl-mpm:sim-dt *sim*))
(format t "Number of particles: ~D~%" (length (cl-mpm:sim-mps *sim*)))

;; Run 50 simulation steps
(format t "Running 50 simulation steps...~%")
(handler-case
    (dotimes (i 50)
      (when (= (mod i 10) 0)
        (format t "Step ~D/50~%" i))
      (cl-mpm:update-sim *sim*))
  (error (e)
    (format t "Simulation Error: ~A~%" e)
    (sb-ext:exit :code 1)))

(format t "Step 50/50 complete!~%")
(format t "~%========================================~%")
(format t "SUCCESS: cl-mpm is running natively on Windows!~%")
(format t "========================================~%")

(sb-ext:exit :code 0)
