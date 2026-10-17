# Komposisi simulasi native

Branch arsitektur: `codex/material-architecture-migration`, berasal dari
`7c399fb`. Seluruh tahapan migrasi kepemilikan (P0–P6) sudah selesai diinstal
dan divalidasi: model material berada di `materials/`, prosedur skenario di
`scenarios/`, dan orkestrasi di `src/simulation/`, dengan ASDF kanonis di root
(`cl-mpm-framework.asd`). Regresi penuh VM 2D/3D (`p6-full/`), rangkaian pendek
11 pemeriksaan (`p6-short/`), dan kontrol serial terbatas Joss 4 detik (`joss-bounded/`)
seluruhnya lulus (`exit 0`, VTK/CSV identik byte); gate G1 dan G3 tetap `PARTIAL`
karena pengecualian kompatibilitas legacy dan penghentian run penuh Joss 40 s oleh pengguna.
Lihat [status aktual](architecture/STATUS.md).

## Menjalankan kasus di Windows

Buka PowerShell pada mesin dengan toolchain yang sudah tersedia:

```powershell
Set-Location D:MPM
$runDir = Join-Path 'D:MPMoutput' ('triaxial-2d-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .windowscl-mpm.cmd scripts
un-case.lisp cases	riaxial-clay-2d.lisp $runDir
if ($LASTEXITCODE -ne 0) { throw 'Run gagal; periksa pesan terminal.' }
& .	oolchainanalysis-venvScriptspython.exe scriptsplot-triaxial.py --run-dir $runDir --video
```

| Kasus di `cases/` | Arti |
| --- | --- |
| `triaxial-clay-2d.lisp` | Persegi panjang 70 × 140 mm, plane strain, ketebalan satuan |
| `triaxial-clay-3d.lisp` | Silinder diameter 70 mm, tinggi 140 mm, MPM 3D |
| `cliff.lisp` | Contoh tebing dengan konfigurasi kecil |
| `joss-collapse.lisp` | Resep Joss legacy; run penuh 40 s yang dihentikan pengguna tetap dihentikan |

Gunakan direktori output baru untuk setiap run. File kasus adalah Lisp lokal
tepercaya yang berjalan dengan hak akses pengguna Windows. Tebing memakai
VTK dan renderer pada [panduan Windows](RUN_ACCEPTED_COLLAPSE_WINDOWS.md),
bukan plotter triaxial. Jangan memulai ulang full Joss yang dibatalkan.

## Material dan geometri yang dapat dipilih

`make-simulation` menyusun skenario, material, geometri, boundary, loading dan
solver. API komponen memakai m, Pa, s, kg/m³ dan fraksi regangan; `0.10d0`
berarti 10%. Adapter tetap mengonversi parameter legacy mm/% secara eksplisit.

Contoh komponen pada kasus triaxial, dengan geometri tetap:

```lisp
:material (make-material :elastic :youngs-modulus 5d6
                         :poisson-ratio 0.49d0 :density 1800d0)
:geometry (make-geometry :rectangle :width 0.07d0 :height 0.14d0)
```

`:von-mises` dengan `:undrained-strength 25d3` memilih VM. Adapter legacy
`:elastic` mempertahankan kelas VM dengan plasticity dimatikan. Elastic native
sebenarnya dapat dipilih melalui `:native` dengan
`:particle-class 'cl-mpm/particle::particle-elastic`.
Native MC memakai `cl-mpm/particle::particle-mc`, tetap independen dari VM.
E, nu dan metadata kekuatan harus konsisten dengan initargs; konflik ditolak.
Parameter MC `:phi` dan `:psi` memakai radian, `:c` memakai Pa.

Geometri silinder 3D memakai komponen berikut:

```lisp
:geometry (make-geometry :cylinder :diameter 0.07d0 :height 0.14d0)
```

`:filter` menerima fungsi lokal `(x y z) -> boolean` pada pembentukan partikel;
filter tersebut tidak mengubah hasil damage setelah solver berjalan.
Triaxial menerima kombinasi material/diagnostik yang didukung dengan confinement
dan compression. Cliff/Joss mempertahankan kontrak geometri dan fase tersendiri.
Opsi atau kombinasi yang tidak didukung harus ditolak, bukan diabaikan.

Diagnostik sudah membedakan VM, MC dan native elastic. Kolom VM yang tidak
bermakna untuk MC tetap unavailable; MC mempunyai field bernama dan residual
Kirchhoff tersendiri. Mode homogeneous/controls tetap dibatasi capability.
`material-state` adalah pembacaan diagnostik, bukan snapshot trial/rollback.
Migrasi ini tidak menambahkan integrator dedicated MC H/HS atau kalibrasi.
Rincian kelas, satuan dan batasannya ada di [katalog model](architecture/MODEL_CATALOG.md).

## Lokasi implementasi

