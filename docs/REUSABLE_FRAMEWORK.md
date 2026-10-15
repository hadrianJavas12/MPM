# Framework simulasi native yang dapat disusun ulang

Branch pengembangan: `codex/reusable-simulation-framework`, dari checkpoint
`main` / PR #7 (`efd0358`). Implementasi awal disimpan pada `66ea5fb` sebelum
validasi setelah refactoring. Perubahan lanjutan memperbaiki launcher dan
kontrak parameter; hasil pengujian dicatat terpisah.

## Jalankan dari file kasus pendek

Buka PowerShell pada komputer Windows yang toolchain-nya sudah tersedia:

```powershell
Set-Location D:\MPM
$runDir = Join-Path 'D:\MPM\output' ('triaxial-2d-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .\windows\cl-mpm.cmd scripts\run-case.lisp cases\triaxial-clay-2d.lisp $runDir
if ($LASTEXITCODE -ne 0) { throw 'Run gagal; periksa pesan terminal.' }
& .\toolchain\analysis-venv\Scripts\python.exe scripts\plot-triaxial.py --run-dir $runDir --video
```

Untuk kasus lain, ganti file pada `cases\`:

| File | Perhitungan |
| --- | --- |
| `triaxial-clay-2d.lisp` | Spesimen 70 × 140 mm, plane strain, ketebalan satuan |
| `triaxial-clay-3d.lisp` | Silinder diameter 70 mm × tinggi 140 mm, MPM 3D |
| `joss-collapse.lisp` | Tebing dengan parameter runtuhan yang diterima sebelumnya |
| `cliff.lisp` | Contoh tebing umum dengan konfigurasi kecil |

Run tebing memakai keluaran VTK dan renderer tebing yang dijelaskan dalam
[panduan Windows](RUN_ACCEPTED_COLLAPSE_WINDOWS.md), bukan plotter triaxial.
Setiap run harus memakai folder baru. File kasus adalah kode Lisp lokal
tepercaya yang dieksekusi dengan hak akses pengguna Windows.

## Apa yang dapat dibongkar pasang?

File kasus menyusun enam hal: skenario, material, geometri, boundary,
pembebanan dan solver. Ukuran pada API memakai m, tegangan Pa, waktu s,
massa jenis kg/m³, dan regangan sebagai fraksi (`0.10d0` berarti 10%).

Contoh mengganti material sambil mempertahankan geometri:

```lisp
:material (make-material :elastic :youngs-modulus 5d6
                         :poisson-ratio 0.49d0 :density 1800d0)
:geometry (make-geometry :rectangle :width 0.07d0 :height 0.14d0)
```

Gunakan `:von-mises` dengan `:undrained-strength 25d3` untuk kembali ke
contoh plastis. Adapter `:elastic` memakai particle VM yang plasticity-nya
dimatikan agar kontrak pencatatan tetap konsisten. Persamaan konstitutif
tetap berasal dari engine asli.

Contoh mengganti geometri menjadi silinder 3D:

```lisp
:geometry (make-geometry :cylinder :diameter 0.07d0 :height 0.14d0)
```

Tambahkan bentuk potongan pada spesimen memakai `:filter`, fungsi lokal
`(x y z) -> boolean`. Filter digunakan pada pembentukan partikel; tidak
mengubah perpindahan atau hasil damage sesudah solver berjalan.

Model native tambahan dapat memakai `:native :particle-class 'kelas-anda
:initargs (...)`. Method konstitutif ditulis pada class tersebut. Metadata E,
nu dan kekuatan harus konsisten dengan initargs; konflik ditolak.
Diagnostik triaxial saat ini membutuhkan particle VM atau subclass-nya.
Model dengan state lain memerlukan adapter pengukuran sendiri.

Tidak semua kombinasi bermakna secara fisik. Resep Joss mempertahankan material
khusus, geometri dasar dan aturan fasenya; substitusi yang tidak didukung
ditolak. API menolak opsi yang tidak dikenal atau tidak digunakan oleh resep,
agar input tidak diam-diam diabaikan.

## Struktur dan tanggung jawab

```text
src/                             engine numerik dan model asli
framework/
  config/                        normalisasi parameter bersama
  components/                    kontrak dan spesifikasi komponen
  simulation.lisp                dispatch dan lifecycle run
  materials/                     constructor dan method chalk khusus
  scenarios/
    cliff/                       geometri, assembly, solver, run
    joss/                        material/base, statistik, fase, output
    triaxial/                    material, geometri, boundary, ukur, run
  output/                        penulisan plot yang sudah ada
cases/                           komposisi eksperimen pendek
scripts/run-case.lisp             launcher Windows tanpa server
tests/                           kontrak komponen dan kompatibilitas
```

Modul skenario tidak menyalin persamaan material dari `src/`. Variasi material
dan geometri dikirim melalui komponen/factory pada tiap run. Pengukuran
triaxial memakai konteks yang diikat lokal untuk satu run; input konfigurasi
tidak dimutasi. Jalur lama `scripts/run-triaxial.lisp` dan entry Lisp tebing
tetap tersedia sebagai adapter kompatibilitas. Tidak ada perubahan UI.

## Reproduksi dan pemeriksaan

Launcher menyalin source framework, kasus, schema dan JSON input sebelum
memuatnya. ASDF harus benar-benar memuat salinan tersebut; kegagalan pemilihan
source menghentikan run. Identitas dependency/FASL/DLL engine merupakan
provenance terpisah. CSV/VTK berisi hasil solver, sedangkan Python hanya
membaca hasil untuk audit dan visualisasi.

Untuk menilai refactoring, bandingkan seluruh field VTK yang tersedia,
kurva CSV, massa, jumlah partikel, waktu akhir, dan status penyelesaian.
Triaxial 2D dibandingkan dengan adaptasi 2D minimal dari kode sebelum
refactoring. Benchmark lama 3D menjadi konteks tambahan: plane strain tidak
memiliki kondisi tegangan lateral yang sama dengan silinder 3D, sehingga
kurva proyeksi q keduanya tidak boleh dianggap identik.

Baseline 2D dengan satu partikel per arah sel gagal karena pembesaran domain
melewati batas penghapusan partikel bawaan engine. Percobaan tersebut dan
pemeriksaan massa yang menangkapnya dipertahankan. Pembandingan lengkap
memakai dua partikel per arah sel pada kedua versi; engine tidak diubah.

Untuk tebing, fresh-start sebelum dan sesudah refactoring dibandingkan
tersendiri dari video pilot historis yang memakai warm start. Perbedaan
historis tidak boleh dilabeli sebagai akibat refactoring tanpa pembandingan
tersebut. Kesamaan hasil kode tidak otomatis menetapkan validitas ilmiah model.
