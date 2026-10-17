;;;; Native Hencky-strain / Kirchhoff-stress constitutive method for particle-mc-evolution.
(in-package :cl-mpm/models/mc-evolution)

(defun %adapter-checked-matrix (matrix rows columns name)
  (unless (and (typep matrix 'magicl:matrix/double-float)
               (= (cl-mpm/utils:nrows matrix) rows)
               (= (cl-mpm/utils:ncols matrix) columns)
               (every #'finite-real-p (cl-mpm/utils:fast-storage matrix)))
    (integration-fail "Invalid native constitutive matrix" name))
  matrix)

(defun %adapter-principal-to-tensor (principal basis)
  "Q diag(PRINCIPAL) Q^T with eigenvectors in columns of Q."
  (let ((tensor (cl-mpm/utils:matrix-zeros)))
    (dotimes (row 3 tensor)
      (dotimes (column 3)
        (setf (magicl:tref tensor row column)
              (loop for axis below 3 sum
                (* (aref principal axis)
                   (magicl:tref basis row axis)
                   (magicl:tref basis column axis))))))))

(defun %adapter-max-plane-value (tau law kappa j)
  (multiple-value-bind (c phi psi) (law-values law kappa)
    (declare (ignore psi))
    (let ((sine (sin phi))
          (offset (* 2d0 c (cos phi)
                     (if (eq (evolution-law-stress-measure law) :cauchy) j 1d0))))
      (loop for i below 3 maximize
        (loop for k below 3 unless (= i k) maximize
          (- (* (+ 1d0 sine) (aref tau i))
             (* (- 1d0 sine) (aref tau k)) offset))))))

(defun particle-phi-deg (mp)
  (* (/ 180d0 pi) (particle-phi mp)))

(defun particle-softened-indicator (mp)
  "1.0d0 when VARIANT is :HS and KAPPA > PEAK-KAPPA, else 0.0d0."
  (let ((law (particle-evolution-law mp)))
    (if (and (eq (evolution-law-variant law) :hs)
             (> (particle-kappa mp) (evolution-law-peak-kappa law)))
        1d0
        0d0)))

(defun particle-yield-residual-kirchhoff (mp)
  "Independently evaluate signed 6-plane MC yield residual in Pa from current Cauchy stress and J."
  (let* ((stress (cl-mpm/particle:mp-stress mp))
         (j (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp)))
         (law (particle-evolution-law mp))
         (kappa (particle-kappa mp)))
    (unless (and (every #'finite-real-p (cl-mpm/utils:fast-storage stress))
                 (finite-real-p j) (> j 0d0))
      (integration-fail "Nonfinite Cauchy stress or det(F) in MC evolution diagnostic"))
    (let ((tau (cl-mpm/utils:voigt-copy stress)))
      (cl-mpm/fastmaths:fast-scale! tau j)
      (multiple-value-bind (principal-list)
          (cl-mpm/utils:eig (cl-mpm/utils:voight-to-matrix tau))
        (let ((principal (coerce principal-list 'vector)))
          (%adapter-max-plane-value principal law kappa j))))))

(defmethod cl-mpm/particle:constitutive-model
    ((mp particle-mc-evolution) strain dt)
  "Return Kirchhoff stress from engineering-Voigt trial elastic Hencky strain.
All projection and tensor reconstruction happens on owned temporary values.
The current material point is changed only after this complete trial succeeds.
The core stress update remains responsible for dividing returned tau by J."
  (declare (ignore dt))
  (%adapter-checked-matrix strain 6 1 "engineering trial strain")
  (%adapter-checked-matrix (cl-mpm/particle:mp-deformation-gradient mp) 3 3 "F")
  (let* ((e (cl-mpm/particle::mp-E mp))
         (nu (cl-mpm/particle::mp-nu mp))
         (j (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp)))
         (law (particle-evolution-law mp))
         (kappa-old (particle-kappa-committed mp)))
    (unless (and (finite-real-p e) (> e 0d0) (finite-real-p nu) (< -1d0 nu 0.5d0)
                 (finite-real-p j) (> j 0d0))
      (integration-fail "Invalid elasticity or deformation Jacobian" e nu j))
    ;; Explicit strain conversion halves engineering shears. Stress later uses
    ;; MATRIX-TO-VOIGHT, which preserves tensor shears, not MATRIX-TO-VOIGT.
    (multiple-value-bind (principal-list basis)
        (cl-mpm/utils:eig (cl-mpm/utils:voigt-to-matrix strain))
      (%adapter-checked-matrix basis 3 3 "trial eigenbasis")
      (let* ((principal (coerce principal-list 'vector))
             (g (/ e (* 2d0 (+ 1d0 nu))))
             (lambda-elastic (/ (* e nu) (* (+ 1d0 nu) (- 1d0 (* 2d0 nu)))))
             (trace (reduce #'+ principal))
             (trial-tau (map 'vector (lambda (eps) (+ (* 2d0 g eps)
                                                       (* lambda-elastic trace)))
                             principal))
             (result (when (cl-mpm/particle::mp-enable-plasticity mp)
                       (project-principal trial-tau e nu j law kappa-old)))
             (tau (if result (projection-tau result) trial-tau))
             (plastic (if result (projection-plastic-increment result)
                          (vector 0d0 0d0 0d0)))
             (kappa (if result (projection-kappa result) kappa-old))
             (elastic (map 'vector #'- principal plastic))
             (new-strain (cl-mpm/utils:matrix-to-voigt
                          (%adapter-principal-to-tensor elastic basis)))
             (new-tau (cl-mpm/utils:matrix-to-voight
                       (%adapter-principal-to-tensor tau basis)))
             (new-plastic (cl-mpm/utils:matrix-to-voigt
                           (%adapter-principal-to-tensor plastic basis)))
             (new-projection (%copy-state-value result))
             (increment (- kappa kappa-old))
             (native-total (* 1.5d0 kappa))
             (native-increment (* 1.5d0 increment))
             (plastic-volume (+ (particle-plastic-volume-committed mp)
                                (reduce #'+ plastic)))
             (plastic-work (+ (particle-plastic-work-committed mp)
                              (if result (/ (projection-work result) j) 0d0)))
             (p-wave-0 (/ (* e (- 1d0 nu))
                          (* (+ 1d0 nu) (- 1d0 (* 2d0 nu)))))
             (p-wave (* (/ p-wave-0 j) (exp (- (reduce #'min elastic)))))
             (residual (if result (projection-max-residual result)
                           (%adapter-max-plane-value tau law kappa j))))
        (unless (and (= (length principal) 3) (every #'finite-real-p principal)
                     (every #'finite-real-p tau) (every #'finite-real-p plastic)
                     (finite-real-p kappa) (>= increment 0d0)
                     (finite-real-p native-total) (finite-real-p native-increment)
                     (finite-real-p plastic-volume) (finite-real-p plastic-work)
                     (finite-real-p residual)
                     (finite-real-p p-wave) (> p-wave 0d0))
          (integration-fail "Nonfinite or inconsistent material projection"))
        (%adapter-checked-matrix new-strain 6 1 "returned elastic strain")
        (%adapter-checked-matrix new-tau 6 1 "returned Kirchhoff stress")
        (%adapter-checked-matrix new-plastic 6 1 "plastic strain increment")
        (%adapter-checked-matrix (cl-mpm/particle:mp-strain mp) 6 1 "target elastic strain")
        (%adapter-checked-matrix (cl-mpm/particle::mp-stress-kirchoff mp) 6 1 "target Kirchhoff stress")
        (%adapter-checked-matrix (cl-mpm/particle::mp-strain-plastic mp) 6 1 "target plastic increment")
        (%adapter-checked-matrix (particle-plastic-increment mp) 6 1 "target custom plastic increment")
        (multiple-value-bind (c phi psi) (law-values law kappa)
          ;; Preserve references held by the engine's outer stress-update method.
          (cl-mpm/utils:voigt-copy-into new-strain (cl-mpm/particle:mp-strain mp))
          (cl-mpm/utils:voigt-copy-into new-tau (cl-mpm/particle::mp-stress-kirchoff mp))
          (cl-mpm/utils:voigt-copy-into new-plastic (cl-mpm/particle::mp-strain-plastic mp))
          (cl-mpm/utils:voigt-copy-into new-plastic (particle-plastic-increment mp))
          (setf (particle-kappa mp) kappa
                (particle-cohesion mp) c (particle-phi mp) phi (particle-psi mp) psi
                (particle-plastic-volume mp) plastic-volume
                (particle-plastic-work mp) plastic-work
                (particle-last-projection mp) new-projection
                (cl-mpm/particle::mp-strain-plastic-vm mp) native-total
                (cl-mpm/particle::mp-strain-plastic-vm-inc mp) native-increment
                (cl-mpm/particle::mp-yield-func mp) residual
                (cl-mpm/particle::mp-plastic-iterations mp)
                (if result (projection-iterations result) 0)
                (cl-mpm/particle::mp-p-modulus-0 mp) p-wave-0
                (cl-mpm/particle::mp-p-modulus mp) p-wave)
          (cl-mpm/particle::mp-stress-kirchoff mp))))))
