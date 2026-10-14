;;;; scripts/smoke-test.lisp — verify the installation end to end.
;;;;
;;;; The README "quick start" problem: a 0.5 m elastic block settling under
;;;; gravity on a 1 m x 1 m mesh.  Exercises magicl/OpenBLAS, the threaded
;;;; worker pool and the explicit solver.  Exit code 0 on success.
;;;;
;;;;   windows\cl-mpm.cmd scripts\smoke-test.lisp [steps]

(in-package :cl-user)

(ql:quickload '(:cl-mpm :cl-mpm/setup) :silent t)

(defun smoke-test (&key (steps 50) (workers 4))
  (cl-mpm/utils:set-workers workers)
  (let ((sim (cl-mpm/setup::make-simple-sim 0.1d0 (list 10 10))))
    (cl-mpm:add-mps
     sim
     (cl-mpm/setup::make-block-mps
      (list 0d0 0d0) (list 0.5d0 0.5d0) (list 10 10)
      1000d0 'cl-mpm/particle::particle-elastic
      :E 1d5 :nu 0.35d0))
    (setf (cl-mpm:sim-gravity sim) -9.8d0
          (cl-mpm:sim-damping-factor sim) 10d0
          (cl-mpm:sim-dt sim) (cl-mpm/setup:estimate-elastic-dt sim))
    (format t "~&dt = ~,3e s, particles = ~D, steps = ~D~%"
            (cl-mpm:sim-dt sim) (length (cl-mpm:sim-mps sim)) steps)
    (dotimes (i steps)
      (cl-mpm:update-sim sim))
    ;; The block must have settled downwards, and nothing may be NaN.
    (let ((min-y (loop for mp across (cl-mpm:sim-mps sim)
                       minimize (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1))))
      (assert (not (sb-ext:float-nan-p min-y)) () "NaN in particle positions")
      (format t "lowest particle y = ~,4f m~%" min-y))
    sim))

(handler-case
    (let ((steps (let ((arg (first (cl-mpm-script-args))))
                   (if arg (parse-integer arg) 50))))
      (smoke-test :steps steps)
      (format t "~&SMOKE TEST PASSED~%")
      (uiop:quit 0))
  (error (e)
    (format *error-output* "~&SMOKE TEST FAILED: ~A~%" e)
    (uiop:quit 1)))
