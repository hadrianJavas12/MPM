(in-package :asdf-user)

(when (find-system :asdf-system-connections)
  (asdf:oos 'asdf:load-op :asdf-system-connections))

;; Platforms without a native MPI runtime (Windows) use a serial stand-in for
;; "cl-mpm/mpi" (src/mpi/serial.lisp). Push :cl-mpm-no-mpi yourself before
;; loading this file to get the same behaviour elsewhere.
#+win32 (pushnew :cl-mpm-no-mpi *features*)

;; (defsystem "symbolic-derivation"
;;   :description "Symbolic derivation library from #TODO"
;;   :author "Aleksander Ksiazek"
;;   :serial t
;;   :components ((:file "src/core/symbolic-derivation")))

(defsystem "cl-mpm/settings"
  :components ((:file "src/settings" :pathname "src/core/settings"))
  :description "Dummy package that can be used to define settings")

(defsystem "cl-mpm/errors"
  :components ((:file "src/errors" :pathname "src/numerics/error-handling/errors"))
  :description "Package that contains the different kinds of error that are signaled")



(defsystem "cl-mpm/magicl"
  :depends-on ("magicl"
               ;; Expokit needs a Fortran-compiled shared library; it is only
               ;; used by dead code (generate-rotation-matrix), so skip it on Windows.
               (:feature (:not :win32) "magicl/ext-expokit"))
  :description "Dummy package that can be used to prune magicl dependancies, i.e. lisp only implementation")

(defsystem "cl-mpm/utils"
  :depends-on ("cl-mpm/magicl"
               "asdf-system-connections"
               "cl-mpm/errors"
               "cl-mpm/settings"
               "lparallel"
               "sb-concurrency"
               "array-operations")
  :description "MPM utility functions definitions"
  :serial t
  :components ((:file "src/utils" :pathname "src/numerics/tensors/utils")))

(defsystem "cl-mpm/fastmaths"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/utils"
               :sb-simd)
  :description "MPM fast maths operations definitions"
  :serial t
  :components ((:file "src/fastmaths" :pathname "src/numerics/fastmaths/fastmaths")))

(defsystem "cl-mpm/linear-solver"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/utils"
               "cl-mpm/fastmaths")
  :description "Iterative matrix-free linear solvers"
  :serial t
  :components ((:file "src/core/linear-solver" :pathname "src/solvers/linear-systems/linear-solver")))

(defsystem "cl-mpm/mesh"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/utils"
               "cl-mpm/fastmaths"
               "cl-mpm/shape-function")
  :description "MPM boundary conditions"
  :serial t
  :components ((:file "src/core/mesh" :pathname "src/core/mesh-base")))

(defsystem "cl-mpm/forces"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/utils"
               "cl-mpm/particle"
               "cl-mpm/mesh")
  :description "MPM forces calculations"
  :serial t
  :components ((:file "src/core/forces" :pathname "src/transfer/forces")))

(defsystem "cl-mpm/bc"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/mesh"
               )
  :description "MPM boundary conditions"
  :serial t
  :components ((:file "src/bc/bc" :pathname "src/boundaries/constraints/bc")))

(defsystem "cl-mpm/setup"
  :depends-on ("cl-mpm"
               "cl-mpm/mesh"
               "cl-mpm/bc"
               "cl-mpm/models/mc-evolution")
  :description "MPM setup system"
  :serial t
  :components ((:file "src/setup" :pathname "src/geometry/setup")))


(defsystem "cl-mpm/constitutive"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/utils"
               "cl-mpm/fastmaths")
  :description "Various constitutive models"
  :serial t
  :components ((:module "src/constitutive" :pathname "./" :serial t
    :components (
      (:file "p2-01-constitutive-package" :pathname "materials/core/constitutive-package")
      (:file "p2-02-constitutive-primitives" :pathname "src/numerics/tensors/constitutive-primitives")
      (:file "p2-03-constitutive" :pathname "materials/models/elastic/constitutive")
      (:file "p2-04-constitutive" :pathname "materials/models/fluid/constitutive")
      (:file "p2-05-constitutive" :pathname "materials/models/viscoelastic/maxwell/constitutive")
      (:file "p2-06-constitutive" :pathname "materials/models/damage/constitutive")
      (:file "p2-07-constitutive" :pathname "materials/models/viscoplastic/glen/constitutive")
      (:file "p2-08-constitutive" :pathname "materials/models/plastic/von-mises/constitutive")
      (:file "p2-09-constitutive" :pathname "materials/models/plastic/mohr-coulomb/constitutive")
      (:file "p2-10-constitutive" :pathname "materials/models/plastic/drucker-prager/constitutive")
      (:file "p2-11-secant-hardening" :pathname "materials/models/plastic/von-mises/evolution/secant-hardening")
    ))))

