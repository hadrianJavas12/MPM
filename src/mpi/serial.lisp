;;;; src/mpi/serial.lisp
;;;;
;;;; Serial stand-in for the CL-MPM/MPI system.
;;;;
;;;; Loaded instead of the real MPI layer when the feature :CL-MPM-NO-MPI is
;;;; present (pushed automatically on Windows by cl-mpm.asd, because cl-mpi
;;;; needs a native MPI runtime that is not available there).
;;;;
;;;; It defines the same package, exported symbols, classes and helper
;;;; functions that the rest of the code base (buoyancy BCs, dynamic
;;;; relaxation, examples) refers to, so that those systems compile and run in
;;;; a single process.  Reductions are identities, every point is inside the
;;;; computational domain, and any operation that would really need
;;;; inter-process communication signals an error.

(defpackage :cl-mpm/mpi
  (:use :cl)
  (:export
   :mpm-sim-mpi
   :mpm-sim-mpi-nodes
   :mpm-sim-mpi-nodes-damage
   #:domain-decompose
   #:mpi-average
   #:mpi-sum))

(in-package :cl-mpm/mpi)

(define-condition mpi-unavailable (error)
  ((operation :initarg :operation :reader mpi-unavailable-operation))
  (:report (lambda (c stream)
             (format stream
                     "~A requires MPI, which is not available in this build (feature :CL-MPM-NO-MPI is active)."
                     (mpi-unavailable-operation c)))))

(defun mpi-unavailable (operation)
  (error 'mpi-unavailable :operation operation))

;;; Classes ------------------------------------------------------------------

(defclass mpm-sim-mpi (cl-mpm::mpm-sim-usf)
  ((domain-count
    :accessor mpm-sim-mpi-domain-count
    :initarg :domain-count
    :initform '(1 1 1)))
  (:documentation "Serial stand-in: never distributed, kept for method dispatch."))

(defclass mpm-sim-mpi-nodes (mpm-sim-mpi) ())

(defclass mpm-sim-mpi-nodes-damage (mpm-sim-mpi-nodes cl-mpm/damage::mpm-sim-damage) ())

(defclass mpm-sim-usl-mpi-nodes-damage (mpm-sim-mpi-nodes-damage) ())

;;; Reductions and domain queries --------------------------------------------

(defun mpi-sum (value)
  "Sum of VALUE over all ranks. With a single rank this is VALUE itself."
  value)

(defun mpi-average (value mp-count)
  "Average of a pre-reduced VALUE representing MP-COUNT local samples."
  (/ value (max 1d0 mp-count)))

(defun mpi-rank () 0)
(defun mpi-size () 1)

(defun in-computational-domain (sim pos)
  (declare (ignore sim pos))
  t)

(defun in-computational-domain-buffer (sim pos node-buffer)
  (declare (ignore sim pos node-buffer))
  t)

(defun node-in-computational-domain (sim node)
  (declare (ignore sim node))
  t)

(defun domain-decompose (sim &key domain-scaler)
  "Nothing to decompose with a single rank."
  (declare (ignore domain-scaler))
  sim)

;;; Communication ------------------------------------------------------------

(defun exchange-node-like (&rest args)
  (declare (ignore args))
  (mpi-unavailable 'exchange-node-like))

(defmacro make-mpi-ser (name mapping-list)
  "Define the MPI-OBJECT-<NAME> structure and (de)serialiser entry points.
The structure and accessors exist so dependent code compiles; the
serialisers signal MPI-UNAVAILABLE."
  (let ((ser-name (intern (format nil "SERIALISE-~:@(~A~)" name)))
        (deser-name (intern (format nil "DESERIALISE-~:@(~A~)" name)))
        (mpi-object-name (intern (format nil "MPI-OBJECT-~:@(~A~)" name))))
    `(progn
       (defstruct ,mpi-object-name
         ,@(mapcar #'second mapping-list))
       (defun ,ser-name (objects)
         (declare (ignore objects))
         (mpi-unavailable ',ser-name))
       (defun ,deser-name (array)
         (declare (ignore array))
         (mpi-unavailable ',deser-name)))))
