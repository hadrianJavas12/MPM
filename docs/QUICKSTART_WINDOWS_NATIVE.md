# Panduan singkat: simulasi Windows native tanpa UI

Untuk file kasus modular yang baru, lihat
[framework reusable](REUSABLE_FRAMEWORK.md). Perintah lama di bawah tetap
tersedia untuk mengulang contoh triaxial 3D.

Panduan ini mengulang **simulasi triaxial clay diameter 70 mm, tinggi 140 mm**
beserta video dan kurva strain–deviatoric stress. Semua perintah dijalankan
melalui **PowerShell**, tanpa membuka Studio atau menjalankan server.

Pada komputer ini SBCL, Quicklisp, Python plotting dan FFmpeg sudah tersedia.
Untuk komputer baru, ikuti [persiapan Windows](windows-setup.md) dan
[persiapan Python plotting](../calibration/README.md#gambar-dan-video-dengan-kurva-di-samping-spesimen)
terlebih dahulu.

## 1. Buka PowerShell dan jalankan simulasi

Salin blok berikut. Folder hasil dibuat dengan tanggal/jam agar hasil lama
tidak tertimpa.

```powershell
Set-Location D:\MPM
New-Item -ItemType Directory -Force -Path .\output | Out-Null
$runDir = Join-Path 'D:\MPM\output' ('triaxial-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .\windows\cl-mpm.cmd scripts\run-triaxial.lisp calibration\triaxial-demo.json $runDir 2>&1 | Tee-Object -FilePath ($runDir + '.log')
if ($LASTEXITCODE -ne 0) { throw ('Simulasi gagal. Baca log: ' + $runDir + '.log') }
```

Tunggu sampai prompt PowerShell muncul kembali. Run 3D sebelumnya memerlukan
sekitar **15 menit** pada komputer ini; durasi dapat berubah. `Ctrl+C`
menghentikan run dan menyisakan hasil parsial.

## 2. Pastikan simulasi selesai

Gunakan **jendela PowerShell yang sama** agar variabel `$runDir` tetap tersedia.

```powershell
$hasil = Get-Content -Raw -LiteralPath (Join-Path $runDir 'manifest.json') | ConvertFrom-Json
$hasil | Select-Object complete, spatialMPM
if (-not $hasil.complete) { throw 'Run belum selesai; periksa log sebelum membuat video.' }
```

Untuk kasus ini, `complete` dan `spatialMPM` harus tampil **True**.
`complete=True` berarti target perhitungan tercapai.

## 3. Buat gambar dan video, lalu buka hasilnya

Masih pada jendela yang sama:

```powershell
& .\toolchain\analysis-venv\Scripts\python.exe scripts\plot-triaxial.py --run-dir $runDir --video
if ($LASTEXITCODE -ne 0) { throw 'Pembuatan gambar/video gagal; lihat pesan di terminal.' }
Invoke-Item -LiteralPath (Join-Path $runDir 'triaxial-result.png')
Invoke-Item -LiteralPath (Join-Path $runDir 'triaxial-simulation.mp4')
```

Hasil tersimpan di folder `$runDir`, di dalam `D:\MPM\output`:

| Berkas | Isi |
| --- | --- |
| `triaxial-simulation.mp4` | Video partikel di kiri dan kurva tegangan–regangan di kanan |
| `triaxial-result.png` | Gambar hasil akhir dengan kurva |
| `stress-strain.csv` | Data numerik kurva, regangan dalam % dan tegangan dalam kPa |
| `particles_*.vtk` | Data partikel dari solver untuk setiap frame |

Untuk membuka foldernya, jalankan `Invoke-Item -LiteralPath $runDir`.
Jika PowerShell terlanjur ditutup, isi ulang variabelnya dengan folder hasil
yang ingin dibuka, misalnya `$runDir = 'D:\MPM\output\triaxial-20261015-160000'`.
Ganti contoh tanggal/jam tersebut dengan nama folder yang benar di komputer Anda.

## Mengubah parameter atau memilih simulasi lain

- Parameter triaxial ada di `calibration\triaxial-demo.json`. Salin file itu
  sebelum mengubahnya, lalu ganti path config pada langkah 1 dengan salinan Anda.
- Untuk percobaan cepat, ganti config menjadi
  `calibration\triaxial-homogeneous.json`. Ini pembanding konstitutif homogen,
  **bukan simulasi MPM spasial 3D**; `spatialMPM=False` memang diharapkan.
- Untuk simulasi **runtuhan tebing** yang telah diterima, ikuti
  [panduan runtuhan Windows tanpa UI](RUN_ACCEPTED_COLLAPSE_WINDOWS.md).

Jika `ffmpeg` tidak dikenali saat membuat video, pastikan FFmpeg terpasang dan
tersedia pada PATH PowerShell; uji dengan `ffmpeg -version`.
Jika solver gagal, baca berkas `$runDir.log`; gunakan folder baru saat mengulang.

Contoh clay memakai parameter asumsi dan pendekatan undrained total stress,
tanpa perhitungan tekanan air pori. Ini belum merupakan kalibrasi terhadap
data laboratorium. Rincian metode ada di [panduan kalibrasi](TRIAXIAL_CALIBRATION.md).
