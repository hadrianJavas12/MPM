;;;; Experimental total-stress undrained clay; not the Wang Soil#1 MC law.
(defpackage :cl-mpm/models/clay-creep
  (:use :cl)
  (:export
   #:clay-creep-law #:make-clay-creep-law
   #:clay-creep-law-yield-peak #:clay-creep-law-yield-residual
   #:clay-creep-law-softening-kappa #:clay-creep-law-viscosity
   #:clay-creep-yield #:clay-creep-update #:clay-creep-result
   #:clay-creep-result-tau #:clay-creep-result-elastic-strain
   #:clay-creep-result-plastic-increment #:clay-creep-result-kappa
   #:clay-creep-result-rate #:clay-creep-result-yield #:clay-creep-result-work
   #:clay-creep-result-q #:clay-creep-result-delta
   #:particle-clay-creep #:particle-creep-law #:particle-enable-creep
   #:particle-kappa #:particle-rate #:particle-current-yield #:particle-work
   #:snapshot-clay-creep-particle #:restore-clay-creep-particle))