(defsystem "cl-mpm/particle"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/constitutive"
               "cl-mpm/ext"
               ;; "cl-mpm/damage"
               "cl-mpm/mesh")
  :description "MPM particle definitions"
  :serial t
  :components ((:module "src"
                :serial t
                :components
                ((:module "particle" :pathname "../" :serial t
                  :components (
                    (:file "p2-01-particle-base" :pathname "src/core/particle-base")
                    (:file "p2-02-particle-protocols" :pathname "src/core/particle-protocols")
                    (:file "p2-03-particle" :pathname "materials/models/elastic/particle")
                    (:file "p2-04-particle-objectivity" :pathname "src/numerics/tensors/particle-objectivity")
                    (:file "p2-05-particle" :pathname "materials/models/fluid/particle")
                    (:file "p2-06-particle" :pathname "materials/models/viscoelastic/particle")
                    (:file "p2-07-particle" :pathname "materials/models/viscoplastic/particle")
                    (:file "p2-08-particle" :pathname "materials/models/damage/particle")
                  ))
                 (:module "models"
                  :serial t
                  :components
                  (;(:file "damage")
                   (:module "plastic" :pathname "../../" :serial t
                     :components (
                       (:file "p2-01-plastic-state" :pathname "materials/core/plastic-state")
                       (:file "p2-02-finite-difference-tangent" :pathname "src/numerics/integration/finite-difference-tangent")
                       (:file "p2-03-particle" :pathname "materials/models/plastic/von-mises/particle")
                       (:file "p2-04-particle" :pathname "materials/models/plastic/mohr-coulomb/particle")
                       (:file "p2-05-particle" :pathname "materials/models/plastic/drucker-prager/particle")
                     ))
                   (:module "concrete" :pathname "../../" :serial t
                     :components (
                       (:file "p2-01-legacy" :pathname "materials/models/concrete/legacy")
                     ))
                   ;; (:file "limestone")
                   ;; (:file "ice")
                   ;(:file "chalk")
                   ))))))

(defsystem "cl-mpm/damage"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/utils"
               "cl-mpm/constitutive"
               "cl-mpm/output"
               "cl-mpm/ghost"
               "cl-mpm/aggregate"
               "cl-mpm/particle")
  :description "MPM damage mechanics"
  :serial t
  :components ((:module "src"
                :serial t
                :components
                ((:module "damage"
                  :serial t
                  :components ((:file "package")
                               (:module "softening" :pathname "../../" :serial t
                                 :components (
                                   (:file "p2-01-responses" :pathname "materials/models/damage/evolution/responses")
                                   (:file "p2-02-softening" :pathname "materials/models/concrete/evolution/softening")
                                   (:file "p2-03-softening" :pathname "materials/models/chalk/evolution/softening")
                                 ))
                               (:module "criteria" :pathname "../../" :serial t
                                 :components (
                                   (:file "p2-01-principal-strains" :pathname "src/numerics/tensors/principal-strains")
                                   (:file "p2-02-criteria" :pathname "materials/models/damage/criteria")
                                 ))
                               (:file "ekl" :pathname "nonlocal/ekl")
                               (:module "damage" :pathname "../../" :serial t
                                 :components (
                                   (:file "p2-01-damage-primitives" :pathname "src/numerics/tensors/damage-primitives")
                                   (:file "p2-02-legacy-state-evolution" :pathname "materials/models/damage/legacy-state-evolution")
                                   (:file "p2-03-legacy" :pathname "src/damage/nonlocal/legacy")
                                   (:file "p2-04-native-hooks" :pathname "materials/models/concrete/evolution/native-hooks")
                                 ))
                               (:module "delay-damage" :pathname "../../" :serial t
                                 :components (
                                   (:file "p2-01-delayed-rate" :pathname "materials/models/damage/evolution/delayed-rate")
                                   (:file "p2-02-delayed-steppers" :pathname "src/numerics/integration/delayed-steppers")
                                 ))
                               (:module "degredation" :pathname "../../" :serial t
                                 :components (
                                   (:file "p2-01-degradation" :pathname "materials/models/damage/evolution/degradation")
                                 ))
                               (:module "output" :pathname "../../" :serial t
                                 :components (
                                   (:file "p2-01-damage-output" :pathname "materials/adapters/damage-output")
                                 ))
                               (:file "solver" :pathname "solver/solver")))
                 (:module "models/damage" :pathname "../" :serial t
                   :components (
                     (:file "p2-01-damage-communication-state" :pathname "src/parallel/damage-communication-state")
                     (:file "p2-02-legacy-particles" :pathname "materials/models/damage/legacy-particles")
                   ))
                 (:module "models/damage-frictional" :pathname "../" :serial t
                   :components (
                     (:file "p2-01-legacy" :pathname "materials/models/frictional-damage/legacy")
                   ))))))
