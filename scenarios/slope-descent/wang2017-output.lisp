;;;; Optional per-frame native Soil2 audit; existing Soil1 creates no extra files.
(in-package :cl-mpm/scenario/slope-descent)

(defstruct (wang2017-audit-context (:constructor %make-wang2017-audit-context))
  sim boundary references (next-frame 0))

(defun wang2017-audit-simulation-p (sim)
  (let ((particles (cl-mpm:sim-mps sim)))
    (flet ((wang-p (particle)
             (typep particle 'cl-mpm/models/wang2017-native:particle-wang2017-soil2)))
      (when (and (some #'wang-p particles) (not (every #'wang-p particles)))
        (error "Wang slope audit does not support silently mixed material particles."))
      (and (plusp (length particles)) (every #'wang-p particles)))))

(defun make-wang2017-audit-context (sim bc)
  "Capture loading-origin positions/contact geometry in a run-owned context."
  (when (wang2017-audit-simulation-p sim)
    (let ((references (make-hash-table :test #'eq)) (ids (make-hash-table)))
      (loop for particle across (cl-mpm:sim-mps sim) do
        (let ((id (cl-mpm/particle::mp-unique-index particle)))
          (when (gethash id ids) (error "Duplicate Wang particle ID ~S." id))
          (setf (gethash id ids) t
                (gethash particle references)
                (list :id id
                      :position (cl-mpm/utils:vector-copy (cl-mpm/particle:mp-position particle))
                      :domain (cl-mpm/utils:vector-copy (cl-mpm/particle::mp-domain-size particle))))))
      (%make-wang2017-audit-context :sim sim :boundary bc :references references))))

(defun wang2017-write-audit-csv (path headers rows first-frame-p)
  (with-open-file (stream path :direction :output
                              :if-exists (if first-frame-p :error :append)
                              :if-does-not-exist (if first-frame-p :create :error))
    (when first-frame-p (format stream "~{~A~^,~}~%" headers))
    (dolist (row rows)
      (unless (= (length row) (length headers)) (error "Wang audit CSV column mismatch."))
      (loop for value in row for first = t then nil do
        (unless first (write-char #\, stream))
        (unless (finite-p value) (error "Wang audit CSV contains a nonfinite value."))
        (if (integerp value) (format stream "~D" value) (format stream "~,16E" value)))
      (terpri stream))
    (finish-output stream)))

(defun wang2017-contact-audit-row (context bc contact frame time command)
  (let* ((particle (contact-mp contact))
         (reference (or (gethash particle (wang2017-audit-context-references context))
                        (error "Unregistered Wang contact particle.")))
         (centre (component (cl-mpm/particle:mp-position particle) 1))
         (half-height (* .5d0 (component (cl-mpm/particle::mp-domain-size particle) 1)))
         (top (+ centre half-height))
         (top-reference (contact-reference-y contact))
         (target (- top-reference command))
         (descent (- top-reference top))
         (gap (- command descent))
         (width (contact-width contact))
         (stiffness (* (strip-epsilon bc) width)))
    ;; This is the spring's geometric gap at the saved state. The force assembler
    ;; also uses a predicted-corner increment, so this row does not relabel its
    ;; energy as exact assembled-force work or a closed mechanical balance.
    (list frame time (getf reference :id) width
          (component (getf reference :position) 1)
          (* .5d0 (component (getf reference :domain) 1))
          top-reference centre half-height top target command descent gap
          stiffness (* .5d0 stiffness gap gap))))

(defun write-wang2017-frame-audit (output sim bc frame time command context)
  "Append actual material/contact observations; no-op for every non-Wang sim."
  (when (wang2017-audit-simulation-p sim)
    (unless (and (typep context 'wang2017-audit-context)
                 (eq sim (wang2017-audit-context-sim context))
                 (eq bc (wang2017-audit-context-boundary context))
                 (= frame (wang2017-audit-context-next-frame context)))
      (error "Wang audit requires its own context and sequential saved frames."))
    (let* ((diagnostics (make-instance 'cl-mpm/framework::wang2017-material-diagnostics))
           (fields (cl-mpm/framework:diagnostics-fields diagnostics))
           (material-headers
             (append '("frame" "time_s" "particle_id" "x_m" "y_m" "z_m"
                       "loading_origin_x_m" "loading_origin_y_m" "loading_origin_z_m"
                       "mass_kg_per_m" "volume_m3_per_m" "reference_volume_m3_per_m")
                     (mapcar #'first fields)))
           (material-rows
             (loop for particle across (cl-mpm:sim-mps sim)
                   for reference = (or (gethash particle (wang2017-audit-context-references context))
                                       (error "Wang particle set changed during audit."))
                   collect
                   (progn
                     (cl-mpm/framework::validate-wang2017-audit-particle particle)
                     (cl-mpm/framework:validate-material-state diagnostics particle)
                     (unless (and (> (cl-mpm/particle:mp-mass particle) 0d0)
                                  (> (cl-mpm/particle:mp-volume particle) 0d0)
                                  (> (cl-mpm/particle::mp-volume-0 particle) 0d0))
                       (error "Wang audit requires positive native mass/current/reference volume."))
                     (let ((position (cl-mpm/particle:mp-position particle))
                           (origin (getf reference :position)))
                       (append (list frame time (getf reference :id)
                                     (component position 0) (component position 1) (component position 2)
                                     (component origin 0) (component origin 1) (component origin 2)
                                     (cl-mpm/particle:mp-mass particle)
                                     (cl-mpm/particle:mp-volume particle)
                                     (cl-mpm/particle::mp-volume-0 particle))
                               (mapcar #'cdr (cl-mpm/framework:material-state diagnostics particle)))))))
           (contact-headers
             '("frame" "time_s" "particle_id" "overlap_width_m" "loading_origin_centre_y_m"
               "loading_origin_half_height_m" "reference_top_y_m" "centre_y_m" "half_height_m"
               "top_y_m" "target_top_y_m" "commanded_settlement_m" "top_surface_descent_m"
               "geometric_gap_m" "spring_stiffness_N_per_m2" "geometric_spring_energy_J_per_m"))
           (contact-rows
             (loop for contact across (strip-contacts bc)
                   collect (wang2017-contact-audit-row context bc contact frame time command))))
      (wang2017-write-audit-csv (merge-pathnames "wang2017-material-history.csv" output)
                               material-headers material-rows (zerop frame))
      (wang2017-write-audit-csv (merge-pathnames "wang2017-contact-history.csv" output)
                               contact-headers contact-rows (zerop frame))
      (incf (wang2017-audit-context-next-frame context))))
  nil)
