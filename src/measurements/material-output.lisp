;;;; Existing read-only diagnostics; defining bodies preserved exactly.
(in-package :cl-mpm/framework)

(defun native-output-field-names (sim previous-owned)
  (append
   (remove-if (lambda (name) (member name previous-owned :test #'string=))
              (mapcar #'first (cl-mpm::sim-output-list-scalar sim)))
   (loop for (name accessor) in (cl-mpm::sim-output-list-vector sim)
         append (cons name (loop for suffix in '("x" "y" "z") collect (format nil "~A_~A" name suffix))))
   (loop for (name accessor) in (append (cl-mpm::sim-output-list-voigt sim)
                                      (cl-mpm::sim-output-list-matrix sim))
         append (cons name (loop for suffix in '("xx" "yy" "zz" "xy" "yx" "yz" "zx")
                                 collect (format nil "~A_~A" name suffix))))))

(defun validate-diagnostic-fields (adapter &optional sim)
  (let* ((fields (diagnostics-fields adapter))
         (names nil)
         (reserved (when sim (native-output-field-names
                              sim (gethash sim (diagnostics-output-ownership adapter))))))
    (unless (listp fields) (error "Material diagnostic fields must be a list."))
    (dolist (field fields)
      (unless (and (listp field) (= (length field) 5))
        (error "A material diagnostic field needs name, unit, reduction, accessor and definition."))
      (destructuring-bind (name unit reduction accessor definition) field
        (unless (and (stringp name) (plusp (length name))
                     (every (lambda (character) (or (alphanumericp character) (find character "-_"))) name)
                     (stringp unit) (plusp (length unit))
                     (member reduction '(:mean :max))
                     (or (functionp accessor) (and (symbolp accessor) (fboundp accessor)))
                     (stringp definition) (plusp (length definition)))
          (error "Invalid material diagnostic descriptor ~S." field))
        (when (or (member name names :test #'string=) (member name reserved :test #'string=))
          (error "Duplicate or reserved native output diagnostic name ~S." name))
        (push name names)))
    fields))

(defun configure-material-output (adapter sim)
  "Configure only this simulation; leave legacy VM output byte behavior intact."
  (let ((fields (validate-diagnostic-fields adapter sim)))
    (when (or fields (not (typep adapter 'vm-material-diagnostics)))
      (let ((owned-names (append (unless (typep adapter 'vm-material-diagnostics) '("yield-function" "plastic-strain"))
                                 (gethash sim (diagnostics-output-ownership adapter)))))
      (setf (cl-mpm::sim-output-list-scalar sim)
          (append
           (remove-if (lambda (field) (member (first field) owned-names
                                              :test #'string=))
                      (copy-list (cl-mpm::sim-output-list-scalar sim)))
           (loop for (name unit reduction accessor definition) in fields
                 collect (list name accessor))))
        (setf (gethash sim (diagnostics-output-ownership adapter)) (mapcar #'first fields)))))
  sim)