(defsystem "cl-mpm/eigenerosion"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm"
               "cl-mpm/utils"
               "cl-mpm/particle")
  :description "MPM eigenerosion damage mechanics"
  :serial t
  :components ((:file "src/eigenerosion" :pathname "src/damage/eigenerosion/eigenerosion")))

(defsystem "cl-mpm/output"
  :depends-on ("cl-mpm/magicl"
               "jonathan"
               "cl-intbytes"
               "ieee-floats"
               "cl-mpm"
               "str")
  :description "MPM output helper functions"
  :serial t
  :components ((:file "src/output" :pathname "src/output/vtk")))

(defsystem "cl-mpm/shape-function"
  :depends-on ("cl-mpm/magicl"
               ;; "symbolic-derivation"
               )
  :description "MPM shape function definitions"
  :serial t
  :components ((:file "src/core/shape-function" :pathname "src/discretization/shape-functions/shape-function")))

(defsystem "cl-mpm/dynamic-relaxation/core"
  :depends-on ("cl-mpm"
               "cl-mpm/penalty"
               "cl-mpm/setup"
               "cl-mpm/mpi"
               "cl-mpm/damage"
               "cl-mpm/aggregate"
               "swank.live"
               "vgplot"
               "cl-mpm/utils")
  :description "MPM dynamic relaxation helpers - allows for modelling quasi-static problems"
  :serial t
  :components
  ((:module "src"
    :serial t
    :components
    ((:module "dynamic-relaxation" :pathname "solvers/dynamic-relaxation"
      :serial t
      :components
      ((:file "package")
       (:file "criteria" :pathname "convergence/criteria")
       (:file "dynamic-relaxation")))))))



(defsystem "cl-mpm/dynamic-relaxation"
  :depends-on ("cl-mpm/dynamic-relaxation/core"
               "swank.live"
               "cl-mpm/implicit"
               "vgplot")
  :description "MPM dynamic relaxation helpers - allows for modelling quasi-static problems"
  :serial t
  :components
  ((:module "src"
    :serial t
    :components
    ((:module "dynamic-relaxation" :pathname "solvers/dynamic-relaxation"
      :serial t
      :components
      ((:file "solvers/quasi-static" :pathname "quasi-static/quasi-static")
       (:file "solvers/dynamic" :pathname "dynamic/dynamic")
       (:file "solvers/multigrid" :pathname "multigrid/multigrid")
       (:file "algorithms")))))))


#-cl-mpm-no-mpi
(defsystem "cl-mpm/dynamic-relaxation-mpi"
  :depends-on ("cl-mpm/dynamic-relaxation"
               "cl-mpm/mpi")
  :description "MPM implicit with MPI"
  :serial t
  :components
  ((:module "src"
    :serial t
    :components
    ((:module "dynamic-relaxation" :pathname "solvers/dynamic-relaxation"
      :serial t
      :components
      ((:file "mpi/solvers" :pathname "../../parallel/mpi/dr-solvers")
       (:file "mpi/dr" :pathname "../../parallel/mpi/dr")))))))



(defsystem "cl-mpm/ext"
  :depends-on ("cl-mpm/magicl"
               "cffi"
               "cl-mpm/utils"
               "cl-mpm/constitutive"
               "array-operations")
  :description "External libraries"
  :serial t
  :components ((:module "src/cpp" :pathname "./" :serial t
    :components (
      (:file "p2-01-cpp" :pathname "src/numerics/native-bridge/cpp")
      (:file "p2-02-legacy-transaction" :pathname "materials/backends/cpp/legacy-transaction")
    )))
  )
