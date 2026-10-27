(in-package :cl-mpm/scenario/urmi-damage40)

(defparameter +extended-inputs+
  (mapcar (lambda (entry)
    (cons (car entry) (or (cdr (assoc (car entry)
      '(("crestLength" . 24d0) ("baseHeight" . 8d0) ("domainWidth" . 72d0) ("domainHeight" . 24d0))
      :test #'string=)) (cdr entry)))) +rapid-inputs+))

(defun compile-extended-configuration (case)
  (let ((actual (fw:simulation-parameters case)) (geometry (fw:simulation-geometry case))
        (input (make-hash-table :test #'equal)))
    (unless (= (hash-table-count actual) (length +extended-inputs+)) (error "Extended input keys differ."))
    (dolist (entry +extended-inputs+)
      (unless (and (gs::finite-p (gethash (car entry) actual)) (= (gethash (car entry) actual) (cdr entry)))
        (error "Extended parameter differs: ~A" (car entry))))
    (fw::check-kind geometry '(:slope))
    (dolist (entry '((:height . 10d0) (:crest-length . 24d0) (:slope . 40d0) (:base-height . 8d0)))
      (unless (= (fw:option geometry (car entry)) (cdr entry)) (error "Extended geometry component differs.")))
    (unless (= (fw:option geometry :width) (+ 24d0 (/ 10d0 (tan (* pi (/ 40d0 180d0))))))
      (error "Extended slope toe differs."))
    (dolist (entry +rapid-inputs+) (setf (gethash (car entry) input) (cdr entry)))
    ;; Validate the unchanged material/solver/boundaries with the existing rapid
    ;; profile using an isolated old-geometry description, never by mutating it.
    (let* ((old (fw:make-simulation :scenario :urmi-damage40-rapid :parameters input
             :material (fw:simulation-material case)
             :geometry (fw:make-geometry :slope :width (+ 12d0 (/ 10d0 (tan (* pi (/ 40d0 180d0)))))
                         :height 10d0 :crest-length 12d0 :slope 40d0 :base-height 4d0)
             :boundary (fw:simulation-boundary case) :loading (fw:simulation-loading case)
             :solver (fw:simulation-solver case)))
           (config (compile-rapid-configuration old)))
      (dolist (entry +extended-inputs+) (setf (gethash (car entry) config) (cdr entry)))
      (setf (gethash "toeX" config) (+ 24d0 (/ 10d0 (tan (* pi (/ 40d0 180d0)))))
            (gethash "observerInitialXGreater" config) 14d0 (gethash "observerInitialYGreater" config) 10d0
            (gethash "displayOriginX" config) 12d0 (gethash "displayOriginY" config) 8d0
            (gethash "rapidScenarioName" config) "urmi-damage40-extended"
            (gethash "geometryLabel" config) "Approved+12m LEFT/base8m: crest24/toe35.9175359/H10/40deg; domain72x24; no notch; same active soil")
      config)))

(in-package :cl-mpm/framework)
(defmethod compile-scenario ((scenario (eql :urmi-damage40-extended)) (case simulation))
  (cl-mpm/scenario/urmi-damage40::compile-extended-configuration case))
(defmethod execute-scenario ((scenario (eql :urmi-damage40-extended)) (case simulation) config directory)
  (declare (ignore scenario))
  (cl-mpm/scenario/urmi-damage40:run (simulation-material case) config directory
    :approximate-preparation-duration 3d0))
