# CL-MPM Studio — custom constitutive model and Lisp export

**Experimental feature.** Studio now has a source editor, import of a local
`.lisp` file, built-in starter templates, a lexical check, and downloads of
`custom-model.lisp` and `simulation.lisp`. The browser can do all authoring
and exports **without running or uploading Lisp code**.

## Where to find it

Open Studio > **Material** > **Constitutive Model**. Choose *Custom Common
Lisp (Advanced)*, load a starter template or import a `.lisp` source file,
and edit the plain-text source field. Use **Cek Tanda Kurung** for a basic
check, **Export custom-model.lisp** to download the source, and
**Export simulation.lisp** to download the numerical configuration and
runner script.

The checker is **lexical only**; it cannot check Common Lisp symbols,
method signatures, model behaviour, dimensions, or numerical stability.
The editor does not currently provide syntax highlighting or a complete IDE.

## Extension contract

The running simulation keeps the existing CL-MPM chalk model as its base,
but custom runs instantiate the subclass `cl-mpm-studio::studio-custom-chalk`.
Define a primary CLOS method on that class:

```lisp
(in-package :cl-mpm-studio)

(defmethod cl-mpm/particle:constitutive-model
    ((mp studio-custom-chalk) strain dt)
  ;; Runs for each particle during the stress-update phase.
  ;; Delegate to the existing chalk model until your law is tested.
  (call-next-method))
```

The supplied *Delegate* template uses this pattern. The *Experimental
elastic* template demonstrates a direct linear-elastic stress update.
A different constitutive equation should only be introduced with corresponding
unit tests and calibration: the engine assumes specific stress, strain,
and particle state conventions. A custom constitutive method does **not**
automatically change the existing independent damage-evolution algorithms,
time stepping, or boundary conditions.

The runner checks for an unqualified primary method specialised on
`studio-custom-chalk` and refuses a custom run if none exists.

## Run locally (trusted files ONLY)

**WARNING: Common Lisp executes with OS-user permissions. It can read,
overwrite, and delete files and invoke system commands. This feature has
no security sandbox. Do not run untrusted files, and do not expose Studio
to a network while custom code execution is enabled.**

Code execution is disabled by default, even when the editor is visible.
On your **local Windows machine**, enable the opt-in flag in the terminal
that starts Studio:

```bat
set STUDIO_HOST=127.0.0.1
set STUDIO_ALLOW_CUSTOM_LISP=1
studio\start-studio.cmd
```

The server rejects arbitrary Lisp unless all these conditions hold:

1. `STUDIO_ALLOW_CUSTOM_LISP=1` and Studio is bound to a loopback host.
2. The selected model is `custom`.
3. The request uses same-origin JSON and explicitly confirms execution.
4. Non-empty source is at most **32 KiB** and contains no NUL bytes.

The server writes user source to `output/studio/custom-model.lisp` and
passes its explicit file path as an argument to a new SBCL child process.
Built-in models never load this file. The runner loads user code before
constructing particles and requires the expected CLOS method.

These checks are **operational safeguards, not isolation**. Imported
scripts may do anything your operating-system account can do.

## Export and reproduction

Download both files to the same directory when using a custom model:

- `custom-model.lisp` — your exact editable source;
- `simulation.lisp` — the configuration as Lisp `gethash` assignments
  plus a runner call that loads the adjacent custom model if selected.

Launch the exported `simulation.lisp` from a correctly configured
CL-MPM repository root, for example:

```bat
windows\cl-mpm.cmd path\to\simulation.lisp
```

A downloaded `.lisp` is **not** a standalone executable. It needs SBCL,
Quicklisp, CL-MPM and its runtime libraries.

## Verification boundaries

Node tests cover lexical checks, templates, export text, default-deny
behaviour, origin and content-type guards. The complete end-to-end
SBCL + custom method integration and numerical benchmark are still
necessary before production or scientific use. This workflow does not
attempt to reproduce the paper's multi-stage Joss Bay analysis.
