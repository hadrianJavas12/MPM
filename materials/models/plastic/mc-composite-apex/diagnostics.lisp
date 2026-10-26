;;;; Failure-only owned inputs for the optional perfect-Cauchy composite apex.
;;;; No JSON library, filesystem access, retry or particle state is used here.
(in-package :cl-mpm/models/mc-composite-apex)

(defun %composite-json-copy (value)
  "Own a JSON-shaped diagnostic tree, including its keys and all strings.
Finite integers/floats remain numbers. Nonfinite derived floats use explicit
tags so an optional JSON writer never receives raw NaN or infinity. Unsupported
values fail capture rather than inventing a lossy representation of an input."
  (cond
    ((or (null value) (eq value t)) value)
    ((stringp value) (copy-seq value))
    ((integerp value) value)
    ((floatp value)
     (cond ((sb-ext:float-nan-p value)
            (%composite-json-copy
             (mc::%diagnostic-object "numberKind" "nonfinite" "value" "nan")))
           ((sb-ext:float-infinity-p value)
            (%composite-json-copy
             (mc::%diagnostic-object "numberKind" "nonfinite" "value"
                                    (if (minusp value) "negative-infinity" "positive-infinity"))))
           (t value)))
    ((hash-table-p value)
     (let ((copy (make-hash-table :test 'equal)))
       (maphash (lambda (key item)
                  (unless (stringp key)
                    (error "Composite diagnostic object keys must be strings."))
                  (setf (gethash (copy-seq key) copy) (%composite-json-copy item)))
                value)
       copy))
    ((or (vectorp value) (listp value))
     (map 'vector #'%composite-json-copy value))
    (t (error "Unsupported composite diagnostic value type ~S." (type-of value)))))

(defun %composite-failure-diagnostic (reason trial e nu j law old-kappa)
  "Reuse the complete strict-law input record with a distinct optional schema.
The recursive copy also owns schema/scope strings and nested keys, so separate
capsules cannot share mutable text. This is a pure-return input, not a restart."
  (let ((record (mc::%principal-failure-diagnostic reason trial e nu j law old-kappa)))
    (setf (gethash "schema" record) "cl-mpm.mc-composite-apex.principal-failure"
          (gethash "schemaVersion" record) 1
          (gethash "materialVariant" record) "perfect-mc-composite-apex"
          (gethash "scope" record)
          "Owned optional composite-apex pure-return inputs; exact supplied J; not a whole-MPM restart")
    (%composite-json-copy record)))

(defun %composite-capture-error-text (condition)
  ;; Even a condition's custom printer must not conceal the material failure.
  (handler-case (copy-seq (princ-to-string condition))
    (error () (copy-seq "Detailed composite diagnostic capture failed."))))

(defun %composite-integration-fail (reason trial e nu j law old-kappa checks-thunk &rest details)
  "Signal the original material failure once, with best-effort owned capture.
CHECKS-THUNK runs only on this failure path. A checks/encoding error retains the
base input capsule; a base capture error leaves its diagnostic NIL. Neither
case changes the condition class, reason, details, or propagation/termination."
  (let* ((condition (make-condition 'mc:material-integration-error :reason reason :details details))
         (record (handler-case
                     (%composite-failure-diagnostic reason trial e nu j law old-kappa)
                   (error () nil))))
    (when record
      (handler-case
          (setf (gethash (copy-seq "checks") record)
                (%composite-json-copy (funcall checks-thunk)))
        (error (capture-error)
          (setf (gethash (copy-seq "checksCaptureError") record)
                (%composite-capture-error-text capture-error)))))
    (setf (slot-value condition 'mc::diagnostic) record)
    (error condition)))

(defun replay-integration-diagnostic (diagnostic)
  "Call only this optional projector once from a matching input capsule.
Every replay input is required. The existing law constructor and optional
projector validate material/numeric inputs; no defaults, I/O or evaluation of
source text are involved. Strict and Wang capsules are explicitly rejected."
  (unless (and (equal (mc::%diagnostic-field diagnostic "schema")
                      "cl-mpm.mc-composite-apex.principal-failure")
               (eql (mc::%diagnostic-field diagnostic "schemaVersion") 1)
               (equal (mc::%diagnostic-field diagnostic "materialVariant")
                      "perfect-mc-composite-apex"))
    (error "Unsupported composite-apex integration diagnostic schema or variant."))
  (let* ((trial (mc::%diagnostic-field diagnostic "trialKirchhoffPa"))
         (e (mc::%diagnostic-field diagnostic "youngsModulusPa"))
         (nu (mc::%diagnostic-field diagnostic "poissonRatio"))
         (j (mc::%diagnostic-field diagnostic "deformationJacobian"))
         (old-kappa (mc::%diagnostic-field diagnostic "oldKappa"))
         (record (mc::%diagnostic-field diagnostic "law"))
         (psi (mc::%diagnostic-field record "psi"))
         (law (mc:make-evolution-law
               :variant (mc::%diagnostic-enum (mc::%diagnostic-field record "variant")
                                             '(("perfect" . :perfect) ("h" . :h) ("hs" . :hs)))
               :points (mc::%diagnostic-table-list (mc::%diagnostic-field record "points"))
               :cohesion-points (mc::%diagnostic-table-list
                                (mc::%diagnostic-field record "cohesionPoints"))
               :psi (if (stringp psi)
                        (mc::%diagnostic-enum psi '(("associated" . :associated))) psi)
               :stress-measure (mc::%diagnostic-enum (mc::%diagnostic-field record "stressMeasure")
                                                    '(("cauchy" . :cauchy) ("kirchhoff" . :kirchhoff)))
               :strain-assumption (mc::%diagnostic-field record "strainAssumption")
               :peak-kappa (mc::%diagnostic-field record "peakKappa"))))
    ;; The optional diagnostics component deliberately loads before projection.
    (funcall 'project-principal-with-apex (map 'vector #'identity trial) e nu j law old-kappa)))