(defsystem "cl-mpm/core"
  :depends-on ("cl-mpm/magicl"
               "cl-mpm/fastmaths"
               "cl-mpm/ext"
               "cl-mpm/utils"
               "cl-mpm/forces"
               "cl-mpm/linear-solver"
               "alexandria"
               "serapeum"
               "local-time"
               "array-operations"
               "lparallel"
               "cl-mpm/constitutive"
               "cl-mpm/particle"
               "cl-mpm/shape-function"
               "cl-mpm/bc"
               "cl-mpm/mesh"
               "cl-mpm/ext"
               )
  :description "An explicit Material Point Method implementation"
  :in-order-to ((test-op (load-op "test/all")))
  :perform (test-op (o c) (symbol-call :test/all :test-suite))
  :serial t
  :components ((:file "src/cl-mpm" :pathname "src/core/package")
               (:file "src/core/iterate")
               (:file "src/core/domain-update" :pathname "src/discretization/domain-update/domain-update")
               (:file "src/core/stress-update")
               (:file "src/core/splitting" :pathname "src/discretization/splitting/splitting")
               (:file "src/core/p2g" :pathname "src/transfer/p2g")
               (:file "src/core/g2p" :pathname "src/transfer/g2p")
               (:file "src/core" :pathname "src/core/simulation-base")
               ))
(defsystem "cl-mpm"
  ;; :class :package-inferred-system
  :depends-on ("cl-mpm/core"
               "cl-mpm/ghost")
  :description "An explicit Material Point Method implementation"
  :in-order-to ((test-op (load-op "test/all")))
  :perform (test-op (o c) (symbol-call :test/all :test-suite))
  :serial t
  :components ((:file "src/solvers/usf" :pathname "src/solvers/explicit/usf")
               (:file "src/solvers/usl" :pathname "src/solvers/explicit/usl")
               (:file "src/solvers/musl" :pathname "src/solvers/explicit/musl")))
#+cl-mpm-no-mpi
(defsystem "cl-mpm/mpi"
  :depends-on ("cl-mpm"
               "cl-mpm/damage")
  :description "Serial stand-in for the MPI layer (no cl-mpi / MPI runtime required)"
  :components ((:file "src/mpi/serial" :pathname "src/parallel/serial/serial")))

#-cl-mpm-no-mpi
(defsystem "cl-mpm/mpi"
  :depends-on ("cl-mpm"
               "lfarm-client"
               "lfarm-server"
               "lfarm-admin"
               "cl-mpm/fastmaths"
               "cl-mpm/utils"
               "alexandria"
               "array-operations"
               "lparallel"
               "cl-intbytes"
               "ieee-floats"
               "cl-mpm/constitutive"
               "cl-mpm/particle"
               "cl-mpm/shape-function"
               "cl-mpm/bc"
               "cl-mpm/mesh"
               "cl-mpm/damage"
               "cl-mpm/setup"
               "cl-mpi"
               "cl-mpi-extensions"
               "trivial-with-current-source-form")

  :description ""
  :components ((:module "src"
                :components
                ((:module "mpi" :pathname "parallel/mpi"
                  :serial t
                  :components
                  ((:file "package")
                   (:file "serialise" :pathname "../serial/serialise")
                   (:file "domain")
                   (:file "sync")
                   (:file "mpi")
                   (:file "damage")
                   ))))
               ;; (:file "src/mpi")
               ))
(defsystem "cl-mpm/buoyancy"
  :depends-on ("cl-mpm"
               "cl-mpm/bc"
               "cl-mpm/mpi"
               )
  :description ""
  :components ((:file "src/bc/buoyancy" :pathname "src/boundaries/buoyancy/buoyancy")))

(defsystem "cl-mpm/erosion"
  :depends-on ("cl-mpm"
               "cl-mpm/bc"
               "cl-mpm/buoyancy"
               "cl-mpm/damage")
  :description "Erosion specific BCs"
  :components ((:file "src/bc/erosion" :pathname "src/boundaries/erosion/erosion")))

(defsystem "cl-mpm/penalty"
  :depends-on ("cl-mpm"
               "cl-mpm/bc")
  :description ""
  :components ((:file "src/bc/penalty" :pathname "src/boundaries/penalty/penalty")))

(defsystem "cl-mpm/ghost"
  :depends-on ("cl-mpm/core"
               "cl-mpm/bc")
  :description ""
  :components ((:file "src/ghost" :pathname "src/discretization/ghost-nodes/ghost")))

(defsystem "cl-mpm/aggregate"
  :depends-on ("cl-mpm"
               "cl-mpm/bc")
  :description ""
  :components ((:file "src/aggregate" :pathname "src/stabilization/aggregate/aggregate")))


(defsystem "cl-mpm/test"
  :depends-on ("cl-mpm"))

(defsystem "cl-mpm/example"
  :depends-on ("cl-mpm/all"
               "vgplot"
               "swank.live"
               "parse-float"
               "lisp-stat")
  :serial t
  :components ((:file "examples/core")))

