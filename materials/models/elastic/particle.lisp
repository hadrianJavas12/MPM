(in-package :cl-mpm/particle)

(declaim (optimize (debug 0) (safety 0) (speed 3)))



;; (defun mp-mass (mp)
;;   (sb-mop:standard-instance-access mp 0))
;; (defun mp-volume (mp)
;;   (sb-mop:standard-instance-access mp 4))
;; (defun mp-volume-0 (mp)
;;   (sb-mop:standard-instance-access mp 5))
;; (defun mp-deformation-gradient (mp)
;;   (sb-mop:standard-instance-access mp 22))

(defclass particle-elastic (particle)
  ((E
    :type double-float
    :accessor mp-E
    :initarg :E)
   (nu
    :type double-float
    :accessor mp-nu
    :initarg :nu)
   (elastic-matrix
    :accessor mp-elastic-matrix
    :type magicl:matrix/double-float)
   (tangent-stiffness
    :accessor mp-tangent-stiffness
    :initform (cl-mpm/utils::tensor-voigt-4th-zeros)
    :type magicl:matrix/double-float)
   (2d-approximation
    :accessor mp-elastic-approximation
    :initarg :elastic-approxmation
    :initform :plane-strain
    :type t
    )
   )
  (:documentation "A Hencky hyperelastic material point"))

(defclass particle-linear-elastic (particle-elastic)
  ()
  (:documentation "A true linear-elastic material point"))

(declaim (ftype (function (double-float double-float) double-float) calculate-bulk-modulus))
(defun calculate-bulk-modulus (E nu)
  (cl-mpm/utils::calculate-bulk-modulus E nu))
(declaim (ftype (function (double-float double-float) double-float) calculate-shear-modulus))
(defun calculate-shear-modulus (E nu)
  (cl-mpm/utils::calculate-shear-modulus E nu))
(declaim (ftype (function (double-float double-float) double-float) calculate-p-wave-modulus))
(defun calculate-p-wave-modulus (E nu)
  (cl-mpm/utils::calculate-p-wave-modulus E nu))

(defun compute-p-modulus (particle)
  (with-accessors ((E  mp-E)
                   (nu mp-nu))
      particle
    (calculate-p-wave-modulus E nu)))

(defun update-p-modulus (particle)
  (with-accessors ((de mp-elastic-matrix)
                   (E  mp-E)
                   (nu mp-nu)
                   (p mp-p-modulus)
                   (p-0 mp-p-modulus-0))
      particle
    (setf p (compute-p-modulus particle))
    (setf p-0 p)))


(defun update-elastic-matrix (particle)
  (with-accessors ((de mp-elastic-matrix)
                   (dep mp-tangent-stiffness)
                   (E  mp-E)
                   (nu mp-nu)
                   (p mp-p-modulus))
      particle
    (update-p-modulus particle)
    (setf de (cl-mpm/constitutive::linear-elastic-matrix E nu))
    (cl-mpm/utils::copy-into de dep)))

(defmethod (setf mp-E) :after (value (p particle-elastic))
  (update-elastic-matrix p))
(defmethod (setf mp-nu) :after (value (p particle-elastic))
  (update-elastic-matrix p))

(defmethod initialize-instance :after ((p particle-elastic) &key)
  (update-elastic-matrix p)
  ;; (setf (cl-mpm/particle::mp-tangent-stiffness p) (cl-mpm/particle::mp-elastic-matrix p))
  ;; (call-next-method)
  )
(defmethod (setf mp-elastic-approximation) :after (value (p particle-elastic))
  (update-elastic-matrix p))
