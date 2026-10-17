# CL-MPM — Architecture, Folder Ownership & Migration Specification

**Status:** TARGET DESIGN / AGENT HANDOVER — **NOT YET IMPLEMENTED**  
**Tanggal penyusunan:** 16 Oktober 2026  
**Repository:** `https://github.com/hadrianJavas12/MPM`  
**Branch yang diaudit:** `codex/reusable-simulation-framework`  
**HEAD GitHub pada saat audit:** `7c399fb23de8e04871855c3911d73e583fdbcdc3`  
**Cakupan inventaris remote:** 884 tracked files; 1.067 Git-tree entries; tree tidak truncated. Ini **bukan** inventaris file lokal yang belum di-commit.  
**Penanggung jawab perubahan:** AI agent pelaksana; **persetujuan merge:** pemilik repository.

> **Instruksi utama:** Rancang dan migrasikan repository CL-MPM secara bertahap menuju *modular monolith* berbasis kepemilikan fungsi, dengan seluruh implementasi model material terkonsentrasi di `materials/`. Hapus kebutuhan arsitektural terhadap direktori `framework/` **hanya sesudah** isi dan semua entry point-nya dipindahkan/diadaptasi dengan bukti kompatibilitas. Jangan ubah persamaan, algoritma, parameter, atau hasil numerik sebagai efek samping pemindahan folder. Jangan merge ke `main` tanpa izin pengguna. Jangan menghapus data, evidence, atau kode legacy yang belum terbukti aman dihapus.

---

## 1. Tujuan dan keputusan desain yang telah disepakati

1. **Tidak wajib ada direktori bernama `framework/` atau `architecture/`.** Reusability adalah sifat kontrak komponen, builder, lifecycle, dan komposisi simulasi; bukan nama folder.
2. **Satu pusat material:** `materials/` di **root repository** (bukan `src/materials/`). Semua implementasi constitutive/material-specific state/law/diagnostics akhirnya tinggal di sini.
3. **Bedakan konsep berikut:**
   - **Material definition:** identitas/profil bahan dan parameter, misalnya *soft clay*; **bukan** persamaan konstitutif.
   - **Constitutive model:** formulasi tegangan–regangan, misalnya Mohr–Coulomb, Von Mises, atau model chalk.
   - **Evolution law:** bagian dari constitutive model yang mengatur perubahan parameter/state (hardening, softening, damage evolution). Hukum spesifik **berada di dalam folder model**.
   - **Material state:** keadaan internal tiap material point (tegangan/regangan dan variabel historis yang relevan). Bedakan *base particle state* umum dengan *model-specific internal state*.
4. `materials/shared/` **hanya** untuk kode material lintas model yang reuse-nya nyata; tensor/aljabar numerik umum berada di `src/numerics/`. Jangan membuat abstraksi atau adapter yang tidak perlu.
5. `src/` adalah engine dan mekanisme MPM generik. `scenarios/` adalah prosedur reusable, `cases/` adalah komposisi/parameter eksekusi, `research/` adalah eksperimen/evidence ilmiah.
6. API publik harus memungkinkan memilih geometri, material, loading, boundary, solver, dan measurement tanpa menulis ulang algoritma engine ataupun kode fisika model.
7. **Struktur folder final adalah target logis.** Pemecahan file harus berdasarkan tanggung jawab aktual di source, bukan hanya berdasarkan nama file. Folder kosong tidak perlu dibuat hanya agar tampak lengkap.
8. Jangan mengklaim suatu model/folder/solver **tersedia atau tervalidasi** hanya karena namanya muncul di blueprint ini. Model dan scenario baru bisa berstatus *planned*.

### Istilah dan aturan singkat

| Konsep | Lokasi owner | Boleh mengandung | Tidak boleh mengandung |
|---|---|---|---|
| Material definition | `materials/definitions/` | Nama, satuan, parameter, model ID, provenance | Constitutive solver |
| Constitutive model | `materials/models/<family>/<model>/` | Yield/flow, integrator, model state, evolution | Geometri/skenario spesifik |
| Model-specific evolution | `materials/models/.../evolution/` | `c(κ)`, `φ(κ)`, hardening/softening | Ketergantungan ke triaxial/cliff |
| Shared material utility | `materials/shared/` | Interpolasi reusable, validasi tabel kurva | Asumsi plastic strain model lain secara diam-diam |
| Engine | `src/` | P2G/G2P, mesh, solve, MPI, generic mechanics | Copy hukum konstitutif per skenario |
| Scenario | `scenarios/<test>/` | Geometry setup, boundary, stages, measurement | Implementasi ulang material/solver |
| Case | `cases/<scenario>/` | Pilihan komponen dan parameter SI | `defmethod` solver/material global |
| Research | `research/` | Data sumber, konfigurasi penelitian, hasil/bukti | Material production implementation yang tersembunyi |

---

## 2. Struktur folder TARGET (komprehensif)

Penamaan file di bawah adalah **blueprint**. File yang belum didukung tidak harus dibuat; struktur ini juga bukan daftar file aktual saat ini.