(defsystem "cl-mpm/examples/bounce"
  :depends-on ("cl-mpm/all"
               "cl-mpm/example")
  :serial t
  :components ((:file "examples/bounce")))

(defsystem "cl-mpm/examples/column"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/ample/column")))

(defsystem "cl-mpm/examples/column-virtual-stress"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/virtual_stress/column-virtual-stress")))

(defsystem "cl-mpm/examples/buoyancy-virtual-stress"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/virtual_stress/buoyancy-virtual-stress")))

(defsystem "cl-mpm/examples/virtual-stress/float"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/virtual_stress/float-virtual-stress")))


(defsystem "cl-mpm/examples/virtual-stress/thick-cylinder"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/virtual_stress/thick-cylinder")))

(defsystem "cl-mpm/examples/virtual-stress/damping"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/virtual_stress/damping")))



(defsystem "cl-mpm/plotter"
  :depends-on ("cl-mpm"
               "cl-mpm/particle"
               "vgplot")
  :serial t
  :components ((:file "src/plotter" :pathname "src/output/plotting/plotter")))

(defsystem "cl-mpm/examples/fracture"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/eigenerosion"
               "vgplot"
               "swank.live"
               "cl-mpm/magicl")
  :serial t
  :components ((:file "examples/damage/fracture")))

(defsystem "cl-mpm/examples/plate-with-hole"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/eigenerosion"
               "vgplot"
               "swank.live"
               "cl-mpm/magicl")
  :serial t
  :components ((:file "examples/damage/plate-with-hole")))

(defsystem "cl-mpm/examples/slump"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/penalty"
               "cl-mpm/eigenerosion"
               "cl-mpm/damage"
               "cl-mpm/mpi"
               "cl-mpm/dynamic-relaxation"
               "cl-mpm/plotter"
               "cl-mpm/models/ice"
               "lfarm-client"
               "vgplot"
               "swank.live"
               "lisp-stat"
               "cl-mpm/magicl")
  :serial t
  :components ((:file "examples/ice/slump")))
(defsystem "cl-mpm/examples/float"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/plotter"
               "cl-mpm/models/ice"
               "vgplot"
               "swank.live"
               "cl-mpm/magicl")
  :serial t
  :components ((:file "examples/ice/float")))
(defsystem "cl-mpm/examples/flow"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/eigenerosion"
               "vgplot"
               "swank.live"
               "cl-mpm/magicl")
  :serial t
  :components ((:file "examples/ice/flow")))

(defsystem "cl-mpm/examples/beam"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/ample/beam")))

(defsystem "cl-mpm/examples/shear"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "vgplot"
               "swank.live"
               "cl-mpm/magicl")
  :serial t
  :components ((:file "examples/shear")))


(defsystem "cl-mpm/examples/creep"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/plotter"
               "cl-mpm/damage"
               "cl-mpm/eigenerosion"
               "vgplot"
               "lisp-stat"
               "swank.live"
               "cl-mpm/magicl")
  :serial t
  :components ((:file "examples/damage/creep")))

(defsystem "cl-mpm/examples/penalty/sliding"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/penalty/sliding")))

(defsystem "cl-mpm/examples/penalty/sitting"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/penalty/sitting")))



(defsystem "cl-mpm/examples/collapse"
  :depends-on ("cl-mpm"
               "cl-mpm/all"
               "vgplot"
               "cl-mpm/models/visco"
               "cl-mpm/models/chalk"
               "cl-mpm/implicit"
               "lisp-stat"
               "swank.live")
  :serial t
  :components ((:file "examples/ample/collapse")))

(defsystem "cl-mpm/examples/rotate"
  :depends-on ("cl-mpm/all"
               "vgplot"
               "swank.live")
  :serial t
  :components ((:file "examples/rotate")))



(defsystem "cl-mpm/examples/penalty-friction"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/penalty"
               "cl-mpm/damage"
               "cl-mpm/plotter"
               "vgplot"
               "swank.live")
  :serial t
  :components ((:file "examples/penalty/penalty-friction")))





(defsystem "cl-mpm/examples/chalk"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/models/chalk"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/penalty"
               "cl-mpm/damage"
               "cl-mpm/plotter"
               "cl-mpm/mpi"
               "parse-float"
               "vgplot"
               "swank.live")
  :serial t
  :components ((:file "examples/chalk/chalk")))

