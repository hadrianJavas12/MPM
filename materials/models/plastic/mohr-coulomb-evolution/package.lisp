;;;; Dedicated evolving Mohr-Coulomb (Hardening / Hardening-Softening) package.
(defpackage :cl-mpm/models/mc-evolution
  (:use :cl)
  (:nicknames :cl-mpm/research/mc-evolution :mc-evolution)
  (:export
   #:evolution-law #:make-evolution-law #:make-urmi-evolution-law
   #:law-values #:law-breakpoints
   #:evolution-law-variant #:evolution-law-points #:evolution-law-cohesion-points
   #:evolution-law-psi #:evolution-law-stress-measure
   #:evolution-law-strain-assumption #:evolution-law-peak-kappa
   #:project-principal #:projection #:projection-tau #:projection-plastic-increment
   #:projection-kappa #:projection-cohesion #:projection-phi #:projection-psi
   #:projection-max-residual #:projection-work #:projection-active
   #:projection-multipliers #:projection-iterations #:projection-residuals
   #:+plane-pairs+ #:material-integration-error
   #:particle-mc-evolution #:particle-evolution-law #:particle-kappa
   #:particle-kappa-committed #:particle-cohesion #:particle-phi #:particle-psi
   #:particle-plastic-increment #:particle-plastic-volume #:particle-plastic-volume-committed
   #:particle-plastic-work #:particle-plastic-work-committed
   #:particle-last-projection #:snapshot-particle #:restore-particle
   #:copy-particle-state
   #:particle-phi-deg #:particle-softened-indicator #:particle-yield-residual-kirchhoff))
(in-package :cl-mpm/models/mc-evolution)

(define-condition material-integration-error (error)
  ((reason :initarg :reason :reader integration-error-reason)
   (details :initarg :details :initform nil :reader integration-error-details))
  (:report (lambda (condition stream)
             (format stream "MC evolution integration failed: ~A ~S"
                     (integration-error-reason condition)
                     (integration-error-details condition)))))

(defun integration-fail (reason &rest details)
  (error 'material-integration-error :reason reason :details details))

(defun finite-real-p (value)
  (and (realp value)
       (let ((number (float value 1d0)))
         (and (not (sb-ext:float-nan-p number))
              (not (sb-ext:float-infinity-p number))))))
