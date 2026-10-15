# Menjalankan kembali simulasi runtuhan melalui Windows native

Panduan ini menjalankan kasus Joss DP yang parameternya menghasilkan video
runtuhan yang telah Anda terima pada 15 Oktober 2026. Gunakan **PowerShell**
di Windows dan workspace **`D:\MPM`**. Tidak memerlukan WSL atau Studio UI.

Kode/bukti pilot asli disimpan pada commit **`cd5e07f`**, branch
`feat/studio-custom-constitutive-lisp-export`. Lihat
[video yang diterima](evidence/joss-collapse-2026-10-15/accepted-collapse.mp4)
dan [gambar akhirnya](evidence/joss-collapse-2026-10-15/accepted-collapse-t40.png).

**Perbedaan reproduksi:** pilot asli memanfaatkan keadaan setimbang yang sudah
tersimpan di proses SBCL, lalu memeriksa ulang satu update. Panduan ini memulai
proses baru dan menghitung equilibrium dari awal. Parameter material/geometri
dan durasi 40 s mengikuti pilot; identitas frame demi frame belum dibuktikan.
Audit ilmiah sedang berlangsung. Menjalankan perintah ini tidak otomatis
menjadikan hasilnya tervalidasi ilmiah.

## 1. Persiapan

```powershell
Set-Location D:\MPM
git branch --show-current
```

Branch yang digunakan: `feat/studio-custom-constitutive-lisp-export`.
SBCL, Quicklisp dan pustaka native telah disiapkan pada komputer ini. Untuk
komputer baru, ikuti [windows-setup.md](windows-setup.md) terlebih dahulu.
Launcher `windows\cl-mpm.cmd` menyiapkan lingkungan dan memuat engine asli.
Tidak perlu menyalin kode ke interpreter lain.

Konfigurasi siap pakai:
[`studio/reference/joss-bay-accepted-collapse.json`](../studio/reference/joss-bay-accepted-collapse.json).
File ini dibuat dari config pilot dan disesuaikan **hanya pada persiapan awal**:
`settleMaxSteps=3000`, `settleTolerance=0.0001`, serta enum JSON huruf kecil
sesuai schema. Input lama `accepted/config.json` dengan `settleMaxSteps=1`
merupakan rekaman warm start; jangan gunakan sebagai input fresh start.

| Parameter | Nilai |
| --- | ---: |
| Tinggi tebing / dasar | 15,5 m / 1 m |
| Domain horizontal / kemiringan bawah | 31 m / 78 derajat |
| Takik / segmen atas vertikal | 0,5 m / 6,8 m |
| Mesh / partikel per arah sel | 0,5 m / 2 |
| Massa jenis / E / nu | 1700 kg/m³ / 1 GPa / 0,24 |
| Gf / nonlocal length | 4,8 J/m² / 0,5 m |
| Ambang damage / delay | 18926,452 Pa / 10 s |
| Ductility / kohesi plastis | 53,599755 / 1965600 Pa |
| Worker / target waktu / cap frame | 4 / 40 s / 1000 |
| Mass scale fase accelerate / collapse | 10000 / 1 |

Mass scaling, transisi fase, damping, dan fondasi elastis adalah bagian metode
numerik yang harus diaudit; waktu yang dilaporkan bukan bukti kecocokan waktu
kejadian dengan eksperimen. Jangan mengganti ambang menjadi 40000 Pa jika ingin
mengulang parameter pilot: kandidat 40 kPa sebelumnya selesai tanpa runtuh.

## 2. Jalankan solver dan simpan log

Jalankan blok berikut dalam satu sesi PowerShell. Folder bertimestamp menjaga
agar bukti run sebelumnya tetap tersimpan.

```powershell
Set-Location D:\MPM
$runDir = Join-Path 'D:\MPM\output' ('joss-accepted-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $runDir | Out-Null

# Solver menulis VTK; gambar akan dirender dari VTK setelah run selesai.
$env:CL_MPM_REFERENCE_PNG = '0'
& .\windows\cl-mpm.cmd studio\lisp\run.lisp studio\reference\joss-bay-accepted-collapse.json $runDir 2>&1 | Tee-Object -FilePath ($runDir + '.log')
if ($LASTEXITCODE -ne 0) { throw ('SBCL gagal. Periksa ' + $runDir + '.log') }
```