| Owner | Isi |
| --- | --- |
| `src/core/` | Base particle, common slots dan generic protocol |
| `materials/` | Profile/adapter, kelas material, constitutive, evolution, diagnostics dan binding backend |
| `src/numerics/`, `src/solvers/` | Tensor, integrasi numerik, fastmaths dan solver generik |
| `src/damage/`, `src/parallel/` | Nonlocal transport, scheduling dan komunikasi engine |
| `src/simulation/` | Konfigurasi, komponen dan lifecycle run |
| `scenarios/{triaxial,cliff,joss}/` | Geometri, boundary, loading, fase dan pengukuran skenario |
| `src/measurements/`, `src/output/` | Mekanisme pengukuran/output generik |
| `cases/`, `scripts/`, `windows/` | Resep dan launcher |
| `libs/` | Kernel/DLL native yang ABI-nya dipertahankan |
| `framework/` dan jalur source lama | Compatibility loaders; deklarasi ASDF kanonis sekarang di root |

Simbol CLOS lama tetap dipakai. Modul skenario tidak menyalin persamaan material.
Lihat [aturan ownership](architecture/FOLDER_OWNERSHIP.md) dan
[API material](../materials/README.md). Kernel C++ campuran, override damage/ice
dan forward class concrete tetap merupakan pengecualian yang dicatat.

## Source yang benar-benar dijalankan

CLI memerlukan proses Windows yang fresh sebelum paket proyek atau
`kirchoff.dll` dimuat. Ia menyalin source first-party `src/`, `materials/`,
`framework/`, `scenarios/`, ASDF, kasus, input, launcher/helper dan DLL native
ke direktori run; manifest menyimpan SHA-256 byte sebelum pemuatan.

ASDF memeriksa containment/hash file first-party yang dipilih sebelum compile
dan load. FASL first-party memakai cache privat pada snapshot. Windows memeriksa
path modul DLL yang benar-benar terpetakan melalui GetModuleHandleW/
GetModuleFileNameW dan mencocokkannya dengan salinan DLL. Kegagalan guard
menghentikan run. Baca `source/source-manifest.json` dan
`source-provenance.json`, bukan hanya HEAD saat proses selesai.

Dependency pihak ketiga tetap berasal dari instalasi eksternal. Probe modul
matematika bukan inventaris semua DLL proses. Arbitrary non-ASDF LOAD dari
kasus tepercaya berada di luar klaim source-ASDF tersebut. CSV/VTK berasal dari
solver; Python hanya membaca hasil untuk audit/visualisasi.

## Bukti dan gate yang masih terbuka

| Bukti | Lingkup yang dapat dinyatakan |
| --- | --- |
| P2 A–D: 20 katalog native | Lima keluarga per checkpoint, exit 0; seluruh serialized catalog identik byte dengan baseline |
| Kontrol pendek P4-F / P6 (`p6-short/`) | Seluruh 11 pemeriksaan native lulus (`exit 0`, 64 artefak terverifikasi SHA-256) dan Node 36/36 lulus |
| Full VM 2D/3D pada layout kanonis final (`p6-full/`, `9dfb58b`) | **PASS exact** terhadap `p1-full` (`62adb50`): 51/51 VTK pada 2D (480 MP, 17.443 update) dan 51/51 VTK pada 3D (780 MP, 17.443 update) serta `stress-strain.csv` identik byte (`SHA-256` sama), selisih posisi/CSV/field nol, dan audit independen lulus |
| Kontrol serial terbatas Joss 4 detik (`joss-bounded/`) | **PASS exact** antara sumber pra-P2 (`before-003`) dan layout kanonis final (`after-001`): 1.658 langkah ekuilibrasi dan waktu fisik 4,0 s (`exit 0`), `equilibrium.vtk`, `sim_00001.vtk`, dan `sim_00002.vtk` identik byte dengan selisih posisi/field/CSV nol |
| Joss serial 40 s historis | PASS exact, sumber asli `c749d32` versus executed `41403f4`; lihat [laporan serial](../research/reports/M0_SERIAL_REGRESSION.md) |
| Joss empat worker historis | FAIL tetap dipertahankan; serial PASS tidak menghapusnya |
| Full Joss 40 s pada cabang migrasi (`62adb50`) | `STOPPED_BY_USER` pada 4,2 s; tidak dimulai ulang atau diganti label PASS |

Kontrol Joss berdurasi pendek (4 detik) adalah bukti inisiasi serial terpisah dan
tidak membuktikan collapse/run-out 40 s atau menutup gate G3 penuh. Bandingkan VTK/CSV,
massa, jumlah partikel, waktu fisik dan completion status dengan toleransi yang tetap.
Plane strain 2D bukan axisymmetry dan tidak setara dengan silinder 3D. Regresi kode
tidak menetapkan kalibrasi, mesh convergence, keseimbangan energi tertutup atau
validasi ilmiah. [Roadmap penelitian](../research/README.md) menjaga gate fisika H/HS terpisah.
