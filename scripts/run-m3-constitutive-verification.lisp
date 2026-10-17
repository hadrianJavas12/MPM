;;;; Milestone M3 — Constitutive Point Verification (C-01: Model H vs C-02: Model HS)
;;;; Executes single-point / virtual-element triaxial compression stress-path tests
;;;; across the Master Plan parameter sets (Residual Soil pair & Zhan Soil Cliff pair)
;;;; plus Urmi et al. (2024) Eq. (2) exponential-linear softening comparison and
;;;; sub-increment convergence verification.
;;;;
;;;; Run via:
;;;;   windows\cl-mpm.cmd scripts\run-m3-constitutive-verification.lisp [output-dir]
(in-package :cl-user)
(require :asdf)
(ql:quickload :cl-mpm-framework :silent t)

(defpackage :cl-mpm/research/m3-verification
  (:use :cl :cl-mpm/models/mc-evolution))
(in-package :cl-mpm/research/m3-verification)

(defparameter *residual-points*
  '((0d0 0d0) (0.0068d0 27.10d0) (0.037d0 33.99d0)
    (0.10d0 27.62d0) (0.20d0 16.34d0)))

(defparameter *residual-pos0-points*
  '((0d0 20.0d0) (0.0068d0 27.10d0) (0.037d0 33.99d0)
    (0.10d0 27.62d0) (0.20d0 16.34d0)))

