;;;; P1 ownership/load compatibility contracts; no spatial solver or output files.
;;;; Run each mode in a fresh native Windows process:
;;;;   windows\cl-mpm.cmd tests\material-ownership-compat.lisp
;;;;   windows\cl-mpm.cmd tests\material-ownership-compat.lisp legacy
;;;; Exit 0 means these contracts passed; it is not numerical regression acceptance.
(in-package :cl-user)

(defparameter *material-ownership-mode*
  (or (first (cl-mpm-script-args)) "normal"))
(cond
  ((string= *material-ownership-mode* "normal")
   (ql:quickload :cl-mpm-framework :silent t))
  ((string= *material-ownership-mode* "legacy")
   (ql:quickload :cl-mpm/setup :silent t)
   (assert (null (find-package :cl-mpm/framework)))
   (load (cl-mpm-path "framework/config/package.lisp"))
   (load (cl-mpm-path "framework/package.lisp"))
   (load (cl-mpm-path "framework/components/specifications.lisp"))
   (load (cl-mpm-path "framework/components/materials.lisp")))
  (t (error "Expected ownership test mode normal or legacy, got ~S."
            *material-ownership-mode*)))

(defpackage :cl-mpm/tests/material-ownership (:use :cl))
(in-package :cl-mpm/tests/material-ownership)

(defvar *checks* 0)
(defvar *failures* nil)

(defun ownership-check (name function)
  (incf *checks*)
  (handler-case
      (progn (funcall function) (format t "~&PASS: ~A~%" name))
    (error (condition)
      (push (format nil "~A: ~A" name condition) *failures*)
      (format t "~&FAIL: ~A: ~A~%" name condition))))

(defun ownership-class-state (name)
  (let ((class (find-class name)))
    (unless (sb-mop:class-finalized-p class) (sb-mop:finalize-inheritance class))
    (list name class (copy-list (sb-mop:class-precedence-list class))
          (loop for slot in (sb-mop:class-slots class)
                collect (list (sb-mop:slot-definition-name slot)
                              (copy-list (sb-mop:slot-definition-initargs slot))
                              (sb-mop:slot-definition-allocation slot)
                              (sb-mop:slot-definition-type slot))))))

(defun ownership-method-signatures (generic)
  (loop for method in (sb-mop:generic-function-methods generic)
        collect (list (copy-list (method-qualifiers method))
                      (copy-list (sb-mop:method-specializers method)))))