```text
MPM/
├── cl-mpm.asd                         # Entry point ASDF engine/komposisi
├── cl-mpm-tests.asd
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── .gitignore / .gitattributes / .gitconfig
│
├── src/                               # ENGINE MPM & RUNTIME REUSABLE
│   ├── core/
│   │   ├── particle-base.lisp         # MP dasar & generic slots
│   │   ├── mesh-base.lisp
│   │   ├── simulation-base.lisp
│   │   ├── domain-state.lisp
│   │   └── timestep.lisp
│   ├── geometry/
│   │   ├── primitives/
│   │   ├── sdf/
│   │   ├── clipping/
│   │   ├── regions/
│   │   └── particle-generation/
│   ├── discretization/
│   │   ├── mesh-generation/
│   │   ├── shape-functions/
│   │   ├── domain-update/
│   │   ├── refinement/
│   │   ├── splitting/
│   │   ├── ghost-nodes/
│   │   └── octree/
│   ├── transfer/
│   │   ├── p2g.lisp
│   │   ├── g2p.lisp
│   │   ├── forces.lisp
│   │   └── momentum.lisp
│   ├── boundaries/
│   │   ├── constraints/
│   │   ├── displacement/
│   │   ├── velocity/
│   │   ├── force/
│   │   ├── pressure/
│   │   ├── contact/
│   │   ├── penalty/
│   │   ├── buoyancy/
│   │   ├── inflow/
│   │   └── erosion/
│   ├── loading/
│   │   ├── gravity.lisp
│   │   ├── displacement.lisp
│   │   ├── force.lisp
│   │   ├── pressure.lisp
│   │   ├── time-functions.lisp
│   │   └── sequences.lisp
│   ├── solvers/
│   │   ├── explicit/                  # USF, USL, MUSL
│   │   ├── implicit/
│   │   ├── dynamic-relaxation/
│   │   │   ├── dynamic/
│   │   │   ├── quasi-static/
│   │   │   ├── multigrid/
│   │   │   └── convergence/
│   │   └── linear-systems/
│   ├── formulations/
│   │   ├── standard-mpm/
│   │   ├── ssa/                       # Solid Shell Approximation
│   │   └── octree/
│   ├── stabilization/
│   │   ├── fbar/
│   │   ├── aggregate/
│   │   ├── damping/
│   │   └── mass-filtering/
│   ├── damage/                        # Generic nonlocal/solver machinery
│   │   ├── nonlocal/
│   │   ├── fracture/
│   │   ├── eigenerosion/
│   │   └── solver/
│   ├── numerics/
│   │   ├── tensors/
│   │   ├── linear-algebra/
│   │   ├── eigen/
│   │   ├── fastmaths/
│   │   ├── integration/
│   │   ├── native-bridge/
│   │   └── error-handling/
│   ├── parallel/
│   │   ├── mpi/
│   │   ├── serial/
│   │   └── workers/
│   ├── simulation/                    # Reusability tanpa folder framework
│   │   ├── config/
│   │   ├── components/
│   │   ├── builder.lisp
│   │   ├── controller.lisp
│   │   ├── lifecycle.lisp
│   │   ├── stages.lisp
│   │   ├── validation.lisp
│   │   └── material-assignment.lisp
│   ├── measurements/
│   │   ├── stress-strain.lisp
│   │   ├── displacement.lisp
│   │   ├── volume.lisp
│   │   ├── energy.lisp
│   │   └── mass-balance.lisp
│   └── output/
│       ├── csv.lisp
│       ├── vtk.lisp
│       ├── plotting.lisp
│       ├── checkpoints.lisp
│       ├── metadata.lisp
│       └── provenance.lisp
│
├── materials/                         # SATU PUSAT MODEL MATERIAL
│   ├── cl-mpm-materials.asd           # Opsional ASDF subsystem/extension
│   ├── core/
│   │   ├── interface.lisp
│   │   ├── definition.lisp
│   │   ├── registry.lisp
│   │   ├── factory.lisp
│   │   ├── parameters.lisp
│   │   ├── state-interface.lisp
│   │   └── validation.lisp
│   ├── models/
│   │   ├── elastic/
│   │   │   ├── linear-elastic/
│   │   │   └── hyperelastic/
│   │   ├── plastic/
│   │   │   ├── von-mises/
│   │   │   │   ├── constitutive.lisp
│   │   │   │   ├── state.lisp
│   │   │   │   └── evolution/
│   │   │   ├── mohr-coulomb/
│   │   │   │   ├── particle.lisp
│   │   │   │   ├── yield-function.lisp
│   │   │   │   ├── plastic-potential.lisp
│   │   │   │   ├── return-mapping.lisp
│   │   │   │   ├── state.lisp
│   │   │   │   ├── evolution/
│   │   │   │   │   ├── perfect-plastic.lisp
│   │   │   │   │   ├── hardening.lisp
│   │   │   │   │   └── hardening-softening.lisp
│   │   │   │   └── legacy/            # Sementara, bukan duplikasi abadi
│   │   │   └── drucker-prager/
│   │   ├── viscoelastic/
│   │   ├── viscoplastic/
│   │   ├── fluid/
│   │   ├── chalk/
│   │   │   ├── constitutive.lisp
│   │   │   ├── state.lisp
│   │   │   └── evolution/
│   │   ├── concrete/
│   │   ├── limestone/
│   │   ├── ice/
│   │   └── frictional-damage/
│   ├── shared/
│   │   └── interpolation/            # Reuse nyata lintas model
│   ├── definitions/                  # Profil reusable + provenance
│   │   ├── soils/
│   │   ├── rocks/
│   │   └── concrete/
│   ├── diagnostics/                  # Diagnostics model-specific
│   ├── adapters/                     # Hanya bila ada kebutuhan API nyata
│   └── backends/                     # Binding Lisp/C++ model-specific
│       ├── lisp/
│       └── cpp/
│
├── scenarios/                        # PROSEDUR SIMULASI REUSABLE
│   ├── triaxial/
│   │   ├── geometry.lisp
│   │   ├── initial-conditions.lisp
│   │   ├── boundaries.lisp
│   │   ├── loading.lisp
│   │   ├── stages.lisp
│   │   ├── measurements.lisp
│   │   └── build.lisp
│   ├── direct-shear/                 # Planned, bukan fitur aktif
│   ├── cliff/
│   │   ├── geometry.lisp
│   │   ├── notch.lisp
│   │   ├── initial-conditions.lisp
│   │   ├── boundaries.lisp
│   │   ├── loading.lisp
│   │   └── measurements.lisp
│   └── joss/
│       ├── geometry.lisp
│       ├── stages.lisp
│       ├── measurements.lisp
│       └── build.lisp
│
├── cases/                            # RESEP / PRESET, TIDAK MENGANDUNG FISIKA
│   ├── triaxial/
│   ├── direct-shear/                 # Planned
│   ├── cliff/
│   └── benchmarks/
│
├── research/                         # MASTER PLAN, REFERENSI, BUKTI ILMIAH
│   ├── plans/
│   ├── references/
│   ├── datasets/
│   ├── configs/
│   ├── experiments/
│   │   ├── constitutive/
│   │   ├── triaxial/
│   │   └── cliff/
│   ├── calibration/
│   ├── comparisons/
│   └── reports/
│
├── tests/                            # TEST BESERTA NEGATIVE CONTROLS
│   ├── unit/
│   ├── materials/
│   ├── engine/
│   ├── scenarios/
│   ├── integration/
│   ├── regression/
│   ├── numerical/
│   ├── performance/
│   └── fixtures/
│
├── scripts/                          # CLI & AUTOMATION
│   ├── run-case.lisp
│   ├── audit/
│   ├── plotting/
│   ├── comparison/
│   └── build/
│
├── studio/                           # Existing UI; compatibility only
├── calibration/                      # Legacy calibration & launchers
├── analysis_scripts/                 # Historical analysis (retain)
├── examples/                         # Original examples (retain)
├── example_data/                     # Original reference data
├── tutorial/                         # Original tutorials
├── movies/                           # Historical media
├── libs/                             # Native sources, DLL, CUDA, MATLAB
├── deps/                             # Third-party dependencies/licenses
├── windows/                          # Windows scripts / launchers
├── docs/
│   ├── architecture/
│   │   ├── FOLDER_OWNERSHIP.md
│   │   ├── DEPENDENCY_RULES.md
│   │   └── FILE_MIGRATION_MATRIX.md
│   ├── evidence/
│   ├── reports/
│   ├── archive/
│   └── AI_HANDOVER.md
├── wiki-vault/                       # Obsidian & LLM Wiki
├── config/                           # Existing hooks/settings
├── .agents/                          # Agent skills
├── .github/                          # GitHub Actions
└── output/                           # Generated runs; untracked by default
```

