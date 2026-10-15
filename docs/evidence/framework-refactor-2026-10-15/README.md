# Bukti refactoring framework — Windows native, 15 Oktober 2026

**Status: triaxial 2D lulus identik; regresi numerik penuh Joss empat worker belum lulus.**
Bundle ini menyimpan hasil aktual dan kegagalannya. Kemiripan gambar tidak
menggantikan hasil comparator. Bukti ini belum memenuhi syarat untuk menyatakan
seluruh refactoring lolos regresi numerik atau tervalidasi ilmiah.

## Run yang dibandingkan

| Kasus | Sebelum | Sesudah | Hasil |
| --- | --- | --- | --- |
| Triaxial 2D | Monolit asli `c749d32` dengan adaptasi plane strain yang disimpan | Framework pada commit `2f6476f` | 51 VTK identik byte; seluruh scalar, posisi dan CSV berbeda tepat 0 |
| Joss fresh start | Sumber Studio asli dibekukan sebelum refactor | Framework pada commit `2f6476f` | Keduanya selesai 40 s, tetapi 176 vs 191 frame; comparator ketat gagal |
| Joss historis yang diterima | Pilot warm start 174 frame | Framework 191 frame | Bukan urutan numerik identik; persiapan historis berbeda |

Tidak ada parameter fisika atau ambang damage yang disesuaikan agar hasil lulus.
Input Joss menggunakan resep fresh start yang diterima, empat worker,
`settleMaxSteps=3000`, toleransi equilibrium `0.0001`, dan target 40 s.
Compiler core menggunakan speed 3/safety 1. Plot tidak mengubah hasil solver.

Triaxial 2D adalah penampang plane strain lebar 70 mm, tinggi 140 mm dan tebal
satuan; **bukan silinder axisymmetric**. `F_zz=1`, sedangkan `sigma_zz` mengikuti
model material. Karena itu tegangan deviatorik J2 dan proyeksi triaxial berbeda.
Model clay tetap merupakan contoh total-stress undrained dengan parameter asumsi.

## Hasil kuantitatif Joss

| Ukuran | Fresh asli | Framework |
| --- | ---: | ---: |
| Frame fisik / waktu terakhir | 176 / 40 s | 191 / 40 s |
| Partikel / massa kg per m | 4.155 / 425.664,0625 | 4.155 / 425.664,0625 |
| Damage bawah > 0,05 pertama | 4,0 s | 4,0 s |
| Damage pada material awal y >= 9 m > 0,05 pertama | 7,5 s | 7,5 s |
| Tepi domain run-out di atas y=1,05 m | 31,01589046 m | 31,01587968 m |
| Rata-rata y partikel yang awalnya y >= 14 m, pada t=40 s | 8,17637462 m | 8,17579450 m |
| Damage rata-rata berbobot massa pada t=40 s | 0,493752770 | 0,493774239 |

Semua 178 VTK fresh asli dan 193 VTK framework, termasuk initial/equilibrium,
memiliki 36 scalar finite. Massa tetap dan 496 partikel dasar yang dilindungi
memiliki damage nol. Bukti ini menunjukkan integritas data dan runtuhan aktual;
bukan validasi hukum material, energi, konvergensi atau akurasi lapangan.

Comparator memakai toleransi titik per titik `atol=1e-8`, `rtol=1e-7` dan waktu
`1e-10 s`. Kriteria tersebut dipertahankan ketika hasil gagal. Pada 164 waktu
simpan yang sama, comparator memasangkan material melalui unique ID yang valid
atau koordinat referensi `x - displacement`; tidak memakai nearest current shape.
Tidak ada interpolasi waktu atau lintasan.

Pada t=40 s perbedaan posisi maksimum adalah **0,0811648 m**, RMS **0,00234568 m**.
Norma global relatif L-infinity adalah 0,00262289 dan juga gagal terhadap kriteria
yang sama. Posisi pertama melewati kriteria titik per titik pada 18,0 s; damage
pada 16,8 s. Urutan clock pertama berbeda pada indeks nol 159:
fresh asli 27,4 s dan framework 25,5 s. Peralihan fase adaptif kemudian berbeda.

