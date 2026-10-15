(asdf:defsystem "cl-mpm-framework"
  :description "Composable, headless native CL-MPM simulation recipes"
  :license "MIT"
  :depends-on ("cl-mpm" "cl-mpm/setup" "cl-mpm/damage" "cl-mpm/models/chalk"
               "cl-mpm/output" "cl-mpm/penalty" "cl-mpm/plotter" "vgplot"
               "jonathan" "yason" "alexandria" "uiop")
  :serial t
  :components
  ((:file "config/package") (:file "config/parameters") (:file "package")
   (:file "components/specifications") (:file "components/materials")
   (:file "components/geometry") (:file "simulation")
   (:file "scenarios/cliff/settings") (:file "materials/chalk")
   (:file "scenarios/cliff/geometry")
   (:file "scenarios/cliff/build") (:file "output/plotting")
   (:file "scenarios/joss/classes") (:file "scenarios/joss/statistics")
   (:file "scenarios/joss/phases") (:file "scenarios/joss/geometry")
   (:file "scenarios/joss/build") (:file "scenarios/joss/measurements")
   (:file "scenarios/joss/output") (:file "scenarios/joss/run")
   (:file "scenarios/cliff/run")
   (:file "scenarios/triaxial/package") (:file "scenarios/triaxial/config")
   (:file "scenarios/triaxial/tensors") (:file "scenarios/triaxial/material")
   (:file "scenarios/triaxial/geometry") (:file "scenarios/triaxial/boundaries")
   (:file "scenarios/triaxial/measurements") (:file "scenarios/triaxial/mpm")
   (:file "scenarios/triaxial/homogeneous") (:file "scenarios/triaxial/controls")
   (:file "scenarios/triaxial/runner")
   (:file "scenarios/triaxial/adapter") (:file "scenarios/cliff/adapter")))
