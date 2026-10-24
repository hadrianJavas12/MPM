;;;; Spatial Hencky/Kirchhoff adapter with rotation-only signed-history transport.
(in-package :cl-mpm/models/wang2017-native)

(defgeneric project-point-variant (variant trial e nu j history basis)
  (:documentation "Pure point dispatch. Optional models add explicit EQL variants."))
(defmethod project-point-variant ((variant (eql :strict)) trial e nu j history basis)
  (point:project-paper-principal trial e nu j history basis))
(defgeneric project-native-point (mp trial e nu j history basis))
(defmethod project-native-point ((mp particle-wang2017-soil2) trial e nu j history basis)
  (project-point-variant :strict trial e nu j history basis))
(defgeneric native-material-variant (mp))
(defmethod native-material-variant ((mp particle-wang2017-soil2)) "strict")

(defun %matrix-rows (matrix)
  (when (typep matrix 'magicl:matrix/double-float)
    (map 'vector (lambda (i)
                   (map 'vector (lambda (j) (magicl:tref matrix i j)) '(0 1 2))) '(0 1 2))))

(defun %array-basis (matrix)
  (let ((array (make-array '(3 3) :element-type 'double-float)))
    (dotimes (i 3 array) (dotimes (j 3)
      (setf (aref array i j) (magicl:tref matrix i j))))))

(defun %guard-history (old new)
  (when (< new (- old 1d-13))
    (mc-evolution::integration-fail
     "Wang signed history decreased outside the declared monotonic scope; healing/irreversible continuation is not approved"
     old new)))

(defun %failure-diagnostic (reason trial e nu j committed rotated basis increment rotation)
  (mc-evolution::%diagnostic-object
   "schema" "cl-mpm.wang2017.native-failure" "schemaVersion" 1 "reason" (copy-seq reason)
   "scope" "Owned failed native constitutive inputs; not a full-MPM restart"
   "trialKirchhoffPa" (when trial (copy-seq trial))
   "youngsModulusPa" e "poissonRatio" nu "deformationJacobian" j
   "committedPlasticTensor" (when committed (copy-seq committed))
   "rotatedPlasticTensor" (when rotated (copy-seq rotated))
   "principalToSpatialBasis" (%matrix-rows basis)
   "transportIncrement" (%matrix-rows increment) "polarRotation" (%matrix-rows rotation)
   "historyDecreaseTolerance" 1d-13
   "historyPolicy" "Reject decrease beyond roundoff; no max/healing/apex convention"
   "transportConvention" "Incremental polar corotation of committed signed spatial Ep; not an exact multiplicative Fp model"))

(defun replay-native-diagnostic (diagnostic)
  "Replay a captured pure point return plus monotonic-scope guard; no particle/I/O."
  (flet ((field (key) (mc-evolution::%diagnostic-field diagnostic key)))
    (unless (and (equal (field "schema") "cl-mpm.wang2017.native-failure")
                 (eql (field "schemaVersion") 1))
      (error "Unsupported Wang native failure schema."))
    (let* ((variant-name (or (field "materialVariant") "strict"))
           (variant (cond ((equal variant-name "strict") :strict)
                          ((equal variant-name "composite-apex") :composite-apex)
                          (t (error "Unsupported Wang material variant ~S." variant-name))))
           (rows (field "principalToSpatialBasis"))
           (basis (make-array '(3 3) :element-type 'double-float)))
      (dotimes (i 3) (dotimes (j 3) (setf (aref basis i j) (elt (elt rows i) j))))
      (let ((result (project-point-variant variant
                     (field "trialKirchhoffPa") (field "youngsModulusPa")
                     (field "poissonRatio") (field "deformationJacobian")
                     (paper:make-paper-history (field "rotatedPlasticTensor")) basis)))
        (%guard-history (paper:paper-kps (field "committedPlasticTensor"))
                        (point:paper-projection-kps result))
        result))))

(defmethod cl-mpm/particle:constitutive-model ((mp particle-wang2017-soil2) strain dt)
  "Return Kirchhoff stress; the engine owns elastic transport and tau/J conversion.
Only committed Ep is polar-rotated. Trial strain/eigenbasis and returned spatial
plastic increments are never rotated twice. All native mutation follows validation."
  (declare (ignore dt))
  (let ((trial nil) (e nil) (nu nil) (j nil) (committed nil) (rotated nil)
        (basis nil) (increment nil) (rotation nil))
    (handler-case
        (progn
          (%validate-fixed-inputs mp)
          (%checked-matrix strain 6 1 "trial elastic Hencky strain")
          (%checked-matrix (cl-mpm/particle:mp-deformation-gradient mp) 3 3 "F")
          (setf e (cl-mpm/particle::mp-E mp) nu (cl-mpm/particle::mp-nu mp)
                j (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp))
                committed (particle-paper-tensor-committed mp)
                increment (cl-mpm/particle::mp-deformation-gradient-strain-increment mp))
          (unless (and (mc-evolution::finite-real-p j) (> j 0d0))
            (mc-evolution::integration-fail "Wang material requires positive finite J"))
          (multiple-value-setq (rotated rotation) (transport-paper-tensor committed increment))
          (multiple-value-bind (principal-list eigenbasis)
              (cl-mpm/utils:eig (cl-mpm/utils:voigt-to-matrix strain))
            (setf basis eigenbasis)
            (%checked-matrix basis 3 3 "trial eigenbasis")
            (let* ((principal (coerce principal-list 'vector))
                   (g (/ e (* 2d0 (+ 1d0 nu))))
                   (lambda-elastic (/ (* e nu) (* (+ 1d0 nu) (- 1d0 (* 2d0 nu)))))
                   (trace (reduce #'+ principal))
                   (old-kps (paper:paper-kps committed)))
              (setf trial (map 'vector (lambda (eps) (+ (* 2d0 g eps) (* lambda-elastic trace))) principal))
              (let* ((result (when (cl-mpm/particle::mp-enable-plasticity mp)
                               (project-native-point mp trial e nu j
                                (paper:make-paper-history rotated) (%array-basis basis))))
                     (tau (if result (point:paper-projection-tau result) trial))
                     (plastic (if result (point:paper-projection-plastic-increment result) #(0d0 0d0 0d0)))
                     (next (if result (paper:history-tensor (point:paper-projection-history result)) rotated))
                     (kps (paper:paper-kps next))
                     (elastic (map 'vector #'- principal plastic))
                     (new-strain (cl-mpm/utils:matrix-to-voigt (mc-evolution::%adapter-principal-to-tensor elastic basis)))
                     (new-tau (cl-mpm/utils:matrix-to-voight (mc-evolution::%adapter-principal-to-tensor tau basis)))
                     (new-plastic (cl-mpm/utils:matrix-to-voigt (mc-evolution::%adapter-principal-to-tensor plastic basis)))
                     (j2-increment (mc-evolution::plastic-kappa-increment plastic))
                     (legacy-j2 (+ (%legacy-j2-committed mp) j2-increment))
                     (volume (+ (mc-evolution:particle-plastic-volume-committed mp) (reduce #'+ plastic)))
                     (work (+ (mc-evolution:particle-plastic-work-committed mp)
                              (if result (/ (point:paper-projection-work result) j) 0d0)))
                     (law (mc-evolution:particle-evolution-law mp))
                     (residual (if result (point:paper-projection-max-residual result)
                                   (mc-evolution::%adapter-max-plane-value tau law kps j)))
                     (p0 (/ (* e (- 1d0 nu)) (* (+ 1d0 nu) (- 1d0 (* 2d0 nu)))))
                     (p-wave (* (/ p0 j) (exp (- (reduce #'min elastic)))))
                     (diagnostic (list :previous-kps old-kps :current-kps kps
                                      :history-decrease-p (< kps old-kps)
                                      :history-residual (if result (point:paper-projection-history-residual result) 0d0)
                                      :yield-residual-pa residual :legacy-j2-increment j2-increment
                                      :branch (if result (point:paper-projection-branch result) :plasticity-disabled)
                                      :evaluations (if result (point:paper-projection-evaluations result) 0)
                                      :transport-convention "Incremental polar corotation of committed signed spatial Ep")))
                (%guard-history old-kps kps)
                (unless (and (every #'mc-evolution::finite-real-p (list kps j2-increment legacy-j2 volume work residual p-wave))
                             (>= j2-increment 0d0) (>= legacy-j2 0d0) (> p-wave 0d0))
                  (mc-evolution::integration-fail "Invalid Wang material result"))
                (dolist (matrix (list new-strain new-tau new-plastic (cl-mpm/particle:mp-strain mp)
                                     (cl-mpm/particle::mp-stress-kirchoff mp)
                                     (cl-mpm/particle::mp-strain-plastic mp)
                                     (mc-evolution:particle-plastic-increment mp)))
                  (%checked-matrix matrix 6 1 "material return/target"))
                (multiple-value-bind (c phi psi) (mc-evolution:law-values law kps)
                  (cl-mpm/utils:voigt-copy-into new-strain (cl-mpm/particle:mp-strain mp))
                  (cl-mpm/utils:voigt-copy-into new-tau (cl-mpm/particle::mp-stress-kirchoff mp))
                  (cl-mpm/utils:voigt-copy-into new-plastic (cl-mpm/particle::mp-strain-plastic mp))
                  (cl-mpm/utils:voigt-copy-into new-plastic (mc-evolution:particle-plastic-increment mp))
                  (setf (%paper-tensor mp) next (%paper-rotation mp) rotation
                        (%history-decrease-p mp) (< kps old-kps) (%paper-diagnostic mp) diagnostic
                        (mc-evolution:particle-kappa mp) kps (mc-evolution:particle-cohesion mp) c
                        (mc-evolution:particle-phi mp) phi (mc-evolution:particle-psi mp) psi
                        (mc-evolution:particle-plastic-volume mp) volume (mc-evolution:particle-plastic-work mp) work
                        (mc-evolution:particle-last-projection mp)
                        (when result (mc-evolution::%copy-state-value (point::%paper-native result)))
                        (cl-mpm/particle::mp-strain-plastic-vm mp) (* 1.5d0 legacy-j2)
                        (cl-mpm/particle::mp-strain-plastic-vm-inc mp) (* 1.5d0 j2-increment)
                        (cl-mpm/particle::mp-yield-func mp) residual
                        (cl-mpm/particle::mp-plastic-iterations mp) (if result (point:paper-projection-evaluations result) 0)
                        (cl-mpm/particle::mp-p-modulus-0 mp) p0 (cl-mpm/particle::mp-p-modulus mp) p-wave)
                  (cl-mpm/particle::mp-stress-kirchoff mp))))))
      (error (condition)
        (let* ((reason (if (typep condition 'mc-evolution:material-integration-error)
                           (mc-evolution:integration-error-reason condition) (princ-to-string condition)))
               (diagnostic (handler-case (%failure-diagnostic reason trial e nu j committed rotated basis increment rotation)
                             (error () nil))))
          (when diagnostic
            (setf (gethash "materialVariant" diagnostic) (native-material-variant mp)
                  (gethash "historyDecrease" diagnostic)
                  (not (null (search "history decreased" reason :test #'char-equal)))))
          (error 'mc-evolution:material-integration-error :reason reason
                 :details (if (typep condition 'mc-evolution:material-integration-error)
                              (mc-evolution:integration-error-details condition) nil)
                 :diagnostic diagnostic))))))

(defmethod cl-mpm::update-stress-mp :around (mesh (mp particle-wang2017-soil2) dt fbar)
  "Rollback registered kinematics and material on an outer stress-update failure.
Normal calls reuse the scratch matrices; the complete restore allocates only on rejection."
  (let ((state (%outer-trial-state mp)))
    (if state (mc-evolution::%sync-particle-state-in-place! mp state)
        (setf state (mc-evolution::%capture-particle-state mp) (%outer-trial-state mp) state))
    (setf (mc-evolution::particle-state-committed-state state)
          (slot-value mp 'mc-evolution::committed-state))
    (handler-case (call-next-method)
      (error (condition) (mc-evolution:restore-particle mp state) (error condition)))))
