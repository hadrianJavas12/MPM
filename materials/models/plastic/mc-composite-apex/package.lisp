;;;; Optional perfect MC model with an explicit additional volumetric apex flow.
(defpackage :cl-mpm/models/mc-composite-apex
  (:use :cl)
  (:local-nicknames (:mc :cl-mpm/models/mc-evolution))
  (:export #:project-principal-with-apex #:particle-mc-composite-apex
           #:apex-projection #:apex-projection-branch
           #:apex-projection-apex-multiplier
           #:particle-last-apex-multiplier #:particle-last-apex-active))
