;;;; New accelerated preset and observational-energy controls; no timesteps.
(in-package :cl-user)
(ql:quickload :cl-mpm-framework :silent t)
(load (cl-mpm-path "cases/benchmarks/wang2017-soil1-fast-005.lisp"))
(in-package :cl-mpm/scenario/slope-descent)
(defvar *fast-checks* 0)
(defmacro fast-check (label &body forms)
  `(progn ,@forms (incf *fast-checks*) (format t "~&PASS: ~A~%" ,label)))
(defun close-energy (actual expected)
  (assert (< (abs (- actual expected)) (* 1d-10 (max 1d0 (abs expected))))))
(cl-mpm/utils:set-workers 1)
(let* ((case cl-mpm/framework:*simulation*) (config (compile-configuration case)))
  (fast-check "Fast trial is explicitly 50x reference and reaches 0.1m in 20s"
    (close-energy (gethash "velocity" config) .005d0)
    (close-energy (gethash "duration" config) 20d0)
    (close-energy (gethash "targetDisplacement" config) .1d0)
    (assert (= (gethash "frames" config) 101)))
  (fast-check "Pure shear energy matches 0.5 G gamma^2 without doubling shear twice"
    (close-energy
     (elastic-energy-density
      (magicl:from-list '(0d0 0d0 0d0 0d0 0d0 8000d0) '(6 1))
      (magicl:from-list '(0d0 0d0 0d0 0d0 0d0 .001d0) '(6 1))) 4d0))
  (fast-check "Hydrostatic elastic energy matches p^2/(2 K)"
    (close-energy
     (elastic-energy-density
      (magicl:from-list '(-100000d0 -100000d0 -100000d0 0d0 0d0 0d0) '(6 1))
      (magicl:from-list '(-.0025d0 -.0025d0 -.0025d0 0d0 0d0 0d0) '(6 1))) 375d0))
  (fast-check "Energy observation preserves all native constitutive state"
    (let* ((sim (make-slope (cl-mpm/framework:simulation-material case) config))
           (before (material-signature sim)))
      (multiple-value-bind (elastic plastic) (energy-diagnostics sim)
        (close-energy elastic 0d0) (close-energy plastic 0d0))
      (assert (equalp before (material-signature sim)))
      (close-energy (cl-mpm::sim-mass-scale sim) 1d0))))
(format t "~&WANG2017 FAST CONTROLS: ~D passed; no physical updates executed.~%" *fast-checks*)
(uiop:quit 0)