**Jangan memindahkan semua `src/` sekarang.** Beberapa file sumber mencampur kelas partikel umum dengan constitutive model, dan ASDF memuat file dengan urutan spesifik. Struktur di atas adalah tujuan, bukan daftar operasi `git mv` otomatis.

---

## 3. Aturan ownership dan dependency

### 3.1 Aturan aliran dependensi

- `scenarios/*` boleh memakai kontrak engine, material registry, boundary/measurement; **material tidak boleh bergantung pada scenario**.
- `cases/*` boleh memilih material definition, evolution law, solver, geometry; **tidak boleh menambal `defmethod` global** untuk menjalankan eksperimen.
- `materials/models/*` boleh memakai *base particle interface* dan numerical primitives; tidak boleh mengimpor modul scenario, Studio, atau report generation.
- `src/numerics/*` tidak boleh bergantung pada spesifik Mohr–Coulomb/Chalk/Joss.
- `src/solvers/*` memanggil generic constitutive protocol; solver tidak mengandung rumus `c(κ)` atau `φ(κ)` spesifik model.
- `src/simulation/*` mengelola composition, config, stage, validation, run state; tidak menghitung return mapping.
- `studio/` adalah klien UI dan **tidak** menjadi dependency yang diperlukan untuk headless run.
- Generic diagnostics berada pada `src/measurements/`; internal state/diagnostic field yang hanya relevan MC berada pada `materials/diagnostics/` atau `materials/models/plastic/mohr-coulomb/`.
- Perintah output umum berada pada `src/output/`; model boleh mendeklarasikan field output melalui interface tanpa mengubah writer global.
- Jangan membuat circular dependency ASDF. Bentuk kontrak base particle/generic update yang dapat dipakai oleh solver dan material, serta muat `defmethod` model setelah kontrak tersedia.

### 3.2 Kapan law berada di folder model?

- **Default:** di `materials/models/<model>/evolution/` (misalnya tabel friksi-kohesi MC).
- `materials/shared/` hanya untuk algoritma yang model-independent dan telah memiliki reuse aktual; contohnya interpolasi piecewise-linear yang diberi interface satuan dan domain yang jelas.
- Jangan menyamakan akumulasi plastic strain `κ` antar-model tanpa konversi tervalidasi.
- Hardening vs hardening–softening **bukan sekadar mengganti fungsi** jika integrator memerlukan iterasi state/yield dan transaction semantics. Return mapping tetap harus menyelesaikan konsistensi strength/state akhir.

### 3.3 Material definition, model, dan case

- Profil `materials/definitions/soils/soft-clay.json`: nama, model ID, parameter dengan satuan, provenance, status validasi.
- Implementasi `materials/models/plastic/mohr-coulomb/`: yield, potential, integrator, state, evolution variants.
- `cases/triaxial/...`: memilih profil/model/law, geometri, tekanan pengekang, loading, discretization, solver, output.
- Parameter referensi PDF yang **belum terkalibrasi** tetap di `research/configs/` dan tidak dipromosikan menjadi profil material validated.
- Banyak material boleh memakai model sama; satu material bisa diuji dengan beberapa model asalkan parameter dan interpretasinya dinyatakan jelas.

---

## 4. Inventaris AS-IS yang diverifikasi di GitHub

Dari snapshot branch pada header, distribusi tracked files teratas:

