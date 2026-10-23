(defpackage :cl-mpm/framework
  (:use :cl)
  (:export #:make-material #:make-geometry #:make-boundary #:make-loading
           #:make-solver #:make-simulation #:run-simulation #:validate-simulation
           #:compile-scenario #:execute-scenario #:*simulation*
           #:component #:component-kind #:component-options #:option
           #:material #:geometry #:boundary #:loading #:solver
           #:simulation #:simulation-scenario #:simulation-material
           #:simulation-geometry #:simulation-boundary #:simulation-loading
           #:simulation-solver #:simulation-parameters
           #:material-particle-class #:material-particle-initargs
           #:material-diagnostics #:specialized-material-diagnostics #:native-material-diagnostics
           #:vm-material-diagnostics #:mc-material-diagnostics #:elastic-material-diagnostics
           #:diagnostics-particle-type #:diagnostics-modes #:diagnostics-conventions
           #:diagnostics-fields #:diagnostics-legacy-values #:material-state
           #:validate-material-diagnostics #:configure-material-output
           #:validate-material-state
           #:make-particle-factory #:geometry-filter #:read-parameters #:case-path
           #:*input-root*))

(defpackage :cl-mpm/framework/cliff
  (:use :cl)
  (:import-from :cl-mpm/framework/config #:param #:describe-config)
  (:export #:make-cliff-sim #:make-joss-reference-sim #:run-joss-reference #:run))
