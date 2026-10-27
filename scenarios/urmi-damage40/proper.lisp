;;;; Explicit opt-in numerical profile; original engine/strict/rough defaults remain unchanged.
(in-package :cl-mpm/scenario/urmi-damage40)
(defparameter *proper-volume-domain* nil)

(defun proper-domain-update (mesh mp)
  "Volume-based cpGIMP domain: l_i=l_i0*sqrt(J) in plane strain.
This is a numerical quadrature domain, not the physical deformation F.
Wyser et al.2020 section2.2 describes this determinant-based alternative."
  (unless (= (cl-mpm/mesh:mesh-nd mesh) 2) (error "Proper profile is plane strain only."))
  (let ((j (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle::mp-deformation-gradient mp)))
        (domain0 (cl-mpm/particle::mp-domain-size-0 mp)))
    (unless (and (gs::finite-p j) (> j 0d0)
                 (loop for i below 2 always (and (gs::finite-p (component domain0 i)) (> (component domain0 i) 0d0))))
      (error "Proper volume-domain guard: nonpositive/nonfinite original domain or J=~S" j))
    (cl-mpm::update-domain-det mesh mp)
    (loop for i below 2 unless (and (gs::finite-p (component (cl-mpm/particle::mp-domain-size mp) i))
                                    (> (component (cl-mpm/particle::mp-domain-size mp) i) 0d0))
          do (error "Proper volume-domain result invalid."))))

(defmethod cl-mpm::update-particle :around (mesh (mp mc:particle-mc-evolution) dt)
  (if *proper-volume-domain*
      (progn (cl-mpm::update-particle-kirchoff mesh mp dt) (proper-domain-update mesh mp))
      (call-next-method)))

(defclass urmi-proper-sim (urmi-damage40-sim) ())
(defmethod cl-mpm::update-node-forces ((sim urmi-proper-sim))
  ;; Primary method retains inherited :after raw-force diagnostics. Standard
  ;; engine primary uses viscous damping regardless of sim-damping-algorithm.
  (cl-mpm::iterate-over-nodes (cl-mpm:sim-mesh sim)
    (lambda (node)
      (when (cl-mpm/mesh:node-active node)
        (cl-mpm::calculate-forces-cundall node (cl-mpm:sim-damping-factor sim)
          (cl-mpm:sim-dt sim) (cl-mpm::sim-mass-scale sim))))))