| Path root | Jumlah | Keputusan awal |
|---|---:|---|
| `src/` | 81 | Migrasi internal bertahap; jangan hapus |
| `framework/` | 39 | Pisahkan ownership ke `src/simulation`, `materials`, `scenarios`, dan `src/output`; jadikan kompatibilitas sementara |
| `cases/` | 4 | Kelompokkan berdasarkan skenario setelah regresi |
| `research/` | 19 | Pertahankan master plan/evidence/provenance |
| `tests/` | 14 | Tambah/migrasikan tes dengan baseline tetap |
| `scripts/` | 15 | Pertahankan CLI yang dipakai |
| `studio/` | 36 | Jangan lakukan feature/UI work; hanya perbaikan kompatibilitas jika perlu |
| `calibration/` | 11 | Pertahankan launchers dan historical config |
| `analysis_scripts/` | 73 | Pertahankan semua sebelum audit manfaat/kepemilikan |
| `docs/` | 281 | Pertahankan seluruh positive/negative evidence; buat arsitektur & handover baru |
| `wiki-vault/` | 24 | Perbarui wiki/handover; jangan hapus konfigurasi personal |
| `examples/` | 72 | Legacy benchmark/regression; pertahankan |
| `tutorial/` | 4 | Pertahankan |
| `example_data/` | 34 | Pertahankan |
| `movies/` | 10 | Pertahankan historical media |
| `libs/` | 25 | Native DLL, C++, CUDA, MATLAB; audit ABI/build/license |
| `deps/` | 117 | Vendored dependencies dan license; jangan pindahkan sembarangan |
| `windows/` | 6 | Pertahankan launcher/toolchain |
| `config/` | 5 | Hooks/config; pertahankan |
| `.agents/` | 4 | Agent skills; pertahankan |
| `.github/` | 2 | CI; perbarui path hanya setelah migrasi |

