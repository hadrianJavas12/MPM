;;;; Optional ASDF subsystem/extension for centralized material models.
(asdf:defsystem "cl-mpm-materials"
  :description "Centralized CL-MPM constitutive models, diagnostics, and material definitions"
  :depends-on ("cl-mpm-framework"
               "cl-mpm/models/chalk"
               "cl-mpm/models/ice"
               "cl-mpm/models/limestone"
               "cl-mpm/models/visco"
               "cl-mpm/models/mc-evolution")
  :serial t
  :components ())