(defsystem "cl-mpm/examples/joss"
  :depends-on ("cl-mpm"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/erosion"
               "cl-mpm/penalty"
               "cl-mpm/damage"
               "cl-mpm/plotter"
               "cl-mpm/mpi"
               "cl-mpm/models/chalk"
               "cl-mpm/dynamic-relaxation"
               "cl-mpm/examples/chalk")
  :serial t
  :components ((:file "examples/chalk/joss")))


(defsystem "cl-mpm/examples/tpb"
  :depends-on ("cl-mpm"
               "cl-mpm/magicl"
               "lisp-stat"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/penalty"
               "cl-mpm/damage"
               "cl-mpm/plotter"
               "cl-mpm/dynamic-relaxation"
               "cl-mpm/models/limestone"
               "vgplot"
               "swank.live")
  :serial t
  :components ((:module "examples"
                :components
                ((:module "damage"
                  :components
                  ((:file "tpb")))))))

(defsystem "cl-mpm/examples/lbar"
  :depends-on ("cl-mpm"
               "cl-mpm/magicl"
               "lisp-stat"
               "cl-mpm/setup"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/penalty"
               "cl-mpm/damage"
               "cl-mpm/plotter"
               "cl-mpm/dynamic-relaxation"
               "cl-mpm/models/limestone"
               "parse-float"
               ;; "cl-mpm/models/limestone"
               "vgplot"
               "swank.live")
  :serial t
  :components ((:file "examples/damage/lbar")))
(defsystem "cl-mpm/all"
  :depends-on ("cl-mpm"
               "cl-mpm/forces"
               "cl-mpm/fastmaths"
               "cl-mpm/setup"
               "cl-mpm/bc"
               "cl-mpm/constitutive"
               "cl-mpm/particle"
               "cl-mpm/output"
               "cl-mpm/buoyancy"
               "cl-mpm/penalty"
               "cl-mpm/damage"
               "cl-mpm/plotter"
               "cl-mpm/mpi"
               "cl-mpm/dynamic-relaxation"
               "cl-mpm/ghost"))


(defsystem "cl-mpm/examples/damage/uniaxial"
  :depends-on ("cl-mpm/models/chalk"
               "cl-mpm/example")
  :serial t
  :components ((:file "examples/damage/uniaxial")))

(defsystem "cl-mpm/examples/brazilian"
  :depends-on ("cl-mpm/examples/tpb")
  :serial t
  :components ((:file "examples/damage/brazilian")))

(defsystem "cl-mpm/examples/shear-box"
  :depends-on ("cl-mpm/all"
               "parse-float"
               "lisp-stat"
               "cl-mpm/models/chalk"
               "vgplot"
               "swank.live")
  :serial t
  :components ((:file "examples/chalk/shear-box")))

(defsystem "cl-mpm/examples/erode"
  :depends-on ("cl-mpm/example")
  :components ((:file "examples/erode")))


(defsystem "cl-mpm/examples/ice-buoyancy"
  :depends-on ("cl-mpm/example"
               "cl-mpm/erosion"
               "cl-mpm/models/chalk"
               "cl-mpm/models/visco"
               "cl-mpm/models/ice"
               )
  :components ((:file "examples/ice/ice-buoyancy")))

;;; SOLVERS


;;; MODELS

(defsystem "cl-mpm/models/chalk"
  :depends-on ("cl-mpm/particle"
               ;; "cl-mpm/models/plastic"
               ;; "cl-mpm/models/damage"
               "cl-mpm/damage"
               )
  :description "MPM chalk particle definitions"
  :serial t
  :components ((:module "src/models/chalk" :pathname "./" :serial t
    :components (
      (:file "p2-01-legacy" :pathname "materials/models/chalk/legacy")
    ))))


(defsystem "cl-mpm/models/ice"
  :depends-on ("cl-mpm/particle"
               "cl-mpm/models/chalk"
               "cl-mpm/models/visco"
               "cl-mpm/damage")
  :description "MPM ice particle definitions"
  :serial t
  :components ((:module "src/models/ice" :pathname "./" :serial t
    :components (
      (:file "p2-01-legacy" :pathname "materials/models/ice/legacy")
    ))))

(defsystem "cl-mpm/models/limestone"
  :depends-on ("cl-mpm/particle"
               "cl-mpm/damage")
  :description "MPM limestone definitions"
  :serial t
  :components ((:module "src/models/limestone" :pathname "./" :serial t
    :components (
      (:file "p2-01-legacy" :pathname "materials/models/limestone/legacy")
    ))))


