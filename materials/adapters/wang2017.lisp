;;;; Optional, read-only framework diagnostics for the explicit Wang Soil2 adapter.
(in-package :cl-mpm/framework)

(defclass wang2017-material-diagnostics (mc-evolution-material-diagnostics) ())

(defmethod specialized-material-diagnostics
    ((particle-class (eql 'cl-mpm/models/wang2017-native:particle-wang2017-soil2))
     (material material))
  (declare (ignore particle-class material))
  (make-instance 'wang2017-material-diagnostics))

(defmethod diagnostics-particle-type ((adapter wang2017-material-diagnostics))
  'cl-mpm/models/wang2017-native:particle-wang2017-soil2)

(defmethod diagnostics-conventions ((adapter wang2017-material-diagnostics))
  (list "plasticStrainConvention"
        "wang-paper-kps=sqrt(.5*dev(Ep):dev(Ep)); Ep is signed accumulated physical-shear tensor, transported by the declared native incremental corotation. It is not accumulated J2 increments or damage."
        "yieldConvention"
        "Signed corrected six-plane MC Kirchhoff residual; c is Cauchy cohesion, tau=det(F)*sigma. Soil2 cohesion30->15kPa over paper kps0->.02; phi35deg,psi0."
        "historyConvention"
        "Candidates whose paper history decreases by more than1e-13 are rejected atomically by the explicit native monotonic-scope guard; no max-history clamp or accepted-state healing is inferred. The flag describes the last accepted step; rejected inputs belong to the separate failure capsule."
        "tensorFrame"
        "Ep components xx,yy,zz,yz,zx,xy use physical shear in the current transported spatial frame. Rotation is the last accepted incremental polar rotation, row-major R00..R22. F is the actual native deformation gradient."
        "drainage" "No pore fluid or pore-pressure coupling; no laboratory calibration or FEM equivalence claimed."))

(defun wang2017-det-f (particle)
  (let ((j (cl-mpm/fastmaths:det-3x3
            (cl-mpm/particle:mp-deformation-gradient particle))))
    (unless (and (realp j) (not (sb-ext:float-nan-p (float j 1d0)))
                 (not (sb-ext:float-infinity-p (float j 1d0))) (> j 0d0))
      (error "Wang audit requires finite positive actual det(F)."))
    j))

(defun wang2017-reconstructed-kps (particle)
  (cl-mpm/models/wang2017:paper-kps
   (cl-mpm/models/wang2017-native:particle-paper-tensor particle)))

(defun wang2017-kps-residual (particle)
  (- (cl-mpm/models/wang2017-native:particle-paper-kps particle)
     (wang2017-reconstructed-kps particle)))

(defun wang2017-vector-reader (reader index)
  (lambda (particle) (aref (funcall reader particle) index)))

(defun wang2017-matrix-reader (reader row column)
  (lambda (particle) (magicl:tref (funcall reader particle) row column)))

(defun wang2017-last-diagnostic-number (particle key)
  (let ((value (getf (cl-mpm/models/wang2017-native:particle-last-paper-diagnostic particle)
                    key 0d0)))
    (unless (realp value) (error "Wang diagnostic ~S must be numeric." key))
    value))

(defmethod diagnostics-fields ((adapter wang2017-material-diagnostics))
  (append
   (list
    (list "wang-paper-kps" "1" :mean
          #'cl-mpm/models/wang2017-native:particle-paper-kps
          "Norm of transported accumulated signed plastic tensor; not J2 history or damage")
    (list "wang-paper-kps-reconstructed" "1" :mean #'wang2017-reconstructed-kps
          "Independent paper tensor invariant reconstructed from exported Ep")
    (list "wang-paper-kps-residual" "1" :max #'wang2017-kps-residual
          "Stored paper kps minus invariant reconstructed from current Ep")
    (list "wang-cohesion-pa" "Pa" :mean
          #'cl-mpm/models/wang2017-native:particle-paper-cohesion
          "Current native Soil2 Cauchy cohesion; no inferred damage scalar")
    (list "wang-det-f" "1" :mean #'wang2017-det-f
          "Actual native det(F), not a volume-ratio proxy")
    (list "wang-history-decrease-accepted" "1" :max
          (lambda (particle)
            (if (cl-mpm/models/wang2017-native:particle-history-decrease-p particle) 1d0 0d0))
          "Last accepted-step history-decrease flag; rejected trial is retained separately")
    (list "wang-previous-paper-kps" "1" :mean
          (lambda (particle) (wang2017-last-diagnostic-number particle :previous-kps))
          "Previous paper kps reported by the last accepted material transaction")
    (list "wang-step-history-residual" "1" :max
          (lambda (particle) (wang2017-last-diagnostic-number particle :history-residual))
          "Last accepted material projection history residual")
    (list "wang-legacy-j2-increment" "1" :mean
          (lambda (particle) (wang2017-last-diagnostic-number particle :legacy-j2-increment))
          "Independent equivalent-J2 increment; not used as paper tensor history")
    (list "mc-yield-residual-kirchhoff-pa" "Pa" :max
          #'cl-mpm/models/mc-evolution:particle-yield-residual-kirchhoff
          "Signed corrected six-plane MC Kirchhoff residual")
    (list "mc-cohesion-pa" "Pa" :mean
          #'cl-mpm/models/wang2017-native:particle-paper-cohesion
          "Current Soil2 Cauchy cohesion, explicit common-field alias")
    (list "mc-friction-rad" "rad" :mean #'cl-mpm/models/mc-evolution:particle-phi
          "Current friction angle")
    (list "mc-dilation-rad" "rad" :mean #'cl-mpm/models/mc-evolution:particle-psi
          "Current dilation angle")
    (list "mc-plastic-work-j-m3" "Pa" :mean #'cl-mpm/models/mc-evolution:particle-plastic-work
          "Native accumulated plastic-work density; not a closed energy balance"))
   (loop for suffix in '("xx" "yy" "zz" "yz" "zx" "xy") for index from 0
         collect (list (format nil "wang-Ep-~A" suffix) "1" :mean
                       (wang2017-vector-reader
                        #'cl-mpm/models/wang2017-native:particle-paper-tensor index)
                       "Current transported plastic tensor component; physical shear"))
   (loop for row below 3 append
         (loop for column below 3
               collect (list (format nil "wang-F-~D~D" row column) "1" :mean
                             (wang2017-matrix-reader
                              #'cl-mpm/particle:mp-deformation-gradient row column)
                             "Actual native deformation-gradient component")))
   (loop for row below 3 append
         (loop for column below 3
               collect (list (format nil "wang-R-~D~D" row column) "1" :mean
                             (wang2017-matrix-reader
                              #'cl-mpm/models/wang2017-native:particle-rotation row column)
                             "Last accepted incremental polar-rotation component")))))

(defun validate-wang2017-audit-particle (particle)
  "Read-only output identity checks; never repair or mutate material state."
  (wang2017-det-f particle)
  (let ((residual (wang2017-kps-residual particle)))
    (unless (and (realp residual)
                 (not (sb-ext:float-nan-p (float residual 1d0)))
                 (not (sb-ext:float-infinity-p (float residual 1d0)))
                 (<= (abs residual) 1d-12))
      (error "Wang paper kps/Ep identity failed: residual ~S." residual)))
  t)
