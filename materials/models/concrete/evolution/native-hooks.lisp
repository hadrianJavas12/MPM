(in-package :cl-mpm/damage)

(declaim (optimize (debug 0) (safety 0) (speed 3)))




(defmethod damage-model-calculate-y ((mp cl-mpm/particle::particle-concrete) dt)
  (let ((damage-increment 0d0))
    (with-accessors ((stress cl-mpm/particle::mp-undamaged-stress)
                     (damage cl-mpm/particle:mp-damage)
                     (init-stress cl-mpm/particle::mp-initiation-stress)
                     (critical-damage cl-mpm/particle::mp-critical-damage)
                     (damage-rate cl-mpm/particle::mp-damage-rate)
                     (pressure cl-mpm/particle::mp-pressure)
                     (ybar cl-mpm/particle::mp-damage-ybar)
                     (def cl-mpm/particle::mp-deformation-gradient)
                     (angle cl-mpm/particle::mp-friction-angle)
                     (c cl-mpm/particle::mp-coheasion)
                     ) mp
      (declare (double-float pressure damage))
        (progn
          (when (< damage 1d0)
            (let ((cauchy-undamaged (magicl:scale stress (/ 1d0 (magicl:det def)))))
              (multiple-value-bind (s_1 s_2 s_3) (principal-stresses-3d cauchy-undamaged)
                (let* (;(s_1 (max 0d0 s_1))
                       )
                  (when (> s_1 0d0)
                    ;; (setf damage-increment s_1)
                    (setf damage-increment (sqrt
                                            (+ (expt s_1 2)
                                               (expt s_2 2)
                                               (expt s_3 2))))
                    )))))
          (when (>= damage 1d0)
            (setf damage-increment 0d0))
          ;;Delocalisation switch
          (setf (cl-mpm/particle::mp-local-damage-increment mp) damage-increment)
          (setf (cl-mpm/particle::mp-damage-y-local mp) damage-increment)
          ))))


(defmethod update-damage ((mp cl-mpm/particle::particle-concrete) dt)
    (with-accessors ((stress cl-mpm/particle:mp-stress)
                     (undamaged-stress cl-mpm/particle::mp-undamaged-stress)
                     (damage cl-mpm/particle:mp-damage)
                     (E cl-mpm/particle::mp-e)
                     (Gf cl-mpm/particle::mp-Gf)
                     (damage-inc cl-mpm/particle::mp-damage-increment)
                     (ybar cl-mpm/particle::mp-damage-ybar)
                     (init-stress cl-mpm/particle::mp-initiation-stress)
                     (damage-rate cl-mpm/particle::mp-damage-rate)
                     (critical-damage cl-mpm/particle::mp-critical-damage)
                     (pressure cl-mpm/particle::mp-pressure)
                     (def cl-mpm/particle::mp-deformation-gradient)
                     ;; (length cl-mpm/particle::mp-true-local-length)
                     (length cl-mpm/particle::mp-local-length)
                     (k cl-mpm/particle::mp-history-stress)
                     ) mp
      (declare (double-float damage damage-inc critical-damage))
        (progn
          ;;Damage increment holds the delocalised driving factor
          (setf ybar damage-inc)
          (setf k (max k ybar))
          (let ((new-damage (max damage
                                 (brittle-concrete-d k E Gf length init-stress)
                                 ;; (brittle-concrete-linear-d k E Gf length init-stress)
                                 )))
            (setf damage-inc (- new-damage damage)))
          ;; (setf damage (max damage (brittle-chalk-d k E Gf length init-stress))
          ;;       damage-inc 0d0)
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
