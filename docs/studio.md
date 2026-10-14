# CL-MPM Studio

A small web UI to configure, run and watch a 2D cliff-collapse simulation (chalk model with
delayed damage). It needs no npm packages (Node.js ≥ 18).

```bat
studio\start-studio.cmd          :: opens http://127.0.0.1:3000   (STUDIO_PORT to change)
```
The default bind address is `127.0.0.1`; `STUDIO_HOST` can override it.
Custom Lisp execution requires a loopback bind and explicit opt-in.

## How it works
```
browser (studio/public) --HTTP--> studio/server.js --spawns--> windows\cl-mpm.cmd studio\lisp\run.lisp config.json out-dir
                                        ^                              |
                                        +---- parses "Step k/N" -------+--> output/studio/{frames,vtk}
```
1. The UI sends the parameters to `POST /api/run`.
2. `server.js` validates them against `studio/schema.json` (clamping to min/max), writes
   `output/studio/config.json` and starts SBCL.
3. `studio/lisp/` (ASDF system `cl-mpm-studio`) builds the scenario, steps the simulation and writes a VTK file and a PNG per frame, printing `Step k/N`.
4. The UI polls status, logs and frames.

The same runner works without the UI:
```bat
windows\cl-mpm.cmd studio\lisp\run.lisp my.json output\run1
```
With no arguments every parameter takes its schema default.

## Parameters (`studio/schema.json`)
The schema is the single source of truth (key, default, range, unit) for both the Node server and
the Lisp runner. `studio/public/config.js` shares normalization between API runs and exports.

| Group | Settings |
| --- | --- |
| Geometry | `shelfHeight`, `shelfAspect`, `cliffSlope`, `undercut`, `notchHeight`, `notchDepth`, `notchShape`, `notchTipFraction`, `soilBoundary` |
| Discretisation | `meshSize`, `mpsPerCell` |
| Material | `constitutiveModel`, `density`, `E`, `nu`, `frictionAngle`, `cohesion`, `dilatancyAngle`, `nonlocalLength`, `ductility`, `initiationStress`, `delayTime`, `enablePlasticity`, `enableDamage` |
| Run | `maxSteps` (output frames), `substeps` (solver steps/frame), `plotMode` (stress/damage/velocity), `workers` |

The UI displays E in GPa and cohesion/initiation stress in kPa; API/export values use Pa.
See [geometry](../studio/GEOMETRY.md) and [material](../studio/MATERIAL.md).

## Custom models and export

In **Material → Constitutive Model**, choose **Custom Common Lisp**.
Import/edit a local `.lisp` file or load the delegate/elastic template.
The lexical checker understands strings, comments, character literals and
escaped symbols; it does not compile the editor source. Download both
`custom-model.lisp` and `simulation.lisp`, keeping them together for custom runs.
Exports contain all normalized settings and retain the runner's method check.

```bat
windows\cl-mpm.cmd path\to\simulation.lisp
```

These scripts need the installed CL-MPM/Quicklisp environment. Custom code has
local OS-user permissions and no sandbox. Execution is disabled by default.
For trusted local scripts only:

```bat
set STUDIO_HOST=127.0.0.1
set STUDIO_ALLOW_CUSTOM_LISP=1
studio\start-studio.cmd
```

Read [the custom-model contract](../studio/CUSTOM_MODELS.md),
[testing](testing.md), and [AI handover](AI_HANDOVER.md).
The preview and stress-interface checks do not establish scientific validity
or reproduce the complete Joss Bay collapse procedure.

## Output (`output/studio/`)
`config.json`, `vtk/mesh.vtk` + `vtk/sim_NNNNN.vtk`, `frames/frame_NNNNN.png`, `video.mp4`.

## HTTP API
| Endpoint | Description |
|---|---|
| `GET /api/status` | `{running, step, totalSteps, percent, statusText, startTime, exitCode}` |
| `GET /api/schema` | The parameter schema |
| `GET /api/custom-model-capabilities` | Execution flag, source limit and warning |
| `GET /api/logs?since=N` | `{lines, next}` — pass `next` back as `since` |
| `GET /api/frames`, `/api/frame/<name>` | Frame list and PNG |
| `GET /api/output-files` | `{directory, files}` of VTK files |
| `POST /api/run` | JSON start (202); 400 invalid payload, 403 denied execution/origin, 409 busy, 413 oversized body, 415 wrong content type |
| `POST /api/stop` | Kill the run |
| `POST /api/make-video` `{fps}` | Encode frames with ffmpeg; `GET /api/video` streams it |

Mutation requests check browser Origin/cross-site headers. Run/video require
JSON; stop accepts an empty body. With custom execution enabled, Host must
name loopback and the actual listening port. User source is never part of
the parameter schema or stored in `config.json`.
