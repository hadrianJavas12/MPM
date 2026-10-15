;;;; scripts/smoke-test.lisp — verify the installation end to end.
;;;;
;;;; The README "quick start" problem: a 0.5 m elastic block settling under
;;;; gravity on a 1 m x 1 m mesh.  Exercises magicl/OpenBLAS, the threaded
;;;; worker pool and the explicit solver.  Exit code 0 on success.
;;;;
;;;;   windows\cl-mpm.cmd scripts\smoke-test.lisp [steps]

(in-package :cl-user)

(ql:quickload '(:cl-mpm :cl-mpm/setup) :silent t)

(defun smoke-finite (value)
  (and (typep value 'double-float)
       (not (sb-ext:float-nan-p value))
       (not (sb-ext:float-infinity-p value))))

(defun smoke-mean-y (mps)
  (/ (loop for mp across mps
           sum (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1))
     (length mps)))

(defun smoke-test (&key (steps 50) (workers 4))
  (assert (plusp steps) () "Smoke test requires at least one update")
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
    (assert (and (smoke-finite (cl-mpm:sim-dt sim)) (plusp (cl-mpm:sim-dt sim))))
    (let ((initial-mean-y (smoke-mean-y (cl-mpm:sim-mps sim))))
      (dotimes (i steps)
        (cl-mpm:update-sim sim))
      ;; Check every component, rather than allowing MIN to hide a bad particle.
      (loop for mp across (cl-mpm:sim-mps sim) do
        (dolist (vector (list (cl-mpm/particle:mp-position mp)
                             (cl-mpm/particle:mp-velocity mp)
                             (cl-mpm/particle:mp-stress mp)))
          (loop for value across (cl-mpm/utils::fast-storage vector) do
            (assert (smoke-finite value) () "Nonfinite particle position, velocity or stress"))))
      (let ((mean-y (smoke-mean-y (cl-mpm:sim-mps sim)))
            (min-y (loop for mp across (cl-mpm:sim-mps sim)
                         minimize (cl-mpm/utils:varef (cl-mpm/particle:mp-position mp) 1))))
        (assert (< mean-y initial-mean-y) () "Gravity did not move the block downwards")
        (format t "lowest particle y = ~,4f m; mean y: ~,8f -> ~,8f m~%"
                min-y initial-mean-y mean-y)))
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