(defun proper-setup (sim)
  ;; Own diagnostic union for overlapping fixed rollers; physical BC objects
  ;; and their actual application are unchanged. Populate serially once.
  (let ((mesh (cl-mpm:sim-mesh sim)))
    (loop for bc across (cl-mpm:sim-bcs sim) do
      (let* ((node (cl-mpm/mesh:get-node mesh (cl-mpm/bc::bc-index bc)))
             (mask (or (cl-mpm/mesh::node-bcs node) (cl-mpm/utils:vector-from-list '(1d0 1d0 1d0))))
             (values (cl-mpm/bc:bc-value bc)))
        (loop for value in values for i from 0 when value do (setf (magicl:tref mask i 0) 0d0))
        (setf (cl-mpm/mesh::node-bcs node) mask))))
  sim)

(defparameter +proper-inputs+
  (mapcar (lambda (entry) (cons (car entry)
    (or (cdr (assoc (car entry)
      '(("crestLength" . 24d0) ("baseHeight" . 8d0) ("domainWidth" . 72d0) ("domainHeight" . 24d0)
        ("meshSize" . 1d0) ("duration" . 20d0) ("frames" . 101)
        ("maxDynamicUpdates" . 50000) ("maxPreparationUpdates" . 60000)
        ("maxPreparationTimeS" . 60d0) ("settleDampingAlpha" . .75d0)) :test #'string=))
      (cdr entry)))) +fixed-inputs+))

(defun compile-proper-configuration (case)
  (let ((input (fw:simulation-parameters case)) (material (fw:simulation-material case))
        (geometry (fw:simulation-geometry case)) (solver (fw:simulation-solver case)))
    (unless (= (hash-table-count input) (length +proper-inputs+)) (error "Proper input keys differ."))
    (dolist (entry +proper-inputs+)
      (unless (and (gs::finite-p (gethash (car entry) input)) (= (gethash (car entry) input) (cdr entry)))
        (error "Proper input differs: ~A" (car entry))))
    (dolist (entry '((:height . 10d0) (:crest-length . 24d0) (:slope . 40d0) (:base-height . 8d0)))
      (unless (= (fw:option geometry (car entry)) (cdr entry)) (error "Proper geometry differs.")))
    (unless (= (fw:option geometry :width) (+ 24d0 (/ 10d0 (tan (* pi (/ 40d0 180d0)))))) (error "Proper toe differs."))
    (dolist (entry '((:mesh-size . 1d0) (:mps-per-cell . 2) (:workers . 1) (:time-step-scale . .2d0)
                     (:frames . 101) (:max-updates . 50000) (:damping . .02d0)))
      (unless (= (fw:option solver (car entry)) (cdr entry)) (error "Proper solver differs.")))
    ;; Reuse exact original material/boundary validation with an isolated
    ;; original geometry/solver/input description, never modifying that case.
    (let* ((old-input (make-hash-table :test #'equal)))
      (dolist (entry +fixed-inputs+) (setf (gethash (car entry) old-input) (cdr entry)))
      (let ((config (compile-configuration
        (fw:make-simulation :scenario :urmi-damage40 :parameters old-input :material material
          :geometry (fw:make-geometry :slope :width (+ 12d0 (/ 10d0 (tan (* pi (/ 40d0 180d0)))))
                      :height 10d0 :crest-length 12d0 :slope 40d0 :base-height 4d0)
          :boundary (fw:simulation-boundary case) :loading (fw:simulation-loading case)
          :solver (fw:make-solver :explicit :mesh-size .5d0 :mps-per-cell 2 :workers 1
                    :time-step-scale .2d0 :frames 301 :max-updates 200000 :damping 0d0)))))
        (dolist (entry +proper-inputs+) (setf (gethash (car entry) config) (cdr entry)))
        (setf (gethash "toeX" config) (+ 24d0 (/ 10d0 (tan (* pi (/ 40d0 180d0)))))
              (gethash "settleDamping" config) .75d0
              (gethash "observerInitialXGreater" config) 14d0 (gethash "observerInitialYGreater" config) 10d0
              (gethash "displayOriginX" config) 12d0 (gethash "displayOriginY" config) 8d0)
        config))))

(defun proper-manifest (manifest)
  (setf (gethash "scenario" manifest) "urmi-damage40-proper"
        (gethash "requestedDynamicDurationS" manifest) 20d0
        (gethash "approximateDemo" manifest) 'yason:false
        (gethash "equilibriumVerified" manifest) 'yason:false
        (gethash "geometry" manifest) "40deg/H10/crest24/base8/domain72x24, no notch; h1/PPC2x2"
        (gethash "domainUpdate" manifest) "Volume-based cpGIMP l_i=l_i0*sqrt(detF); opt-in numerical domain, F/globalV0/history never reset; positive J required"
        (gethash "damping" manifest) "Cundall local0.75 measured preparation,0 undamped hold,0.02 undrained dynamics (Urmi2024)"
        (gethash "equilibriumCriterion" manifest) "RF<1e-4 and RK<1e-8 for>=50 consecutive post-ramp updates spanning>=1s, then>=100 undamped updates spanning>=1s ALL passing; caps60000updates/60spreparation"
        (gethash "scope" manifest) "Improved numerical trial; mesh-sensitive local softening, not exact Urmi reproduction/convergence/calibrated landslide validation")
  manifest)

(in-package :cl-mpm/framework)
(defmethod compile-scenario ((scenario (eql :urmi-damage40-proper)) (case simulation))
  (cl-mpm/scenario/urmi-damage40::compile-proper-configuration case))
(defmethod execute-scenario ((scenario (eql :urmi-damage40-proper)) (case simulation) config directory)
  (declare (ignore scenario))
  (setf cl-mpm/scenario/urmi-damage40::*proper-volume-domain* t)
  (unwind-protect
    (cl-mpm/scenario/urmi-damage40:run (simulation-material case) config directory
      :sim-type 'cl-mpm/scenario/urmi-damage40::urmi-proper-sim
      :setup-sim #'cl-mpm/scenario/urmi-damage40::proper-setup
      :dynamic-damping .02d0 :manifest-customizer #'cl-mpm/scenario/urmi-damage40::proper-manifest)
    (setf cl-mpm/scenario/urmi-damage40::*proper-volume-domain* nil)))
