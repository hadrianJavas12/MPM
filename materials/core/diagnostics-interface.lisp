;;;; Existing read-only diagnostics; defining bodies preserved exactly.
(in-package :cl-mpm/framework)

(defclass native-material-diagnostics ()
  ((output-ownership :initform (make-hash-table :test #'eq) :reader diagnostics-output-ownership)))

(defgeneric material-diagnostics (material)
  (:documentation "Return a run-local adapter for the material's native class."))

(defgeneric specialized-material-diagnostics (particle-class material)
  (:documentation "Optional native-class adapter; return NIL to preserve default dispatch."))

(defmethod specialized-material-diagnostics (particle-class material)
  (declare (ignore particle-class material)) nil)

(defgeneric diagnostics-particle-type (diagnostics))

(defgeneric diagnostics-modes (diagnostics))

(defgeneric diagnostics-conventions (diagnostics))

(defgeneric diagnostics-fields (diagnostics)
  (:documentation "Fields: (name SI-unit reduction accessor definition). No mutation."))

(defgeneric diagnostics-legacy-values (diagnostics particle)
  (:documentation "Legacy VM plastic strain and normalized yield excess, or NIL unavailable."))
