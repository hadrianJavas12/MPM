# CL-MPM Studio

A small web UI to configure, run and watch a 2D cliff-collapse simulation (chalk model with
delayed damage). It needs no npm packages (Node.js ≥ 18).

```bat
studio\start-studio.cmd          :: opens http://127.0.0.1:3000   (STUDIO_PORT to change)
```
The server binds to `127.0.0.1` only.

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
the Lisp runner. Main groups: geometry (`shelfHeight`, `shelfAspect`, `cliffSlope`, `undercut`, `notchHeight`, `notchDepth`, `soilBoundary`), discretisation (`meshSize`, `mpsPerCell`), material (`density`, `E`, `nu`, `frictionAngle`, `ductility`, `initiationStress`, `delayTime`, `enableDamage`) and run control (`maxSteps` = output frames, `substeps` = solver steps per frame, `plotMode` = stress | damage | velocity, `workers`).

## Output (`output/studio/`)
`config.json`, `vtk/mesh.vtk` + `vtk/sim_NNNNN.vtk`, `frames/frame_NNNNN.png`, `video.mp4`.

## HTTP API
| Endpoint | Description |
|---|---|
| `GET /api/status` | `{running, step, totalSteps, percent, statusText, startTime, exitCode}` |
| `GET /api/schema` | The parameter schema |
| `GET /api/logs?since=N` | `{lines, next}` — pass `next` back as `since` |
| `GET /api/frames`, `/api/frame/<name>` | Frame list and PNG |
| `GET /api/output-files` | `{directory, files}` of VTK files |
| `POST /api/run` | Start (202), 409 if already running |
| `POST /api/stop` | Kill the run |
| `POST /api/make-video` `{fps}` | Encode frames with ffmpeg; `GET /api/video` streams it |