Kompilasi pertama dapat memerlukan waktu. Selama persiapan akan ada log
`Settling`; setelah konvergen muncul `Step ...; physical time ...`.
Jika equilibrium tidak konvergen, runner berhenti. Jangan mengubah status gagal
menjadi berhasil atau melewati pemeriksaan tersebut untuk mendapatkan gambar.
`Ctrl+C` menghentikan run; keluaran parsial tidak sama dengan run selesai.

## 3. Periksa status penyelesaian

Masih pada PowerShell yang sama:

```powershell
$meta = Get-Content -Raw -LiteralPath (Join-Path $runDir 'reference-metadata.json') | ConvertFrom-Json
$meta | Select-Object complete, termination, physicalTime, frames, equilibrationSteps, scientificValidation
Get-Content -LiteralPath (Join-Path $runDir 'timesteps.csv') -Tail 5
```

Run sampai target memiliki `complete=True`, `termination=simulation-time`
dan `physicalTime=40`. `frame-limit` atau `equilibrium-not-converged` berarti
belum selesai. `scientificValidation=unverified` sengaja dipertahankan sampai
validasi tersendiri selesai. Status fase `collapse` bukan bukti bahwa tebing
benar-benar runtuh; periksa perubahan posisi partikel dan bentuk hasilnya.

Keluaran utama: `vtk\initial.vtk`, `vtk\equilibrium.vtk`, `vtk\sim_NNNNN.vtk`,
`timesteps.csv`, `transitions.csv`, dan `reference-metadata.json`.

## 4. Buat gambar dan video dari data VTK

Engine tidak memerlukan Python. Tahap visualisasi berikut memerlukan Python
dengan NumPy/Pillow dan FFmpeg. Pada komputer ini runtime berikut sudah tersedia:

```powershell
$pythonExe = 'C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $pythonExe -c 'import numpy, PIL; print("Renderer dependencies OK")'
```

Jika memakai Python sendiri, ganti `$pythonExe` dengan lokasinya dan pasang
`numpy` serta `pillow` pada interpreter tersebut. Kemudian:

```powershell
$frames = Join-Path $runDir 'rendered'
& $pythonExe scripts\render-particle-vtk.py --run-dir $runDir --output $frames --particle-shape rectangle --title 'Native Joss DP - computed damage'
if ($LASTEXITCODE -ne 0) { throw 'Render VTK gagal.' }

# 30 fps adalah kecepatan pemutaran, bukan timestep solver.
& .\windows\make-video.cmd $frames 30 (Join-Path $runDir 'simulation.mp4')
if ($LASTEXITCODE -ne 0) { throw 'Encoding video gagal.' }
Invoke-Item -LiteralPath (Join-Path $runDir 'simulation.mp4')
```

Renderer mengambil posisi, ukuran domain partikel dan nilai `damage` dari
setiap VTK. Waktu judul diambil dari CSV; warna memakai skala damage tetap 0–1.
Video baru dimulai dari frame solver pertama. Video pilot arsip juga menyertakan
keadaan awal t=0 sehingga jumlah frame berbeda satu; ini bukan tambahan langkah
fisika. Untuk inspeksi 3D/data, buka VTK langsung di ParaView dan pilih `damage`.

## 5. Audit integritas hasil

```powershell
& $pythonExe scripts\audit-particle-damage.py --run-dir $runDir --output (Join-Path $runDir 'damage-location-audit.json')
if ($LASTEXITCODE -ne 0) { throw 'Audit VTK gagal.' }
```

Audit memeriksa field finite, massa positif, damage dalam 0–1, perubahan massa
dan lokasi damage. Ini bukan pengganti validasi konstitutif, konvergensi mesh/
timestep atau pembandingan eksperimen. Bukti pilot dan batas klaimnya tersedia
di [bundle hasil yang diterima](evidence/joss-collapse-2026-10-15/README.md).

Panduan/config ini telah diperiksa konsistensinya dengan schema; **fresh full
replay melalui perintah di atas belum selesai diverifikasi saat panduan dibuat**.
Tidak ada konstanta bentuk runtuhan atau timeline referensi yang diberikan ke
renderer. Audit berikutnya memeriksa jalur solver dan asumsi numeriknya.
