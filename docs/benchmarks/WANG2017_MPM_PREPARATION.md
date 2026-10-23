# Persiapan Wang 2017 dengan MPM

Keputusan pengguna pada23Oktober2026: **"Tetap MPM, ikuti input paper"**.
Branch: `codex/wang2017-reference-preparation`. Target sekarang adalah input
fisik Section2 Wang2017, bukan eksperimen J2 clay-creep sebelumnya. Metode MPM
tetap digunakan; metode FEM/local arc-length paper bukan bagian dari klaim ini.

Acuan: [Wang et al.,2017, DOI10.1007/s11629-016-3951-1](https://doi.org/10.1007/s11629-016-3951-1),
[salinan publik yang diunggah penulis](https://www.researchgate.net/profile/Qiguo-Rong/publication/312201146_Stability_analysis_of_slope_in_strain-softening_soils_using_local_arc-length_solution_scheme/links/59cdde08aca272b0ec164432/Stability-analysis-of-slope-in-strain-softening-soils-using-local-arc-length-solution-scheme.pdf).
Table1/Figure2 berada di halaman cetak179, Figure3–4 di180, dan definisi history
pada Eq5–6 di178. Teks salinan penulis dibaca ulang melalui web; unduhan lokal
ditolak layanan, sehingga gambar/endpoint kurva belum diverifikasi ulang.

## Parameter yang disiapkan

Kontrak pusat: [mpm-reference-contract.json](../../research/references/wang2017/mpm-reference-contract.json).

| Parameter | Soil #1 | Soil #2 |
| --- | --- | --- |
| Model | Mohr–Coulomb plastis sempurna | Mohr–Coulomb, kohesi melunak |
| E; nu; berat isi |20MPa;0,25;20kN/m³ | sama |
| Kohesi |30kPa konstan |30→15kPa |
| Friksi; dilatansi |35°;0° | sama |
| Koordinat pelunakan paper | tidak dipakai |kps=0→0,02 |
| Kecepatan penurunan puncak |0,0001m/s | sama |
| Bidang penurunan |3m, x=7–10m | sama |

Geometri yang tercatat: lebar20m, base5m, kemiringan60°, puncak7+3m.
Massa jenis dihitung sebagai20000/g kg/m³. Tidak ada penggantian dengan material
J2, pengurangan kekuatan tersembunyi, mass scaling atau percepatan waktu fisik.

Soil #1 adalah kontrol kurva gaya–penurunan Figure3. Perilaku dengan reaksi
menjadi nol akibat pelunakan dibahas pada Soil #2/Figure4. Karena itu keberhasilan
Soil #1 tidak otomatis berarti longsor bebas atau keberhasilan Soil #2.

## Satu perintah persiapan Windows native

Dari PowerShell, tanpa Studio:

```powershell
Set-Location D:\MPM
.\scripts\prepare-wang2017.ps1 -OutputDirectory output\wang-reference-FRESH
```

Gunakan nama folder baru. Perintah ini membangun dua material native dan
mengompilasi case penuh/pilot, lalu membandingkan inputnya dengan kontrak paper.
**Tidak ada timestep atau simulasi lereng yang dijalankan.** Hasilnya:

- `native-inputs.json`: konfigurasi aktual, konstanta material dan pemeriksaan
  kekuatan pada beberapa history;
- `preparation-report.json`: setiap pemeriksaan input dan gap yang masih terbuka;
- `preparation-status.json` serta log native/audit dengan commit sumber.

Case Soil #1 yang tersedia:

| Case | Kecepatan | Target yang disiapkan | Durasi fisik |
| --- | ---: | ---: | ---: |
| `cases/benchmarks/wang2017-soil1-pilot.lisp` |10⁻⁴m/s |0,0001m |1s |
| `cases/benchmarks/wang2017-soil1.lisp` |10⁻⁴m/s |0,1m |1000s |

Target0,1m adalah target perbandingan implementasi; bukan endpoint paper yang
telah diverifikasi ulang. Pilot reference-speed1s sebelumnya sudah selesai.
Jangan mengulanginya sekadar untuk memperoleh bukti yang sama, atau memulai
run1000s sebelum gate berikut ditutup. Perkiraan lama dari pilot sebelumnya
sekitar2,35hari; ini estimasi historis, bukan jaminan runtime terbaru.

## Matriks fidelitas dan gate sebelum run penuh

| Bagian | Status | Tindakan berikut |
| --- | --- | --- |
| Konstanta Soil #1 dan kecepatan asli | diverifikasi dari konstruksi native | pertahankan input; bukan kurva tervalidasi |
| Tinggi relief |10m masih asumsi; Figure2 tidak memberi dimensi numerik | konfirmasi data geometri sebelum klaim identik |
| Batas bawah | kode mengunci x/y; tangensial paper belum pasti | verifikasi gambar/data; jangan mengubah diam-diam |
| Penurunan puncak | bilateral penalty dengan compliance | uji sensitivitas tracking/penalty dan bandingkan reaksi mentah |
| Inisialisasi | prestress/internal elastic state dipertahankan saat reset pelaporan | rekonsiliasi dengan reset strain yang disebut paper |
| Metode dan mesh | MPM eksplisit, grid1m/915MP; pilihan pengguna | lakukan sensitivitas; bukan FEM10820segitiga |
| Integrasi MC | fast trial lama gagal pada15,4s/77mm | capture/replay state lengkap sebelum run panjang |
| Soil #2 | primitive Eq5–6/state/law tersedia; adapter particle belum tersedia | lanjutkan projector dengan tensor history, lalu transport/rollback particle |
| Kurva referensi | belum didigitisasi/dibandingkan kuantitatif | simpan sumber dan toleransi sebelum penilaian |

Pada Soil #2, kps paper adalah norma tensor plastic deviatoric strain. History
native yang menjumlahkan increment equivalent-J2 tidak otomatis sama pada
lintasan nonproporsional. Menyalin angka0,02 ke history native tanpa pembuktian
tidak memenuhi target ini. Belum ada case Soil #2 yang memakai pengganti tersebut.

### Checkpoint history dan diagnostik native

Pada source `db71b63`, **17 kontrol history Wang,7 kontrol capture/replay dan34
kelompok regresi material MC lulus**, semuanya exit0 lewat launcher Windows.
System opsional `cl-mpm/models/wang2017` memisahkan norma tensor, state bertanda
dengan salinan milik sendiri, konversi shear engineering dan hukum kohesi Soil2.
Ini belum menjalankan particle Soil2 atau timestep lereng. Rincian kontrak dan
gate integrasi: [WANG2017_HISTORY_ADAPTER.md](WANG2017_HISTORY_ADAPTER.md).

Condition kegagalan MC sekarang membawa trial principal Kirchhoff, E,nu,J yang
benar-benar diberikan, history dan seluruh parameter law. Input disalin hanya
ketika gagal; persamaan, toleransi dan jalur proyeksi yang berhasil tetap sama.
CLI menyimpan `mc-integration-failure.json` ketika condition ini muncul selama
run, lalu membiarkan error asli menghentikan proses. File ini adalah input
replay satu return material, **bukan checkpoint untuk melanjutkan seluruh MPM**.

```powershell
.\windows\cl-mpm.cmd scripts\replay-mc-failure.lisp `
  output\RUN\mc-integration-failure.json output\FRESH-replay.json
```

Fixture sintetis memakai J1.0123456789012345 dan particle native J1.1 untuk
menguji JSON/replay serta rollback. Keduanya **bukan J update Wang yang gagal**.
Kegagalan lama belum menjadi state aktual yang berhasil direkam hanya karena
fixture ini lulus. Tidak ada psi, tensile cap atau apex clamp yang diubah.

Kegagalan MC lama dekat tensile apex dengan dilatansi nol mempunyai reproducer
unit yang sudah ada. Trial mean tau42985,371Pa mensyaratkan J≥1,003289361 agar
`mean(tau) <= J*c*cot(phi)`; J aktual pada update gagal belum direkam. Penyebab
ini masih diagnosis bersyarat. Jangan mengubah psi, menambah tensile cap atau
melakukan apex clamp untuk membuat hasil lewat. Perbaikan retensi CSV saat
exception sudah tersedia; hilangnya CSV adalah kondisi snapshot lama.

Status paket: **input Soil #1 siap diperiksa; reproduksi kurva dan Soil #2 belum
terverifikasi**. Pengujian input, keberhasilan solver, dan validasi ilmiah adalah
tiga status yang berbeda.
