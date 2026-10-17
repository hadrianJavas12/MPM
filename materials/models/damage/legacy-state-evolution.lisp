(in-package :cl-mpm/damage)

(declaim (optimize (debug 0) (safety 0) (speed 3)))


;; (declaim (optimize (debug 3) (safety 3) (speed 0)))


(defmethod cl-mpm/particle::compute-mp-energy-release ((mp cl-mpm/particle::particle-damage))
  (with-accessors ((volume cl-mpm/particle::mp-volume)
                   (stress cl-mpm/particle::mp-undamaged-stress)
                   (damage-inc cl-mpm/particle::mp-damage-increment)
                   (strain cl-mpm/particle::mp-strain))
      mp
    (* 0.5d0 volume damage-inc (cl-mpm/fastmaths:dot stress strain))))

(defmethod set-mp-damage ((mp cl-mpm/particle::particle-damage) d)
  (setf
   (cl-mpm/particle::mp-damage mp) d
   (cl-mpm/particle::mp-damage-n mp) d))

(defmethod cl-mpm/particle::reset-loadstep-mp ((mp cl-mpm/particle::particle-damage))
  (with-accessors ((ybar      cl-mpm/particle::mp-damage-ybar)
                   (ybar-prev cl-mpm/particle::mp-damage-ybar-prev)
                   (y         cl-mpm/particle::mp-damage-y-local)
                   ;; (y-prev    cl-mpm/particle::mp-damage-y-local-prev)
                   (damage    cl-mpm/particle::mp-damage)
                   (damage-n  cl-mpm/particle::mp-damage-n)
                   (stress cl-mpm/particle::mp-undamaged-stress))
      mp
    (setf ybar ybar-prev)
    (setf damage damage-n)
    (cl-mpm/fastmaths::fast-zero stress)
    (cl-mpm/damage::compute-damage mp)
    (call-next-method)))

(declaim
 ;(inline damage-rate-profile)
 (ftype (function (double-float double-float double-float double-float ) (double-float)) damage-rate-profile))
(defun damage-rate-profile (stress damage rate init-stress)
  (declare (double-float stress damage rate init-stress))
  "Function that controls how damage evolves with principal stresses"
  (if (> stress init-stress)
      ;(* (expt (max 0d0 (- stress init-stress)) 0.43d0) rate)
      ;(* (expt (max 0d0 (- stress init-stress)) 0.50d0) rate)
      (* (expt (max 0d0 (/ (- stress init-stress) init-stress)) 2d0) rate)
      ;; (* (expt (max 0d0 (- stress init-stress)) 3d0) rate)
      0d0))

(defun damage-profile (damage damage-crit)
  "Constitive law describing the scalar stress decrease as a function of damage"
  (if (< damage damage-crit)
    (expt (- 1d0 damage) 2d0)
    0d0))

