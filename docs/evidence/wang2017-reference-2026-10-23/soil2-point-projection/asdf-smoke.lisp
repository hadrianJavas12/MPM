(in-package :cl-user)
(require :asdf)
(ql:quickload :cl-mpm/models/wang2017-point :silent t)
(let ((p (cl-mpm/models/wang2017-point:project-paper-principal
          #(0d0 0d0 0d0) 20d6 .25d0 1d0
          (cl-mpm/models/wang2017:make-paper-history)
          #2A((1d0 0d0 0d0) (0d0 1d0 0d0) (0d0 0d0 1d0)))))
  (assert (typep p 'cl-mpm/models/wang2017-point:paper-projection))
  (assert (eq (cl-mpm/models/wang2017-point:paper-projection-branch p) :elastic)))
(format t "~&OPTIONAL ASDF POINT SYSTEM LOAD/ELASTIC CALL PASS; ZERO PHYSICAL UPDATES.~%")
(uiop:quit 0)
