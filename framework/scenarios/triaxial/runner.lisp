;;;; Native triaxial scenario: runner.lisp
(in-package :cl-mpm/calibration/triaxial)

(defun run-config (config output-directory &key particle-factory geometry-filter)
  "Execute one scenario with run-local measurement context. CONFIG is never mutated."
  (let* ((directory (uiop:ensure-directory-pathname output-directory))
         (mode (value config "mode" "mpm"))
         (start (get-internal-real-time)))
    (when (and (= (num config "spatialDimensions" 3) 2) (not (string= mode "mpm")))
      (error "2D plane strain is a spatial MPM mode; use dimensions3 for homogeneous/controls"))
    (when (probe-file (merge-pathnames "stress-strain.csv" directory))
      (error "Output already contains a run: ~A. Choose a fresh directory." directory))
    (ensure-directories-exist directory)
    (json-file (merge-pathnames "effective-config.json" directory) config)
    (cl-mpm/utils:set-workers (round (num config "workers" 4)))
    (when (string= mode "controls")
      (run-controls (alexandria:copy-hash-table config) directory)
      (return-from run-config t))
    (multiple-value-bind (sim offset center height diameter)
        (setup config :particle-factory particle-factory :geometry-filter geometry-filter)
      (declare (ignore diameter))
      (let ((*initial-height* height)
            (*initial-volume* (reduce #'+ (cl-mpm:sim-mps sim) :key #'cl-mpm/particle:mp-volume))
            (*pressure* (num config "cellPressurePa" 50d3)))
      (with-open-file (csv (merge-pathnames "stress-strain.csv" directory)
                           :direction :output :if-exists :supersede)
        (format csv "frame,updates,axial_strain_pct,time_s,deviatoric_stress_kpa,q_j2_kpa,axial_stress_kpa,lateral_stress_kpa,volume_m3,mass_kg,kinetic_energy_j,elastic_strain_energy_j,plastic_strain,J_mean,max_yield_excess,platen_work_j,particle_extents_axial_strain_pct,volume_drift_pct,cell_pressure_work_j~%"))
      (multiple-value-bind (data updates frame)
          (cond ((string= mode "mpm") (run-mpm sim config directory offset height))
                ((string= mode "homogeneous") (run-homogeneous sim config directory offset center height))
                (t (error "Unknown triaxial mode ~A" mode)))
        (json-file (merge-pathnames "manifest.json" directory)
                   (object "complete" t "mode" mode "nativeModel" "cl-mpm/particle::particle-vm"
                           "geometry" (if (= (num config "spatialDimensions" 3) 2)
                                          "2D plane strain rectangle; 70mm width x 140mm height defaults; unit thickness"
                                          "70mm diameter x 140mm height cylinder defaults; see config")
                           "spatialDimensions" (round (num config "spatialDimensions" 3))
                           "planeStrain" (if (= (num config "spatialDimensions" 3) 2) t 'yason:false)
                           "planeStrainConvention" "2D: F_zz=1; sigma_zz evolves constitutively; qJ2 and qtriaxial differ; not axisymmetric"
                           "stressConvention" "compression positive CSV; native tension positive Cauchy stress"
                           "axialStrainConvention" "MPM: prescribed platen engineering strain; separate measured particle-domain extent diagnostic; homogeneous: computed F_yy"
                           "plasticStrainConvention" "native sqrt(3 J2 of deviatoric plastic strain increment); 1.5 times conventional von Mises equivalent plastic strain"
                           "platenWorkConvention" (if (string= mode "mpm")
                                                       "rectified added platen force work, with cell-pressure work separate; not signed energy closure"
                                                       "signed added platen work integral V*(sigma_yy+p)*dlog(F_yy), with cell-pressure work separate")
                           "yieldConvention" "rho=sqrt(8/3)*su; q_J2_kirchhoff_yield=2su; q_J2_cauchy_yield=2su/J; triaxial projection differs in plane strain"
                           "drainage" "assumed total-stress undrained surrogate; no pore fluid or pore pressure"
                           "spatialMPM" (if (string= mode "mpm") t 'yason:false)
                           "deformationSource" (if (string= mode "mpm") (if (= (num config "spatialDimensions" 3) 2)
                                                       "native 2D plane-strain grid/particle momentum solve with full 3D constitutive state"
                                                       "native 3D grid/particle momentum solve")
                                                   "homogeneous native constitutive solve; affine F visualization")
                           "damageEnabled" 'yason:false "fbarEnabled" 'yason:false
                           "aggregationEnabled" 'yason:false "gravity" 0
                           "particleCount" (length (cl-mpm:sim-mps sim))
                           "updates" updates "lastFrame" frame
                           "wallSeconds" (/ (- (get-internal-real-time) start)
                                            (float internal-time-units-per-second 1d0))
                           "finalDeviatoricStressKpa" (first data)
                           "finalLateralStressKpa" (fourth data))))))))

(defun main (args)
  (let ((config-path (or (first args) (cl-user::cl-mpm-path "calibration/triaxial-demo.json"))))
    (run-config (with-open-file (in config-path) (yason:parse in))
                (or (second args) (cl-user::cl-mpm-path "output/triaxial-demo/")))))