;; (declaim
;;  ;(inline calculate-damage-increment)
;;  (ftype (function (cl-mpm/particle:particle double-float) t) calculate-damage-increment))
(defun calculate-damage-increment (mp dt)
  (let ((damage-increment 0d0))
    (with-accessors (;(stress cl-mpm/particle::mp-stress)
                     (stress cl-mpm/particle::mp-undamaged-stress)
                     ;; (strain cl-mpm/particle::mp-strain)
                     (damage cl-mpm/particle:mp-damage)
                     (strain-rate cl-mpm/particle::mp-velocity-rate)
                     (critical-stress cl-mpm/particle:mp-critical-stress)
                     (init-stress cl-mpm/particle::mp-initiation-stress)
                     (critical-damage cl-mpm/particle::mp-critical-damage)
                     (damage-rate cl-mpm/particle::mp-damage-rate)
                     (pressure cl-mpm/particle::mp-pressure)
                     (ybar cl-mpm/particle::mp-damage-ybar)
                     (def cl-mpm/particle::mp-deformation-gradient)
                     ;(damage-driving-factor cl-mpm/particle::mp-damage-driving-factor)
                     (ybar-tensor cl-mpm/particle::mp-damage-ybar-tensor)
                     (local-length cl-mpm/particle::mp-local-length)
                     (local-length-damaged cl-mpm/particle::mp-local-length-damaged)
                     (local-length-t cl-mpm/particle::mp-true-local-length)
                     ) mp
      (declare (double-float pressure damage))
        (progn
          (progn
                                        ;multiple-value-bind (l v) (cl-mpm/utils::eig (magicl:scale (voight-to-matrix stress) (/ 1d0 (magicl:det def))))

            (when t;(< damage 1d0)
              (let ((cauchy-undamaged (magicl:scale stress (/ 1d0 (* 1d0;(- 1d0 damage)
                                                                     (magicl:det def))))))
                (multiple-value-bind (s_1 s_2 s_3) (principal-stresses-3d cauchy-undamaged)
                  (let* (;;Only allow tensile damage
                         (pressure-effective (* 1d0 damage pressure))
                         ;; (pressure-effective (* 1d0 pressure))
                         (j2 (sqrt (cl-mpm/constitutive::voigt-j2 (cl-mpm/constitutive::deviatoric-voigt
                                                                   cauchy-undamaged))))
                         (p (* 0.3d0 (+ s_1 s_2 s_3)))
                         (s_1 (- s_1 pressure-effective))
                         (s_2 (- s_2 pressure-effective))
                         (s_3 (- s_3 pressure-effective))
                         (s_1 (max 0d0 s_1))
                         (s_2 (max 0d0 s_2))
                         (s_3 (max 0d0 s_3))
                         ;; (vm (* (sqrt (/ 3 4)) (- s_1 s_2)))
                         ;; (vm (sqrt (* 0.5d0
                         ;;              (+ (expt (- s_1 s_2) 2)
                         ;;                 (expt (- s_2 s_3) 2)
                         ;;                 (expt (- s_3 s_1) 2)))))
                         (s_1 (- j2 (* 0.2d0 p)))

                         ;; (s_1 (- s_1 s_3))
                         ;; (s_1 vm)

                                        ;(damage-inv (- 1d0 damage))
                         )
                    (when (> s_1 0d0)
                      (setf damage-increment (* (- 1d0 damage) s_1))
                      ;; (if (< damage 1d0)
                      ;;     (setf damage-increment (/ s_1 (expt (- 1d0 damage) 0.5d0)))
                      ;;     (setf damage-increment s_1)
                      ;;     )
                      )))))
            (when (>= damage 1d0)
              (setf damage-increment 0d0))

            ;;Delocalisation switch
            (setf (cl-mpm/particle::mp-local-damage-increment mp) damage-increment)
            ))))
  (values))

(declaim
 (inline apply-damage)
 (ftype (function (cl-mpm/particle:particle double-float) (values)) apply-damage))