Lainnya: root `cl-mpm.asd`, `cl-mpm-tests.asd`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitconfig`, `.gitattributes`, `.gitignore`.

**Hati-hati:** status acceptance berubah antar-commit. Baca `docs/AI_HANDOVER.md`, `research/reports/M0_OWNERSHIP_AND_ACCEPTANCE.md`, `research/reports/M0_MATERIAL_CONTRACT_AUDIT.md`, `research/reports/M0_SERIAL_REGRESSION.md`, dan `research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md` sebelum menjalankan tugas. Regresi serial Joss pernah PASS pada snapshot tertentu, sedangkan paralel empat worker tetap FAIL strict; ini tidak boleh digabung sebagai klaim "Joss sepenuhnya lulus". Refresh hasil 3D/recent head di lapangan.

---

## 5. Migration Map: file dan kelompok file yang harus diperiksa

**Definisi status:** `KEEP`, `MOVE_CANDIDATE`, `SPLIT_REVIEW`, `COMPATIBILITY`, `PRESERVE_EVIDENCE`, `OPTIONAL/NOT_LOADED`, `BLOCKED`. Semua target adalah *candidate ownership*, bukan perintah move langsung.

### 5.1 Engine dan model material bawaan

| Path AS-IS | Owner TO-BE | Action / catatan |
|---|---|---|
| `src/particle.lisp` | `src/core/` + `materials/models/*` | **SPLIT_REVIEW**; base MP/particle tetap kompatibel; method elastic/fluid/visco/constitutive terkait model dipetakan ke material. Jangan gandakan `defclass` atau simbol package. |
| `src/models/plastic.lisp` | `materials/models/plastic/{von-mises,mohr-coulomb,drucker-prager}/` | **SPLIT_REVIEW** berdasarkan class/method, bukan rename satu file; pertahankan native legacy MC tanpa perubahan numerik. |
| `src/models/elastic.lisp` | `materials/models/elastic/` | **OPTIONAL/NOT_LOADED:** verifikasi apakah loaded oleh ASDF sebelum migrasi. |
| `src/models/visco.lisp` | `materials/models/viscoelastic/` | **SPLIT_REVIEW** sesuai tipe implementasi. |
| `src/models/chalk.lisp` | `materials/models/chalk/` | **OPTIONAL/NOT_LOADED:** cek ASDF/entry point khusus; jangan aktifkan otomatis. |
| `src/models/concrete.lisp` | `materials/models/concrete/` | **MOVE_CANDIDATE** setelah source/API audit. |
| `src/models/ice.lisp` | `materials/models/ice/` | **OPTIONAL/NOT_LOADED**, cek loader spesifik. |
| `src/models/limestone.lisp` | `materials/models/limestone/` | **OPTIONAL/NOT_LOADED**, cek loader spesifik. |
| `src/models/damage-frictional.lisp` | `materials/models/frictional-damage/` | **MOVE_CANDIDATE** untuk constitutive aspects; generic damage tetap engine. |
| `src/models/damage.lisp` | `materials/models/` + `src/damage/` | **SPLIT_REVIEW**, bedakan particle damage model vs generic operators. |
| `src/constitutive.lisp` | `materials/models/*` + `src/numerics/` | **SPLIT_REVIEW**, sebagian hukum material, sebagian utilitas elastis/tensor. |
| `src/cpp.lisp` | `src/numerics/native-bridge/` + `materials/backends/cpp/` | **SPLIT_REVIEW**, pelihara ABI, Lisp fallback, loader DLL, dan provenance backend. |
| `libs/src/constitutive.h` | `libs/src/` (sementara), target model-specific kernels bila aman | **KEEP** sampai C++ linkage/regresi teruji; jangan `git mv` lalu merusak build. |
| `libs/src/utils.h` | `libs/src/` | **KEEP**, generic native utilities. |

### 5.2 Engine umum (path AS-IS lengkap untuk 81 file `src/`)

| Path(s) AS-IS | Owner TO-BE | Action |
|---|---|---|
| `src/cl-mpm.lisp`, `src/core.lisp` | `src/core/` | **SPLIT_REVIEW**: simulation/grid/base generic |
| `src/core/mesh.lisp` | `src/core/` atau `src/discretization/` | **REVIEW** menurut tanggung jawab sebenarnya |
| `src/core/shape-function.lisp` | `src/discretization/shape-functions/` | MOVE_CANDIDATE |
| `src/core/domain-update.lisp` | `src/discretization/domain-update/` | MOVE_CANDIDATE |
| `src/core/splitting.lisp` | `src/discretization/splitting/` | MOVE_CANDIDATE |
| `src/core/p2g.lisp`, `src/core/g2p.lisp`, `src/core/forces.lisp` | `src/transfer/` | MOVE_CANDIDATE |
| `src/core/iterate.lisp`, `src/core/iterate-test.lisp`, `src/core/stress-update.lisp` | `src/core/`, `src/simulation/`, atau `src/solvers/` | **SPLIT_REVIEW**: jangan mengubah urutan timestep |
| `src/core/linear-solver.lisp` | `src/numerics/linear-algebra/` atau `src/solvers/linear-systems/` | REVIEW |
| `src/core/symbolic-derivation.lisp` | `src/numerics/` | REVIEW; verifikasi apakah loaded |
| `src/setup.lisp` | `src/geometry/`, `src/discretization/`, `src/boundaries/`, `src/simulation/` | **SPLIT_REVIEW**: SDF, MP creation, self-weight, timestep, BC |
| `src/solvers/usf.lisp`, `src/solvers/usl.lisp`, `src/solvers/musl.lisp` | `src/solvers/explicit/` | MOVE_CANDIDATE |
| `src/implicit.lisp` | `src/solvers/implicit/` | REVIEW, preserve loaded/non-loaded state |
| `src/dynamic-relaxation/package.lisp`, `dynamic-relaxation.lisp`, `algorithms.lisp`, `criteria.lisp` | `src/solvers/dynamic-relaxation/` | MOVE_CANDIDATE |
| `src/dynamic-relaxation/solvers/dynamic.lisp`, `quasi-static.lisp`, `multigrid.lisp` | `src/solvers/dynamic-relaxation/` | MOVE_CANDIDATE |
| `src/dynamic-relaxation/mpi/dr.lisp`, `mpi/solvers.lisp` | `src/parallel/mpi/` + solver integration | REVIEW, preserve ASDF system |
| `src/dynamic-relaxation/misc/erosion.lisp` | `src/boundaries/erosion/` atau `src/damage/` | REVIEW berdasarkan fungsi aktual |
| `src/bc/bc.lisp`, `buoyancy.lisp`, `erosion.lisp`, `inflow.lisp`, `penalty.lisp` | `src/boundaries/` | MOVE_CANDIDATE |
| `src/solvers/octree/buoyancy.lisp`, `penalty.lisp` | `src/formulations/octree/` + boundaries | REVIEW extension methods |
| `src/ssa/package.lisp`, `mesh.lisp`, `p2g.lisp`, `particles.lisp`, `solvers.lisp` | `src/formulations/ssa/` | MOVE_CANDIDATE, preserve formulation semantics |
| `src/aggregate.lisp` | `src/stabilization/aggregate/` | MOVE_CANDIDATE; keep original numerical operation |
| `src/ghost.lisp` | `src/discretization/ghost-nodes/` | MOVE_CANDIDATE |
| `src/eigenerosion.lisp` | `src/damage/eigenerosion/` | MOVE_CANDIDATE |
| `src/damage/package.lisp`, `criteria.lisp`, `damage.lisp`, `degredation.lisp`, `delay-damage.lisp`, `ekl.lisp`, `nonlocal-stress-based.lisp`, `softening.lisp`, `solver.lisp`, `output.lisp`, `mpi.lisp` | `src/damage/` + `materials/models/*/evolution/` + `src/parallel/` + `src/output/` | **SPLIT_REVIEW**; klasifikasikan per fungsi; jangan otomatis pindah semuanya ke material |
| `src/mpi.lisp`, `src/mpi/package.lisp`, `serial.lisp`, `serialise.lisp`, `domain.lisp`, `sync.lisp`, `mpi.lisp`, `damage.lisp` | `src/parallel/` | REVIEW; pertahankan serial fallback yang sedang dipakai |
| `src/output.lisp` | `src/output/` | SPLIT_REVIEW output formats, native fields, stable defaults |
| `src/plotter.lisp` | `src/output/plotting/` atau `scripts/plotting/` | REVIEW runtime vs analysis |
| `src/fastmaths.lisp`, `src/utils.lisp` | `src/numerics/` | SPLIT_REVIEW utilitas lintas MPM |
| `src/settings.lisp` | `src/core/` atau `src/simulation/config/` | REVIEW compiler and runtime settings |
| `src/errors.lisp` | `src/numerics/error-handling/` atau `src/core/` | REVIEW error classes |

**Catatan completeness:** daftar pada tabel ini merujuk ke semua kelompok/path teramati dalam `src/` (81 file). Verifikasi ulang dengan `git ls-files src` dari clone lokal dan hasilkan register satu baris per path; tabel beberapa baris memang menggabungkan file serumpun.

### 5.3 `framework/` → ownership baru, bukan direct rename

| Path AS-IS | Owner TO-BE | Catatan |
|---|---|---|
| `framework/components/materials.lisp` | `materials/core/` + `materials/adapters/` | Factory, class mapping; preserve native material identity |
| `framework/components/diagnostics.lisp` | `materials/diagnostics/` + `src/measurements/` | MC vs VM diagnostics tidak boleh dicampur |
| `framework/components/geometry.lisp`, `specifications.lisp` | `src/geometry/` + `src/simulation/components/` | SPLIT_REVIEW capability declarations |
| `framework/config/package.lisp`, `parameters.lisp` | `src/simulation/config/` | Verify JSON schema + precedence |
| `framework/materials/chalk.lisp` | `materials/models/chalk/` | Freeze Joss numerical behavior and class identity |
| `framework/simulation.lisp` | `src/simulation/` | Builder/lifecycle, no material physics |
| `framework/output/plotting.lisp` | `src/output/plotting/` atau `scripts/plotting/` | Runtime vs analysis decision |
| `framework/scenarios/triaxial/package.lisp`, `config.lisp`, `geometry.lisp`, `boundaries.lisp`, `mpm.lisp`, `runner.lisp` | `scenarios/triaxial/` | Scenario lifecycle / compatibility |
| `framework/scenarios/triaxial/material.lisp` | `materials/core/` + `scenarios/triaxial/initial-conditions.lisp` | Constructor & prestress must separate |
| `framework/scenarios/triaxial/measurements.lisp`, `tensors.lisp` | `scenarios/triaxial/` + `src/measurements/` + `src/numerics/` | Generic vs scenario-specific metrics |
| `framework/scenarios/triaxial/homogeneous.lisp`, `controls.lisp` | `scenarios/triaxial/` (modes) | Preserve VM capability gate & state snapshot behavior |
| `framework/scenarios/triaxial/adapter.lisp` | `scenarios/triaxial/` compatibility adapter | Remove only after callers transition |
| `framework/scenarios/cliff/settings.lisp`, `geometry.lisp`, `build.lisp`, `run.lisp`, `adapter.lisp` | `scenarios/cliff/` | Existing integration and defaults must remain |
| `framework/scenarios/joss/classes.lisp`, `statistics.lisp`, `phases.lisp`, `geometry.lisp`, `build.lisp`, `measurements.lisp`, `output.lisp`, `run.lisp` | `scenarios/joss/` + material chalk specifics | Split model-owned class from scenario-specific implementation |
| `framework/package.lisp`, `framework/cl-mpm-framework.asd` | New ASDF systems + temporary compatibility loader | Defer deletion until all historical `ql:quickload` and launchers pass |
| `framework/README.md`, `framework/components/README.md`, `framework/scenarios/triaxial/README.md` | `docs/` + scenario README | Preserve information, update links |

### 5.4 Cases dan compatibility

| Path AS-IS | Target | Status |
|---|---|---|
| `cases/cliff.lisp` | `cases/cliff/cliff.lisp` | MOVE_CANDIDATE with preserved alias/loader |
| `cases/joss-collapse.lisp` | `cases/benchmarks/joss-collapse.lisp` | MOVE_CANDIDATE with preserved alias/loader |
| `cases/triaxial-clay-2d.lisp`, `cases/triaxial-clay-3d.lisp` | `cases/triaxial/` | MOVE_CANDIDATE; keep old entry paths temporarily |
| `scripts/run-case.lisp`, `scripts/run-triaxial.lisp` | `scripts/` | KEEP, update loaders only with regression |
| `calibration/triaxial.lisp`, JSON configs, CMD & Python | `calibration/` | COMPATIBILITY; do not break old calibration |
| `studio/lisp/*`, `studio/schema.json`, `studio/server.js`, `studio/public/*` | `studio/` | KEEP; no UI changes under this task unless essential backward compatibility |
| `windows/cl-mpm.cmd`, `windows/init.lisp`, `windows/env.cmd`, `windows/setup.ps1`, `windows/build-kirchoff.cmd`, `windows/make-video.cmd` | `windows/` | KEEP; native Windows is supported baseline |
| `examples/**`, `tutorial/**`, `example_data/**` | Same paths initially | PRESERVE; update only explicitly tested references |
| `research/**`, `docs/evidence/**`, `movies/**` | Same paths | PRESERVE_EVIDENCE; no deletion |
| `analysis_scripts/**`, `libs/**`, `deps/**` | Same paths initially | KEEP pending separate audit |
| `wiki-vault/**`, `.agents/**`, `.github/**`, `config/**` | Same paths initially | KEEP; update only necessary docs/CI paths |

---

## 6. Mandatory **file-by-file** inventory at execution time

Dokumen ini mengaudit seluruh **kategori dan source utama**, **belum mengklaim** telah meninjau semantik 884 file satu per satu. AI agent **wajib** membuat `docs/architecture/FILE_MIGRATION_MATRIX.md` atau `.json` dari working tree aktual **sebelum** migrasi. Setiap tracked path dari `git ls-files` harus muncul sekali, termasuk file di luar source code.

**Schema record wajib:**

```json
{
  "source_path": "src/models/plastic.lisp",
  "target_path": "MULTIPLE:materials/models/plastic/*",
  "decision": "SPLIT_REVIEW",
  "owner": "materials",
  "category": "constitutive-model",
  "current_asdf_systems": ["cl-mpm/particle"],
  "public_symbols_or_entrypoints": [],
  "referencing_files_or_callers": [],
  "numerical_behavior_change_allowed": false,
  "required_tests": ["constitutive unit", "legacy solver regression"],
  "evidence": "source inspection pending",
  "status": "NOT_STARTED"
}
```

`current_asdf_systems` di atas hanya contoh struktur record; agent harus memperoleh nilainya dari audit ASDF dan tidak menganggapnya satu-satunya loader. Untuk **satu file yang dipecah**, tulis daftar target aktual beserta alasan pemisahan.

Prosedur:

1. `git status --short --branch`, `git rev-parse HEAD`, `git ls-files` dan catat untracked yang mungkin milik pengguna.
2. Hitung total tracked paths; lengkapkan matriks sebanyak total tersebut. **Dilarang menganggap `git ls-files` menemukan file lokal yang tidak terlacak.**
3. Klasifikasikan setiap file sebagai: `KEEP`, `MOVE_CANDIDATE`, `SPLIT_REVIEW`, `COMPATIBILITY`, `PRESERVE_EVIDENCE`, `OPTIONAL/NOT_LOADED`, `BLOCKED`, atau `NEW`.
4. Audit `cl-mpm.asd`, `cl-mpm-tests.asd`, `framework/cl-mpm-framework.asd`, dan `studio/lisp/cl-mpm-studio.asd`; kumpulkan referensi file relatif dan `:depends-on`. Bedakan package/class/method/ASDF system dari sekadar filesystem path.
5. Audit `load`, `asdf:load-system`, `ql:quickload`, path via `asdf:system-relative-pathname`, script Windows, runner snapshot, test harness, schema, dan references pada dokumen.
6. Untuk file source campuran, tetapkan pemilik **per top-level form/defmethod** bila perlu; jangan hanya menggunakan keyword filename.
7. Tuliskan kecocokan *source hash*, target, test, dan commit; jangan menghapus original sebelum target tervalidasi serta compatibility transition ditetapkan.
8. Semua folder root yang tercatat pada §4 harus tercakup; keluarkan daftar `UNCLASSIFIED` dan jangan mulai bulk migration jika masih ada path aktif yang belum diklasifikasikan.

---

## 7. Acceptance dan numerical safety gates

### Gate G0 — Baseline / inventory

- Capture Git branch, HEAD, status, local modifications, installed toolchain, version OS/SBCL/native libraries, existing run outputs, complete inventory.
- Baca handover dan reports terbaru; audit apakah proses native masih berjalan **sebelum** menjadwalkan ulang run berat.
- Bekukan referensi input dan output baseline; semua negative evidence dipertahankan.
- Mempunyai manifest/matriks pemindahan lengkap dan baseline existing tests.

### Gate G1 — Material architecture

- Definisi `MaterialDefinition`, `ConstitutiveModel`, `EvolutionLaw`, `MaterialState`, dan `MaterialDiagnostics` dipisahkan pada kontrak yang sesuai.
- Tidak ada duplicate class definition atau global method override yang mengubah kelas lain.
- Native VM, MC, elastic/chalk sesuai availability aktual tetap dapat dibuat dan identitas kelasnya terjaga.
- MC **tidak** diubah menjadi subclass VM untuk melewati checks.
- Model diagnostics tidak salah mengartikan plastic strain, yield residual, strength, maupun unit.
- Tidak ada perubahan behavior solver dari langkah pengelompokan material.

### Gate G2 — Scenario & orchestration

- `src/simulation/` dan `scenarios/` melakukan komposisi generic, bukan constitutive calculations.
- CLI/headless runs untuk kasus lama valid; custom controls yang belum didukung harus **fail explicitly**.
- Material assignment multi-region tidak mengubah state model yang tidak dipilih.
- Konfigurasi menolak unknown/duplicate keys, invalid physical range, source conflict; tidak ada silent fallback.
- Setiap run adalah local state (tidak bocor konfigurasi global), output unik, failure status/manifest jujur.

### Gate G3 — Numerical regressions

- Deterministic regression diulang pada **executed code snapshot** yang jelas, bukan HEAD yang berubah saat run.
- Minimum: triaxial VM 2D, triaxial VM 3D, Joss serial, Joss parallel (open exception dicatat), bounded cliff MC, engine/material unit tests, output CSV/VTK.
- **PASS** hanya jika metrik yang sudah ditetapkan sesuai (bila baseline menuntut exact byte/hash equivalence, jangan menggantinya dengan plot visual mirip).
- Kegagalan parallel 4-worker tidak boleh diubah menjadi PASS karena serial berhasil.
- Semua regression yang belum diuji diberi `NOT_RUN`/`BLOCKED`, bukan `PASS`.

### Gate G4 — Optional physics M2 (separate experimental branch)

- MC H/HS baru **bukan otomatis selesai** setelah restrukturisasi folder.
- Native MC lama memiliki isu return mapping/apex untuk `φ=0`, khususnya `c=0`, dan sifat iterasi/state yang memerlukan desain baru untuk coupling H/HS.
- Verifikasi yield residual setelah correction, corner/apex, nonassociated flow, state trial/commit/rollback, strain measure `κ`, stress sign/unit, C++ vs Lisp backend, spatial test, lalu convergence/sensitivity.
- Pisahkan kasus residual soil dari benchmark Zhan; jangan fit ke kurva PDF. Tanpa pore-pressure coupling jangan mengklaim *true CU*.
- Perubahan fisika masuk branch terpisah dan review tersendiri; **jangan diselundupkan ke commit pemindahan folder**.

### Gate G5 — Compatibility and completion

- `ql:quickload`/ASDF entrypoints lama, Windows runners, Studio backend compatibility, calibration, original examples, scripts smoke, docs links dan CI kembali bekerja.
- `framework/` hanya boleh dihapus dari branch target setelah tidak ada caller aktif dan compatibility/provenance terbukti.
- Dokumentasi `docs/architecture/*`, `docs/AI_HANDOVER.md`, `docs/REUSABLE_FRAMEWORK.md`, `wiki-vault/wiki/*` ter-update.
- Tersedia per-test summary dan artifact reference; tidak ada bukti lama dihapus.
- **Tidak merge `main` tanpa konfirmasi pengguna.**

---

## 8. Urutan eksekusi yang aman

| Phase | Perubahan | Boleh coding? | Keluar jika |
|---|---|---|---|
| P0 | Inventory, dependency analysis, source/ASDF map, freeze baseline, class & method ownership | Hanya tooling audit/dokumen | G0 lengkap |
| P1 | Material contracts & registry dengan compatibility layer | Ya, kecil dan teruji | G1 unit tests + regression snapshot |
| P2 | Pindahkan **owner** model bawaan ke `materials/` secara bertahap, preserve symbols + backend | Ya, satu keluarga model per checkpoint | G1/G3 setiap tahap |
| P3 | Material diagnostics, definitions, shared utilities; hapus duplikasi setelah audit | Ya | G1/G2/G3 |
| P4 | Integrasi `framework/` ke `src/simulation/` dan `scenarios/` dengan compatibility loaders | Ya | G2/G3/G5 |
| P5 | Perapihan internal `src/` (transfer, solvers, SSA, damage, numerics, MPI) | Hanya bila manfaat jelas, dan perubahan kecil | G3/G5 |
| P6 | Hapus file/wrapper usang **hanya bila terbukti aman**, final docs/handover/reports | Ya setelah acceptance | G5 + review pengguna |

**Parallel work:** pemindahan struktur dan eksperimen model MC H/HS dapat berjalan pada branch terpisah; jangan menggabungkan hasil keduanya sebelum conflict/integration testing. Master plan M0–M6 tetap berlaku untuk pekerjaan ilmiah; dokumen ini adalah **spesifikasi arsitektur/migrasi**, bukan pengganti master plan.

Checkpoint setiap phase: branch/commit, perubahan file, rationale, original-vs-after executable source hash, per-test PASS/FAIL/BLOCKED, output artifact path, known risk, next step, dan updated handover. Jangan mengklaim pekerjaan complete hanya dengan mengisi dokumen bila implementasi/run yang diminta belum selesai.

---

## 9. Operasi dan perlindungan kerja

- Jangan force-push, rebase destruktif, reset hard, overwrite output, menghapus backup/editor recovery, atau mengubah hasil penelitian sebelumnya.
- Jangan menyentuh `main` dan jangan merge PR tanpa persetujuan.
- Hindari perubahan UI/Studio feature; hanya kompatibilitas yang perlu, dan beri catatan eksplisit.
- Jangan mengklaim project memiliki lisensi repository-wide yang belum dibuktikan. `deps/` mengandung lisensi tersendiri; atribut ASDF bukan pengganti izin kode asli.
- Pertahankan `docs/evidence/`, raw logs, hash, movie, negative runs, dataset/provenance, dan original examples sampai ada kebijakan arsip eksplisit.
- Jika harus membangun native DLL/ABI, catat compiler/toolchain dan verifikasi fallback; jangan menambah CUDA requirement pada baseline Windows tanpa persetujuan.
- Source snapshot harus mencakup material model/evolution/backend baru. Jangan membekukan sebagian source lalu memuat model lain langsung dari working tree tanpa tercatat.
- Saat baseline tidak memenuhi gate, laporkan `BLOCKED` beserta minimal reproduksi; boleh lanjut *non-dependent work* pada branch terpisah tanpa menamainya PASS.

---

## 10. Dokumentasi dan deliverable yang agent WAJIB hasilkan

1. `docs/architecture/FOLDER_OWNERSHIP.md`: struktur aktual dan target, aturan material/model/law/state, dependency graph, daftar design decisions.
2. `docs/architecture/FILE_MIGRATION_MATRIX.md` atau `.json`: **seluruh tracked paths**, termasuk unchanged dan preserved.
3. `docs/architecture/DEPENDENCY_RULES.md`: package, ASDF systems, native libs, scenario, and compatibility contracts; daftar cyclic dependency yang ditolak.
4. `docs/architecture/MIGRATION_EXECUTION_LOG.md`: tahapan, commit, changed files, verification, failures, rollback strategy.
5. Updated `docs/AI_HANDOVER.md` dan `wiki-vault/wiki/reusable-simulation-framework.md` / `wiki-vault/wiki/cl-mpm-architecture.md`; catat juga di Obsidian tanpa menimpa personal vault settings.
6. Bukti tes versi sebelum/sesudah beserta source hashes, CLI invocation, exit code, regression metrics, log/output locations.
7. Ringkasan FINAL berupa status `DONE`, `PARTIAL`, `BLOCKED`, `NOT_RUN` untuk tiap phase dan gate, beserta open risks.

**Deliverable tambahan yang tidak boleh dipalsukan:** pada tahap dokumen saja, jangan menulis hasil run yang belum dijalankan, angka stress–strain simulasi, atau klaim verifikasi CU.

---

## 11. Prompt eksekusi langsung untuk AI agent

> Baca dokumen `CL_MPM_ARCHITECTURE_MIGRATION_SPEC_AGENT.md` ini **bersama** `docs/AI_HANDOVER.md`, `research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md`, `research/reports/M0_OWNERSHIP_AND_ACCEPTANCE.md`, dan konfigurasi ASDF saat ini. Audit Git branch/HEAD/working tree dan existing tests sebelum perubahan. Implementasikan modularisasi bertahap: engine tetap di `src/`, semua implementasi constitutive model/material state/evolution law dipusatkan di `materials/`, scenario reusable dipindah ke `scenarios/`, dan orchestration masuk `src/simulation/`. Tidak ada folder `framework/` permanen pada target akhir, tetapi jangan menghapusnya sampai compatibility gate benar-benar PASS. Buat migration matrix lengkap untuk semua tracked file, preserve legacy source/results, lakukan tes numerik sesudah setiap perubahan, terus perbarui handover, docs, dan wiki. Model fisika MC H/HS baru tetap experimental dan diuji terpisah. Jangan melakukan pekerjaan UI fitur baru, jangan fit data PDF, jangan klaim full CU tanpa pore pressure, jangan force-push atau merge ke `main` tanpa persetujuan pengguna. Laporkan milestone, bukti PASS/FAIL/BLOCKED, dan blocker secara jujur.

---

## 12. Referensi internal untuk ditinjau, bukan assumed PASS

- `cl-mpm.asd`, `cl-mpm-tests.asd`
- `framework/cl-mpm-framework.asd`
- `studio/lisp/cl-mpm-studio.asd`, `studio/schema.json`
- `docs/AI_HANDOVER.md`, `docs/REUSABLE_FRAMEWORK.md`, `docs/architecture.md`
- `research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md`
- `research/reports/M0_OWNERSHIP_AND_ACCEPTANCE.md`
- `research/reports/M0_CLEANUP_INVENTORY.md`
- `research/reports/M0_MATERIAL_CONTRACT_AUDIT.md`
- `research/reports/M0_SERIAL_REGRESSION.md`
- `research/reports/M2_RETURN_MAPPING_DESIGN.md`
- `docs/evidence/framework-refactor-2026-10-15/`
- `wiki-vault/wiki/reusable-simulation-framework.md`

**Aturan penutup:** *architecture follows ownership, not the other way around*. Jangan menciptakan folder atau abstraction baru jika tidak punya owner, kontrak, dan use case nyata. Reusability diukur dengan kemampuan mengganti material/solver/geometry/case tanpa mengubah fisika material atau kode skenario yang tidak terkait—dan hasil numerik legacy tetap dapat diverifikasi.
