;;;; Optional exact-class integration; no geometry, solver or strength changes.
(in-package :cl-mpm/scenario/gravity-slope)

(defmethod check-gravity-material-class
    ((particle-class (eql 'cl-mpm/models/mc-composite-apex:particle-mc-composite-apex))
     material config)
  (let* ((diagnostics (cl-mpm/framework:material-diagnostics material))
         (conventions (cl-mpm/framework:diagnostics-conventions diagnostics)))
    (unless (and (eq (class-name (class-of diagnostics))
                     'cl-mpm/framework::mc-composite-apex-material-diagnostics)
                 (eq (cl-mpm/framework:diagnostics-particle-type diagnostics) particle-class))
      (error "Composite gravity slope requires its explicitly installed diagnostics adapter."))
    (labels ((convention (key)
               (let ((value (loop for (name value) on conventions by #'cddr
                                  when (string= name key) return value)))
                 (unless (and (stringp value) (plusp (length value)))
                   (error "Composite diagnostics lack convention ~A." key))
                 value)))
      (unless (string= (convention "materialVariant") "perfect-mc-composite-apex")
        (error "Unexpected composite gravity-slope material variant."))
      (dolist (key '("materialVariant" "apexConvention" "apexCapBandPolicy" "apexMultiplierConvention"))
        (setf (gethash key config) (copy-seq (convention key)))))
    ;; The exact class symbol selects the model. This derived string records
    ;; that choice; no caller-supplied metadata string can enable the model.
    (setf (gethash "materialClass" config)
          (format nil "~A:~A" (package-name (symbol-package particle-class)) (symbol-name particle-class))
          (gethash "strengthReduction" config)
          (format nil "Independent pre-reduced perfect Cauchy MC at SRF=~F: c/F and atan(tan(phi)/F); explicit additional hydrostatic-apex gA=p volumetric flow, not unchanged strict MC or a verified unstable bound"
                  (gethash "strengthReductionFactor" config)))
    t))
