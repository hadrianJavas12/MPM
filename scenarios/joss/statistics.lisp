;;;; Reference force, work and kinetic-energy statistics.
;;;; Extracted without changing the existing numerical expressions.
(in-package :cl-mpm/framework/cliff)

(defun reference-finite-p (value)
  (and (typep value 'double-float)
       (not (sb-ext:float-nan-p value))
       (not (sb-ext:float-infinity-p value))))

(defmethod cl-mpm::update-dynamic-stats ((sim joss-reference-sim))
  ;; Called by the explicit USF solver after force/velocity BCs are enforced.
  ;; OOBF excludes viscous damping: it measures internal + external imbalance.
  (let ((kinetic 0d0) (residual2 0d0) (external2 0d0) (work-increment 0d0))
    (let* ((mesh (cl-mpm:sim-mesh sim))
           (nodes (cl-mpm/mesh::mesh-nodes mesh))
           (nominal-volume (expt (cl-mpm/mesh:mesh-resolution mesh) (cl-mpm/mesh:mesh-nd mesh))))
      ;; Serial reduction: ITERATE-OVER-NODES is threaded and shared INCF
      ;; accumulators would lose updates with more than one worker.
      (loop for i below (array-total-size nodes)
            for node = (row-major-aref nodes i) do
       (when (cl-mpm/mesh:node-active node)
         ;; Mapped nodal volume, rather than node-volume-true, penalizes
         ;; ill-integrated nodes as in Eqs.64-66. For OOBF retain the engine's
         ;; L2 norm convention; the printed Eq.67 has ambiguous L1/square notation.
         (let ((weight (/ (cl-mpm/mesh::node-volume node) nominal-volume)))
           (unless (and (reference-finite-p weight) (>= weight 0d0))
             (error "Invalid mapped nodal-volume weight"))
           (incf kinetic (* weight 0.5d0 (cl-mpm/mesh:node-mass node)
                            (cl-mpm/fastmaths::mag-squared (cl-mpm/mesh:node-velocity node))))
           (dotimes (d 3)
             (let ((external (cl-mpm/utils:varef (cl-mpm/mesh::node-external-force node) d))
                   (internal (cl-mpm/utils:varef (cl-mpm/mesh::node-internal-force node) d))
                   (displacement (cl-mpm/utils:varef (cl-mpm/mesh::node-displacment node) d)))
               (incf residual2 (* weight (expt (+ internal external) 2)))
               (incf external2 (* weight (expt external 2)))
               (incf work-increment (* weight external displacement))))))))
    (unless (and (reference-finite-p kinetic) (reference-finite-p residual2)
                 (reference-finite-p external2) (reference-finite-p work-increment))
      (error "Nonfinite reference energy/force/work statistics"))
    (when (and (= external2 0d0) (> residual2 0d0))
      (error "Reference OOBF is undefined: zero external-force norm with a nonzero residual"))
    (setf (cl-mpm::sim-stats-energy sim) kinetic
          (cl-mpm::sim-stats-oobf sim) (if (> external2 0d0) (sqrt (/ residual2 external2)) 0d0)
          (cl-mpm::sim-stats-power sim) work-increment)
    (incf (cl-mpm::sim-stats-work sim) work-increment)
    (unless (reference-finite-p (cl-mpm::sim-stats-work sim))
      (error "Nonfinite accumulated reference work"))))

(defun reference-aggregate-statistics (sim)
  ;; The independent aggregate DOFs satisfy E^T*(f_int+f_ext)=0. Their dependent
  ;; exterior nodal forces need not vanish individually. Keep viscous damping
  ;; out of the physical residual, and do not count aggregate nodes twice.
  (let* ((mesh (cl-mpm:sim-mesh sim))
         (nodes (cl-mpm/mesh::mesh-nodes mesh))
         (energy 0d0) (residual2 0d0) (external2 0d0) (increment 0d0))
    (loop for i below (array-total-size nodes)
          for node = (row-major-aref nodes i) do
      (when (and (cl-mpm/mesh:node-active node) (not (cl-mpm/mesh::node-agg node)))
        (incf energy (* 0.5d0 (cl-mpm/mesh:node-mass node)
                       (cl-mpm/fastmaths::mag-squared (cl-mpm/mesh:node-velocity node))))
        (dotimes (d (cl-mpm/mesh:mesh-nd mesh))
          (let ((external (cl-mpm/utils:varef (cl-mpm/mesh::node-external-force node) d))
                (internal (cl-mpm/utils:varef (cl-mpm/mesh::node-internal-force node) d))
                (disp (cl-mpm/utils:varef (cl-mpm/mesh::node-displacment node) d)))
            (incf residual2 (expt (+ internal external) 2))
            (incf external2 (expt external 2))
            (incf increment (* external disp))))))
    (dotimes (d (cl-mpm/mesh:mesh-nd mesh))
      (let* ((external (cl-mpm/aggregate::assemble-global-vec sim #'cl-mpm/mesh::node-external-force d))
             (internal (cl-mpm/aggregate::assemble-global-vec sim #'cl-mpm/mesh::node-internal-force d))
             (residual (cl-mpm/fastmaths::fast-.+ external internal))
             (disp (cl-mpm/aggregate::assemble-global-vec sim #'cl-mpm/mesh::node-displacment d))
             (velocity (cl-mpm/aggregate::assemble-internal-vec sim #'cl-mpm/mesh::node-velocity d)))
        (incf residual2 (cl-mpm/fastmaths::mag-squared (cl-mpm/aggregate::aggregate-vec sim residual d)))
        (incf external2 (cl-mpm/fastmaths::mag-squared (cl-mpm/aggregate::aggregate-vec sim external d)))
        (incf increment (cl-mpm/fastmaths:dot disp external))
        (incf energy (* 0.5d0 (cl-mpm/fastmaths:dot velocity
                              (cl-mpm/aggregate::@-mass-matrix-vec sim velocity d))))))
    (dolist (value (list energy residual2 external2 increment))
      (unless (reference-finite-p value) (error "Nonfinite aggregate reference statistic")))
    (when (and (= external2 0d0) (> residual2 0d0))
      (error "Aggregate reference OOBF is undefined: zero external norm with nonzero residual"))
    (values energy (if (> external2 0d0) (sqrt (/ residual2 external2)) 0d0) increment)))

(defmethod cl-mpm::update-dynamic-stats ((sim joss-reference-aggregate-sim))
  (multiple-value-bind (energy oobf increment) (reference-aggregate-statistics sim)
    (setf (cl-mpm::sim-stats-energy sim) energy
          (cl-mpm::sim-stats-oobf sim) oobf
          (cl-mpm::sim-stats-power sim) increment)
    (incf (cl-mpm::sim-stats-work sim) increment)
    (unless (reference-finite-p (cl-mpm::sim-stats-work sim))
      (error "Nonfinite accumulated aggregate reference work"))))

(defun reference-energy-ratio (sim)
  (let ((energy (cl-mpm::sim-stats-energy sim))
        (work (abs (cl-mpm::sim-stats-work sim))))
    (cond ((> work 0d0) (/ energy work))
          ((= energy 0d0) 0d0)
          (t (error "Reference energy ratio is undefined: zero accumulated work with nonzero kinetic energy")))))
