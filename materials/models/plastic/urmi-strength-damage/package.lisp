;;;; Optional owned adaptation. No existing model or dispatch is replaced.
(defpackage :cl-mpm/models/urmi-strength-damage
  (:use :cl)
  (:local-nicknames (:mc :cl-mpm/models/mc-evolution))
  (:export #:+peak-strength-pa+ #:+transition-strength-pa+ #:+remolded-strength-pa+
           #:+shear-modulus-pa+ #:+youngs-modulus-pa+ #:+poisson-ratio+
           #:+gamma-peak+ #:+gamma-transition+ #:+gamma-remolded+ #:+beta+
           #:+table-tolerance-pa+ #:+maximum-segments+
           #:reference-strength #:reference-node #:make-strength-damage-law #:replay-strength-damage-diagnostic
           #:strength-damage-reference #:particle-urmi-strength-damage
           #:particle-kappa-origin #:particle-strength-damage #:particle-reference-info))
(in-package :cl-mpm/models/urmi-strength-damage)
