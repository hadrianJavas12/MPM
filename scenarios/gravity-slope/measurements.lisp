(in-package :cl-mpm/scenario/gravity-slope)

(defstruct (reference-state (:constructor %make-reference-state))
  particles positions masses volumes upper-p mass upper-mass)

(defun capture-reference-state (sim config)
  "IDs are captured vector indices; every saved frame verifies object identity."
  (let* ((particles (copy-seq (cl-mpm:sim-mps sim)))
         (positions (map 'vector (lambda (mp) (cl-mpm/utils:vector-copy
                                               (cl-mpm/particle:mp-position mp))) particles))
         (masses (map 'vector #'cl-mpm/particle:mp-mass particles))
         (volumes (map 'vector #'cl-mpm/particle:mp-volume particles))
         (cutoff (* 2d0 (gethash "meshSize" config)))
         (upper (map 'vector (lambda (p) (and (> (component p 0) cutoff)
                                              (> (component p 1) cutoff))) positions))
         (upper-mass (loop for m across masses for selected across upper
                           when selected sum m)))
    (unless (> upper-mass 0d0) (error "No MPs in the fixed free-upper observation subset."))
    (%make-reference-state :particles particles :positions positions :masses masses
                           :volumes volumes :upper-p upper :mass (reduce #'+ masses)
                           :upper-mass upper-mass)))

(defparameter +particle-columns+
  '("frame" "time_s" "particle_id" "x_m" "y_m" "vx_m_per_s" "vy_m_per_s"
    "initial_x_m" "initial_y_m" "free_upper_reference_subset"
    "mass_kg_per_m" "volume_m3_per_m" "reference_volume_m3_per_m" "J"
    "F_00" "F_01" "F_02" "F_10" "F_11" "F_12" "F_20" "F_21" "F_22"
    "sig_xx_pa" "sig_yy_pa" "sig_zz_pa" "sig_yz_pa" "sig_xz_pa" "sig_xy_pa"
    "mc_kappa" "cohesion_pa" "friction_rad" "dilation_rad"
    "plastic_volume" "plastic_work_pa" "yield_residual_kirchhoff_pa"))

(defparameter +history-columns+
  '("frame" "time_s" "updates" "gravity_factor" "gravity_m_per_s2"
    "particle_count" "mass_kg_per_m" "mass_error_fraction" "kinetic_energy_j_per_m"
    "min_J" "max_displacement_m" "max_speed_m_per_s" "max_kappa"
    "max_yield_residual_pa" "free_residual_ratio"
    "min_x_m" "min_y_m" "max_x_m" "max_y_m"
    "min_center_domain_margin_m" "min_particle_domain_margin_m" "near_boundary_mass_fraction"
    "free_upper_count" "free_upper_mass_kg_per_m"
    "free_upper_centroid_x_m" "free_upper_centroid_y_m"
    "free_upper_mean_vx_m_per_s" "free_upper_mean_vy_m_per_s"
    "free_upper_rms_speed_m_per_s" "free_upper_velocity_coherence"
    "free_upper_moving_mass_fraction" "free_upper_downslope_moving_mass_fraction"
    "free_upper_toe_crossing_mass_fraction" "free_upper_front_x_m"))

