;;;; Run after the refactoring commit, via windows\cl-mpm.cmd.
;;;; Construction/extension contracts; full solver regression is a separate run.
(in-package :cl-user)
(require :asdf)
(ql:quickload '(:cl-mpm :cl-mpm/setup :cl-mpm/output :cl-mpm/penalty :yason) :silent t)
(load (cl-mpm-path "calibration/triaxial.lisp"))
(in-package :cl-mpm/calibration/triaxial)

(let* ((config (with-open-file (stream (cl-user::cl-mpm-path "calibration/triaxial-2d.json"))
                 (yason:parse stream)))
       (original-count (hash-table-count config))
       (original-height *initial-height*)
       (original-volume *initial-volume*)
       (original-pressure *pressure*)
       (calls 0))
  ;; The explicit factory and geometry callback compose without global methods.
  (let ((sim (setup config
                    :geometry-filter (lambda (x y z)
                                       (declare (ignore y z)) (< x 0.065d0))
                    :particle-factory
                    (lambda (configuration origin size counts clip)
                      (incf calls)
                      (assert (= (length size) 2))
                      (apply #'cl-mpm/setup:make-block-mps
                             origin size counts (num configuration "densityKgM3" 1800)
                             'cl-mpm/particle::particle-vm
                             :clip-func clip (material-initargs configuration))))))
    (assert (= calls 1))
    (assert (= (length (cl-mpm:sim-mps sim)) 240))
    (loop for mp across (cl-mpm:sim-mps sim) do
      (assert (= (magicl:tref (cl-mpm/particle:mp-deformation-gradient mp) 2 2) 1d0))))
  ;; An incompatible extension fails at construction rather than midway through a run.
  (assert (handler-case
              (progn (setup config :particle-factory
                             (lambda (&rest arguments) (declare (ignore arguments)) #())) nil)
            (error () t)))
  (assert (= (hash-table-count config) original-count))
  (assert (= *initial-height* original-height))
  (assert (= *initial-volume* original-volume))
  (assert (= *pressure* original-pressure))
  (format t "~&TRIAXIAL COMPONENT CONTRACTS PASSED: composed callbacks, 2D Fzz, incompatible factory rejection, context isolation~%"))
