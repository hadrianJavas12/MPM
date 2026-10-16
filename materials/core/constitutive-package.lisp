(defpackage :cl-mpm/constitutive
  (:use :cl
        :cl-mpm/utils)
  (:export
   #:linear-elastic
   #:linear-elastic-mat
   #:linear-elastic-matrix
   #:newtonian-fluid
   #:maxwell
   #:maxwell-exp
   #:maxwell-exp-v
   #:maxwell-exp-v-simd
   #:norton-hoff
   ))
(in-package :cl-mpm/constitutive)
(declaim #.cl-mpm/settings:*optimise-setting*)
