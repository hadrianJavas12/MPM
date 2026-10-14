(defpackage :swank.live
  (:use :cl)
  (:export #:update-swank))

(in-package :swank.live)

(defun update-swank ()
  "No-op: there is no interactive SWANK session to service."
  nil)