(defsystem "cl-mpm/models/visco"
  :depends-on ("cl-mpm"
               "cl-mpm/particle"
               "cl-mpm/ext")
  :description "MPM limestone definitions"
  :serial t
  :components ((:module "src/models/visco" :pathname "./" :serial t
    :components (
      (:file "p2-01-visco-package" :pathname "materials/core/visco-package")
      (:file "p2-02-voigt-2d" :pathname "src/numerics/tensors/voigt-2d")
      (:file "p2-03-legacy" :pathname "materials/models/viscoelastic/finite-strain/legacy")
    ))))

(defsystem "cl-mpm/models/wang2017"
  :description "Isolated Wang2017 paper tensor-history primitives; no particle adapter"
  :serial t
  :components ((:module "materials/models/plastic/wang2017"
                :pathname "materials/models/plastic/wang2017"
                :serial t
                :components ((:file "package") (:file "history") (:file "law")))))

(defsystem "cl-mpm/models/clay-creep"
  :depends-on ("cl-mpm/particle")
  :description "Experimental total-stress clay Perzyna creep with strain softening"
  :serial t
  :components ((:module "materials/models/viscoplastic/clay-creep"
                :pathname "materials/models/viscoplastic/clay-creep"
                :serial t
                :components ((:file "package") (:file "law") (:file "particle")))))

(defsystem "cl-mpm/models/mc-evolution"
  :depends-on ("cl-mpm/particle")
  :description "Dedicated evolving Mohr-Coulomb (Hardening / Hardening-Softening) model"
  :serial t
  :components ((:module "materials/models/plastic/mohr-coulomb-evolution"
                :pathname "materials/models/plastic/mohr-coulomb-evolution"
                :serial t
                :components ((:file "package")
                             (:file "law")
                             (:file "diagnostics")
                             (:file "projection")
                             (:file "state")
                             (:file "material")))))

(defsystem "cl-mpm/examples/ice-visco"
  :depends-on ("cl-mpm/example"
               "cl-mpm/erosion"
               "cl-mpm/models/chalk"
               "cl-mpm/models/visco"
               )
  :components ((:file "examples/ice/ice-visco")))


(defsystem "cl-mpm/examples/aggregate-condition"
  :depends-on ("cl-mpm/example"
               "cl-mpm/aggregate")
  :components ((:file "examples/aggregate/aggregate-condition")))


(defsystem "cl-mpm/iter-test"
  :depends-on ("coalton"
              "cl-mpm")
  :components((:file "src/core/iterate-test"))
  )

(defsystem "cl-mpm/ssa"
  :depends-on ("cl-mpm")
  :serial t
  :components ((:file "src/ssa/package" :pathname "src/formulations/ssa/package")
               (:file "src/ssa/mesh" :pathname "src/formulations/ssa/mesh")
               (:file "src/ssa/particles" :pathname "src/formulations/ssa/particles")
               (:file "src/ssa/p2g" :pathname "src/formulations/ssa/p2g")
               (:file "src/ssa/solvers" :pathname "src/formulations/ssa/solvers")))

(defsystem "cl-mpm/examples/ssa/box"
  :depends-on ("cl-mpm/example"
               "cl-mpm/ssa")
  :components ((:file "examples/ssa/box")))



