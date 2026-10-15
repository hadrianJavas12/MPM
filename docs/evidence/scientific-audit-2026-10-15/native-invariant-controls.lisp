;;;; Bounded native diagnostics, 2026-10-15; no production definitions replaced.
;;;; Run: windows\cl-mpm.cmd output\scientific-audit-2026-10-15\native-invariant-controls.lisp
(in-package :cl-user)
(ql:quickload '(:cl-mpm/aggregate :jonathan) :silent t)
(cl-mpm/utils::set-workers 1)

(defun audit-object (&rest pairs)
  (let ((h (make-hash-table :test #'equal)))
    (loop for (key value) on pairs by #'cddr do (setf (gethash key h) value))
    h))
(defun audit-vector (m)
  (coerce (loop for i below 3 collect (cl-mpm/utils:varef m i)) 'vector))
(defun audit-matrix (m)
  (coerce (loop for i below (magicl:nrows m)
                collect (coerce (loop for j below (magicl:ncols m)
                                      collect (magicl:tref m i j)) 'vector)) 'vector))

(defun audit-disconnected-aggregation ()
  ;; Two occupied cells, with eight empty cells between their x extents.
  ;; Occupancy flags are explicit, not reconstructed from a dynamic run.
  (let* ((sim (cl-mpm:make-mpm-sim '(14d0 4d0) 1d0 0.001d0 nil
                                :sim-type 'cl-mpm/aggregate::mpm-sim-aggregated))
         (mesh (cl-mpm:sim-mesh sim))
         (fragment (cl-mpm/mesh::get-cell mesh '(1 1 0)))
         (support (cl-mpm/mesh::get-cell mesh '(10 1 0)))
         (local-candidates 0))
    (cl-mpm::iterate-over-cells mesh
      (lambda (c) (setf (cl-mpm/mesh::cell-active c) nil
                        (cl-mpm/mesh::cell-partial c) t
                        (cl-mpm/mesh::cell-agg c) nil)))
    (cl-mpm::iterate-over-nodes mesh
      (lambda (n) (setf (cl-mpm/mesh::node-active n) nil)))
    (setf (cl-mpm/mesh::cell-active fragment) t
          (cl-mpm/mesh::cell-volume fragment) 0.2d0
          (cl-mpm/mesh::cell-mp-count fragment) 1
          (cl-mpm/mesh::cell-active support) t
          (cl-mpm/mesh::cell-partial support) nil
          (cl-mpm/mesh::cell-volume support) 1d0
          (cl-mpm/mesh::cell-mp-count support) 4)
    (dolist (c (list fragment support))
      (loop for n across (cl-mpm/mesh::cell-nodes c)
            do (setf (cl-mpm/mesh::node-active n) t
                     (cl-mpm/mesh::node-mass n) 1d0)))
    (cl-mpm/aggregate::iterate-over-cell-patch mesh
      (cl-mpm/mesh::cell-centroid fragment) 2
      (lambda (c)
        (when (and (cl-mpm/mesh::cell-active c)
                   (not (cl-mpm/mesh::cell-partial c))
                   (not (cl-mpm/mesh::cell-agg c)))
          (incf local-candidates))))
    (let* ((chosen (cl-mpm/aggregate::get-closest-cell mesh
                      (cl-mpm/mesh::cell-centroid fragment)))
           (distance-squared (cl-mpm/fastmaths::diff-norm
                      (cl-mpm/mesh::cell-centroid fragment)
                      (cl-mpm/mesh::cell-centroid chosen)))
           (distance (sqrt distance-squared)))
      (cl-mpm/aggregate::locate-aggregate-nodes sim)
      (let* ((dense-e (cl-mpm/aggregate::assemble-e sim))
             (sparse-e (cl-mpm/aggregate::assemble-sparse-e sim))
             (e (cl-mpm/utils::arb-matrix
                 (cl-mpm/utils::sparse-matrix-nrows sparse-e)
                 (cl-mpm/utils::sparse-matrix-ncols sparse-e)))
             (max-row-error 0d0) (max-weight 0d0)
             (coupled-rows 0)
             (fragment-rows (make-array 0 :adjustable t :fill-pointer 0)))
        (loop for i below (magicl:nrows e) do
          (loop for j below (magicl:ncols e) do
            (setf (magicl:tref e i j) (cl-mpm/utils::sparse-matrix-aref sparse-e i j))
            (assert (< (abs (- (magicl:tref e i j) (magicl:tref dense-e i j))) 1d-12))))
        (loop for i below (magicl:nrows e) do
          (let ((sum 0d0))
            (loop for j below (magicl:ncols e) do
              (incf sum (magicl:tref e i j))
              (setf max-weight (max max-weight (abs (magicl:tref e i j)))))
            (setf max-row-error (max max-row-error (abs (- sum 1d0))))))
        (loop for n across (cl-mpm/mesh::cell-nodes fragment) do
          (when (eq (cl-mpm/mesh::node-agg-interior-cell n) support)
            (incf coupled-rows)
            (let* ((i (cl-mpm/mesh::node-agg-fd n))
                   (sum (loop for j below (magicl:ncols e) sum (magicl:tref e i j))))
              (vector-push-extend
               (audit-object "nodePosition" (audit-vector (cl-mpm/mesh::node-position n))
                             "supportCell" (coerce (cl-mpm/mesh::cell-index support) 'vector)
                             "weights" (coerce (loop for j below (magicl:ncols e)
                                                      collect (magicl:tref e i j)) 'vector)
                             "extendedUnitTranslation" sum)
               fragment-rows))))
        (assert (eq chosen support))
        (assert (= local-candidates 0))
        (assert (= coupled-rows 4))
        (assert (< max-row-error 1d-12))
        (format t "AUDIT A: local-candidates=~D chosen=~S distance=~F h gap=8h coupled-rows=~D maxabsE=~F row-sum-error=~E~%"
                local-candidates (cl-mpm/mesh::cell-index chosen) distance coupled-rows max-weight max-row-error)
        (audit-object "test" "disconnected-aggregation" "status" "reproduced"
          "setup" "Explicit native cell/node occupancy flags; no MPs/time integration. 1m grid; occupied fragment [1,2]x[1,2], full support [10,11]x[1,2], empty gap 8m."
          "localCandidateCount" local-candidates
          "fragmentCell" #(1 1 0) "selectedCell" (coerce (cl-mpm/mesh::cell-index chosen) 'vector)
          "centroidDistance" distance "nativeSquaredDistance" distance-squared "emptyGap" 8d0
          "coupledFragmentNodes" coupled-rows "maxAbsEWeight" max-weight
          "maxERowSumError" max-row-error "E" (audit-matrix e) "sparseDenseAgreement" "within1e-12" "fragmentRows" fragment-rows
          "interpretation" "Native fallback chooses a disconnected full cell. Native locate/assemble produces cross-gap extrapolation; rows preserve unit translation but tie fragment motion to remote support. This does not establish how often the accepted collapse triggers this condition.")))))

(defun audit-fbar-case (fbar)
  ;; Native GIMP cache and displacement-gradient assembly from nonuniform nodal
  ;; displacement. One particle away from boundaries, no constitutive override.
  (let* ((mesh (cl-mpm/mesh::make-mesh '(6d0 6d0) 1d0 nil))
         (mp (make-instance 'cl-mpm/particle:particle
                 :position (cl-mpm/utils:vector-from-list '(2.9d0 2.7d0 0d0))
                 :size (cl-mpm/utils:vector-from-list '(0.8d0 0.8d0 0d0))
                 :size-0 (cl-mpm/utils:vector-from-list '(0.8d0 0.8d0 0d0))
                 :mass 1d0 :volume 0.64d0)))
    (cl-mpm::iterate-over-nodes mesh
      (lambda (node)
        (let* ((p (cl-mpm/mesh::node-position node))
               (x (cl-mpm/utils:varef p 0)) (y (cl-mpm/utils:varef p 1))
               (u (cl-mpm/mesh::node-displacment node)))
          (setf (cl-mpm/mesh::node-active node) t
                (cl-mpm/utils:varef u 0) (* 0.02d0 x y)
                (cl-mpm/utils:varef u 1) (* -0.01d0 x y)))))
    (cl-mpm::calculate-strain-rate-disp mesh mp 0.01d0 fbar)
    (let ((gradient (audit-matrix (cl-mpm/particle::mp-stretch-tensor mp)))
          (fbar-gradient (audit-matrix (cl-mpm/particle::mp-stretch-tensor-fbar mp))))
      (cl-mpm::update-strain-kirchoff mesh mp 0.01d0 fbar)
      (cl-mpm::update-domain-det mesh mp)
      (let* ((v-ratio (/ (cl-mpm/particle:mp-volume mp) (cl-mpm/particle::mp-volume-0 mp)))
             (j (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp)))
             (domain (cl-mpm/particle::mp-domain-size mp))
             (domain0 (cl-mpm/particle::mp-domain-size-0 mp))
             (area-ratio (/ (* (cl-mpm/utils:varef domain 0) (cl-mpm/utils:varef domain 1))
                            (* (cl-mpm/utils:varef domain0 0) (cl-mpm/utils:varef domain0 1))))
             (mismatch (- j v-ratio)))
        (if fbar (assert (> (abs mismatch) 1d-6)) (assert (< (abs mismatch) 1d-12)))
        (assert (< (abs (- j area-ratio)) 1d-12))
        (format t "AUDIT B: Fbar=~S V/V0=~,12F detF=~,12F area/area0=~,12F difference=~,12F~%"
                fbar v-ratio j area-ratio mismatch)
        (audit-object "fbar" (if fbar "on" "off") "VoverV0" v-ratio "detF" j
          "domainAreaRatio" area-ratio "detFMinusVolumeRatio" mismatch
          "gradient" gradient "fbarGradient" fbar-gradient
          "F" (audit-matrix (cl-mpm/particle:mp-deformation-gradient mp))
          "cachedNodeCount" (length (cl-mpm/particle::mp-cached-nodes mp)))))))

(let* ((a (audit-disconnected-aggregation))
       (b-on (audit-fbar-case t))
       (b-off (audit-fbar-case nil))
       (results (audit-object
          "date" "2026-10-15" "head" "8549c32bb53b69e6cbbb93246b412084eab9a2c1"
          "runtime" (lisp-implementation-version)
          "productionDefinitionsReplaced" "none"
          "aggregation" a
          "fbar" (audit-object "test" "native-nonuniform-nodal-displacement"
                     "setup" "6x6m 2D native GIMP mesh, h=1m; one MP (2.9,2.7), domain .8x.8, initial F=I and V=.64. All nodes active; prescribed ux=.02*x*y, uy=-.01*x*y. Native calculate-strain-rate-disp, update-strain-kirchoff, update-domain-det; no stress/material response or time integration."
                     "status" "reproduced" "on" b-on "off" b-off
                     "interpretation" "Fbar stores strain-modified F while physical volume uses unmodified increment. Domain-area update follows stored F. Different Jacobians may be an intentional Fbar convention, but volume/domain/stress consistency needs a documented and validated contract. This diagnostic does not quantify accepted-run error."))))
  (with-open-file (s (cl-mpm-path "output/scientific-audit-2026-10-15/native-invariant-controls.json")
                     :direction :output :if-exists :supersede :if-does-not-exist :create)
    (write-string (jonathan:to-json results) s)
    (terpri s))
  (format t "AUDIT NATIVE CONTROLS COMPLETE~%"))