(defun write-csv-row (stream row columns)
  (unless (= (length row) (length columns)) (error "Gravity-slope CSV column mismatch."))
  (loop for value in row for first = t then nil do
    (unless (finite-p value) (error "Nonfinite gravity-slope CSV value."))
    (unless first (write-char #\, stream))
    (if (integerp value) (format stream "~D" value) (format stream "~,16E" value)))
  (terpri stream))

(defun particle-row (mp reference index frame time)
  (let ((p (cl-mpm/particle:mp-position mp)) (v (cl-mpm/particle:mp-velocity mp))
        (p0 (aref (reference-state-positions reference) index))
        (f (cl-mpm/particle:mp-deformation-gradient mp)))
    (append
     (list frame time index (component p 0) (component p 1) (component v 0) (component v 1)
           (component p0 0) (component p0 1) (if (aref (reference-state-upper-p reference) index) 1 0)
           (cl-mpm/particle:mp-mass mp) (cl-mpm/particle:mp-volume mp)
           (aref (reference-state-volumes reference) index) (cl-mpm/fastmaths:det-3x3 f))
     (loop for row below 3 append (loop for col below 3 collect (magicl:tref f row col)))
     (loop for axis below 6 collect (component (cl-mpm/particle:mp-stress mp) axis))
     (list (cl-mpm/models/mc-evolution:particle-kappa mp)
           (cl-mpm/models/mc-evolution:particle-cohesion mp)
           (cl-mpm/models/mc-evolution:particle-phi mp)
           (cl-mpm/models/mc-evolution:particle-psi mp)
           (cl-mpm/models/mc-evolution:particle-plastic-volume mp)
           (cl-mpm/models/mc-evolution:particle-plastic-work mp)
           (cl-mpm/models/mc-evolution:particle-yield-residual-kirchhoff mp)))))

(defun measure-state (sim diagnostics reference config)
  "Raw physical observables, not an automatic landslide/scientific verdict."
  (let* ((particles (cl-mpm:sim-mps sim)) (count (length particles))
         (mass 0d0) (ke 0d0) (min-j most-positive-double-float)
         (max-disp 0d0) (max-speed 0d0) (max-kappa 0d0)
         (max-yield (- most-positive-double-float))
         (min-x most-positive-double-float) (min-y most-positive-double-float)
         (max-x (- most-positive-double-float)) (max-y (- most-positive-double-float))
         (center-margin most-positive-double-float) (domain-margin most-positive-double-float)
         (boundary-mass 0d0) (upper-count 0) (upper-x 0d0) (upper-y 0d0)
         (upper-vx 0d0) (upper-vy 0d0) (upper-speed2 0d0) (moving-mass 0d0)
         (downslope-mass 0d0) (crossing-mass 0d0) (front (- most-positive-double-float))
         (width (gethash "domainWidth" config)) (height (gethash "domainHeight" config))
         (beta (* pi (/ (gethash "slope" config) 180d0)))
         (upper-mass (reference-state-upper-mass reference)))
    (unless (= count (length (reference-state-particles reference)))
      (error "Gravity-slope particle count changed; no deletion or splitting is authorized."))
    (loop for mp across particles for id from 0 do
      (unless (eq mp (aref (reference-state-particles reference) id))
        (error "Gravity-slope particle identity/order changed at captured ID ~D." id))
      (cl-mpm/framework:validate-material-state diagnostics mp)
      (dolist (matrix (list (cl-mpm/particle:mp-position mp) (cl-mpm/particle:mp-velocity mp)
                            (cl-mpm/particle:mp-stress mp) (cl-mpm/particle:mp-strain mp)
                            (cl-mpm/particle:mp-deformation-gradient mp)
                            (cl-mpm/particle::mp-domain-size mp)))
        (unless (matrix-finite-p matrix) (error "Nonfinite native gravity-slope field.")))
      (let* ((p (cl-mpm/particle:mp-position mp)) (v (cl-mpm/particle:mp-velocity mp))
             (p0 (aref (reference-state-positions reference) id))
             (m (cl-mpm/particle:mp-mass mp)) (volume (cl-mpm/particle:mp-volume mp))
             (x (component p 0)) (y (component p 1))
             (vx (component v 0)) (vy (component v 1))
             (speed2 (loop for axis below 3 sum (expt (component v axis) 2)))
             (j (cl-mpm/fastmaths:det-3x3 (cl-mpm/particle:mp-deformation-gradient mp)))
             (domain (cl-mpm/particle::mp-domain-size mp))
             (margin (min x y (- width x) (- height y))))
        (unless (and (finite-p m) (> m 0d0) (= m (aref (reference-state-masses reference) id))
                     (finite-p volume) (> volume 0d0) (finite-p j) (> j 0d0))
          (error "Invalid J, volume or conserved mass at captured particle ID ~D." id))
        (unless (>= margin 0d0)
          (error "Particle ~D left computational domain: (~S, ~S); no deletion/clamp applied." id x y))
        (incf mass m) (incf ke (* .5d0 m speed2))
        (setf min-j (min min-j j) min-x (min min-x x) min-y (min min-y y)
              max-x (max max-x x) max-y (max max-y y)
              center-margin (min center-margin margin)
              domain-margin (min domain-margin
                                 (- x (* .5d0 (component domain 0)))
                                 (- width x (* .5d0 (component domain 0)))
                                 (- y (* .5d0 (component domain 1)))
                                 (- height y (* .5d0 (component domain 1))))
              max-speed (max max-speed (sqrt speed2))
              max-disp (max max-disp (sqrt (+ (expt (- x (component p0 0)) 2)
                                             (expt (- y (component p0 1)) 2))))
              max-kappa (max max-kappa (cl-mpm/models/mc-evolution:particle-kappa mp))
              max-yield (max max-yield (cl-mpm/models/mc-evolution:particle-yield-residual-kirchhoff mp)))
        (when (< margin (gethash "meshSize" config)) (incf boundary-mass m))
        (when (aref (reference-state-upper-p reference) id)
          (incf upper-count) (incf upper-x (* m x)) (incf upper-y (* m y))
          (incf upper-vx (* m vx)) (incf upper-vy (* m vy)) (incf upper-speed2 (* m speed2))
          (when (> (sqrt speed2) 1d-3) (incf moving-mass m))
          (when (> (- (* vx (cos beta)) (* vy (sin beta))) 1d-3) (incf downslope-mass m))
          (when (> x (gethash "toeX" config)) (incf crossing-mass m))
          (setf front (max front x)))))
    (let* ((mass-error (/ (- mass (reference-state-mass reference)) (reference-state-mass reference)))
           (mean-vx (/ upper-vx upper-mass)) (mean-vy (/ upper-vy upper-mass))
           (rms (sqrt (/ upper-speed2 upper-mass)))
           (residual (cl-mpm/scenario/slope-descent::free-residual sim))
           (stats (json-object
                   "particle_count" count "mass_kg_per_m" mass "mass_error_fraction" mass-error
                   "kinetic_energy_j_per_m" ke "min_J" min-j "max_displacement_m" max-disp
                   "max_speed_m_per_s" max-speed "max_kappa" max-kappa
                   "max_yield_residual_pa" max-yield "free_residual_ratio" residual
                   "min_x_m" min-x "min_y_m" min-y "max_x_m" max-x "max_y_m" max-y
                   "min_center_domain_margin_m" center-margin "min_particle_domain_margin_m" domain-margin
                   "near_boundary_mass_fraction" (/ boundary-mass mass)
                   "free_upper_count" upper-count "free_upper_mass_kg_per_m" upper-mass
                   "free_upper_centroid_x_m" (/ upper-x upper-mass) "free_upper_centroid_y_m" (/ upper-y upper-mass)
                   "free_upper_mean_vx_m_per_s" mean-vx "free_upper_mean_vy_m_per_s" mean-vy
                   "free_upper_rms_speed_m_per_s" rms
                   "free_upper_velocity_coherence" (if (> rms 0d0) (/ (sqrt (+ (* mean-vx mean-vx) (* mean-vy mean-vy))) rms) 0d0)
                   "free_upper_moving_mass_fraction" (/ moving-mass upper-mass)
                   "free_upper_downslope_moving_mass_fraction" (/ downslope-mass upper-mass)
                   "free_upper_toe_crossing_mass_fraction" (/ crossing-mass upper-mass)
                   "free_upper_front_x_m" front)))
      (unless (< (abs mass-error) 1d-12) (error "Gravity-slope aggregate mass conservation failed."))
      (maphash (lambda (key value) (unless (finite-p value) (error "Nonfinite statistic ~A." key))) stats)
      stats)))