(defparameter *zhan-phi-points*
  '((0d0 15.0d0) (0.05d0 20.0d0) (0.20d0 13.0d0)))

(defparameter *zhan-c-points*
  '((0d0 5000d0) (0.05d0 7000d0) (0.20d0 2000d0)))

(defparameter *zhan-plateau-phi-points*
  '((0d0 20.0d0) (0.05d0 20.0d0) (0.20d0 13.0d0)))

(defparameter *zhan-plateau-c-points*
  '((0d0 7000d0) (0.05d0 7000d0) (0.20d0 2000d0)))

(defun make-triaxial-point (e nu law)
  (make-instance 'particle-mc-evolution
                 :E (float e 1d0)
                 :nu (float nu 1d0)
                 :evolution-law law
                 :kappa 0d0
                 :enable-plasticity t))

(defun initialize-isotropic-confinement (mp sigma3-pa)
  "Set initial elastic isotropic compression sigma_xx = sigma_yy = sigma_zz = -sigma3-pa."
  (let* ((e (cl-mpm/particle::mp-E mp))
         (nu (cl-mpm/particle::mp-nu mp))
         (bulk (/ e (* 3d0 (- 1d0 (* 2d0 nu)))))
         (eps-iso (- (/ (float sigma3-pa 1d0) (* 3d0 bulk))))
         (strain (cl-mpm/utils:voigt-from-list (list eps-iso eps-iso eps-iso 0d0 0d0 0d0)))
         (f (cl-mpm/particle:mp-deformation-gradient mp)))
    (dotimes (i 3)
      (dotimes (j 3)
        (setf (magicl:tref f i j) (if (= i j) 1d0 0d0))))
    (let ((tau (cl-mpm/particle:constitutive-model mp strain 1d-4)))
      (cl-mpm/utils:voigt-copy-into tau (cl-mpm/particle:mp-stress mp))
      (cl-mpm/particle::new-loadstep-mp mp)
      (values eps-iso eps-iso))))

(defun evaluate-radial-trial (mp eps-y-el-base eps-r-el-base d-eps-y d-eps-r sigma3-pa)
  "Evaluate trial strain increment (d-eps-r, d-eps-y, d-eps-r) without committing.
Returns (values (sigma_xx - (-sigma3-pa)) tau_xx tau_yy)."
  (let* ((eps-x (+ eps-r-el-base d-eps-r))
         (eps-y (+ eps-y-el-base d-eps-y))
         (eps-z (+ eps-r-el-base d-eps-r))
         (trial-strain (cl-mpm/utils:voigt-from-list (list eps-x eps-y eps-z 0d0 0d0 0d0)))
         (tau (cl-mpm/particle:constitutive-model mp trial-strain 1d-4))
         (sxx (cl-mpm/utils:varef tau 0))
         (syy (cl-mpm/utils:varef tau 1)))
    (values (+ sxx sigma3-pa) sxx syy)))

(defun step-constant-confinement (mp d-eps-y sigma3-pa)
  "Advance axial logarithmic strain by d-eps-y (< 0 for compression) while holding
radial stress sigma_xx = sigma_zz = -sigma3-pa via Illinois/secant + bisection on d-eps-r."
  (let* ((strain-committed (cl-mpm/particle:mp-strain-n mp))
         (eps-r-base (cl-mpm/utils:varef strain-committed 0))
         (eps-y-base (cl-mpm/utils:varef strain-committed 1))
         (left (* -0.05d0 (abs d-eps-y)))
         (right (* 2.5d0 (abs d-eps-y))))
    (multiple-value-bind (res-l)
        (evaluate-radial-trial mp eps-y-base eps-r-base d-eps-y left sigma3-pa)
      (multiple-value-bind (res-r)
          (evaluate-radial-trial mp eps-y-base eps-r-base d-eps-y right sigma3-pa)
        (loop repeat 12 while (>= (* res-l res-r) 0d0) do
          (setf left (* 2d0 left)
                right (* 2d0 right))
          (setf res-l (nth-value 0 (evaluate-radial-trial mp eps-y-base eps-r-base d-eps-y left sigma3-pa))
                res-r (nth-value 0 (evaluate-radial-trial mp eps-y-base eps-r-base d-eps-y right sigma3-pa))))
        (unless (< (* res-l res-r) 0d0)
          (error "Could not bracket radial strain increment for sigma3=~F Pa, d-eps-y=~E (res-l=~E, res-r=~E)"
                 sigma3-pa d-eps-y res-l res-r))
        (let ((ill-l res-l)
              (ill-r res-r)
              (last-side 0))
          (loop for iter below 40 do
            (let* ((span (- right left))
                   (secant (if (> (abs (- ill-r ill-l)) 1d-30)
                               (- left (* ill-l (/ span (- ill-r ill-l))))
                               (* 0.5d0 (+ left right))))
                   (margin (* 0.05d0 span))
                   (mid (if (and (< (mod iter 3) 2)
                                 (> secant (+ left margin))
                                 (< secant (- right margin)))
                            secant
                            (* 0.5d0 (+ left right)))))
              (multiple-value-bind (res-m)
                  (evaluate-radial-trial mp eps-y-base eps-r-base d-eps-y mid sigma3-pa)
                (when (or (<= (abs res-m) 1d-8) (<= (abs (- right left)) 1d-15))
                  (setf left mid right mid)
                  (return))
                (if (< (* res-l res-m) 0d0)
                    (progn
                      (setf right mid res-r res-m ill-r res-m)
                      (when (= last-side -1) (setf ill-l (* 0.5d0 ill-l)))
                      (setf last-side -1))
                    (progn
                      (setf left mid res-l res-m ill-l res-m)
                      (when (= last-side 1) (setf ill-r (* 0.5d0 ill-r)))
                      (setf last-side 1)))))))
        (let ((d-eps-r (* 0.5d0 (+ left right))))
          (evaluate-radial-trial mp eps-y-base eps-r-base d-eps-y d-eps-r sigma3-pa)
          (cl-mpm/utils:voigt-copy-into (cl-mpm/particle::mp-stress-kirchoff mp)
                                        (cl-mpm/particle:mp-stress mp))
          (cl-mpm/particle::new-loadstep-mp mp)
          d-eps-r)))))

(defun run-single-point-path (case-id dataset-id variant-label e nu sigma3-pa law
                              &key (max-axial-strain 0.25d0) (steps 250))
  "Integrate a single-point triaxial compression path up to MAX-AXIAL-STRAIN."
  (let* ((mp (make-triaxial-point e nu law))
         (eps-y-total 0d0)
         (eps-r-total 0d0)
         (rows nil))
    (initialize-isotropic-confinement mp sigma3-pa)
    (labels ((record-step (step eng-strain)
               (let* ((stress (cl-mpm/particle:mp-stress mp))
                      (sxx (cl-mpm/utils:varef stress 0))
                      (syy (cl-mpm/utils:varef stress 1))
                      (szz (cl-mpm/utils:varef stress 2))
                      (sigma1 (- syy))
                      (sigma3 (* -0.5d0 (+ sxx szz)))
                      (q-pa (- sigma1 sigma3))
                      (p-mean-pa (/ (+ sigma1 (* 2d0 sigma3)) 3d0))
                      (vol-strain (+ eps-y-total (* 2d0 eps-r-total)))
                      (kappa (particle-kappa mp))
                      (phi-deg (particle-phi-deg mp))
                      (c-pa (particle-cohesion mp))
                      (psi-deg (* (/ 180d0 pi) (particle-psi mp)))
                      (plastic-vol (particle-plastic-volume mp))
                      (plastic-work (particle-plastic-work mp))
                      (yield-res (particle-yield-residual-kirchhoff mp))
                      (softened (particle-softened-indicator mp)))
                 (push (list :case-id case-id
                             :dataset dataset-id
                             :variant variant-label
                             :step step
                             :sigma3-kpa (/ sigma3-pa 1000d0)
                             :axial-strain-pct (* 100d0 eng-strain)
                             :vol-strain-pct (* 100d0 vol-strain)
                             :q-kpa (/ q-pa 1000d0)
                             :p-kpa (/ p-mean-pa 1000d0)
                             :sigma1-kpa (/ sigma1 1000d0)
                             :sigma3-actual-kpa (/ sigma3 1000d0)
                             :kappa kappa
                             :phi-deg phi-deg
                             :c-kpa (/ c-pa 1000d0)
                             :psi-deg psi-deg
                             :plastic-vol-pct (* 100d0 plastic-vol)
                             :plastic-work-j-m3 plastic-work
                             :yield-residual-pa yield-res
                             :softened softened)
                       rows))))
      (record-step 0 0d0)
      (let ((prev-log 0d0))
        (loop for step from 1 to steps
              for eng = (* max-axial-strain (/ (float step 1d0) (float steps 1d0)))
              for new-log = (log (- 1d0 eng))
              for d-eps-y = (- new-log prev-log)
              for d-eps-r = (step-constant-confinement mp d-eps-y sigma3-pa) do
                (incf eps-y-total d-eps-y)
                (incf eps-r-total d-eps-r)
                (setf prev-log new-log)
                (record-step step eng)))
      (nreverse rows))))

(defun write-trajectories-csv (path all-rows)
  (ensure-directories-exist path)
  (with-open-file (stream path :direction :output :if-exists :supersede :if-does-not-exist :create)
    (format stream "case_id,dataset,variant,step,sigma3_kpa,axial_strain_pct,vol_strain_pct,q_kpa,p_kpa,sigma1_kpa,sigma3_actual_kpa,kappa,phi_deg,c_kpa,psi_deg,plastic_vol_pct,plastic_work_j_m3,yield_residual_pa,softened~%")
    (dolist (row all-rows)
      (format stream "~A,~A,~A,~D,~,4F,~,6F,~,6F,~,6F,~,6F,~,6F,~,6F,~,8F,~,6F,~,6F,~,4F,~,6F,~,6F,~,6E,~,1F~%"
              (getf row :case-id) (getf row :dataset) (getf row :variant)
              (getf row :step) (getf row :sigma3-kpa)
              (getf row :axial-strain-pct) (getf row :vol-strain-pct)
              (getf row :q-kpa) (getf row :p-kpa)
              (getf row :sigma1-kpa) (getf row :sigma3-actual-kpa)
              (getf row :kappa) (getf row :phi-deg) (getf row :c-kpa)
              (getf row :psi-deg) (getf row :plastic-vol-pct)
              (getf row :plastic-work-j-m3) (getf row :yield-residual-pa)
              (getf row :softened)))))

(defun summarize-pair (pair-id h-rows hs-rows peak-kappa)
  (let ((prepeak-max-q-diff 0d0)
        (prepeak-max-kappa-diff 0d0)
        (prepeak-steps 0)
        (postpeak-steps 0)
        (h-peak-q (reduce #'max h-rows :key (lambda (r) (getf r :q-kpa))))
        (hs-peak-q (reduce #'max hs-rows :key (lambda (r) (getf r :q-kpa))))
        (h-final (car (last h-rows)))
        (hs-final (car (last hs-rows)))
        (max-yield-res-h (reduce #'max h-rows :key (lambda (r) (getf r :yield-residual-pa))))
        (max-yield-res-hs (reduce #'max hs-rows :key (lambda (r) (getf r :yield-residual-pa)))))
    (loop for rh in h-rows
          for rhs in hs-rows
          for kh = (getf rh :kappa)
          for khs = (getf rhs :kappa) do
            (if (and (<= kh peak-kappa) (<= khs peak-kappa))
                (progn
                  (incf prepeak-steps)
                  (setf prepeak-max-q-diff (max prepeak-max-q-diff (abs (- (getf rh :q-kpa) (getf rhs :q-kpa))))
                        prepeak-max-kappa-diff (max prepeak-max-kappa-diff (abs (- kh khs)))))
                (incf postpeak-steps)))
    (assert (<= prepeak-max-q-diff 1d-7) ()
            "Pre-peak q divergence in ~A: ~E kPa" pair-id prepeak-max-q-diff)
    (assert (<= prepeak-max-kappa-diff 1d-10) ()
            "Pre-peak kappa divergence in ~A: ~E" pair-id prepeak-max-kappa-diff)
    (assert (> (getf h-final :q-kpa) (getf hs-final :q-kpa)) ()
            "Post-peak HS did not soften below H in ~A" pair-id)
    (assert (<= max-yield-res-h 1d-3) ()
            "Max yield residual exceeded tolerance in ~A H: ~E Pa" pair-id max-yield-res-h)
    (assert (<= max-yield-res-hs 1d-3) ()
            "Max yield residual exceeded tolerance in ~A HS: ~E Pa" pair-id max-yield-res-hs)
    (let ((ht (make-hash-table :test #'equal)))
      (setf (gethash "pairId" ht) pair-id
            (gethash "prepeakSteps" ht) prepeak-steps
            (gethash "postpeakSteps" ht) postpeak-steps
            (gethash "prepeakMaxQDiffKpa" ht) prepeak-max-q-diff
            (gethash "prepeakMaxKappaDiff" ht) prepeak-max-kappa-diff
            (gethash "hPeakQKpa" ht) h-peak-q
            (gethash "hsPeakQKpa" ht) hs-peak-q
            (gethash "hFinalQKpa" ht) (getf h-final :q-kpa)
            (gethash "hsFinalQKpa" ht) (getf hs-final :q-kpa)
            (gethash "postpeakDropPct" ht) (* 100d0 (/ (- (getf h-final :q-kpa) (getf hs-final :q-kpa))
                                                       (max 1d-9 (getf h-final :q-kpa))))
            (gethash "hFinalPhiDeg" ht) (getf h-final :phi-deg)
            (gethash "hsFinalPhiDeg" ht) (getf hs-final :phi-deg)
            (gethash "hFinalCKpa" ht) (getf h-final :c-kpa)
            (gethash "hsFinalCKpa" ht) (getf hs-final :c-kpa)
            (gethash "hFinalKappa" ht) (getf h-final :kappa)
            (gethash "hsFinalKappa" ht) (getf hs-final :kappa)
            (gethash "maxYieldResidualPaH" ht) max-yield-res-h
            (gethash "maxYieldResidualPaHS" ht) max-yield-res-hs)
      ht)))

(let* ((out-dir (uiop:ensure-directory-pathname
                 (or (first (cl-user::cl-mpm-script-args))
                     (cl-user::cl-mpm-path "research/constitutive-tests/"))))
       (res-law-h (make-evolution-law :variant :h :points *residual-points* :cohesion 0d0 :psi 0d0
                                      :peak-kappa 0.037d0 :strain-assumption "Residual soil raw table kappa_eq"))
       (res-law-hs (make-evolution-law :variant :hs :points *residual-points* :cohesion 0d0 :psi 0d0
                                       :peak-kappa 0.037d0 :strain-assumption "Residual soil raw table kappa_eq"))
       (res-urmi-h (make-urmi-evolution-law :variant :h :prepeak-points '((0d0 0d0) (0.0068d0 27.10d0) (0.037d0 33.99d0))
                                            :peak-kappa 0.037d0 :residual-kappa 0.20d0
                                            :phi-peak-deg 33.99d0 :phi-post-rupture-deg 27.62d0 :phi-residual-deg 16.34d0
                                            :c-peak-pa 0d0 :beta -25d0 :postpeak-segments 8))
       (res-urmi-hs (make-urmi-evolution-law :variant :hs :prepeak-points '((0d0 0d0) (0.0068d0 27.10d0) (0.037d0 33.99d0))
                                             :peak-kappa 0.037d0 :residual-kappa 0.20d0
                                             :phi-peak-deg 33.99d0 :phi-post-rupture-deg 27.62d0 :phi-residual-deg 16.34d0
                                             :c-peak-pa 0d0 :beta -25d0 :postpeak-segments 8))
       (zhan-law-h (make-evolution-law :variant :h :points *zhan-phi-points* :cohesion-points *zhan-c-points*
                                       :psi 0d0 :peak-kappa 0.05d0 :strain-assumption "Zhan cliff soil table kappa_eq"))
       (zhan-law-hs (make-evolution-law :variant :hs :points *zhan-phi-points* :cohesion-points *zhan-c-points*
                                        :psi 0d0 :peak-kappa 0.05d0 :strain-assumption "Zhan cliff soil table kappa_eq"))
       (zhan-urmi-h (make-urmi-evolution-law :variant :h :prepeak-points '((0d0 15.0d0) (0.05d0 20.0d0))
                                             :peak-kappa 0.05d0 :residual-kappa 0.20d0
                                             :phi-peak-deg 20.0d0 :phi-post-rupture-deg 16.5d0 :phi-residual-deg 13.0d0
                                             :c-peak-pa 7000d0 :c-post-rupture-pa 4500d0 :c-residual-pa 2000d0
                                             :beta -25d0 :postpeak-segments 8))
       (zhan-urmi-hs (make-urmi-evolution-law :variant :hs :prepeak-points '((0d0 15.0d0) (0.05d0 20.0d0))
                                              :peak-kappa 0.05d0 :residual-kappa 0.20d0
                                              :phi-peak-deg 20.0d0 :phi-post-rupture-deg 16.5d0 :phi-residual-deg 13.0d0
                                              :c-peak-pa 7000d0 :c-post-rupture-pa 4500d0 :c-residual-pa 2000d0
                                              :beta -25d0 :postpeak-segments 8))
       (all-rows nil)
       (summaries nil))
  (format t "~&Running M3 Constitutive Point Verification (C-01 vs C-02)...~%")
  (dolist (spec (list (list "C-RES-100" "residual_soil" "piecewise" 20d6 0.2d0 100d3 0.037d0 res-law-h res-law-hs)
                      (list "C-RES-200" "residual_soil" "piecewise" 20d6 0.2d0 200d3 0.037d0 res-law-h res-law-hs)
                      (list "C-RES-URMI-100" "residual_soil_urmi" "urmi_eq2" 20d6 0.2d0 100d3 0.037d0 res-urmi-h res-urmi-hs)
                      (list "C-RES-URMI-200" "residual_soil_urmi" "urmi_eq2" 20d6 0.2d0 200d3 0.037d0 res-urmi-h res-urmi-hs)
                      (list "C-ZHAN-50" "zhan_cliff" "piecewise" 5.25d6 0.2d0 50d3 0.05d0 zhan-law-h zhan-law-hs)
                      (list "C-ZHAN-100" "zhan_cliff" "piecewise" 5.25d6 0.2d0 100d3 0.05d0 zhan-law-h zhan-law-hs)
                      (list "C-ZHAN-URMI-50" "zhan_cliff_urmi" "urmi_eq2" 5.25d6 0.2d0 50d3 0.05d0 zhan-urmi-h zhan-urmi-hs)))
    (destructuring-bind (pair-id dataset law-tag e nu s3 peak-k law-h law-hs) spec
      (let ((rows-h (run-single-point-path (concatenate 'string pair-id "-H") dataset
                                           (concatenate 'string law-tag "_H") e nu s3 law-h))
            (rows-hs (run-single-point-path (concatenate 'string pair-id "-HS") dataset
                                            (concatenate 'string law-tag "_HS") e nu s3 law-hs)))
        (setf all-rows (append all-rows rows-h rows-hs))
        (let ((summary (summarize-pair pair-id rows-h rows-hs peak-k)))
          (push summary summaries)
          (format t "~&PASS ~A: prepeak_q_diff=~,3E kPa | H_peak=~,2F kPa, HS_peak=~,2F kPa | H_final=~,2F kPa, HS_final=~,2F kPa (-~,1F%)~%"
                  pair-id
                  (gethash "prepeakMaxQDiffKpa" summary)
                  (gethash "hPeakQKpa" summary)
                  (gethash "hsPeakQKpa" summary)
                  (gethash "hFinalQKpa" summary)
                  (gethash "hsFinalQKpa" summary)
                  (gethash "postpeakDropPct" summary))))))
  (write-trajectories-csv (merge-pathnames "c01_c02_trajectories.csv" out-dir) all-rows)
  ;; Sub-increment convergence study on C-RES-100-HS
  (let ((conv-path (merge-pathnames "c01_c02_substep_convergence.csv" out-dir))
        (conv-records nil))
    (with-open-file (stream conv-path :direction :output :if-exists :supersede :if-does-not-exist :create)
      (format stream "steps,peak_q_kpa,final_q_kpa,final_kappa,final_phi_deg,max_yield_residual_pa~%")
      (dolist (n '(125 250 500 1000))
        (let* ((rows (run-single-point-path (format nil "CONV-~D" n) "residual_soil" "HS" 20d6 0.2d0 100d3 res-law-hs :steps n))
               (peak-q (reduce #'max rows :key (lambda (r) (getf r :q-kpa))))
               (last-row (car (last rows)))
               (max-res (reduce #'max rows :key (lambda (r) (getf r :yield-residual-pa))))
               (ht (make-hash-table :test #'equal)))
          (format stream "~D,~,8F,~,8F,~,8F,~,6F,~,6E~%"
                  n peak-q (getf last-row :q-kpa) (getf last-row :kappa) (getf last-row :phi-deg) max-res)
          (setf (gethash "steps" ht) n
                (gethash "peakQKpa" ht) peak-q
                (gethash "finalQKpa" ht) (getf last-row :q-kpa)
                (gethash "finalKappa" ht) (getf last-row :kappa)
                (gethash "finalPhiDeg" ht) (getf last-row :phi-deg)
                (gethash "maxYieldResidualPa" ht) max-res)
          (push ht conv-records))))
    (let ((root (make-hash-table :test #'equal)))
      (setf (gethash "milestone" root) "M3"
            (gethash "status" root) "PASS"
            (gethash "pairs" root) (nreverse summaries)
            (gethash "substepConvergence" root) (nreverse conv-records))
      (with-open-file (stream (merge-pathnames "m3_verification_summary.json" out-dir)
                              :direction :output :if-exists :supersede :if-does-not-exist :create)
        (yason:encode root stream)
        (terpri stream))))
  (format t "~&M3 CONSTITUTIVE VERIFICATION COMPLETE: 7 pairs + substep convergence written to ~A~%" out-dir))
(uiop:quit 0)
