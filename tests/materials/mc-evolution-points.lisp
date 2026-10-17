;;;; M2 material-point and framework adapter checks for Mohr-Coulomb Hardening / Hardening-Softening.
;;;; Run via: windows\cl-mpm.cmd tests\materials\mc-evolution-points.lisp
(in-package :cl-user)
(require :asdf)
(ql:quickload :cl-mpm-framework :silent t)

(defpackage :cl-mpm/tests/mc-evolution-points
  (:use :cl :cl-mpm/models/mc-evolution))
(in-package :cl-mpm/tests/mc-evolution-points)

(defparameter *checks* 0)
(defparameter *failures* nil)
(defconstant +stress-tolerance-pa+ 1d-3)
(defconstant +strain-tolerance+ 1d-11)
(defconstant +angle-tolerance+ 1d-11)
(defconstant +test-e+ 24d6)
(defconstant +test-nu+ 0.2d0)
(defparameter +test-plane-pairs+ '((0 1) (0 2) (1 0) (1 2) (2 0) (2 1)))
(defparameter +reference-points+
  '((0d0 0d0) (0.0068d0 27.10d0) (0.037d0 33.99d0)
    (0.1d0 27.62d0) (0.2d0 16.34d0)))

(defun check-true (value control &rest arguments)
  (unless value (error (apply #'format nil control arguments))))
(defun check-close (actual expected tolerance &optional (label "value"))
  (check-true (and (realp actual) (= actual actual)
                   (<= (abs (- actual expected)) tolerance))
              "~A: expected ~,16G, actual ~,16G, tolerance ~G"
              label expected actual tolerance))
(defun check-vector (actual expected tolerance &optional (label "vector"))
  (check-true (= (length actual) (length expected)) "~A length differs" label)
  (dotimes (i (length expected))
    (check-close (elt actual i) (elt expected i) tolerance
                 (format nil "~A[~D]" label i))))
(defun signals-error-p (function)
  (handler-case (progn (funcall function) nil) (error () t)))
(defmacro point-check (name &body body)
  `(handler-case
       (progn ,@body (incf *checks*) (format t "~&PASS: ~A~%" ,name))
     (error (condition)
       (push (list ,name (princ-to-string condition)) *failures*)
       (format t "~&FAIL: ~A: ~A~%" ,name condition))))
(defun degrees (angle) (* angle (/ pi 180d0)))
(defun law (&key (variant :perfect) (phi 0d0) (psi 0d0) (cohesion 10d3)
                  (stress-measure :cauchy) points)
  (make-evolution-law :variant variant :points (or points (list (list 0d0 phi)))
                      :cohesion cohesion :psi psi :stress-measure stress-measure
                      :strain-assumption "Illustrative mapping: table coordinate is kappa_eq; no multiplier"))
(defun reference-law (variant)
  (law :variant variant :cohesion 0d0 :points (copy-tree +reference-points+)))
(defun elastic-g (&optional (e +test-e+) (nu +test-nu+)) (/ e (* 2d0 (+ 1d0 nu))))
(defun elastic-d-times (strain &optional (e +test-e+) (nu +test-nu+))
  (let* ((g (elastic-g e nu))
         (lambda (/ (* e nu) (* (+ 1d0 nu) (- 1d0 (* 2d0 nu)))))
         (trace (reduce #'+ strain)))
    (map 'vector (lambda (x) (+ (* 2d0 g x) (* lambda trace))) strain)))
(defun equivalent-increment (b)
  (let ((mean (/ (reduce #'+ b) 3d0)))
    (sqrt (* (/ 2d0 3d0) (reduce #'+ b :key (lambda (x) (expt (- x mean) 2)))))))
(defun six-residuals (tau cohesion phi j stress-measure)
  (let ((s (sin phi))
        (strength (* 2d0 (if (eq stress-measure :cauchy) j 1d0) cohesion (cos phi))))
    (map 'vector
         (lambda (pair)
           (- (* (+ 1d0 s) (elt tau (first pair)))
              (* (- 1d0 s) (elt tau (second pair))) strength))
         +test-plane-pairs+)))
(defun verify-projection (projection trial j material kappa-old
                         &optional (e +test-e+) (nu +test-nu+))
  (let* ((tau (projection-tau projection))
         (b (projection-plastic-increment projection))
         (multipliers (projection-multipliers projection))
         (kappa (projection-kappa projection))
         (residuals (six-residuals tau (projection-cohesion projection)
                                  (projection-phi projection) j
                                  (evolution-law-stress-measure material)))
         (work (loop for i below 3 sum (* (elt tau i) (elt b i))))
         (flow (make-array 3 :element-type 'double-float :initial-element 0d0))
         (correction (elastic-d-times b e nu)))
    (check-true (= (length multipliers) 6) "Expected six plane multipliers")
    (dotimes (a 6)
      (let ((multiplier (elt multipliers a)) (pair (nth a +test-plane-pairs+))
            (s (sin (projection-psi projection))))
        (check-true (>= multiplier (- +strain-tolerance+)) "Negative multiplier ~D: ~G" a multiplier)
        (incf (aref flow (first pair)) (* multiplier (+ 1d0 s)))
        (decf (aref flow (second pair)) (* multiplier (- 1d0 s)))
        (check-true (<= (aref residuals a) +stress-tolerance-pa+)
                    "Independent plane ~D residual ~G Pa is positive" a (aref residuals a))
        (when (> multiplier +strain-tolerance+)
          (check-close (aref residuals a) 0d0 +stress-tolerance-pa+ "Complementarity"))))
    (dolist (active (projection-active projection))
      (check-true (and (integerp active) (<= 0 active 5)) "Invalid active plane index")
      (check-close (aref residuals active) 0d0 +stress-tolerance-pa+ "Active plane residual"))
    (check-vector b flow +strain-tolerance+ "Flow reconstruction")
    (dotimes (i 3)
      (check-close (elt tau i) (- (elt trial i) (elt correction i))
                   +stress-tolerance-pa+ "Elastic correction"))
    (check-close kappa (+ kappa-old (equivalent-increment b)) +strain-tolerance+ "Kappa equation")
    (check-true (>= work (- +stress-tolerance-pa+)) "Negative final Kirchhoff plastic work: ~G" work)
    (check-close (projection-work projection) work +stress-tolerance-pa+ "Reported plastic work")
    (check-close (projection-max-residual projection) (reduce #'max residuals)
                 +stress-tolerance-pa+ "Reported signed maximum residual")
    (multiple-value-bind (c phi psi) (law-values material kappa)
      (check-close (projection-cohesion projection) c +stress-tolerance-pa+ "Final cohesion")
      (check-close (projection-phi projection) phi +angle-tolerance+ "Final friction")
      (check-close (projection-psi projection) psi +angle-tolerance+ "Final dilation"))
    (check-true (and (integerp (projection-iterations projection))
                     (>= (projection-iterations projection) 0)) "Invalid iteration count")
    projection))
(defun project (trial material &optional (kappa 0d0) (j 1d0))
  (verify-projection (project-principal trial +test-e+ +test-nu+ j material kappa)
                     trial j material kappa))
(defun native-values (matrix)
  (copy-seq (magicl::matrix/double-float-storage matrix)))
(defun voigt (values) (cl-mpm/utils:voigt-from-list (coerce values 'list)))
(defun native-particle (material &optional (kappa 0d0))
  (make-instance 'particle-mc-evolution :E +test-e+ :nu +test-nu+
                 :evolution-law material :kappa kappa :enable-plasticity t))
(defun compliance-voigt (tau)
  (let ((answer (make-array 6 :element-type 'double-float :initial-element 0d0)))
    (dotimes (i 3)
      (setf (aref answer i)
            (/ (- (elt tau i) (* +test-nu+ (loop for k below 3 unless (= k i) sum (elt tau k))))
               +test-e+)))
    (loop for i from 3 below 6 do (setf (aref answer i) (/ (elt tau i) (elastic-g))))
    answer))
(defun native-from-trial (mp tau)
  (let* ((strain (voigt (compliance-voigt tau))) (before (native-values strain))
         (result (cl-mpm/particle:constitutive-model mp strain 1d-4)))
    (check-vector (native-values strain) before 0d0 "External trial strain is read-only")
    (values (native-values result) strain)))
(defun identity3 ()
  (make-array '(3 3) :element-type 'double-float
                    :initial-contents '((1d0 0d0 0d0) (0d0 1d0 0d0) (0d0 0d0 1d0))))
(defun multiply3 (left right)
  (let ((answer (make-array '(3 3) :element-type 'double-float :initial-element 0d0)))
    (dotimes (i 3) (dotimes (j 3)
      (setf (aref answer i j) (loop for k below 3 sum (* (aref left i k) (aref right k j))))))
    answer))
(defun transpose3 (matrix)
  (let ((answer (identity3)))
    (dotimes (i 3) (dotimes (j 3) (setf (aref answer i j) (aref matrix j i)))) answer))
(defun test-rotation ()
  (let* ((a (degrees 37d0)) (b (degrees 23d0))
         (z (make-array '(3 3) :element-type 'double-float
                 :initial-contents (list (list (cos a) (- (sin a)) 0d0)
                                         (list (sin a) (cos a) 0d0) '(0d0 0d0 1d0))))
         (x (make-array '(3 3) :element-type 'double-float
                 :initial-contents (list '(1d0 0d0 0d0) (list 0d0 (cos b) (- (sin b)))
                                         (list 0d0 (sin b) (cos b))))))
    (multiply3 z x)))
(defun rotated-principal-voigt (principal rotation)
  (let ((diagonal (make-array '(3 3) :element-type 'double-float :initial-element 0d0)))
    (dotimes (i 3) (setf (aref diagonal i i) (elt principal i)))
    (let ((tensor (multiply3 (multiply3 rotation diagonal) (transpose3 rotation))))
      (vector (aref tensor 0 0) (aref tensor 1 1) (aref tensor 2 2)
              (aref tensor 1 2) (aref tensor 0 2) (aref tensor 0 1)))))
(defun install-f (mp entries)
  (let ((f (cl-mpm/particle:mp-deformation-gradient mp)))
    (dotimes (i 3) (dotimes (j 3) (setf (magicl:tref f i j) (aref entries i j))))) mp)
(defun freeze-state (value &optional seen)
  (cond ((or (null value) (numberp value) (symbolp value)) value)
        ((stringp value) (copy-seq value))
        ((typep value 'magicl:matrix/double-float)
         (list :matrix (copy-list (magicl:shape value)) (coerce (native-values value) 'list)))
        ((consp value) (cons (freeze-state (car value) seen) (freeze-state (cdr value) seen)))
        ((arrayp value)
         (list :array (array-dimensions value)
               (loop for i below (array-total-size value) collect (freeze-state (row-major-aref value i) seen))))
        ((or (typep value 'standard-object) (typep value 'structure-object))
         (if (member value seen :test #'eq) (list :cycle (class-name (class-of value)))
             (list (class-name (class-of value))
                   (loop for slot in (sb-mop:class-slots (class-of value))
                         for name = (sb-mop:slot-definition-name slot)
                         collect (list name (if (slot-boundp value name)
                                                (freeze-state (slot-value value name) (cons value seen))
                                                :unbound))))))
        (t (error "Unhandled state object in deep fingerprint: ~S" (type-of value)))))
(defun corrupt-particle-state (mp)
  (dolist (slot (sb-mop:class-slots (class-of mp)))
    (let ((name (sb-mop:slot-definition-name slot)))
      (when (and (slot-boundp mp name)
                 (member (symbol-name name)
                         '("STRESS" "STRESS-KIRCHOFF" "STRESS-EIGENVALUES" "STRESS-EIGENVECTORS"
                           "STRAIN" "STRAIN-N" "TRIAL-ELASTIC-STRAIN" "STRAIN-RATE" "ENG-STRAIN-RATE"
                           "VELOCITY-RATE" "VELOCITY-GRADIENT" "STRETCH-TENSOR" "STRETCH-TENSOR-FBAR"
                           "VORTICITY" "DEFORMATION-GRADIENT" "DEFORMATION-GRADIENT-0"
                           "DEFORMATION-GRADIENT-INCREMENT" "DEFORMATION-GRADIENT-INCREMENT-INVERSE"
                           "DEFORMATION-JACOBIAN-STRAIN" "DEFORMATION-GRADIENT-STRAIN-INCREMENT"
                           "DEFORMATION-GRADIENT-STRAIN-INCREMENT-INVERSE" "J-FBAR" "FBAR-J" "FBAR-J-GATHER"
                           "VOLUME" "VOLUME-N" "POSITION-TRIAL" "DISPLACEMENT-INCREMENT"
                           "PENALTY-FRICTIONAL-FORCE" "PENALTY-FRICTIONAL-FORCE-PREV"
                           "E" "NU" "ELASTIC-MATRIX" "TANGENT-STIFFNESS" "P-MODULUS" "P-MODULUS-0"
                           "SOFTENING" "STRAIN-PLASTIC" "STRAIN-PLASTIC-VM" "STRAIN-PLASTIC-VM-1"
                           "STRAIN-PLASTIC-VM-INC" "YIELD-FUNC" "PLASTIC-ITERATIONS"
                           "KAPPA" "KAPPA-COMMITTED" "COHESION" "PHI" "PSI" "PLASTIC-INCREMENT"
                           "PLASTIC-VOLUME" "PLASTIC-VOLUME-COMMITTED" "PLASTIC-WORK" "PLASTIC-WORK-COMMITTED"
                           "LAST-PROJECTION")
                         :test #'string=))
        (let ((value (slot-value mp name)))
          (cond ((typep value 'magicl:matrix/double-float)
                 (let ((storage (magicl::matrix/double-float-storage value)))
                   (dotimes (i (length storage)) (incf (aref storage i) (* 0.125d0 (1+ i))))))
                ((floatp value) (setf (slot-value mp name) (+ value 0.125d0)))
                ((integerp value) (incf (slot-value mp name) 3))
                ((typep value 'projection)
                 (dolist (array (list (projection-tau value) (projection-plastic-increment value)
                                      (projection-multipliers value)))
                   (dotimes (i (length array)) (incf (elt array i) 0.125d0)))))))))
  (setf (cl-mpm/particle::mp-enable-plasticity mp) nil)
  mp)

(format t "~&M2 MATERIAL-POINT & ADAPTER TESTS; stress tolerance ~G Pa, strain tolerance ~G.~%"
        +stress-tolerance-pa+ +strain-tolerance+)

(point-check "Law degree interpolation, endpoint clamp, and defensive source-table copy"
  (let* ((points '((0d0 0d0) (0.01d0 20d0) (0.02d0 30d0)))
         (owned (copy-tree points)) (material (law :variant :hs :cohesion 0d0 :points owned)))
    (setf (second (second owned)) 77d0)
    (dolist (pair '((0d0 0d0) (0.005d0 10d0) (0.015d0 25d0) (0.4d0 30d0)))
      (multiple-value-bind (c phi psi) (law-values material (first pair))
        (check-close c 0d0 0d0 "Zero cohesion")
        (check-close phi (degrees (second pair)) +angle-tolerance+ "Angle interpolation")
        (check-close psi 0d0 0d0 "Zero dilation")))))

(point-check "H and HS retain raw zero initialization, identical prepeak, and explicit postpeak endpoints"
  (let ((h (reference-law :h)) (hs (reference-law :hs)))
    (dolist (kappa '(0d0 0.0034d0 0.0068d0 0.02d0 0.037d0))
      (check-vector (multiple-value-list (law-values h kappa))
                    (multiple-value-list (law-values hs kappa)) +angle-tolerance+ "Shared prepeak"))
    (check-close (nth-value 1 (law-values h 0.3d0)) (degrees 33.99d0) +angle-tolerance+ "H peak plateau")
    (check-close (nth-value 1 (law-values hs 0.1d0)) (degrees 27.62d0) +angle-tolerance+ "HS middle knot")
    (check-close (nth-value 1 (law-values hs 0.3d0)) (degrees 16.34d0) +angle-tolerance+ "HS residual plateau")))

(point-check "Associated option uses the final friction angle as dilation"
  (let ((material (law :variant :hs :psi :associated :points '((0d0 20d0) (0.1d0 35d0)))))
    (multiple-value-bind (c phi psi) (law-values material 0.05d0)
      (declare (ignore c)) (check-close phi (degrees 27.5d0) +angle-tolerance+)
      (check-close psi phi 0d0 "Associated flow"))))

(point-check "Invalid laws and missing or blank strain-coordinate assumptions reject"
  (dolist (arguments
           (list (list :variant :unknown :points '((0d0 10d0)))
                 (list :points '((0d0 10d0)) :stress-measure :unknown)
                 (list :points '((0d0 10d0)) :cohesion -1d0)
                 (list :points '((0d0 -1d0))) (list :points '((0d0 90d0)))
                 (list :points '((0.1d0 10d0)))
                 (list :points '((0d0 10d0) (0d0 20d0)))
                 (list :points '((0d0 10d0) (0.1d0 20d0) (0.05d0 30d0)))
                 (list :points '((0d0 10d0)) :psi 11d0)
                 (list :points '((0d0 10d0)) :psi -1d0)))
    (check-true (signals-error-p
                 (lambda () (apply #'make-evolution-law :strain-assumption "Declared kappa_eq" arguments)))
                "Invalid law was accepted: ~S" arguments))
  (dolist (assumption (list nil "" (format nil " ~C~C " #\Tab #\Newline)))
    (check-true (signals-error-p (lambda () (make-evolution-law :variant :perfect :points '((0d0 0d0))
                                                               :strain-assumption assumption)))
                "Blank strain assumption was accepted")))

(point-check "Invalid elastic, Jacobian, and history inputs reject without modifying the trial vector"
  (let ((trial (vector -20d3 -80d3 -50d3)) (material (law)))
    (dolist (parameters '((0d0 0.2d0 1d0 0d0) (24d6 0.5d0 1d0 0d0)
                          (24d6 -1d0 1d0 0d0) (24d6 0.2d0 0d0 0d0)
                          (24d6 0.2d0 -1d0 0d0) (24d6 0.2d0 1d0 -1d0)))
      (let ((before (copy-seq trial)))
        (destructuring-bind (e nu j kappa) parameters
          (check-true (signals-error-p (lambda () (project-principal trial e nu j material kappa)))
                      "Invalid projection parameters accepted: ~S" parameters))
        (check-vector trial before 0d0 "Rejected input atomicity")))))

(point-check "Compressive hydrostat stays elastic at raw zero cohesion and friction"
  (let* ((trial (vector -100d3 -100d3 -100d3))
         (result (project trial (law :cohesion 0d0))))
    (check-vector (projection-tau result) trial 0d0)
    (check-vector (projection-plastic-increment result) #(0d0 0d0 0d0) 0d0)
    (check-close (projection-kappa result) 0d0 0d0)))

(point-check "Strictly admissible MC stress preserves all elastic state"
  (let* ((trial (vector -80d3 -100d3 -90d3)) (result (project trial (law :phi 30d0) 0.01d0)))
    (check-vector (projection-tau result) trial 0d0)
    (check-close (projection-kappa result) 0.01d0 0d0)
    (check-vector (projection-multipliers result) #(0d0 0d0 0d0 0d0 0d0 0d0) 0d0)))

(point-check "Exactly on the Tresca surface does not create a plastic increment"
  (let* ((trial (vector -40d3 -60d3 -50d3)) (result (project trial (law))))
    (check-vector (projection-tau result) trial 0d0)
    (check-close (projection-kappa result) 0d0 0d0)
    (check-vector (projection-plastic-increment result) #(0d0 0d0 0d0) 0d0)))

(point-check "Analytical Tresca face fixture and independent kappa convention"
  (let ((result (project (vector -20d3 -80d3 -50d3) (law))))
    (check-vector (projection-tau result) #(-40d3 -60d3 -50d3) +stress-tolerance-pa+)
    (check-vector (projection-plastic-increment result) #(0.001d0 -0.001d0 0d0) +strain-tolerance+)
    (check-close (projection-kappa result) (/ 0.002d0 (sqrt 3d0)) +strain-tolerance+)
    (check-close (projection-work result) 20d0 +stress-tolerance-pa+)))

(point-check "Tresca solution is invariant under all six principal-axis permutations"
  (dolist (permutation '((0 1 2) (0 2 1) (1 0 2) (1 2 0) (2 0 1) (2 1 0)))
    (let* ((trial (map 'vector (lambda (i) (elt #(-20d3 -80d3 -50d3) i)) permutation))
           (expected (map 'vector (lambda (i) (elt #(-40d3 -60d3 -50d3) i)) permutation))
           (result (project trial (law))))
      (check-vector (projection-tau result) expected +stress-tolerance-pa+ "Permuted stress"))))

(point-check "Analytical nonassociated MC face uses final six-plane consistency"
  (let* ((trial (vector -20d3 -120d3 -80d3)) (material (law :phi 30d0))
         (lambda (/ (- 30d3 (* 20d3 (cos (/ pi 6d0)))) (* 4d0 (elastic-g))))
         (expected (vector (- -20d3 (* 2d0 (elastic-g) lambda))
                           (+ -120d3 (* 2d0 (elastic-g) lambda)) -80d3))
         (result (project trial material)))
    (check-vector (projection-tau result) expected +stress-tolerance-pa+)
    (check-vector (projection-plastic-increment result) (vector lambda (- lambda) 0d0) +strain-tolerance+)
    (check-close (projection-kappa result) (* (/ 2d0 (sqrt 3d0)) lambda) +strain-tolerance+)))

(point-check "Analytical nonassociated MC edge handles repeated maximum principal stress"
  (let* ((trial (vector -20d3 -160d3 -20d3))
         (lambda (/ (- 50d3 (* 20d3 (cos (/ pi 6d0)))) (* 5d0 (elastic-g))))
         (expected (vector (- -20d3 (* 2d0 (elastic-g) lambda))
                           (+ -160d3 (* 4d0 (elastic-g) lambda))
                           (- -20d3 (* 2d0 (elastic-g) lambda))))
         (result (project trial (law :phi 30d0))))
    (check-vector (projection-tau result) expected +stress-tolerance-pa+)
    (check-vector (projection-plastic-increment result) (vector lambda (* -2d0 lambda) lambda) +strain-tolerance+)
    (check-close (projection-kappa result) (* 2d0 lambda) +strain-tolerance+)))

(point-check "Associated tensile apex has hydrostatic correction and zero equivalent shear increment"
  (let* ((material (law :phi 30d0 :psi :associated))
         (result (project (vector 20d3 20d3 20d3) material))
         (apex (/ 10d3 (tan (/ pi 6d0)))))
    (check-vector (projection-tau result) (vector apex apex apex) +stress-tolerance-pa+)
    (check-close (projection-kappa result) 0d0 +strain-tolerance+)
    (check-true (plusp (reduce #'+ (projection-plastic-increment result))) "Apex correction must dilate")))

(point-check "Cauchy cohesion scales with J while the explicit Kirchhoff-strength option does not"
  (let* ((trial (vector -20d3 -80d3 -50d3))
         (cauchy (project trial (law :stress-measure :cauchy) 0d0 1.5d0))
         (kirchhoff (project trial (law :stress-measure :kirchhoff) 0d0 1.5d0)))
    (check-vector (projection-tau cauchy) #(-35d3 -65d3 -50d3) +stress-tolerance-pa+)
    (check-vector (projection-tau kirchhoff) #(-40d3 -60d3 -50d3) +stress-tolerance-pa+)))

(point-check "H and HS coupled returns are identical while the entire increment remains prepeak"
  (let* ((trial (vector -50d3 -180d3 -90d3))
         (h (project trial (reference-law :h) 0.01d0))
         (hs (project trial (reference-law :hs) 0.01d0)))
    (check-true (< 0.01d0 (projection-kappa h) 0.037d0) "Fixture did not remain in prepeak plastic loading")
    (check-vector (projection-tau h) (projection-tau hs) +stress-tolerance-pa+)
    (check-close (projection-kappa h) (projection-kappa hs) +strain-tolerance+)
    (check-close (projection-phi h) (projection-phi hs) +angle-tolerance+)))

(point-check "Raw zero-cohesion zero-friction H and HS laws develop identical coupled prepeak strength"
  (let* ((trial (vector -50d3 -120d3 -80d3))
         (h (project trial (reference-law :h)))
         (hs (project trial (reference-law :hs))))
    (check-true (< 0d0 (projection-kappa h) 0.0068d0) "Zero-initial fixture did not enter the first hardening segment")
    (check-true (plusp (projection-phi h)) "Coupled hardening did not develop friction")
    (check-close (projection-cohesion h) 0d0 0d0)
    (check-vector (projection-tau h) (projection-tau hs) +stress-tolerance-pa+)
    (check-close (projection-kappa h) (projection-kappa hs) +strain-tolerance+)))

(point-check "Coupled hardening crosses a table knot with final rather than stale strength"
  (let* ((trial (vector -50d3 -180d3 -90d3)) (material (reference-law :h))
         (result (project trial material 0.0067d0))
         (kappa (projection-kappa result)))
    (check-true (< 0.0068d0 kappa 0.037d0) "Fixture did not cross the intended prepeak knot")
    (check-close (projection-phi result)
                 (degrees (+ 27.10d0 (* (/ (- kappa 0.0068d0) (- 0.037d0 0.0068d0))
                                         (- 33.99d0 27.10d0))))
                 +angle-tolerance+ "Independent post-knot angle")))

(point-check "H and HS postpeak returns differ only through their declared strength law"
  (let* ((trial (vector -50d3 -240d3 -90d3))
         (h (project trial (reference-law :h) 0.06d0))
         (hs (project trial (reference-law :hs) 0.06d0)))
    (check-close (projection-phi h) (degrees 33.99d0) +angle-tolerance+)
    (check-true (< (projection-phi hs) (projection-phi h)) "HS must soften after the peak")
    (check-true (> (abs (- (elt (projection-tau h) 0) (elt (projection-tau hs) 0))) 100d0)
                "Declared postpeak laws did not produce a distinct accepted stress")))

(point-check "HS never extrapolates friction below the declared residual endpoint"
  (let ((result (project (vector -50d3 -200d3 -90d3) (reference-law :hs) 0.25d0)))
    (check-true (> (projection-kappa result) 0.25d0) "Residual fixture must plastify")
    (check-close (projection-phi result) (degrees 16.34d0) +angle-tolerance+)))

(point-check "Accumulated kappa adds increment norms even when plastic tensors cancel"
  (let* ((material (law))
         (first (project (vector -20d3 -80d3 -50d3) material))
         (second (project (vector -80d3 -20d3 -50d3) material (projection-kappa first)))
         (sum (map 'vector #'+ (projection-plastic-increment first) (projection-plastic-increment second))))
    (check-vector sum #(0d0 0d0 0d0) +strain-tolerance+)
    (check-close (projection-kappa second) (/ 0.004d0 (sqrt 3d0)) +strain-tolerance+)))

(point-check "Incompatible zero-dilation tensile apex rejects with untouched projector input"
  (let* ((trial (vector 20d3 20d3 20d3)) (before (copy-seq trial)))
    (check-true (signals-error-p (lambda () (project-principal trial +test-e+ +test-nu+ 1d0 (law :phi 30d0) 0d0)))
                "Zero-dilation tensile apex was silently accepted")
    (check-vector trial before 0d0)))

(point-check "Dedicated native class preserves elastic/plastic inheritance without legacy MC inheritance"
  (let ((mp (native-particle (law))))
    (check-true (typep mp 'cl-mpm/particle::particle-elastic) "Missing native elastic contract")
    (check-true (typep mp 'cl-mpm/particle::particle-plastic) "Missing native plastic contract")
    (check-true (not (typep mp 'cl-mpm/particle::particle-mc)) "Dedicated class unexpectedly inherits legacy MC")
    (check-close (cl-mpm/particle::mp-E mp) +test-e+ 0d0)
    (check-close (cl-mpm/particle::mp-nu mp) +test-nu+ 0d0)))

(point-check "Native engineering pure shear returns tensor shear and the analytical Tresca kappa"
  (let ((mp (native-particle (law))))
    (multiple-value-bind (tau strain) (native-from-trial mp #(-50d3 -50d3 -50d3 0d0 0d0 30d3))
      (check-close (cl-mpm/utils:varef strain 5) 0.003d0 +strain-tolerance+ "Engineering gamma_xy")
      (check-vector tau #(-50d3 -50d3 -50d3 0d0 0d0 10d3) +stress-tolerance-pa+)
      (check-vector (native-values (cl-mpm/particle::mp-stress-kirchoff mp)) tau 0d0)
      (check-close (particle-kappa mp) (/ 0.002d0 (sqrt 3d0)) +strain-tolerance+)
      (check-close (cl-mpm/particle::mp-strain-plastic-vm mp) (* 1.5d0 (particle-kappa mp))
                   +strain-tolerance+ "Separate native scalar convention")
      (check-close (cl-mpm/particle::mp-strain-plastic-vm-inc mp) (* 1.5d0 (particle-kappa mp))
                   +strain-tolerance+ "Separate native increment convention")
      (check-vector (native-values (cl-mpm/particle:mp-strain mp)) (compliance-voigt tau)
                    +strain-tolerance+ "Returned elastic engineering strain"))))

(point-check "Native MC face correction is covariant under a general proper rigid rotation"
  (let* ((material (law :phi 30d0)) (rotation (test-rotation))
         (trial (vector -20d3 -120d3 -80d3)) (direct (project trial material))
         (mp (install-f (native-particle material) rotation))
         (expected (rotated-principal-voigt (projection-tau direct) rotation)))
    (multiple-value-bind (tau strain) (native-from-trial mp (rotated-principal-voigt trial rotation))
      (declare (ignore strain))
      (check-vector tau expected +stress-tolerance-pa+ "Rotated Kirchhoff stress")
      (check-close (particle-kappa mp) (projection-kappa direct) +strain-tolerance+ "Rotation-invariant kappa"))))

(point-check "Native constitutive J handling returns Kirchhoff stress exactly once"
  (let ((f (identity3)))
    (setf (aref f 0 0) 1.5d0)
    (dolist (measure '(:cauchy :kirchhoff))
      (let ((mp (install-f (native-particle (law :stress-measure measure)) f)))
        (multiple-value-bind (tau strain) (native-from-trial mp #(-20d3 -80d3 -50d3 0d0 0d0 0d0))
          (declare (ignore strain))
          (check-vector tau (if (eq measure :cauchy) #(-35d3 -65d3 -50d3 0d0 0d0 0d0)
                               #(-40d3 -60d3 -50d3 0d0 0d0 0d0)) +stress-tolerance-pa+))))))

(point-check "Rejected native apex leaves every bound state slot and external strain unchanged"
  (let ((mp (native-particle (law :phi 30d0))))
    (native-from-trial mp #(-80d3 -100d3 -90d3 0d0 0d0 0d0))
    (cl-mpm/particle::new-loadstep-mp mp)
    (let* ((before (freeze-state mp)) (strain (voigt (compliance-voigt #(20d3 20d3 20d3 0d0 0d0 0d0))))
           (input (native-values strain)))
      (check-true (signals-error-p (lambda () (cl-mpm/particle:constitutive-model mp strain 1d-4)))
                  "Native incompatible apex must fail")
      (check-true (equalp before (freeze-state mp)) "Failed native trial partially mutated particle state")
      (check-vector (native-values strain) input 0d0))))

(point-check "Snapshot and restore deeply preserve complete native and custom current/committed state"
  (let ((mp (native-particle (law))))
    (native-from-trial mp #(-20d3 -80d3 -50d3 0d0 0d0 0d0))
    (cl-mpm/particle::new-loadstep-mp mp)
    (let ((before (freeze-state mp)) (snapshot (snapshot-particle mp)))
      (corrupt-particle-state mp)
      (restore-particle mp snapshot)
      (check-true (equalp before (freeze-state mp)) "Snapshot aliases mutable current or committed state")
      (corrupt-particle-state mp)
      (restore-particle mp snapshot)
      (check-true (equalp before (freeze-state mp)) "Restore consumed or aliased the reusable snapshot"))))

(point-check "Particle-state copy deeply preserves baseline and does not alias either direction"
  (let ((source (native-particle (law))) (target (native-particle (law))))
    (native-from-trial source #(-20d3 -80d3 -50d3 0d0 0d0 0d0))
    (cl-mpm/particle::new-loadstep-mp source)
    (copy-particle-state source target)
    (let ((source-before (freeze-state source)) (target-before (freeze-state target)))
      (check-true (equalp source-before target-before) "State copy is incomplete")
      (corrupt-particle-state target)
      (check-true (equalp source-before (freeze-state source)) "Copied target aliases source")
      (copy-particle-state source target)
      (corrupt-particle-state source)
      (check-true (equalp target-before (freeze-state target)) "Copied source aliases target"))))

(point-check "Native loadstep commit/reset restores the complete accepted state after arbitrary trial mutations"
  (let ((mp (native-particle (law :phi 30d0))))
    (native-from-trial mp #(-20d3 -120d3 -80d3 0d0 0d0 0d0))
    (cl-mpm/particle::new-loadstep-mp mp)
    (let ((accepted (freeze-state mp)))
      (native-from-trial mp #(-20d3 -160d3 -20d3 0d0 0d0 0d0))
      (corrupt-particle-state mp)
      (cl-mpm/particle::reset-loadstep-mp mp)
      (check-true (equalp accepted (freeze-state mp)) "Loadstep reset does not restore full accepted state")
      (check-close (particle-kappa mp) (particle-kappa-committed mp) 0d0))))

(point-check "Repeated uncommitted native trials do not double-count committed kappa"
  (let ((mp (native-particle (law))))
    (native-from-trial mp #(-20d3 -80d3 -50d3 0d0 0d0 0d0))
    (let ((first (particle-kappa mp)))
      (native-from-trial mp #(-20d3 -80d3 -50d3 0d0 0d0 0d0))
      (check-close (particle-kappa mp) first +strain-tolerance+)
      (check-close (particle-kappa-committed mp) 0d0 0d0))))

(point-check "Sequential committed native increments accumulate kappa without tensor-history cancellation"
  (let ((mp (native-particle (law))))
    (native-from-trial mp #(-20d3 -80d3 -50d3 0d0 0d0 0d0))
    (cl-mpm/particle::new-loadstep-mp mp)
    (native-from-trial mp #(-80d3 -20d3 -50d3 0d0 0d0 0d0))
    (check-close (particle-kappa mp) (/ 0.004d0 (sqrt 3d0)) +strain-tolerance+)
    (cl-mpm/particle::new-loadstep-mp mp)
    (check-close (particle-kappa-committed mp) (particle-kappa mp) 0d0)))

(point-check "Explicit native elastic-only mode returns the full trial stress with unchanged plastic history"
  (let ((mp (native-particle (law))))
    (setf (cl-mpm/particle::mp-enable-plasticity mp) nil)
    (multiple-value-bind (tau strain) (native-from-trial mp #(-20d3 -80d3 -50d3 0d0 0d0 0d0))
      (declare (ignore strain))
      (check-vector tau #(-20d3 -80d3 -50d3 0d0 0d0 0d0) +stress-tolerance-pa+)
      (check-close (particle-kappa mp) 0d0 0d0))))

(point-check "Framework :mc-h and :mc-hs materials and diagnostics construct and validate cleanly"
  (let* ((law-h (reference-law :h))
         (law-hs (reference-law :hs))
         (mat-h (cl-mpm/framework:make-material :mc-h :youngs-modulus 20d6 :poisson-ratio 0.2d0
                                                :density 1716.1824d0 :evolution-law law-h))
         (mat-hs (cl-mpm/framework:make-material :mc-hs :youngs-modulus 20d6 :poisson-ratio 0.2d0
                                                 :density 1716.1824d0 :evolution-law law-hs))
         (diag-h (cl-mpm/framework:material-diagnostics mat-h))
         (diag-hs (cl-mpm/framework:material-diagnostics mat-hs))
         (mps-h (funcall (cl-mpm/framework:make-particle-factory mat-h)
                         nil '(0d0 0d0) '(0.01d0 0.01d0) '(1 1)
                         (lambda (x y z) (declare (ignore x y z)) t)))
         (mps-hs (funcall (cl-mpm/framework:make-particle-factory mat-hs)
                          nil '(0d0 0d0) '(0.01d0 0.01d0) '(1 1)
                          (lambda (x y z) (declare (ignore x y z)) t))))
    (check-true (typep (aref mps-h 0) 'particle-mc-evolution) "Expected particle-mc-evolution for :mc-h")
    (check-true (typep (aref mps-hs 0) 'particle-mc-evolution) "Expected particle-mc-evolution for :mc-hs")
    (cl-mpm/framework:validate-material-diagnostics diag-h mps-h "mpm")
    (cl-mpm/framework:validate-material-diagnostics diag-hs mps-hs "mpm")
    (check-true (signals-error-p
                 (lambda ()
                   (cl-mpm/framework:material-particle-initargs
                    (cl-mpm/framework:make-material :mc-h :evolution-law law-hs))))
                "Mismatched :mc-h with :hs law must reject")))

(point-check "Urmi et al. (2024) Eq. 2 exponential-linear softening law matches H prepeak and softens postpeak"
  (let* ((urmi-h (make-urmi-evolution-law
                  :variant :h
                  :prepeak-points '((0d0 0d0) (0.0068d0 27.10d0) (0.037d0 33.99d0))
                  :peak-kappa 0.037d0 :residual-kappa 0.20d0
                  :phi-peak-deg 33.99d0 :phi-post-rupture-deg 27.62d0 :phi-residual-deg 16.34d0
                  :c-peak-pa 0d0 :beta -50d0 :postpeak-segments 8))
         (urmi-hs (make-urmi-evolution-law
                   :variant :hs
                   :prepeak-points '((0d0 0d0) (0.0068d0 27.10d0) (0.037d0 33.99d0))
                   :peak-kappa 0.037d0 :residual-kappa 0.20d0
                   :phi-peak-deg 33.99d0 :phi-post-rupture-deg 27.62d0 :phi-residual-deg 16.34d0
                   :c-peak-pa 0d0 :beta -50d0 :postpeak-segments 8))
         (trial (vector -50d3 -240d3 -90d3))
         (proj-h (project trial urmi-h 0.06d0))
         (proj-hs (project trial urmi-hs 0.06d0)))
    (check-close (projection-phi proj-h) (degrees 33.99d0) +angle-tolerance+)
    (check-true (< (projection-phi proj-hs) (projection-phi proj-h)) "Urmi HS must soften postpeak")))

(if *failures*
    (progn
      (format t "~&M2 MATERIAL POINTS FAIL: ~D passed; ~D failed.~%" *checks* (length *failures*))
      (dolist (failure (reverse *failures*)) (format t "~&  ~A: ~A~%" (first failure) (second failure)))
      (uiop:quit 1))
    (progn
      (format t "~&M2 MATERIAL POINTS PASS: ~D passed; 0 failed.~%" *checks*)
      (uiop:quit 0)))
