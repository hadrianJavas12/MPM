(in-package :cl-mpm/damage)
(declaim (optimize (debug 0) (safety 0) (speed 3)))

(defmethod cl-mpm::reset-loadstep ((sim mpm-sim-damage))
  (call-next-method)
  ;; (calculate-damage sim 1d0)
  )

(defmethod cl-mpm/particle::post-damage-step ((mp cl-mpm/particle::particle) dt))
(defmethod cl-mpm/particle:post-stress-step (mesh (mp cl-mpm/particle:particle-damage) dt)
  )
(defun find-nodal-local-length (mesh mp)
  (let ((nodal-damage 0d0))
    (cl-mpm::iterate-over-neighbours
     mesh mp
     (lambda (node svp grads fsvp fgrads)
       (with-accessors ((node-damage cl-mpm/mesh::node-damage)
                        (node-svp cl-mpm/mesh::node-svp-sum))
           node
         (incf nodal-damage (* node-damage svp)))))
    (with-accessors ((local-length cl-mpm/particle::mp-local-length)
                     (local-length-damaged cl-mpm/particle::mp-local-length-damaged)
                     (local-length-t cl-mpm/particle::mp-true-local-length)
                     ) mp
      ;;Damage length control
      (setf local-length-t (length-localisation local-length local-length-damaged nodal-damage))
      ;; (setf local-length-t local-length)
      )))
(defun find-intergral-local-length (mesh mp)
  (with-accessors ((tll cl-mpm/particle::mp-true-local-length)
                   (ll cl-mpm/particle::mp-local-length)
                   (lld cl-mpm/particle::mp-local-length-damaged))
      mp
    (setf tll
          (length-localisation
           ll
           lld
           (calculate-average-damage mesh mp ll)))))