(defsystem "cl-mpm/examples/penalty/billet"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/penalty/billet")))

(defsystem "cl-mpm/examples/cpt"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/cpt/cpt")))



#+(and asdf-system-connections (not cl-mpm-no-mpi))
(defsystem-connection "cl-mpm/dynamic-relaxation-mpi"
  :requires ("cl-mpm/dynamic-relaxation" "cl-mpm/mpi")
  :components ((:file "src/dynamic-relaxation/mpi/solvers" :pathname "src/parallel/mpi/dr-solvers")))


#+asdf-system-connections
(defsystem-connection "cl-mpm/dynamic-relaxation-erosion"
  :requires ("cl-mpm/dynamic-relaxation"
               "cl-mpm/erosion")
  :description "MPM DR erosions specific criteria"
  :serial t
  :components ((:file "src/dynamic-relaxation/misc/erosion" :pathname "src/boundaries/erosion/dr-erosion")))



;; #+asdf-system-connections
;; (defsystem-connection "cl-mpm/damage-mpi"
;;   :requires ("cl-mpm/dynamic-relaxation" "cl-mpm/mpi")
;;   :components ((:file "src/dynamic-relaxation/mpi")))


(defsystem "cl-mpm/implicit"
  :depends-on ("cl-mpm"
               "cl-mpm/ghost"
               "cl-mpm/aggregate"
               "cl-mpm/linear-solver"
               "cl-mpm/dynamic-relaxation/core"
               "cl-mpm/utils")
  :description "Implicit mpm test file"
  :serial t
  :components
  ((:module "src"
    :serial t
    :components
    ((:file "implicit" :pathname "solvers/implicit/implicit")))))


;;Ice stuff

(defsystem "cl-mpm/examples/ice/cliff-stability"
  :depends-on ("cl-mpm/example"
               "cl-mpm/models/chalk"
               "cl-mpm/models/visco"
               "cl-mpm/models/ice")
  :description "MPM fast maths operations definitions"
  :serial t
  :components ((:file "examples/ice/ice-cliff-stability")))

(defsystem "cl-mpm/examples/ice/creep"
  :depends-on ("cl-mpm/example"
               "cl-mpm/models/chalk"
               "cl-mpm/models/visco"
               "cl-mpm/models/ice")
  :description "Ice creeping flow test"
  :serial t
  :components ((:file "examples/ice/creep")))


;;Fbar tests
(defsystem "cl-mpm/examples/fbar/rigid-footing"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/fbar/rigid-footing")))

;; Slope stability
(defsystem "cl-mpm/examples/ice/slope-stability"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/ice/slope-stability")))


(defsystem "cl-mpm/examples/damage/biaxial"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:module "examples"
                :components
                ((:module "damage"
                  :components
                  ((:file "biaxial")))))))

(defsystem "cl-mpm/examples/damage/triaxial"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:module "examples"
                :components
                ((:module "damage"
                  :components
                  ((:file "triaxial")))))))




(defsystem "cl-mpm/examples/octree/two-squares"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/octree/two-squares")))

(defsystem "cl-mpm/examples/octree/collapse"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/octree/collapse")))

(defsystem "cl-mpm/examples/octree/column"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/octree/column")))

(defsystem "cl-mpm/examples/octree/float"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/octree/float")))

(defsystem "cl-mpm/examples/octree/slope-stability"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/octree/slope-stability")))


#+asdf-system-connections
(defsystem-connection "cl-mpm/octree-penalty"
  :requires ("cl-mpm/dynamic-relaxation" "cl-mpm/penalty")
  :components ((:file "src/solvers/octree/penalty" :pathname "src/formulations/octree/penalty")))

#+asdf-system-connections
(defsystem-connection "cl-mpm/octree-buoyancy"
  :requires ("cl-mpm/dynamic-relaxation" "cl-mpm/buoyancy")
  ;; :perform (load-op :after (op c)
  ;;                   ;; (use-package (find-package :metabang-bind)
  ;;                   ;;              (find-package :metatilities)))
  ;;                   (compile-op "src/solvers/octree/buoyancy")
  ;;                   )

  ;; :serial t
  :components ((:file "src/solvers/octree/buoyancy" :pathname "src/formulations/octree/buoyancy"))
  )


(defsystem "cl-mpm/examples/dr/collapse-mass-matrix"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/dr/collapse-mass-matrix")))


(defsystem "cl-mpm/examples/dr/quasi-time"
  :depends-on ("cl-mpm/example")
  :serial t
  :components ((:file "examples/dr/quasi-time")))

;; Optional pure point prototype; no existing system loads this or gains a particle.
(defsystem "cl-mpm/models/wang2017-point"
  :depends-on ("cl-mpm/models/wang2017" "cl-mpm/models/mc-evolution")
  :description "Experimental fixed-frame signed-tensor Wang2017 Soil2 point return; no particle adapter"
  :components ((:file "materials/models/plastic/wang2017/point-projection")))

(defsystem "cl-mpm/models/wang2017-native"
  :description "Experimental Wang Soil2 native adapter with declared incremental-polar plastic history"
  :depends-on ("cl-mpm/models/wang2017-point" "cl-mpm/models/mc-evolution")
  :serial t
  :components ((:module "materials/models/plastic/wang2017"
                :pathname "materials/models/plastic/wang2017"
                :components ((:file "native-package") (:file "transport")
                             (:file "state") (:file "material")))))

(defsystem "cl-mpm/models/wang2017-apex"
  :description "Opt-in Soil2 extension with explicit hydrostatic volumetric apex flow"
  :depends-on ("cl-mpm/models/wang2017-native")
  :serial t
  :components ((:module "materials/models/plastic/wang2017"
                :pathname "materials/models/plastic/wang2017"
                :components ((:file "apex-package") (:file "apex-projection")
                             (:file "apex-native") (:file "apex-residual-history")))))
