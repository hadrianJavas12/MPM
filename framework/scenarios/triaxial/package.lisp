;;;; Native triaxial compression harness. Units: m, Pa, kg, s.
;;;; No material law, damage field or curve is replaced here.
(defpackage :cl-mpm/calibration/triaxial
  (:use :cl)
  (:export :main :run-config :setup :run-controls))
(in-package :cl-mpm/calibration/triaxial)
(declaim (optimize (speed 2) (safety 1) (debug 1)))
(defvar *initial-height* 0.14d0)
(defvar *initial-volume* 1d0)
(defvar *pressure* 50000d0)
