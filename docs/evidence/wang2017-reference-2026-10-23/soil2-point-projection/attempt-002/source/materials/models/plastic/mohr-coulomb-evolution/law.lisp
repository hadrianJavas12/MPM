;;;; Shared immutable-by-contract piecewise angle/cohesion laws; no curve fitting.
(in-package :cl-mpm/models/mc-evolution)

(defstruct (evolution-law (:constructor %make-evolution-law))
  variant points cohesion-points psi stress-measure strain-assumption peak-kappa)

(defun checked-table (points name predicate)
  (unless (and (listp points) points)
    (integration-fail "A nonempty table is required" name))
  (let ((previous -1d0))
    (mapcar (lambda (point)
              (unless (and (listp point) (= (length point) 2)
                           (every #'finite-real-p point)
                           (>= (first point) 0d0) (> (first point) previous)
                           (funcall predicate (second point)))
                (integration-fail "Invalid or unordered table point" name point))
              (setf previous (float (first point) 1d0))
              (list previous (float (second point) 1d0))) points)))

(defun make-evolution-law (&key (variant :hs) points (cohesion 0d0)
                               cohesion-points (psi 0d0) (stress-measure :cauchy)
                               strain-assumption (peak-kappa 0.037d0))
  (unless (member variant '(:h :hs :perfect))
    (integration-fail "Unknown evolution variant" variant))
  (unless (member stress-measure '(:cauchy :kirchhoff))
    (integration-fail "Declare Cauchy or Kirchhoff cohesion" stress-measure))
  (unless (and (stringp strain-assumption)
               (plusp (length (string-trim '(#\Space #\Tab #\Newline #\Return) strain-assumption))))
    (integration-fail "An explicit strain-coordinate assumption is required"))
  (unless (and (finite-real-p cohesion) (>= cohesion 0d0)
               (finite-real-p peak-kappa) (> peak-kappa 0d0))
    (integration-fail "Cohesion and peak coordinate are invalid" cohesion peak-kappa))
  (let* ((phi-table (checked-table points "friction degrees" (lambda (x) (and (<= 0d0 x) (< x 90d0)))))
         (c-table (if cohesion-points
                      (checked-table cohesion-points "cohesion Pa" (lambda (x) (>= x 0d0)))
                      (list (list 0d0 (float cohesion 1d0)))))
         (minimum-phi (reduce #'min phi-table :key #'second)))
    (unless (and (= (caar phi-table) 0d0) (= (caar c-table) 0d0))
      (integration-fail "Tables must explicitly start at kappa zero"))
    (unless (or (eq psi :associated)
                (and (finite-real-p psi) (<= 0d0 psi minimum-phi)))
      (integration-fail "Baseline dilation must lie between zero and every friction angle" psi))
    (when (and (eq variant :h) (> peak-kappa (first (car (last phi-table)))))
      (integration-fail "H peak coordinate is beyond its friction table" peak-kappa))
    (%make-evolution-law :variant variant :points phi-table :cohesion-points c-table
                        :psi (if (eq psi :associated) psi (float psi 1d0))
                        :stress-measure stress-measure :strain-assumption (copy-seq strain-assumption)
                        :peak-kappa (float peak-kappa 1d0))))

(defun make-urmi-evolution-law (&key (variant :hs)
                                     prepeak-points
                                     prepeak-cohesion-points
                                     (peak-kappa 0.037d0)
                                     (residual-kappa 0.20d0)
                                     (phi-peak-deg 33.99d0)
                                     (phi-post-rupture-deg 27.62d0)
                                     (phi-residual-deg 16.34d0)
                                     (c-peak-pa 0d0)
                                     (c-post-rupture-pa nil)
                                     (c-residual-pa nil)
                                     (beta -50d0)
                                     (postpeak-segments 8)
                                     (psi 0d0)
                                     (stress-measure :cauchy)
                                     strain-assumption)
  "Construct a piecewise-linear evolution-law whose post-peak branch discretizes
the combined exponential + linear strain-softening form of Urmi et al. (2024), Eq. (2):
  s(dk) = s_r + (s_pr - s_r)*(1 - dk/dk_r) + (s_p - s_pr)*exp(beta * dk / dk_r)
for dk = kappa - peak_kappa in [0, residual_kappa - peak_kappa].
For VARIANT :H, the law remains identical up to PEAK-KAPPA and clamps at peak."
  (unless (and (finite-real-p peak-kappa) (> peak-kappa 0d0)
               (finite-real-p residual-kappa) (> residual-kappa peak-kappa)
               (finite-real-p beta) (< beta 0d0)
               (integerp postpeak-segments) (>= postpeak-segments 2))
    (integration-fail "Invalid Urmi softening law parameters"
                      peak-kappa residual-kappa beta postpeak-segments))
  (let* ((dk-total (- (float residual-kappa 1d0) (float peak-kappa 1d0)))
         (c-pr (float (or c-post-rupture-pa c-peak-pa) 1d0))
         (c-res (float (or c-residual-pa c-peak-pa) 1d0))
         (c-pk (float c-peak-pa 1d0))
         (phi-pk (float phi-peak-deg 1d0))
         (phi-pr (float phi-post-rupture-deg 1d0))
         (phi-res (float phi-residual-deg 1d0))
         (base-prepeak (or prepeak-points
                           (list (list 0d0 phi-pk)
                                 (list (float peak-kappa 1d0) phi-pk))))
         (base-c-prepeak (or prepeak-cohesion-points
                             (list (list 0d0 c-pk)
                                   (list (float peak-kappa 1d0) c-pk))))
         (phi-post
           (loop for i from 1 to postpeak-segments
                 for ratio = (/ (float i 1d0) (float postpeak-segments 1d0))
                 for k = (+ (float peak-kappa 1d0) (* ratio dk-total))
                 for val = (+ phi-res
                              (* (- phi-pr phi-res) (- 1d0 ratio))
                              (* (- phi-pk phi-pr) (exp (* (float beta 1d0) ratio))))
                 collect (list k (if (= i postpeak-segments) phi-res val))))
         (c-post
           (loop for i from 1 to postpeak-segments
                 for ratio = (/ (float i 1d0) (float postpeak-segments 1d0))
                 for k = (+ (float peak-kappa 1d0) (* ratio dk-total))
                 for val = (+ c-res
                              (* (- c-pr c-res) (- 1d0 ratio))
                              (* (- c-pk c-pr) (exp (* (float beta 1d0) ratio))))
                 collect (list k (if (= i postpeak-segments) c-res val)))))
    (make-evolution-law
     :variant variant
     :points (append base-prepeak phi-post)
     :cohesion-points (append base-c-prepeak c-post)
     :psi psi
     :stress-measure stress-measure
     :peak-kappa peak-kappa
     :strain-assumption
     (or strain-assumption
         (format nil "Urmi et al. (2024) Eq. 2 exponential-linear softening (beta=~,2F, N=~D) on kappa_eq"
                 beta postpeak-segments)))))

(defun table-value (table coordinate)
  (loop for (left right) on table while right
        when (<= coordinate (first right))
          return (+ (second left)
                    (* (/ (- coordinate (first left)) (- (first right) (first left)))
                       (- (second right) (second left))))
        finally (return (second (car (last table))))))

(defun law-values (law kappa)
  (unless (and (finite-real-p kappa) (>= kappa 0d0))
    (integration-fail "Kappa must be finite and nonnegative" kappa))
  (let* ((coordinate (case (evolution-law-variant law)
                       (:perfect 0d0)
                       (:h (min kappa (evolution-law-peak-kappa law)))
                       (otherwise kappa)))
         (phi (* (/ pi 180d0) (table-value (evolution-law-points law) coordinate)))
         (psi (if (eq (evolution-law-psi law) :associated) phi
                  (* (/ pi 180d0) (evolution-law-psi law))))
         (c (table-value (evolution-law-cohesion-points law) coordinate)))
    (values c phi psi)))

(defun law-breakpoints (law)
  (if (eq (evolution-law-variant law) :perfect) (list 0d0)
      (sort (remove-duplicates
             (append (mapcar #'first (evolution-law-points law))
                     (mapcar #'first (evolution-law-cohesion-points law))
                     (when (eq (evolution-law-variant law) :h)
                       (list (evolution-law-peak-kappa law)))) :test #'=) #'<)))
