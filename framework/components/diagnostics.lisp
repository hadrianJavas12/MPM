;;;; Read-only material state and diagnostics, separate from constitutive updates.
(in-package :cl-mpm/framework)

(defclass native-material-diagnostics ()
  ((output-ownership :initform (make-hash-table :test #'eq) :reader diagnostics-output-ownership)))
(defclass vm-material-diagnostics (native-material-diagnostics)
  ((particle-class :initarg :particle-class :initform 'cl-mpm/particle::particle-vm
                   :reader vm-diagnostics-particle-class)
   (legacy-affine-p :initarg :legacy-affine-p :initform nil :reader vm-diagnostics-legacy-affine-p)))
(defclass mc-material-diagnostics (native-material-diagnostics) ())
(defclass elastic-material-diagnostics (native-material-diagnostics) ())

(defgeneric material-diagnostics (material)
  (:documentation "Return a run-local adapter for the material's native class."))
(defgeneric diagnostics-particle-type (diagnostics))
(defgeneric diagnostics-modes (diagnostics))
(defgeneric diagnostics-conventions (diagnostics))
(defgeneric diagnostics-fields (diagnostics)
  (:documentation "Fields: (name SI-unit reduction accessor definition). No mutation."))
(defgeneric diagnostics-legacy-values (diagnostics particle)
  (:documentation "Legacy VM plastic strain and normalized yield excess, or NIL unavailable."))

(defmethod material-diagnostics ((material material))
  (let ((type (material-particle-class material)))
    (cond ((subtypep type 'cl-mpm/particle::particle-vm)
           (make-instance 'vm-material-diagnostics :particle-class type
                          :legacy-affine-p (not (null (member (component-kind material) '(:von-mises :elastic))))))
          ((and (subtypep type 'cl-mpm/particle::particle-mc)
                (not (subtypep type 'cl-mpm/particle::particle-dp)))
           (make-instance 'mc-material-diagnostics))
          ((eq type 'cl-mpm/particle::particle-elastic)
           (make-instance 'elastic-material-diagnostics))
          (t (error "No material diagnostics adapter for ~S; specialize MATERIAL-DIAGNOSTICS." type)))))

(defmethod diagnostics-particle-type ((adapter vm-material-diagnostics))
  'cl-mpm/particle::particle-vm)
(defmethod diagnostics-particle-type ((adapter mc-material-diagnostics))
  'cl-mpm/particle::particle-mc)
(defmethod diagnostics-particle-type ((adapter elastic-material-diagnostics))
  'cl-mpm/particle::particle-elastic)
(defmethod diagnostics-modes ((adapter native-material-diagnostics)) '("mpm"))
(defmethod diagnostics-modes ((adapter vm-material-diagnostics))
  ;; A bare native VM can still receive history-changing :SOFTENING initargs.
  ;; Only the known framework constructors opt into the legacy affine state path.
  (if (and (vm-diagnostics-legacy-affine-p adapter)
           (eq (vm-diagnostics-particle-class adapter) 'cl-mpm/particle::particle-vm))
      '("mpm" "homogeneous" "controls") '("mpm")))

(defmethod diagnostics-conventions ((adapter vm-material-diagnostics))
  (list "plasticStrainConvention"
        "native sqrt(3 J2 of deviatoric plastic strain increment); 1.5 times conventional von Mises equivalent plastic strain"
        "yieldConvention"
        "rho=sqrt(8/3)*su; q_J2_kirchhoff_yield=2su; q_J2_cauchy_yield=2su/J; triaxial projection differs in plane strain"))
(defmethod diagnostics-conventions ((adapter mc-material-diagnostics))
  (list "plasticStrainConvention"
        "VM plastic_strain CSV column unavailable; mc-plastic-strain-native is accumulated sqrt(3 J2(dev delta epsilon_p)), 1.5 times conventional equivalent plastic strain; no PDF strain conversion"
        "yieldConvention"
        "VM max_yield_excess CSV column unavailable; mc-yield-residual-kirchhoff-pa=k*tau_max-tau_min-2*c*sqrt(k), k=(1+sin(phi))/(1-sin(phi)), tau=J*sigma_Cauchy, native tension-positive; signed Pa; stored native yield-function is trial f"
        "drainage" "no pore fluid or pore pressure; no true CU effective-stress path"))
(defmethod diagnostics-conventions ((adapter elastic-material-diagnostics))
  (list "plasticStrainConvention" "not available: elastic material has no plastic internal state"
        "yieldConvention" "not available: elastic material has no yield surface"))

(defmethod diagnostics-legacy-values ((adapter native-material-diagnostics) particle)
  (declare (ignore particle)) (values nil nil))
(defmethod diagnostics-legacy-values ((adapter vm-material-diagnostics) mp)
  ;; Preserve the legacy arithmetic, including its Cauchy -> Kirchhoff conversion.
  (values (cl-mpm/particle::mp-strain-plastic-vm mp)
          (- (/ (* (sqrt (* 3d0 (cl-mpm/fastmaths::voigt-j2
                                (cl-mpm/utils::deviatoric-voigt (cl-mpm/particle:mp-stress mp)))))
                    (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp)))
                 (* (sqrt 1.5d0) (cl-mpm/particle::mp-rho mp))) 1d0)))

(defun mc-kirchhoff-yield-residual (mp)
  "Independently evaluate corrected native MC yield, not stored trial f. Signed Pa."
  (let* ((tau (cl-mpm/utils::voigt-copy (cl-mpm/particle:mp-stress mp)))
         (j (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp))))
    ;; Fail before passing a nonfinite matrix to a native eigensolver.
    (loop for value across (cl-mpm/utils::fast-storage tau) do
      (unless (and (not (sb-ext:float-nan-p value)) (not (sb-ext:float-infinity-p value)))
        (error "Nonfinite Cauchy stress in MC diagnostic.")))
    (unless (and (> j 0d0) (not (sb-ext:float-nan-p j)) (not (sb-ext:float-infinity-p j)))
      (error "MC diagnostics require finite positive det(F)."))
    (cl-mpm/fastmaths:fast-scale! tau j)
    (cl-mpm/constitutive::fast-mc tau (cl-mpm/particle::mp-phi mp) (cl-mpm/particle::mp-c mp))))

(defmethod diagnostics-fields ((adapter native-material-diagnostics)) nil)
(defmethod diagnostics-fields ((adapter mc-material-diagnostics))
  (list
   (list "mc-plastic-strain-native" "1" :mean #'cl-mpm/particle::mp-strain-plastic-vm
         "accumulated sqrt(3 J2(dev delta epsilon_p)); shared native plastic state, not VM inheritance")
   (list "mc-yield-residual-kirchhoff-pa" "Pa" :max #'mc-kirchhoff-yield-residual
         "signed corrected MC residual, native tension-positive Kirchhoff stress")
   (list "mc-trial-yield-kirchhoff-pa" "Pa" :max #'cl-mpm/particle::mp-yield-func
         "stored trial yield value; not corrected residual")
   (list "mc-cohesion-pa" "Pa" :mean #'cl-mpm/particle::mp-c "current native MC cohesion")
   (list "mc-friction-rad" "rad" :mean #'cl-mpm/particle::mp-phi "current friction angle")
   (list "mc-dilation-rad" "rad" :mean #'cl-mpm/particle::mp-psi "current dilation angle")))

(defun material-state (adapter particle)
  "Read-only named material diagnostics. This is not a trial/rollback snapshot."
  (loop for (name unit reduction accessor definition) in (diagnostics-fields adapter)
        collect (cons name (funcall accessor particle))))

(defun validate-material-state (adapter particle)
  (dolist (entry (material-state adapter particle))
    (let ((value (cdr entry)))
      (unless (and (realp value)
                   (not (sb-ext:float-nan-p (float value 1d0)))
                   (not (sb-ext:float-infinity-p (float value 1d0))))
        (error "Nonfinite material state ~A." (car entry)))))
  (when (typep adapter 'mc-material-diagnostics)
    (let ((phi (cl-mpm/particle::mp-phi particle))
          (psi (cl-mpm/particle::mp-psi particle))
          (c (cl-mpm/particle::mp-c particle)))
      (unless (and (<= 0d0 phi) (< phi (* 0.5d0 pi))
                   (< (* -0.5d0 pi) psi (* 0.5d0 pi)) (>= c 0d0)
                   (>= (cl-mpm/particle::mp-strain-plastic-vm particle) 0d0))
        (error "Invalid MC material state: require nonnegative cohesion/plastic strain and finite admissible angles."))
      (when (and (cl-mpm/particle::mp-enable-plasticity particle) (= phi 0d0))
        (error "Native MC phi=0 return mapping has an unhandled apex singularity; use a declared positive-friction case or a separately verified implementation."))))
  t)

(defun validate-material-diagnostics (adapter particles mode)
  (validate-diagnostic-fields adapter)
  (unless (member mode (diagnostics-modes adapter) :test #'string=)
    (error "~A diagnostics do not support ~A: complete constitutive snapshot/restore hooks are required."
           (class-name (class-of adapter)) mode))
  (unless (and (plusp (length particles))
               (every (lambda (mp)
                        (and (typep mp (diagnostics-particle-type adapter))
                             (not (and (typep adapter 'mc-material-diagnostics)
                                       (typep mp 'cl-mpm/particle::particle-dp)))
                             (not (and (typep adapter 'elastic-material-diagnostics)
                                       (typep mp 'cl-mpm/particle::particle-plastic))))) particles))
    (error "Particles are incompatible with ~A diagnostics (expected ~S)."
           (class-name (class-of adapter)) (diagnostics-particle-type adapter)))
  (map nil (lambda (particle) (validate-material-state adapter particle)) particles)
  adapter)

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