;; (defun make-particle (nD &rest args &key (constructor 'particle) (pos nil) (volume 1) (mass 1))
;;   (progn
;;     (if (eq pos nil)
;;         (setf pos (magicl:zeros (list nD 1)))
;;         (setf pos (magicl:from-list (mapcar (lambda (x) (coerce x 'double-float)) pos) (list nD 1))))
;;     (let ((stress-size 3))
;;       (make-instance constructor
;;                      :nD nD
;;                      :volume (coerce volume 'double-float)
;;                      :mass (coerce mass 'double-float)
;;                      :position pos))))
(defun make-particle-elastic (nD E nu &key (pos nil) (volume 1) (mass 1))
    (let ((p (make-particle nD 'particle-elastic :position pos :volume volume :mass mass) ))
        (progn
            (setf (mp-E p) E)
            (setf (mp-nu p) nu)
        p)))

(defun estimate-stiffness-hencky (mp)
  (*
   (the double-float (/ 1d0 (cl-mpm/fastmaths::det-3x3 (cl-mpm/particle::mp-deformation-gradient mp))))
   (the double-float (estimate-log-enhancement mp))
   (the double-float (mp-p-modulus-0 mp))))

(defmethod estimate-stiffness ((mp particle-elastic))
  (estimate-stiffness-hencky mp))

(defmethod estimate-stiffness ((mp particle-linear-elastic))
  (mp-p-modulus-0 mp))

(declaim (ftype (function (particle) double-float)
                estimate-log-enhancement
                ))
(defun estimate-log-enhancement (particle)
  (with-accessors ((def-inc mp-deformation-gradient-increment)
                   (def mp-deformation-gradient)
                   (eps mp-strain))
      particle
    ;; (multiple-value-bind (l v) (cl-mpm/utils::eig  (cl-mpm/utils::voight-to-matrix eps))
    ;;   (let ((lmax (reduce #'min l)))
    ;;     (the double-float (expt (the double-float (exp (- lmax))) 1))))
    ;; (multiple-value-bind (s1 s2 s3) (cl-mpm/fastmaths::eigenvalues-3x3 eps)
    ;;   (declare (double-float s1 s2 s3))
    ;;   (let ((lmax (min s1 s2 s3)))
    ;;     (format t "~E ~E ~E~%" s1 s2 s3)
    ;;     (the double-float (expt (the double-float (exp (- lmax))) 1))))
    (let ((lmax (cl-mpm/fastmaths::min-eigenvalue-3x3 eps)))
      ;; (format t "~E ~%" lmax)
      (the double-float (expt (the double-float (exp (- lmax))) 1)))
    ;; (the double-float (expt (the double-float (exp (- (varef eps 0)))) 1))
    ))

(defmethod constitutive-model ((mp particle-elastic) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-slots ((de elastic-matrix)
               (stress stress)
               (stress-kirchoff stress-kirchoff))
      mp
    (cl-mpm/constitutive::linear-elastic-mat strain de stress-kirchoff)))


(defclass particle-elastic-inc (particle-elastic)
  ()
  (:documentation "A linear-elastic material point"))
(defmethod constitutive-model ((mp particle-elastic-inc) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-slots ((E E)
               (nu nu)
               (de elastic-matrix)
               (stress stress)
               (strain-rate strain-rate)
               (velocity-rate velocity-rate)
               (vorticity vorticity)
               (def deformation-gradient)
               )
      mp
    ;; Non-objective stress intergration
    ;; (cl-mpm/fastmaths::fast-.+
    ;;  stress
    ;;  (cl-mpm/constitutive::linear-elastic-mat strain-rate de))
    (magicl:.+ stress (magicl:@ de strain-rate))
    ))
(defclass particle-elastic-jaumann (particle-elastic)
  ()
  (:documentation "A linear-elastic material point"))
(defmethod constitutive-model ((mp particle-elastic-jaumann) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-slots ((E E)
               (nu nu)
               (de elastic-matrix)
               (stress stress)
               (strain-rate strain-rate)
               (velocity-rate velocity-rate)
               (vorticity vorticity)
               (def deformation-gradient)
               )
      mp
    ;;Jaumann rate equation
    (cl-mpm/fastmaths::fast-.+
     stress
     (objectify-stress-jaumann
      (cl-mpm/constitutive::linear-elastic-mat strain-rate de)
      stress
      vorticity))
    ))
(defclass particle-elastic-truesdale (particle-elastic)
  ()
  (:documentation "A linear-elastic material point"))
(defmethod constitutive-model ((mp particle-elastic-truesdale) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-slots ((E E)
               (nu nu)
               (de elastic-matrix)
               (stress stress)
               (strain-rate strain-rate)
               (velocity-rate velocity-rate)
               (vorticity vorticity)
               (def deformation-gradient)
               )
      mp
    ;; Truesdale rate
    (cl-mpm/fastmaths::fast-.+
     stress
     (objectify-stress-kirchoff-truesdale
      (cl-mpm/constitutive::linear-elastic-mat strain-rate de)
      stress
      strain-rate))
    ))
(defclass particle-elastic-logspin (particle-elastic)
  ()
  (:documentation "A linear-elastic material point"))
(defmethod constitutive-model ((mp particle-elastic-logspin) strain dt)
  "Strain intergrated elsewhere, just using elastic tensor"
  (with-slots ((E E)
               (nu nu)
               (de elastic-matrix)
               (stress stress-kirchoff)
               (strain-rate strain-rate)
               (D stretch-tensor)
               (vorticity vorticity)
               (def deformation-gradient))
      mp
    (let (
          ;; (strain-rate (magicl:scale strain-rate (/ 1d0 dt)))
          ;; (vorticity (magicl:scale vorticity (/ 1d0 dt)))
          )
      (cl-mpm/fastmaths::fast-.+
       stress
       (objectify-stress-logspin
        (cl-mpm/constitutive::linear-elastic-mat strain-rate de)
        stress
        def
        vorticity
        ;; strain-rate
        D
        )))
    ))