Secara geometri, IoU domain partikel akhir fresh/framework adalah **0,99667193**;
historis/framework **0,96764183**. Angka ini menggunakan rectangle domain VTK asli,
viewport x=0–31 m, y=0–17,333333333 m, spacing 0,025 m dan pengecualian fondasi
y<=1,05 m. **IoU merupakan kemiripan bentuk numerik, bukan persentase akurasi fisik.**

Perbedaan sangat kecil pada awal run lalu berkembang pada fase fracture, konsisten
dengan akumulasi roundoff dalam runtime paralel. Penyebab ini **belum terbukti**
dari dua run tersebut. Kontrol deterministik yang memisahkan variasi runtime
sejenis dari perubahan refactor masih diperlukan sebelum menyatakan ekuivalensi.

## Isi bundle

- `joss-before/`, `joss-after/`: CSV, metadata, audit seluruh frame dengan SHA-256,
  snapshot VTK terpilih, dan gambar akhir aktual. Video framework berasal dari
  191 VTK/CSV aktual, H.264 1280x720, 30 fps, decode penuh lulus. FPS playback
  tidak sama dengan timestep solver. Fase akhir bernama `accelerate`; runtuhnya
  dikonfirmasi melalui posisi material, bukan nama fase.
- `triaxial-before/`, `triaxial-after/`: seluruh 51 VTK per run, CSV, hasil audit,
  gambar/video serta overlay dengan benchmark 3D lama sebagai konteks berlabel.
  Full `sigma_zz` tidak diekspor VTK 2D; audit tidak merekonstruksi nilai itu atau
  mengklaim qJ2 penuh telah dihitung ulang dari field yang tidak tersedia.
- `verification/`: comparator ketat, diagnostik norma global, clock yang sama,
  audit lokasi damage, hash sumber/config serta kontrol comparator. JSON besar
  disimpan sebagai `.json.gz` tanpa mengubah isinya.
- `bounded-cliff-mc/`: dua update native model Mohr–Coulomb melalui adapter cliff,
  satu VTK akhir, sumber yang dieksekusi, dan audit massa/finite. Ini bukti
  integrasi komponen; bukan kalibrasi MC atau run runtuhan penuh.
- `sources/`: sumber sebelum refactor, sumber framework yang disalin sebelum
  dieksekusi, launcher, input serta script comparator/render/audit yang digunakan.
  Identitas seluruh DLL/FASL/dependensi transitif tidak dibekukan komprehensif.
- `logs/`: log native dan pemeriksaan integrasi; kegagalan awal package lock CLI
  dipertahankan terpisah. Log tersebut tidak disamarkan sebagai run berhasil.
- `context/`: CSV/input run triaxial 3D sebelumnya untuk reproduksi overlay;
  tidak ada run 3D baru dalam checkpoint ini.
- `manifest.json`: ukuran dan SHA-256 setiap berkas, termasuk hash anggota arsip.
  Semua VTK penuh Joss tetap ada di output lokal; bundle memuat hash semua frame
  dan snapshot initial/equilibrium/awal damage bawah/atas/akhir.

## Memeriksa ulang

Dari `D:\MPM`, memakai interpreter analisis yang tersedia:

```powershell
$python = 'D:\MPM\toolchain\analysis-venv\Scripts\python.exe'
& $python scripts\compare-framework-runs.py --baseline output\framework-refactor-2026-10-15\triaxial-2d-before-mps2 --candidate output\framework-refactor-2026-10-15\triaxial-2d-after --output output\triaxial-regression-recheck.json
& $python scripts\compare-framework-runs.py --baseline output\framework-refactor-2026-10-15\joss-baseline --candidate output\framework-refactor-2026-10-15\joss-after --output output\joss-regression-recheck.json
```

Perintah kedua sengaja menghasilkan exit code 1 karena ketidaksamaan tersebut.
Tidak perlu menjalankan solver ulang untuk memeriksa data yang sudah tersimpan.
Sumber raw dan bukti lama tidak ditimpa. Kontrol lanjutan harus memakai folder
output baru dan ditambahkan sebagai bukti tersendiri.
