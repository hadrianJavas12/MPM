;;;; Linear Perzyna overstress with piecewise-linear J2 strength loss.
;;;; All stresses, strengths and viscosity refer to Kirchhoff stress: q_tau,
;;;; Y_tau [Pa], eta [Pa s]. This is not a calibrated effective-stress soil law.
(in-package :cl-mpm/models/clay-creep)

(defstruct (clay-creep-law (:constructor %make-clay-creep-law))
  (yield-peak 0d0 :type double-float :read-only t)
  (yield-residual 0d0 :type double-float :read-only t)
  (softening-kappa 0d0 :type double-float :read-only t)
  (viscosity 0d0 :type double-float :read-only t))

(defun finite-number-p (value)
  (and (realp value)
       (handler-case (and (= value value) (<= (abs value) most-positive-double-float))
         (arithmetic-error () nil))))

(defun make-clay-creep-law (&key yield-peak yield-residual softening-kappa viscosity)
  "Explicit assumed J2 q-strengths [Pa], equivalent-strain scale and eta [Pa s].
For pure shear q=sqrt(3)*abs(tau_xy), so Y=sqrt(3)*su. Phi_u=0.
No parameter is inferred from the Wang reference or from elapsed run time."
  (unless (and (every #'finite-number-p
                      (list yield-peak yield-residual softening-kappa viscosity))
               (> yield-peak 0d0) (<= 0d0 yield-residual yield-peak)
               (> softening-kappa 0d0) (> viscosity 0d0))
    (error "Invalid explicit clay creep strengths, softening strain or viscosity."))
  (%make-clay-creep-law :yield-peak (float yield-peak 1d0)
                        :yield-residual (float yield-residual 1d0)
                        :softening-kappa (float softening-kappa 1d0)
                        :viscosity (float viscosity 1d0)))

(defun clay-creep-yield (law kappa)
  "Current q_tau strength; kappa accumulates conventional equivalent vp strain."
  (unless (and (typep law 'clay-creep-law) (finite-number-p kappa) (>= kappa 0d0))
    (error "Invalid clay creep law or accumulated equivalent strain."))
  (+ (clay-creep-law-yield-residual law)
     (* (- (clay-creep-law-yield-peak law) (clay-creep-law-yield-residual law))
        (max 0d0 (- 1d0 (/ kappa (clay-creep-law-softening-kappa law)))))))

(defstruct (clay-creep-result (:constructor %make-clay-creep-result))
  tau elastic-strain plastic-increment kappa rate yield work q delta)

(defun checked-six-vector (values)
  (unless (and (typep values 'sequence) (= (length values) 6)
               (every #'finite-number-p values))
    (error "Clay creep requires six finite engineering-Voigt strain components."))
  (map 'vector (lambda (x) (float x 1d0)) values))

(defun clay-creep-update (trial-strain youngs-modulus poisson-ratio law kappa dt
                          &key (enabled t))
  "Pure backward-Euler radial integration in engineering elastic Hencky strain.
q=sqrt(3/2*s:s), kappa_dot=<q-Y(kappa)>/eta, isochoric associated J2 flow.
The residual-strength crossing is integrated algebraically, without apex clamp,
time-step cap, artificial stress correction, mass scaling or particle mutation.
WORK is the nonnegative BE increment tau_new:delta_epsilon_vp [Pa], not a
closed finite-strain mechanical-energy balance. Return owned six-vectors."
  (let* ((strain (checked-six-vector trial-strain))
         (yield-old (clay-creep-yield law kappa)))
    (unless (and (finite-number-p youngs-modulus) (> youngs-modulus 0d0)
                 (finite-number-p poisson-ratio) (< -1d0 poisson-ratio .5d0)
                 (finite-number-p dt) (>= dt 0d0))
      (error "Invalid elasticity or physical timestep in clay creep update."))
    (let* ((g (/ youngs-modulus (* 2d0 (+ 1d0 poisson-ratio))))
           (bulk (/ youngs-modulus (* 3d0 (- 1d0 (* 2d0 poisson-ratio)))))
           (hardening-loss (/ (- (clay-creep-law-yield-peak law)
                                  (clay-creep-law-yield-residual law))
                               (clay-creep-law-softening-kappa law)))
           (trace (+ (aref strain 0) (aref strain 1) (aref strain 2)))
           (mean-strain (/ trace 3d0))
           (mean-tau (* bulk trace))
           (dev (make-array 6 :element-type 'double-float :initial-element 0d0))
           (elastic (copy-seq strain))
           (tau (make-array 6 :element-type 'double-float :initial-element 0d0))
           (plastic (make-array 6 :element-type 'double-float :initial-element 0d0)))
      ;; This restriction guarantees a unique radial root on the softening branch.
      ;; Reject an unsuitable parameter set; never silently cap its softening.
      (unless (< hardening-loss (* 3d0 g))
        (error "Clay softening modulus H=~G must be less than 3G=~G."
               hardening-loss (* 3d0 g)))
      (dotimes (i 6)
        (setf (aref dev i) (if (< i 3)
                              (* 2d0 g (- (aref strain i) mean-strain))
                              (* g (aref strain i)))))
      (let* ((q-trial (sqrt (* 1.5d0
                               (loop for i below 6 sum
                                 (* (if (< i 3) 1d0 2d0) (expt (aref dev i) 2))))))
             (eta (clay-creep-law-viscosity law))
             (remaining (max 0d0 (- (clay-creep-law-softening-kappa law) kappa)))
             (delta 0d0))
        (when (and enabled (> dt 0d0) (> q-trial yield-old))
          (setf delta (/ (* dt (- q-trial yield-old))
                         (+ eta (* dt (- (* 3d0 g)
                                          (if (> remaining 0d0) hardening-loss 0d0))))))
          (when (> delta remaining)
            ;; A single step crosses the kink: the final residual branch supplies
            ;; the same backward-Euler equation, with kappa_old retained.
            (setf delta (/ (* dt (- q-trial (clay-creep-law-yield-residual law)))
                           (+ eta (* dt 3d0 g))))))
        (let* ((new-kappa (+ kappa delta))
               (new-yield (clay-creep-yield law new-kappa))
               (q-new (- q-trial (* 3d0 g delta)))
               (factor (if (> q-trial 0d0) (/ q-new q-trial) 1d0))
               (rate (if (> dt 0d0) (/ delta dt) 0d0))
               (work (* q-new delta)))
          (unless (and (every #'finite-number-p
                              (list q-trial new-kappa new-yield q-new factor rate work))
                       (>= delta 0d0) (>= new-kappa kappa) (>= q-new 0d0)
                       (<= 0d0 factor 1d0) (>= work 0d0))
            (error "Nonfinite or inadmissible clay creep radial state."))
          (dotimes (i 6)
            (setf (aref tau i) (+ (* factor (aref dev i)) (if (< i 3) mean-tau 0d0))
                  ;; Plastic engineering shears are twice tensor shears.
                  (aref plastic i) (if (> q-trial 0d0)
                                        (* delta (/ (if (< i 3) 1.5d0 3d0) q-trial)
                                           (aref dev i)) 0d0)
                  (aref elastic i) (- (aref strain i) (aref plastic i))))
          (unless (and (every #'finite-number-p tau) (every #'finite-number-p elastic)
                       (every #'finite-number-p plastic))
            (error "Nonfinite clay creep tensor reconstruction."))
          (%make-clay-creep-result
           :tau tau :elastic-strain elastic :plastic-increment plastic
           :kappa new-kappa :rate rate :yield new-yield :work work :q q-new :delta delta))))))