(defun apply-damage (mp dt)
    (with-accessors ((stress cl-mpm/particle:mp-stress)
                     (undamaged-stress cl-mpm/particle::mp-undamaged-stress)
                     (damage cl-mpm/particle:mp-damage)
                     (damage-inc cl-mpm/particle::mp-damage-increment)
                     (ybar cl-mpm/particle::mp-damage-ybar)
                     (init-stress cl-mpm/particle::mp-initiation-stress)
                     (damage-rate cl-mpm/particle::mp-damage-rate)
                     (critical-damage cl-mpm/particle::mp-critical-damage)
                     (pressure cl-mpm/particle::mp-pressure)
                     (def cl-mpm/particle::mp-deformation-gradient)
                     ) mp
      (declare (double-float damage damage-inc critical-damage))
        (progn
          ;;Damage increment holds the delocalised driving factor
          (setf ybar damage-inc)
          ;; (when (< damage 1d0)
          ;; (setf damage-inc (* damage-inc (/ 1d0 (expt (- 1d0 damage) 1d0))));3
          ;;Normal
          ;; (setf damage-inc (* dt (- critical-damage damage) (damage-rate-profile damage-inc damage damage-rate init-stress)))
          (setf damage-inc (* dt (damage-rate-profile-chalk damage-inc damage damage-rate init-stress)))
          ;;Mohr coloumb
          ;; (let ((angle 30d0))
          ;;   (multiple-value-bind (s_1 s_2 s_3) (principal-stresses-3d (magicl:scale stress (/ 1d0 (magicl:det def))))
          ;;     (let ((init-stress (* (+ s_1 s_3) (sin angle))))
          ;;       (setf damage-inc (* dt (damage-rate-profile damage-inc damage damage-rate init-stress))))
          ;;     ))


          (when (>= damage 1d0)
            (setf damage-inc 0d0)
            (setf ybar 0d0))
          (incf (cl-mpm/particle::mp-time-averaged-damage-inc mp) damage-inc)
          (incf (cl-mpm/particle::mp-time-averaged-ybar mp) ybar)
          (incf (cl-mpm/particle::mp-time-averaged-counter mp))
          ;;Transform to log damage
          (incf damage damage-inc)
          ;;Transform to linear damage
          (setf damage (max 0d0 (min 1d0 damage)))
          (when (> damage critical-damage)
            (setf damage 1d0)
            (setf damage-inc 0d0)))
  (values)
  ))

(defun compute-effective-length-stress (stress init-stress direction length)
  (let ((effect 0d0)
        (fts (expt init-stress 2))
        (direction (cl-mpm/fastmaths::norm direction))
        )
    (multiple-value-bind (l v) (cl-mpm/utils::eig (cl-mpm/utils::voight-to-matrix stress))
      (loop for val in l
            for i from 0
            do (when (> (abs val) init-stress)
                 (setf effect (+ effect
                                 (/ (*
                                     (expt (max 0d0 val) 2)
                                     (abs
                                      (expt
                                       (cl-mpm/fastmaths::dot
                                        (cl-mpm/utils::matrix-column v i)
                                        ;; (cl-mpm/utils::matrix-row v i)
                                        direction)
                                       1)))
                                    fts))))))
    (/ length (sqrt (max 1d0 effect)))))
(defun compute-effective-length-stress-precomputed (mp init-stress direction length)
  (let ((effect 0d0)
        (fts (expt init-stress 2))
        (direction (cl-mpm/fastmaths::norm direction))
        (l (cl-mpm/particle::mp-stress-eigenvalues mp))
        (v (cl-mpm/particle::mp-stress-eigenvectors mp)))
    ;; (multiple-value-bind (l v) (cl-mpm/utils::eig (cl-mpm/utils::voight-to-matrix stress)))
    (loop for val in l
          for i from 0
          do (when (> (abs val) init-stress)
               (setf effect (+ effect
                               (/ (*
                                   (expt (max 0d0 val) 2)
                                   ;; (expt val 2)
                                   (abs
                                    (expt
                                     (cl-mpm/fastmaths::dot
                                      (cl-mpm/utils::matrix-column v i)
                                      ;; (cl-mpm/utils::matrix-row v i)
                                      direction)
                                     1)))
                                  fts)))))
    (/ length (sqrt (max 1d0 effect)))))

(declaim (notinline length-localisation))
(defun length-localisation (local-length local-length-damaged damage)
  ;; (+ (* local-length (- 1d0 damage)) (* local-length-damaged damage))
  (* local-length (max (sqrt (- 1d0 damage)) 1d-10))
  ;; local-length
  ;; (* local-length (max (/ (- (exp (- damage)) (exp -1d0))
  ;;                         (- 1d0 (exp -1d0))) 1d-10))
  )







(defstruct damage-model
  name)

(defstruct (damage-model-creep (:include damage-model))
           (initiation-stress
            0d0
            :type DOUBLE-FLOAT)
           (damage-rate
            0d0
            :type DOUBLE-FLOAT)
           )

(defstruct (damage-model-rankine (:include damage-model))
  (initiation-stress
   0d0
   :type DOUBLE-FLOAT)
  (failure-stress
   0d0
   :type DOUBLE-FLOAT)
  (y-history
   0d0
   :type DOUBLE-FLOAT)
  )

(defstruct (damage-model-chalk (:include damage-model))
  (coheasion
   0d0
   :type DOUBLE-FLOAT)
  (friction-angle
   0d0
   :type DOUBLE-FLOAT)
  (damage-rate
   0d0
   :type DOUBLE-FLOAT)
  )
(defmethod damage-model-calculate-y ((mp cl-mpm/particle::particle-damage) dt)
  (let ((damage-increment 0d0))
    (with-accessors ((stress cl-mpm/particle::mp-undamaged-stress)
                     (damage cl-mpm/particle:mp-damage)
                     (init-stress cl-mpm/particle::mp-initiation-stress)
                     (critical-damage cl-mpm/particle::mp-critical-damage)
                     (damage-rate cl-mpm/particle::mp-damage-rate)
                     (pressure cl-mpm/particle::mp-pressure)
                     (ybar cl-mpm/particle::mp-damage-ybar)
                     (def cl-mpm/particle::mp-deformation-gradient)
                     ) mp
      (declare (double-float pressure damage))
        (progn
          (when (< damage 1d0)
            (let ((cauchy-undamaged (cl-mpm/fastmaths:fast-scale-voigt stress (/ 1d0 (cl-mpm/fastmaths:det-3x3 def)))))
              (multiple-value-bind (s_1 s_2 s_3) (principal-stresses-3d cauchy-undamaged)
                (let* (;;Only allow tensile damage
                       (pressure-effective (* 1d0 damage pressure))
                       ;; (pressure-effective (* 1d0 pressure))
                       (j2 (sqrt (cl-mpm/constitutive::voigt-j2 (cl-mpm/constitutive::deviatoric-voigt
                                                                 cauchy-undamaged))))
                       (p (* 0.3d0 (+ s_1 s_2 s_3)))
                       (s_1 (- s_1 pressure-effective))
                       (s_2 (- s_2 pressure-effective))
                       (s_3 (- s_3 pressure-effective))
                       (s_1 (max 0d0 s_1))
                       (s_2 (max 0d0 s_2))
                       (s_3 (max 0d0 s_3))
                       ;; (s_1 (- j2 (* 0.2d0 p)))
                       )
                  (when (> s_1 0d0)
                    (setf damage-increment s_1)
                    )))))
          (when (>= damage 1d0)
            ;; (setf damage-increment 0d0)
            )
          ;;Delocalisation switch
          (setf (cl-mpm/particle::mp-local-damage-increment mp) damage-increment)
          ))))
(defmethod compute-damage ((mp cl-mpm/particle::particle-damage)))

(defmethod update-damage ((mp cl-mpm/particle::particle-damage) dt)
    (with-accessors ((stress cl-mpm/particle:mp-stress)
                     (undamaged-stress cl-mpm/particle::mp-undamaged-stress)
                     (damage cl-mpm/particle:mp-damage)
                     (damage-inc cl-mpm/particle::mp-damage-increment)
                     (ybar cl-mpm/particle::mp-damage-ybar)
                     (init-stress cl-mpm/particle::mp-initiation-stress)
                     (damage-rate cl-mpm/particle::mp-damage-rate)
                     (critical-damage cl-mpm/particle::mp-critical-damage)
                     (pressure cl-mpm/particle::mp-pressure)
                     (def cl-mpm/particle::mp-deformation-gradient)
                     ) mp
      (declare (double-float damage damage-inc critical-damage))
        (progn
          ;;Damage increment holds the delocalised driving factor
          (setf ybar damage-inc)
          ;; (setf damage-inc (* dt (- critical-damage damage) (damage-rate-profile damage-inc damage damage-rate init-stress)))
          (setf damage-inc (* dt (damage-rate-profile damage-inc damage damage-rate init-stress)))
          (when (>= damage 1d0)
            ;; (setf damage-inc 0d0)
            (setf ybar 0d0))
          (incf (cl-mpm/particle::mp-time-averaged-damage-inc mp) damage-inc)
          (incf (cl-mpm/particle::mp-time-averaged-ybar mp) ybar)
          (incf (cl-mpm/particle::mp-time-averaged-counter mp))
          (incf damage damage-inc)
          (setf damage (max 0d0 (min 1d0 damage)))
          (when (> damage critical-damage)
            (setf damage 1d0)
            (setf damage-inc 0d0)))
  (values)
  ))
