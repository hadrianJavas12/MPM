;;;; Failure-only principal-return inputs. No I/O or per-update capture overhead.
(in-package :cl-mpm/models/mc-evolution)

(defun %diagnostic-object (&rest entries)
  (let ((object (make-hash-table :test 'equal)))
    (loop for (key value) on entries by #'cddr
          do (setf (gethash key object) value))
    object))

(defun %diagnostic-table-copy (table)
  (map 'vector (lambda (row) (map 'vector #'identity row)) table))

(defun %principal-failure-diagnostic (reason trial e nu j law old-kappa)
  "Own all mutable inputs needed to replay this pure return, including supplied J.
The hash tables, strings and vectors can be encoded as JSON by an optional caller.
This is not a whole-MPM restart state and does not infer any missing input."
  (%diagnostic-object
   "schema" "cl-mpm.mc-evolution.principal-failure" "schemaVersion" 1
   "reason" (copy-seq reason)
   "scope" "Pure principal return inputs; exact supplied J; not a whole-MPM restart"
   "trialKirchhoffPa" (map 'vector #'identity trial)
   "youngsModulusPa" e "poissonRatio" nu "deformationJacobian" j "oldKappa" old-kappa
   "law"
   (%diagnostic-object
    "variant" (string-downcase (symbol-name (evolution-law-variant law)))
    "points" (%diagnostic-table-copy (evolution-law-points law))
    "cohesionPoints" (%diagnostic-table-copy (evolution-law-cohesion-points law))
    "psi" (if (eq (evolution-law-psi law) :associated)
              "associated" (evolution-law-psi law))
    "stressMeasure" (string-downcase (symbol-name (evolution-law-stress-measure law)))
    "strainAssumption" (copy-seq (evolution-law-strain-assumption law))
    "peakKappa" (evolution-law-peak-kappa law))))

(defun %principal-integration-fail (reason trial e nu j law old-kappa &rest details)
  "Attach an owned diagnostic only on failure; preserve legacy reason/details.
An invalid diagnostic input must never replace or conceal the original condition."
  (let ((diagnostic (handler-case
                        (%principal-failure-diagnostic reason trial e nu j law old-kappa)
                      (error () nil))))
    (error 'material-integration-error :reason reason :details details :diagnostic diagnostic)))

(defun %diagnostic-field (object key)
  (unless (hash-table-p object) (error "MC diagnostic must contain JSON objects."))
  (multiple-value-bind (value present-p) (gethash key object)
    (unless present-p (error "Missing required MC diagnostic field ~S." key))
    value))

(defun %diagnostic-enum (value allowed)
  (or (and (stringp value) (cdr (assoc value allowed :test #'string=)))
      (error "Unknown MC diagnostic enum value ~S." value)))

(defun %diagnostic-table-list (table)
  (map 'list (lambda (row) (coerce row 'list)) table))

(defun replay-integration-diagnostic (diagnostic)
  "Replay the pure PROJECT-PRINCIPAL call or signal its original failure again.
Accept an in-memory payload or the decoded JSON object. Every required input,
especially J, must be supplied. No material defaults or filesystem I/O are used."
  (unless (and (equal (%diagnostic-field diagnostic "schema")
                      "cl-mpm.mc-evolution.principal-failure")
               (eql (%diagnostic-field diagnostic "schemaVersion") 1))
    (error "Unsupported MC integration diagnostic schema."))
  (let* ((record (%diagnostic-field diagnostic "law"))
         (psi (%diagnostic-field record "psi"))
         (law (make-evolution-law
               :variant (%diagnostic-enum (%diagnostic-field record "variant")
                                          '(("perfect" . :perfect) ("h" . :h) ("hs" . :hs)))
               :points (%diagnostic-table-list (%diagnostic-field record "points"))
               :cohesion-points (%diagnostic-table-list (%diagnostic-field record "cohesionPoints"))
               :psi (if (stringp psi)
                        (%diagnostic-enum psi '(("associated" . :associated))) psi)
               :stress-measure (%diagnostic-enum (%diagnostic-field record "stressMeasure")
                                                 '(("cauchy" . :cauchy) ("kirchhoff" . :kirchhoff)))
               :strain-assumption (%diagnostic-field record "strainAssumption")
               :peak-kappa (%diagnostic-field record "peakKappa"))))
    ;; A symbol function designator permits this diagnostic module to load before
    ;; the projector without adding a dependency on JSON or a second model.
    (funcall 'project-principal
             (map 'vector #'identity (%diagnostic-field diagnostic "trialKirchhoffPa"))
             (%diagnostic-field diagnostic "youngsModulusPa")
             (%diagnostic-field diagnostic "poissonRatio")
             (%diagnostic-field diagnostic "deformationJacobian")
             law (%diagnostic-field diagnostic "oldKappa"))))