(defmethod calculate-damage ((sim mpm-sim-damage) dt)
  (with-accessors ((mps cl-mpm:sim-mps)
                   (mesh cl-mpm:sim-mesh)
                   (enable-damage cl-mpm::sim-enable-damage)
                   (delocal-counter sim-damage-delocal-counter)
                   (delocal-counter-max sim-damage-delocal-counter-max)
                   (non-local-damage cl-mpm::sim-nonlocal-damage))
      sim
    (when enable-damage
      (when non-local-damage
        ;;When delocal counter max is -1, we want to update never -> 0 is always
        (unless (= delocal-counter-max -1)
          (when (<= delocal-counter 0)
            ;;Ensure they have a home
            ;; (create-delocalisation-list mesh mps)
            (update-delocalisation-list mesh mps)
            (setf delocal-counter delocal-counter-max)))
        ;;Worst case we want dont want our delocal counter to exceed the max incase we get adjusted
        (setf delocal-counter (min (- delocal-counter 1) delocal-counter-max)))
      (cl-mpm:iterate-over-mps
       mps
       (lambda (mp)
         (when (typep mp 'cl-mpm/particle:particle-damage)
           (damage-model-calculate-y mp dt))))

      ;; (g2p-damage sim)
      (if non-local-damage
          (progn
            (when (sim-enable-length-localisation sim)
              (update-localisation-lengths sim))
            (cond
              ((cl-mpm/damage::sim-enable-ekl sim)
               (delocalise-damage-ekl sim))
              ((cl-mpm/damage::sim-enable-stress-based-length sim)
               (delocalise-damage-stress sim))
              (t
               (delocalise-damage sim))))
          (localise-damage mesh mps dt))
      (cl-mpm:iterate-over-mps
       mps
       (lambda (mp)
         (when (typep mp 'cl-mpm/particle:particle-damage)
           (update-damage mp dt)))))

    (cl-mpm:iterate-over-mps
     mps
     (lambda (mp)
       (when (typep mp 'cl-mpm/particle:particle-damage)
         (cl-mpm/particle::post-damage-step mp dt))))
      ;; (let* ((crit 1d-3)
      ;;        (dconv crit)
      ;;        (iterative-damage t))
      ;;   (if t;enable-damage
      ;;       (if iterative-damage
      ;;           (loop for d from 0 to 10
      ;;                 while (>= dconv crit)
      ;;                 do
      ;;                    (progn
      ;;                      (damage-update)
      ;;                      (setf dconv (compute-damage-delta sim))
      ;;                      ;; (format t "Damage inc ~D - ~E~%" d dconv)
      ;;                      (when (> d 1)
      ;;                        (format t "Damage inc ~D - ~E~%" d dconv))))
      ;;           (damage-update))
      ;;       (cl-mpm:iterate-over-mps
      ;;        mps
      ;;        (lambda (mp)
      ;;          (when (typep mp 'cl-mpm/particle:particle-damage)
      ;;            (cl-mpm/particle::post-damage-step mp dt))))
      ;;       ))
      ;))
    ))

(defun create-delocalisation-list (mesh mps)
  (with-accessors ((nodes cl-mpm/mesh:mesh-nodes))
        mesh
    (cl-mpm:iterate-over-nodes
     mesh
     (lambda (node)
       (setf (fill-pointer (cl-mpm/mesh::node-local-list node)) 0)))
    (cl-mpm:iterate-over-mps
     mps
      (lambda (mp)
        (when (typep mp 'cl-mpm/particle:particle-damage)
            (let ((node-id (cl-mpm/mesh:position-to-index mesh (cl-mpm/particle:mp-position mp))))
              (when (cl-mpm/mesh:in-bounds mesh node-id)
                (let ((node (cl-mpm/mesh:get-node mesh node-id)))
                (sb-thread:with-mutex ((cl-mpm/mesh:node-lock node))
                  (vector-push-extend mp (cl-mpm/mesh::node-local-list node)))))))))
    ;;Smart in thought but actually super dumb
    (cl-mpm:iterate-over-nodes
     mesh
     (lambda (node)
       (when (= 0 (length (cl-mpm/mesh::node-local-list node)))
         (adjust-array (cl-mpm/mesh::node-local-list node) 0 :fill-pointer 0))))
    ))

(defun local-list-add-particle (mesh mp)
  "A function for putting an MP into the nodal MP lookup table"
  (let ((node-id (cl-mpm/mesh:position-to-index mesh (cl-mpm/particle:mp-position mp))))
    (if (cl-mpm/mesh:in-bounds mesh node-id)
      (let ((node (cl-mpm/mesh:get-node mesh node-id)))
        (setf (cl-mpm/particle::mp-damage-position mp)
              (cl-mpm/utils::vector-copy (cl-mpm/particle:mp-position mp)))
        (sb-thread:with-mutex ((cl-mpm/mesh:node-lock node))
          (vector-push-extend mp (cl-mpm/mesh::node-local-list node))))
      (error "Could not add damage MP to local list as it is out of bounds"))))

(defun local-list-remove-particle (mesh mp)
  "A function for removing an MP into the nodal MP lookup table"
  (flet ((remove-mp-ll (node)
           (with-accessors ((ll cl-mpm/mesh::node-local-list)
                            (lock cl-mpm/mesh:node-lock)
                            ) node
             (if (position mp ll)
                 (progn
                   (sb-thread:with-mutex (lock)
                     (setf ll (delete mp ll)))
                   t)
                 nil))))
    ;;Check if the particle has been inserted by checking nil equality of damage position
    (if (cl-mpm/particle::mp-damage-position mp)
        (let ((node-id (cl-mpm/mesh:position-to-index mesh (cl-mpm/particle::mp-damage-position mp))))
          (if (cl-mpm/mesh:in-bounds mesh node-id)
            (let ((node (cl-mpm/mesh:get-node mesh node-id)))
              (when (not (remove-mp-ll node))
                  (cl-mpm::iterate-over-nodes
                   mesh
                   (lambda (node)
                     (remove-mp-ll node))))
              t)
            nil))
        nil)))

(declaim (notinline update-delocalisation-list))
(defgeneric update-delocalisation-list (mesh mps))
(defmethod update-delocalisation-list (mesh mps)
  (with-accessors ((nodes cl-mpm/mesh:mesh-nodes)
                   (h cl-mpm/mesh:mesh-resolution))
        mesh
    (cl-mpm:iterate-over-mps
     mps
     (lambda (mp)
       (when (typep mp 'cl-mpm/particle:particle-damage)
         (if (eq (cl-mpm/particle::mp-damage-position mp) nil)
             ;;New particle - needs to be added to the mesh
             (local-list-add-particle mesh mp)
             ;; Already inserted mesh - sanity check to see if it should be recalced
             (let* ((delta (cl-mpm/fastmaths::diff-norm (cl-mpm/particle:mp-position mp)
                                                        (cl-mpm/particle::mp-damage-position mp))))
               (declare (double-float delta h))
               (when (> delta (/ h 4d0))
                 (when (not (equal
                             (cl-mpm/mesh:position-to-index mesh (cl-mpm/particle:mp-position mp))
                             (cl-mpm/mesh:position-to-index mesh (cl-mpm/particle::mp-damage-position mp))))
                   (local-list-remove-particle mesh mp)
                   (local-list-add-particle mesh mp))))))))
    ;;Smart in thought, presumably creates lots of garbage
    ;; (cl-mpm::iterate-over-nodes
    ;;  mesh
    ;;  (lambda (node)
    ;;    (when (= 0 (length (cl-mpm/mesh::node-local-list node)))
    ;;      (adjust-array (cl-mpm/mesh::node-local-list node) 0 :fill-pointer 0))))
    ))





(declaim
 (inline weight-func)
 (ftype (function (double-float
                   double-float
                   ) double-float)
        weight-func
        ))
(defun weight-func (dist-squared length)
  (if (< dist-squared (* length length))
      (the double-float (expt (- 1d0 (expt (/ dist-squared (* length length)) 2)) 2))
      ;; (the double-float (exp (the double-float (* 1d0 (/ (- dist-squared) (* 2d0 length length))))))
      0d0)
  )
;; (defun weight-func (dist-squared length)
;;   ;(values (the double-float (exp (the double-float (- (* (/ 4d0 (* length length)) dist-squared))))))
;;   (if (< dist-squared (* 4d0 length length))
;;       (values (the double-float (exp (the double-float (* 1d0 (/ (- dist-squared) (* 2d0 length length)))))))
;;       0d0)
;;   ;; (values (the double-float (exp (the double-float (* 4d0 (/ (- dist-squared) (* 1.00d0 length length)))))))
;;   ;; (if (= dist-squared 0d0)
;;   ;;   1d0
;;   ;;   0d0)
;;   )
(declaim
 (inline weight-func-mps)
 (ftype (function (cl-mpm/mesh::mesh
                   cl-mpm/particle:particle
                   cl-mpm/particle:particle
                   double-float
                   ) double-float)
        weight-func-mps
        ))
(defun weight-func-mps (mesh mp-a mp-b length)
  (weight-func (diff-squared mp-a mp-b) length)
  )

(defun weight-func-pos (mesh pos-a pos-b length)
  (weight-func (the double-float (cl-mpm/fastmaths::dot-vector pos-a pos-b)) length))

(defun patch-in-bounds-2d (mesh pos bound)
  (destructuring-bind (x y z) pos
    (declare (fixnum x y z bound))
    (and
     (cl-mpm/mesh:in-bounds mesh (list (+ x bound) (+ y bound) z))
     (cl-mpm/mesh:in-bounds mesh (list (- x bound) (- y bound) z)))))
(defun patch-in-bounds-3d (mesh pos bound)
  (destructuring-bind (x y z) pos
    (declare (fixnum x y z bound))
    (and
     (cl-mpm/mesh:in-bounds mesh (list (+ x bound) (+ y bound) (+ z bound)))
     (cl-mpm/mesh:in-bounds mesh (list (- x bound) (- y bound) (- z bound))))))

(defun iterate-over-damage-bounds (mesh pos length func)
  "Function for calling a function over every node that could contain mps within 2*length
Calls the function with the mesh mp and node"
  (if (= (cl-mpm/mesh:mesh-nd mesh) 2)
      (iterate-over-damage-bounds-2d mesh pos length func)
      (iterate-over-damage-bounds-3d mesh pos length func)))

(defun iterate-over-damage-bounds-2d (mesh pos length func)
  (declare (optimize (speed 3)))
  (declare (function func)
           (double-float length))
  (let* ((node-id (cl-mpm/mesh:position-to-index mesh pos))
         (node-reach (the fixnum (ceiling (* length 1d0) (the double-float (cl-mpm/mesh:mesh-resolution mesh)))))
         (potentially-in-bounds (patch-in-bounds-2d mesh node-id node-reach)))
    (declare (dynamic-extent node-id))
    (loop for dx fixnum from (- node-reach) to node-reach
          do (loop for dy fixnum from (- node-reach) to node-reach
                   do
                      (progn
                        (destructuring-bind (x y z) node-id
                          (declare (fixnum dx dy x y)
                                   (ignore z))
                          (let ((idx
                                (list (+ x dx) (+ y dy) 0)))
                            (declare (dynamic-extent idx))
                            (when (or
                                   potentially-in-bounds
                                   (cl-mpm/mesh:in-bounds mesh idx))
                              (let ((node (cl-mpm/mesh:get-node mesh idx)))
                                (funcall func node))))))))))

(defun iterate-over-damage-bounds-3d (mesh pos length func)
  (let ((node-id (cl-mpm/mesh:position-to-index mesh pos))
        (node-reach (the fixnum (+ 0 (truncate (ceiling (* length 1d0)
                                                        (the double-float (cl-mpm/mesh:mesh-resolution mesh))))))))
    (declare (dynamic-extent node-id))
    (destructuring-bind (ix iy iz) node-id
      (declare (fixnum ix iy iz))
      (loop for dx fixnum from (- node-reach) to node-reach
            do
               (when (cl-mpm/mesh::in-bounds-1d mesh (+ ix dx) 0)
                 (loop for dy fixnum from (- node-reach) to node-reach
                       do
                          (when (cl-mpm/mesh::in-bounds-1d mesh (+ iy dy) 1)
                            (loop for dz fixnum from (- node-reach) to node-reach
                                  do
                                     (when (cl-mpm/mesh::in-bounds-1d mesh (+ iz dz) 2)
                                       (let ((idx (list (+ ix dx)
                                                        (+ iy dy)
                                                        (+ iz dz))))
                                         (declare (dynamic-extent idx))
                                         (let ((node (cl-mpm/mesh:get-node mesh idx)))
                                           (funcall func node))))))))))))

(defparameter *enable-reflect-x* nil)
(defparameter *enable-reflect-y* nil)
(defparameter *enable-reflect-z* nil)

(defun iterate-over-neighour-mps (mesh mp length func)
  "Search for mps in a patch sized 2*length, then return the "
  (declare (double-float length)
           (function func))
  (let ((len-squared (* length length)))
    (declare (double-float length len-squared))
    (iterate-over-damage-bounds
     mesh
     (cl-mpm/particle::mp-position mp)
     length
     (lambda (node)
       (loop for mp-other across (cl-mpm/mesh::node-local-list node)
                                        ;(the (vector cl-mpm/particle::particle *))
             do
                (with-accessors ((d cl-mpm/particle::mp-damage)
                                 (m cl-mpm/particle:mp-volume)
                                 (ll cl-mpm/particle::mp-true-local-length)
                                 (p cl-mpm/particle:mp-position))
                    mp-other
                  (let ((distance (diff-squared mp mp-other)))
                    (when (< distance len-squared)
                      (funcall func mesh mp mp-other (sqrt distance)))))))))
  (values))

(defun iterate-over-point-neighbour-mps (mesh point length func)
  "Search for mps in a patch sized 2*length, then return the "
  (declare (double-float length)
           (function func))
  (let ((len-squared (* length length)))
    (declare (double-float length len-squared))
    (iterate-over-damage-bounds
     mesh
     point
     length
     (lambda (node)
       (loop for mp-other across (cl-mpm/mesh::node-local-list node)
             do
                (with-accessors ((d cl-mpm/particle::mp-damage)
                                 (m cl-mpm/particle:mp-volume)
                                 (ll cl-mpm/particle::mp-true-local-length)
                                 (p cl-mpm/particle:mp-position))
                    mp-other
                  (let ((distance (cl-mpm/fastmaths::diff-norm
                                   point
                                   (cl-mpm/particle::mp-position mp-other))))
                    (when (< distance len-squared)
                      (funcall func mesh mp-other (sqrt distance)))))))))
  (values))

(defun calculate-average-damage (mesh mp length)
  (let ((damage-average 0d0)
        (volume-average 0d0))
    (declare (double-float damage-average))
    (iterate-over-neighour-mps
     mesh mp length
     (lambda (mesh mp mp-other dist)
       (with-accessors ((d cl-mpm/particle::mp-damage)
                        (m cl-mpm/particle:mp-volume)
                        (p cl-mpm/particle:mp-position))
           mp-other
         (declare (double-float d m length))
         (when t
           (let ((weight (weight-func-mps mesh mp mp-other length)))
             (declare (double-float weight m d damage-average volume-average))
             (incf volume-average (* weight m))
             (incf damage-average (* d weight m)))))))
    (when (> volume-average 0d0)
      (setf damage-average (/ damage-average volume-average)))
    damage-average))

(declaim
 (notinline calculate-delocalised-damage)
 (ftype (function (cl-mpm/mesh::mesh
                   cl-mpm/particle:particle-damage
                   double-float
                   ) double-float)
        calculate-delocalised-damage
        ))
(defun calculate-delocalised-damage (mesh mp length)
  (let ((damage-inc 0d0)
        (mass-total 0d0))
    (declare (double-float damage-inc mass-total))
    (iterate-over-neighour-mps
     mesh mp length
     (lambda (mesh mp mp-other dist)
       (with-accessors ((d cl-mpm/particle::mp-damage)
                        (m cl-mpm/particle:mp-volume)
                        (ll cl-mpm/particle::mp-true-local-length)
                        (p cl-mpm/particle:mp-position))
           mp-other
         (when t;(< (the double-float d) 1d0)
           (let (
                 ;;Nodally averaged local funcj
                 ;; (weight (weight-func-mps mesh mp mp-other (* 0.5d0 (+ length ll))))
                 ;; (weight (weight-func-mps mesh mp mp-other (sqrt (* length ll))))
                 ;;
                 (weight
                   (weight-func-mps mesh mp mp-other (sqrt (* length ll)))
                   ;; (weight-func-mps mesh mp mp-other length)
                   ;; (weight-func-mps mesh mp mp-other (* 0.5d0 (+ length ll)))
                   ;; (weight-func-mps mesh mp mp-other ll)
                   ;; (weight-func-mps mesh mp mp-other ll)
                   ;; (weight-func-mps-damaged mesh mp mp-other
                   ;;                          (cl-mpm/particle::mp-local-length mp)
                   ;;                          )
                   ))
             (declare (double-float weight m d mass-total damage-inc))
             (incf mass-total (* weight m))
             (incf damage-inc
                   (* (the double-float (cl-mpm/particle::mp-damage-y-local mp-other))
                      weight m)))
           (macrolet ((reflect-axis (axis enable)
                        (declare (fixnum axis))
                        `(when (and ,enable
                                    (< (magicl:tref (cl-mpm/particle::mp-position mp) ,axis 0) (* 0.5d0 length)))
                           (let ((weight (weight-func-pos
                                          mesh
                                          (cl-mpm/particle::mp-position mp)
                                          (cl-mpm/fastmaths::fast-.* (cl-mpm/particle:mp-position mp-other)
                                                                     (cl-mpm/utils::vector-from-list
                                                                      (list ,(if (= axis 0) -1d0 0d0)
                                                                            ,(if (= axis 1) -1d0 0d0)
                                                                            ,(if (= axis 2) -1d0 0d0)
                                                                            )))
                                          (sqrt (* length ll))
                                          )))
                             (declare (double-float weight m d mass-total damage-inc))
                             (incf mass-total (* weight m))
                             (incf damage-inc
                                   (* (the double-float (cl-mpm/particle::mp-damage-y-local mp-other))
                                      weight m))))))
             (reflect-axis 0 *enable-reflect-x*)
             (reflect-axis 1 *enable-reflect-y*)
             (reflect-axis 2 *enable-reflect-z*)
             )
           ))
       ))
    (when (> mass-total 0d0)
      (setf damage-inc (/ damage-inc mass-total)))
    damage-inc))

(defun calculate-delocalised-damage-stress (mesh mp length)
  (let ((damage-inc 0d0)
        (mass-total 0d0)
        )
    (declare (double-float damage-inc mass-total))
    (iterate-over-neighour-mps
     mesh mp length
     (lambda (mesh mp mp-other dist)
       (with-accessors ((d cl-mpm/particle::mp-damage)
                        (m cl-mpm/particle:mp-volume)
                        (ll cl-mpm/particle::mp-true-local-length)
                        (p cl-mpm/particle:mp-position))
           mp-other
         (when t;(< (the double-float d) 1d0)
           (let* (
                 ;;Nodally averaged local funcj
                 ;; (weight (weight-func-mps mesh mp mp-other (* 0.5d0 (+ length ll))))
                 ;; (weight (weight-func-mps mesh mp mp-other (sqrt (* length ll))))
                 ;;
                 (diff
                   (cl-mpm/fastmaths:fast-.-
                    (cl-mpm/particle::mp-position mp-other)
                    (cl-mpm/particle::mp-position mp)))
                 (weight
                   (weight-func-mps mesh mp mp-other
                                    (sqrt
                                     (*
                                      (compute-effective-length-stress-precomputed
                                       mp
                                       ;; (cl-mpm/particle::mp-undamaged-stress mp)
                                       (cl-mpm/particle::mp-initiation-stress mp)
                                       diff
                                       (cl-mpm/particle::mp-local-length mp))
                                      (compute-effective-length-stress-precomputed
                                       mp-other
                                       ;; (cl-mpm/particle::mp-undamaged-stress mp-other)
                                       (cl-mpm/particle::mp-initiation-stress mp-other)
                                       diff
                                       (cl-mpm/particle::mp-local-length mp-other)))))
                   ;; (weight-func-mps mesh mp mp-other length)
                   ;; (weight-func-mps mesh mp mp-other (* 0.5d0 (+ length ll)))
                   ;; (weight-func-mps mesh mp mp-other ll)
                   ;; (weight-func-mps mesh mp mp-other ll)
                   ;; (weight-func-mps-damaged mesh mp mp-other
                   ;;                          (cl-mpm/particle::mp-local-length mp)
                   ;;                          )
                   ))
             (declare (double-float weight m d mass-total damage-inc))
             (incf mass-total (* weight m))
             (incf damage-inc
                   (* (the double-float (cl-mpm/particle::mp-damage-y-local mp-other))
                      weight m)))
           (macrolet ((reflect-axis (axis enable)
                        (declare (fixnum axis))
                        `(when (and ,enable
                                    (< (magicl:tref (cl-mpm/particle::mp-position mp) ,axis 0) (* 0.5d0 length)))
                           (let ((weight (weight-func-pos
                                          mesh
                                          (cl-mpm/particle::mp-position mp)
                                          (cl-mpm/fastmaths::fast-.* (cl-mpm/particle:mp-position mp-other)
                                                                     (cl-mpm/utils::vector-from-list
                                                                      (list ,(if (= axis 0) -1d0 0d0)
                                                                            ,(if (= axis 1) -1d0 0d0)
                                                                            ,(if (= axis 2) -1d0 0d0)
                                                                            )))
                                          (sqrt (* length ll))
                                          )))
                             (declare (double-float weight m d mass-total damage-inc))
                             (incf mass-total (* weight m))
                             (incf damage-inc
                                   (* (the double-float (cl-mpm/particle::mp-damage-y-local mp-other))
                                      weight m))))))
             (reflect-axis 0 *enable-reflect-x*)
             (reflect-axis 1 *enable-reflect-y*)
             (reflect-axis 2 *enable-reflect-z*)
             )
           ))
       ))
    (when (> mass-total 0d0)
      (setf damage-inc (/ damage-inc mass-total)))
    damage-inc))
(defun find-mp-local-length (mesh mp)
  (with-accessors ((tll cl-mpm/particle::mp-true-local-length)
                   (ll cl-mpm/particle::mp-local-length)
                   (lld cl-mpm/particle::mp-local-length-damaged)
                   (damage cl-mpm/particle::mp-damage))
      mp
    (setf tll
          (length-localisation
           ll
           lld
           damage))))


(defgeneric g2p-damage (sim)
  (:documentation
   "Map damage to grid"))

(defmethod g2p-damage ((sim cl-mpm/damage::mpm-sim-damage))
  (cl-mpm:iterate-over-nodes
   (cl-mpm:sim-mesh sim)
   (lambda (n)
     (when (cl-mpm/mesh::node-active n)
       (setf (cl-mpm/mesh::node-damage n) 0d0
             (cl-mpm/mesh::node-volume n) 0d0))))
  (cl-mpm::iterate-over-mps
   (cl-mpm:sim-mps sim)
   (lambda (mp)
     (when (typep mp 'cl-mpm/particle::particle-damage)
       (cl-mpm:iterate-over-neighbours
        (cl-mpm:sim-mesh sim)
        mp
        (lambda (node svp grads fsvp fgrads)
          (sb-thread:with-mutex ((cl-mpm/mesh:node-lock node))
            (incf (cl-mpm/mesh::node-volume node)
                  (* svp
                     (cl-mpm/particle::mp-volume mp)))
            (incf (cl-mpm/mesh::node-damage node)
                  (* svp
                     (cl-mpm/particle::mp-volume mp)
                     (cl-mpm/particle::mp-damage mp)))))))))
  (cl-mpm:iterate-over-nodes
   (cl-mpm:sim-mesh sim)
   (lambda (n)
     (if (> (cl-mpm/mesh::node-volume n) 0d0);(cl-mpm/mesh::node-active n)
         (progn
           (setf (cl-mpm/mesh::node-damage n)
                 (min 1d0
                      (max 0d0 (/ (cl-mpm/mesh::node-damage n)
                                  (cl-mpm/mesh::node-volume n))))))
       (setf (cl-mpm/mesh::node-damage n) 0d0)))))

(defgeneric update-localisation-lengths (sim))
(defmethod update-localisation-lengths ((sim cl-mpm/damage::mpm-sim-damage))
  (with-accessors ((mps cl-mpm::sim-mps)
                   (mesh cl-mpm:sim-mesh)
                   (stress-based sim-enable-stress-based-length)
                   )
      sim
    (cl-mpm:iterate-over-mps
     mps
     (lambda (mp)
       (when (typep mp 'cl-mpm/particle:particle-damage)
         ;; (find-mp-local-length mesh mp)
         (find-intergral-local-length mesh mp)
         )))))

(defgeneric delocalise-damage (sim))

(defmethod delocalise-damage ((sim cl-mpm/damage::mpm-sim-damage))
  (declare (optimize (speed 3)))
  (with-accessors ((mps cl-mpm::sim-mps)
                   (mesh cl-mpm:sim-mesh))
      sim
    ;; Calculate the delocalised damage for each damage particle
    (cl-mpm:iterate-over-mps
     mps
     (lambda (mp)
       (when (typep mp 'cl-mpm/particle:particle-damage)
         (with-accessors ((damage-ybar cl-mpm/particle::mp-damage-ybar)
                          (damage cl-mpm/particle::mp-damage)
                          (local-length-t cl-mpm/particle::mp-local-length))
             mp
           (setf damage-ybar (calculate-delocalised-damage mesh mp local-length-t)))))))
  (values))

(defgeneric delocalise-damage-stress (sim))

(defmethod delocalise-damage-stress ((sim cl-mpm/damage::mpm-sim-damage))
  (declare (optimize (speed 3)))
  (with-accessors ((mps cl-mpm::sim-mps)
                   (mesh cl-mpm:sim-mesh))
      sim
    (cl-mpm:iterate-over-mps
     mps
     (lambda (mp)
       (when (typep mp 'cl-mpm/particle:particle-damage)
         (let (;; (stress (cl-mpm/particle::mp-undamaged-stress mp))
               (stress (cl-mpm/constitutive::linear-elastic-mat
                        (cl-mpm/particle::mp-strain-n mp)
                        (cl-mpm/particle::mp-elastic-matrix mp))))
           (multiple-value-bind (l v) (cl-mpm/utils::eig (cl-mpm/utils::voight-to-matrix stress))
             (setf (cl-mpm/particle::mp-stress-eigenvalues mp) l)
             (setf (cl-mpm/particle::mp-stress-eigenvectors mp) v))))))
    ;; Calculate the delocalised damage for each damage particle
    (cl-mpm:iterate-over-mps
     mps
     (lambda (mp)
       (when (typep mp 'cl-mpm/particle:particle-damage)
         (with-accessors ((damage-ybar cl-mpm/particle::mp-damage-ybar)
                          (damage cl-mpm/particle::mp-damage)
                          (local-length-t cl-mpm/particle::mp-local-length))
             mp
           (setf damage-ybar (calculate-delocalised-damage-stress mesh mp local-length-t)))))))
  (values))


(defun localise-damage (mesh mps dt)
  "Apply local damage model"
  (cl-mpm:iterate-over-mps
   mps
    (lambda (mp)
      (when (typep mp 'cl-mpm/particle:particle-damage)
        (with-accessors ((damage-ybar cl-mpm/particle::mp-damage-ybar)
                         (damage-y cl-mpm/particle::mp-damage-y-local))
            mp
          (setf damage-ybar damage-y)))))
  (values))


(defun remove-mp-damage (sim func)
  )

(defmethod cl-mpm::remove-mps-func ((sim mpm-sim-damage) func)
  (with-accessors ((mesh cl-mpm::sim-mesh)
                   (mps cl-mpm::sim-mps))
      sim
    (when (> (length mps) 0)
      (loop for mp across mps
            when (and
                  (typep mp 'cl-mpm/particle:particle-damage)
                  (funcall func mp))
              do (local-list-remove-particle mesh mp))
      (call-next-method))))

(defmethod cl-mpm::sim-add-mp ((sim mpm-sim-damage) mp)
  (when (typep mp 'cl-mpm/particle::particle-damage)
    (local-list-add-particle (cl-mpm:sim-mesh sim) mp))
  (call-next-method))

(defmethod (setf cl-mpm::sim-mps) (mps (sim cl-mpm/damage::mpm-sim-damage))
  ;; (with-accessors ((mesh cl-mpm::sim-mesh))
  ;;     sim
  ;;   (loop for mp across mps
  ;;         when (and
  ;;               (typep mp 'cl-mpm/particle:particle-damage)
  ;;               (eq (cl-mpm/particle::mp-damage-position mp) nil))
  ;;           do (local-list-add-particle mesh mp)))
  (call-next-method))


(defmethod damage-model-calculate-y ((mp cl-mpm/particle::particle) dt)
  0d0)


;; (defmethod damage-model-calculate-y (mp (dm damage-model-rankine) dt)
;;   (let ((damage-increment 0d0))
;;     (with-accessors ((stress cl-mpm/particle::mp-stress)
;;                      (damage cl-mpm/particle:mp-damage)
;;                      (pressure cl-mpm/particle::mp-pressure)
;;                      (ybar cl-mpm/particle::mp-local-damage-increment)
;;                      ) mp
;;       (declare (double-float pressure damage))
;;       (progn
;;         (progn
;;           (multiple-value-bind (s_1 s_2) (principal-stresses stress)
;;             (let* ((pressure-effective (* pressure 1d0))
;;                    (s_1 (- s_1 pressure-effective))
;;                    (s_2 (- s_2 pressure-effective))
;;                    (s_1 (max 0d0 s_1))
;;                    (s_2 (max 0d0 s_2))
;;                    ;; (vm (- s_1 s_2))
;;                                         ;(s_1 vm)
;;                    )
;;               (when (> s_1 0d0)
;;                 (if (< damage 1d0)
;;                     (setf damage-increment (/ s_1 (expt (- 1d0 damage) 2d0)))
;;                     (setf damage-increment s_1)))))
;;           (when (>= damage 1d0)
;;             (setf damage-increment 0d0))
;;           ;; damage-increment
;;           (setf ybar damage-increment)
;;           ;; (setf (cl-mpm/particle::mp-local-damage-increment mp) damage-increment)
;;           )))))

;; (defmethod damage-model-calculate-y (mp (dm damage-model-creep) dt)
;;   (let ((damage-increment 0d0))
;;     (with-accessors ((stress cl-mpm/particle::mp-stress)
;;                      (damage cl-mpm/particle:mp-damage)
;;                      (pressure cl-mpm/particle::mp-pressure)
;;                      (ybar cl-mpm/particle::mp-local-damage-increment)
;;                      ) mp
;;       (with-accessors
;;             ((init-stress damage-model-creep-initiation-stress)
;;              (damage-rate damage-model-creep-damage-rate)
;;              )
;;           dm
;;         (declare (double-float pressure damage))
;;         (progn
;;           (progn
;;             (multiple-value-bind (s_1 s_2) (principal-stresses stress)
;;               (let* ((pressure-effective (* pressure 1d0))
;;                      ;; (s_1 (- s_1 pressure-effective))
;;                      ;; (s_2 (- s_2 pressure-effective))
;;                      (s_1 (max 0d0 s_1))
;;                      (s_2 (max 0d0 s_2))
;;                      ;; (vm (- s_1 s_2))
;;                                         ;(s_1 vm)
;;                      )
;;                 (when (> s_1 0d0)
;;                   (if (< damage 1d0)
;;                       (setf damage-increment (/ s_1 (expt (- 1d0 damage) 2d0)))
;;                       (setf damage-increment s_1)))))
;;             (when (>= damage 1d0)
;;               (setf damage-increment 0d0))
;;             ;; damage-increment
;;             (setf ybar damage-increment)
;;             ;; (setf (cl-mpm/particle::mp-local-damage-increment mp) damage-increment)
;;             ))))))





(defun compute-damage-delta (sim)
  (let* ((delta-ds
           (cl-mpm::reduce-over-mps
            (cl-mpm:sim-mps sim)
            (lambda (mp)
              (if (typep mp 'cl-mpm/particle::particle-damage)
                (with-accessors ((damage cl-mpm/particle::mp-damage)
                                 (damage-prev cl-mpm/particle::mp-damage-prev-trial)
                                 (inc cl-mpm/particle::mp-damage-increment)
                                 (mass cl-mpm/particle::mp-mass))
                    mp
                  (expt (* mass (- damage damage-prev)) 2))
                0d0))
            #'+))
         (delta-incs
           (cl-mpm::reduce-over-mps
            (cl-mpm:sim-mps sim)
            (lambda (mp)
              (if (typep mp 'cl-mpm/particle::particle-damage)
                  (with-accessors ((damage cl-mpm/particle::mp-damage)
                                   (damage-prev cl-mpm/particle::mp-damage-prev-trial)
                                   (inc cl-mpm/particle::mp-damage-increment)
                                   (mass cl-mpm/particle::mp-mass))
                      mp
                    (expt (* mass damage) 2))
                  0d0))
            #'+)))
    (if (> delta-incs 0d0)
        (sqrt (/ delta-ds delta-incs))
        0d0)))

(defmethod compute-damage ((mp cl-mpm/particle::particle)))

(defmethod update-damage ((mp cl-mpm/particle::particle) dt))














;; (defun solve-quasi-static ()
;;   (let ((damage-0 0d0)
;;         (damage-1 0d0))
;;     (loop for i from 0 to 100
;;           while (or (= i 0) (> damage-1 (* 1.1d0 damage-0)))
;;           do
;;              (progn
;;                (setf damage-0 damage-1)
;;                (cl-mpm/dynamic-relaxation:converge-quasi-static
;;                 *sim*
;;                 :energy-crit 1d-2
;;                 :oobf-crit 1d-2
;;                 :substeps 50
;;                 :conv-steps 200
;;                 :dt-scale dt-scale
;;                 :post-iter-step
;;                 (lambda (i energy oobf)
;;                   (setf *piston-confinement* 0d0
;;                         *piston-steps* 0)))
;;                (cl-mpm/damage::calculate-damage *sim*)
;;                ;; (plot *sim*)
;;                (setf damage-1 (get-damage))
;;                ;; (plot-domain)
;;                ))
;;     (when (> damage-1 (* damage-0 1.1d0))
;;       (break "Staggered error"))))



(defun get-nonlocal-interactions (sim mp)
  (cond
    ((cl-mpm/damage::sim-enable-ekl sim)
     (get-nonlocal-interactions-ekl sim mp))
    ((cl-mpm/damage::sim-enable-stress-based-length sim)
     (get-nonlocal-interactions-stress-based sim mp))
    (t
     (when (cl-mpm/damage::sim-enable-length-localisation sim)
       (update-localisation-lengths sim))
     (get-nonlocal-interactions-standard sim mp))))

(defun get-nonlocal-interactions-standard (sim mp)
  (g2p-damage sim)
  (with-accessors ((mesh cl-mpm:sim-mesh)
                   (mps cl-mpm:sim-mps))
      sim
    (let ((data-positions (list))
          (data-weights (list))
          (damage-inc 0d0)
          (mass-total 0d0)
          (length (* 1d0 (cl-mpm/particle::mp-true-local-length mp))))
      (declare (double-float damage-inc mass-total))
      (iterate-over-neighour-mps
       mesh mp length
       (lambda (mesh mp mp-other dist)
         (with-accessors ((d cl-mpm/particle::mp-damage)
                          (m cl-mpm/particle:mp-volume)
                          (ll cl-mpm/particle::mp-true-local-length)
                          (p cl-mpm/particle:mp-position))
             mp-other
           (when t
             (push (cl-mpm/fastmaths::fast-.-
                    (cl-mpm/particle::mp-position mp-other)
                    (cl-mpm/particle::mp-position mp)
                    ) data-positions)
             (let* ((weight (weight-func-mps mesh mp mp-other (sqrt (* length ll)))))
               (declare (double-float weight m d mass-total damage-inc))
               (incf mass-total (* weight m))
               (incf damage-inc
                     (* (the double-float (cl-mpm/particle::mp-damage-y-local mp-other))
                        weight m))
               (push (* weight m) data-weights))))))
      (when (> mass-total 0d0)
        (setf damage-inc (/ damage-inc mass-total))
        (setf data-weights (mapcar (lambda (w) (/ w mass-total)) data-weights)))
      (values data-positions data-weights))))

(defun get-nonlocal-interactions-ekl (sim mp)
  (g2p-damage sim)
  (with-accessors ((mesh cl-mpm:sim-mesh)
                   (mps cl-mpm:sim-mps)) sim
    (let ((data-positions (list))
          (data-weights (list))
          (mass-total 0d0)
          (length (* 1d0 (cl-mpm/particle::mp-local-length mp))))
      (declare (double-float mass-total))
      (iterate-over-neighour-mps
       mesh mp length
       (lambda (mesh mp mp-other dist)
         (with-accessors ((d cl-mpm/particle::mp-damage)
                          (m cl-mpm/particle:mp-volume)
                          (ll cl-mpm/particle::mp-local-length)
                          (p cl-mpm/particle:mp-position))
             mp-other
           (push (cl-mpm/fastmaths::fast-.-
                  (cl-mpm/particle::mp-position mp-other)
                  (cl-mpm/particle::mp-position mp)
                  ) data-positions)
           (let ((weight (weight-func-mps-damaged mesh mp mp-other length)))
             (declare (double-float weight m d mass-total))
             (incf mass-total (* weight m))
             (push (* weight m) data-weights)))))
      (when (> mass-total 0d0)
        (setf data-weights (mapcar (lambda (w) (/ w mass-total)) data-weights)))
      (values data-positions data-weights))))

(defun get-nonlocal-interactions-stress-based (sim mp)
  (g2p-damage sim)
  (with-accessors ((mesh cl-mpm:sim-mesh)
                   (mps cl-mpm:sim-mps)) sim
    (let ((data-positions (list))
          (data-weights (list))
          (damage-inc 0d0)
          (mass-total 0d0)
          (length (* 1d0 (cl-mpm/particle::mp-local-length mp))))
      (declare (double-float damage-inc mass-total))
      (iterate-over-neighour-mps
       mesh mp length
       (lambda (mesh mp mp-other dist)
         (with-accessors ((d cl-mpm/particle::mp-damage)
                          (m cl-mpm/particle:mp-volume)
                          (ll cl-mpm/particle::mp-local-length)
                          (p cl-mpm/particle:mp-position))
             mp-other
           (when t;(< (the double-float d) 1d0)
             (push (cl-mpm/fastmaths::fast-.-
                    (cl-mpm/particle::mp-position mp-other)
                    (cl-mpm/particle::mp-position mp)
                    ) data-positions)
             (let ((weight (weight-func-mps mesh mp mp-other
                                            (compute-effective-length-stress
                                             (cl-mpm/particle::mp-undamaged-stress mp-other)
                                             (cl-mpm/particle::mp-initiation-stress mp-other)
                                             (cl-mpm/fastmaths:fast-.-
                                              (cl-mpm/particle::mp-position mp-other)
                                              (cl-mpm/particle::mp-position mp)
                                              )
                                             (cl-mpm/particle::mp-local-length mp)))))
               (declare (double-float weight m d mass-total damage-inc))
               (incf mass-total (* weight m))
               (incf damage-inc
                     (* (the double-float (cl-mpm/particle::mp-damage-y-local mp-other))
                        weight m))
               (push (* weight m) data-weights))))))
      (when (> mass-total 0d0)
        (setf damage-inc (/ damage-inc mass-total))
        (setf data-weights (mapcar (lambda (w) (/ w mass-total)) data-weights)))
      (values data-positions data-weights))))