(defun ownership-generic-state (name)
  (let* ((generic (fdefinition name))
         (signatures (ownership-method-signatures generic)))
    (assert (= (length signatures)
               (length (remove-duplicates signatures :test #'equal))))
    (list name generic signatures)))

(defun ownership-one-particle (material)
  (let ((particles
          (funcall (cl-mpm/framework:make-particle-factory material)
                   nil '(0d0 0d0) '(0.01d0 0.01d0) '(1 1)
                   (lambda (x y z) (declare (ignore x y z)) t))))
    (assert (= (length particles) 1))
    (aref particles 0)))

(defun ownership-mc-material (plasticity)
  (cl-mpm/framework:make-material
   :native :particle-class 'cl-mpm/particle::particle-mc
   :youngs-modulus 20d6 :poisson-ratio 0.2d0 :density 1800d0
   :plasticity plasticity
   :initargs (list :phi (/ pi 6d0) :psi 0d0 :c 6d3 :softening 0d0)))

(defun ownership-point-state (material)
  "Exercise the existing positive-friction MC backend at F=I, without an MPM step."
  (let* ((mp (ownership-one-particle material))
         (strain (cl-mpm/particle:mp-strain mp)))
    (assert (eq (class-of mp) (find-class 'cl-mpm/particle::particle-mc)))
    (assert (not (typep mp 'cl-mpm/particle::particle-vm)))
    (setf (cl-mpm/utils:varef strain 0) -0.0001d0
          (cl-mpm/utils:varef strain 1) -0.01d0
          (cl-mpm/utils:varef strain 2) -0.0001d0)
    (cl-mpm/particle:constitutive-model mp strain 1d-6)
    (let ((state
            (list (coerce (cl-mpm/utils::fast-storage (cl-mpm/particle:mp-stress mp)) 'list)
                  (coerce (cl-mpm/utils::fast-storage strain) 'list)
                  (cl-mpm/particle::mp-yield-func mp)
                  (cl-mpm/particle::mp-strain-plastic-vm mp)
                  (cl-mpm/particle::mp-p-modulus-0 mp))))
      (dolist (value (append (first state) (second state) (cddr state)))
        (assert (and (realp value) (not (sb-ext:float-nan-p value))
                     (not (sb-ext:float-infinity-p value)))))
      (assert (plusp (fifth state)))
      state)))

(defun ownership-source-components (component)
  (cond ((typep component 'asdf:cl-source-file) (list component))
        ((typep component 'asdf:module)
         (mapcan #'ownership-source-components (asdf:component-children component)))))

(defun ownership-check-asdf-paths ()
  (let* ((system (asdf:find-system "cl-mpm-framework"))
         (components (ownership-source-components system)))
    (dolist (entry '(("components/base" "src/simulation/components/base.lisp")
                     ("components/material-definition" "materials/core/definition.lisp")
                     ("components/specifications" "src/simulation/components/specifications.lisp")
                     ("components/materials" "materials/adapters/native.lisp")))
      (destructuring-bind (id relative) entry
        (let* ((component (asdf:find-component system id))
               (expected (truename (cl-user::cl-mpm-path relative))))
          (assert component () "Missing compatibility component ID ~S." id)
          (assert (equal (truename (asdf:component-pathname component)) expected))
          (assert (= 1 (count expected components :test #'equal
                             :key (lambda (file) (truename (asdf:component-pathname file)))))))))
    (dolist (old '("framework/components/specifications.lisp"
                   "framework/components/materials.lisp"))
      (assert (not (find (truename (cl-user::cl-mpm-path old)) components :test #'equal
                         :key (lambda (file) (truename (asdf:component-pathname file)))))))))

(setf *checks* 0 *failures* nil)
(let* ((material (ownership-mc-material t))
       (elastic-mc (ownership-mc-material nil))
       (old-factory (cl-mpm/framework:make-particle-factory material))
       (old-material-class (class-of material))
       (classes (mapcar #'ownership-class-state
                       '(cl-mpm/framework:component cl-mpm/framework:material
                         cl-mpm/framework:simulation cl-mpm/framework:geometry
                         cl-mpm/particle:particle cl-mpm/particle::particle-elastic
                         cl-mpm/particle::particle-plastic cl-mpm/particle::particle-vm
                         cl-mpm/particle::particle-mc)))
       (generics (mapcar #'ownership-generic-state
                        '(cl-mpm/framework:component-kind cl-mpm/framework:component-options
                          cl-mpm/framework:material-particle-class
                          cl-mpm/framework:material-particle-initargs
                          cl-mpm/particle:constitutive-model)))
       (native-method
         (find-method #'cl-mpm/particle:constitutive-model nil
                      (list (find-class 'cl-mpm/particle::particle-mc)
                            (find-class t) (find-class t))))
       (backend (fdefinition 'cl-mpm/ext::constitutive-mohr-coulomb))
       (point-before nil) (elastic-before nil))
  (ownership-check "Material direct ancestry and native factories preserve distinct MC, VM and elastic identities"
   (lambda ()
     (assert (equal (mapcar #'class-name (sb-mop:class-direct-superclasses old-material-class))
                    '(cl-mpm/framework:component)))
     (assert (not (subtypep 'cl-mpm/particle::particle-mc 'cl-mpm/particle::particle-vm)))
     (dolist (kind '(:von-mises :elastic))
       (let ((mp (ownership-one-particle (cl-mpm/framework:make-material kind))))
         (assert (eq (class-of mp) (find-class 'cl-mpm/particle::particle-vm)))
         (assert (eql (cl-mpm/particle::mp-enable-plasticity mp) (eq kind :von-mises)))))
     (assert (eq (class-of (ownership-one-particle
                            (cl-mpm/framework:make-material
                             :native :particle-class 'cl-mpm/particle::particle-elastic)))
                 (find-class 'cl-mpm/particle::particle-elastic)))))
  (ownership-check "Native MC point activates plasticity and differs from its disabled control"
   (lambda ()
     (assert (fboundp 'cl-mpm/ext::CppMohrCoulomb) () "This native contract requires the existing DLL.")
     (setf point-before (ownership-point-state material)
           elastic-before (ownership-point-state elastic-mc))
     (assert (plusp (third point-before)))
     (assert (plusp (fourth point-before)))
     (assert (zerop (fourth elastic-before)))
     (assert (not (equal (first point-before) (first elastic-before))))))
  (if (string= cl-user::*material-ownership-mode* "normal")
      (ownership-check "ASDF compatibility IDs resolve exactly once to the four new owner files"
                       #'ownership-check-asdf-paths)
      (ownership-check "Legacy source loaders construct native factories without loading framework execution"
       (lambda () (assert (not (fboundp 'cl-mpm/framework:run-simulation))))))
  (ownership-check "Old source shims reload twice from another default directory without losing existing objects"
   (lambda ()
     (let ((cl-mpm/framework:*simulation* material)
           (*default-pathname-defaults* (uiop:temporary-directory)))
       (loop repeat 2 do
         (load (cl-user::cl-mpm-path "framework/components/specifications.lisp"))
         (load (cl-user::cl-mpm-path "framework/components/materials.lisp")))
       (assert (eq cl-mpm/framework:*simulation* material)))
     (assert (eq (class-of material) old-material-class))
     (let ((particles (funcall old-factory nil '(0d0 0d0) '(0.01d0 0.01d0) '(1 1)
                              (lambda (x y z) (declare (ignore x y z)) t))))
       (assert (= (length particles) 1))
       (assert (eq (class-of (aref particles 0)) (find-class 'cl-mpm/particle::particle-mc))))))
  (ownership-check "Reload preserves class objects, precedence and slot/initarg contracts"
   (lambda ()
     (dolist (before classes)
       (let ((after (ownership-class-state (first before))))
         (assert (eq (second before) (second after)))
         (assert (equal (third before) (third after)))
         (assert (equal (fourth before) (fourth after)))))))
  (ownership-check "Reload retains protocol generics without duplicate methods or changed native dispatch"
   (lambda ()
     (dolist (before generics)
       (let ((after (ownership-generic-state (first before))))
         (assert (eq (second before) (second after)))
         (assert (= (length (third before)) (length (third after))))
         (assert (null (set-exclusive-or (third before) (third after) :test #'equal)))))
     (assert (eq native-method
                 (find-method #'cl-mpm/particle:constitutive-model nil
                              (list (find-class 'cl-mpm/particle::particle-mc)
                                    (find-class t) (find-class t)))))
     (assert (eq backend (fdefinition 'cl-mpm/ext::constitutive-mohr-coulomb)))))
  (ownership-check "Native MC returned state stays exactly equal across compatibility reloads"
   (lambda ()
     (assert point-before)
     (assert (equal point-before (ownership-point-state material)))
     (assert (equal elastic-before (ownership-point-state elastic-mc))))))

(format t "~&MATERIAL OWNERSHIP COMPATIBILITY (~A): ~D passed, ~D failed.~%"
        cl-user::*material-ownership-mode* (- *checks* (length *failures*)) (length *failures*))
(when *failures* (uiop:quit 1))
(uiop:quit 0)
