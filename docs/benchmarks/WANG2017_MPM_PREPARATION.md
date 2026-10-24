# Persiapan Wang 2017 dengan MPM

**Perkembangan terbaru24Oktober:** native Soil2 strict sudah diimplementasikan,
tetapi trial pertamanya gagal pada return konstitutif. Model opsional dengan
tambahan aliran volumetrik apex kini menyelesaikan60mm/6s tanpa error; belum
ada longsor koheren. [Hasil, bukti dan studi endpoint berikutnya](WANG2017_APEX_TRIAL.md).
Tambahan fisika ini dinyatakan eksplisit, bukan hukum Wang yang identik.
Render halaman180 yang sudah tersimpan memverifikasi sumbu Figure3 sampai0,10m;
endpoint Soil2/Figure4–5 tetap belum terverifikasi.

**Selesai24Oktober:** pengguna memilih uji0.01m/s, penurunan60mm/**6s fisik**.
Run `fast-010-001` selesai nativeexit0 pada01:45:23WIB dan audit/video0 pada
01:46:32WIB;61frame native, belum ada longsor koheren.100x paper. Ini penurunan yang
sama dengan600s pada kecepatan paper, bukan durasi600s atau dorongan6m.
[Panduan dan batas uji cepat](WANG2017_FAST_TRIAL.md).

Run rate0.002 sebelumnya terputus pada6.4s/12.8mm, exit tidak diketahui; status
asli NATIVE_RUNNING tertinggal. Bukti proses/data dan24hash disimpan pada
`docs/evidence/wang2017-reference-2026-10-24/rate-002-001-interruption/`.
Kejadian logoff Windows berkorelasi dengan berhentinya keluaran; tidak ada bukti
kegagalan MC atau timeout terkontrol. [Diagnosis apex dan studi laju](WANG2017_APEX_REVIEW.md).

[Video parsial diagnostik002](../evidence/wang2017-reference-2026-10-23/diagnostic-fast-005-002-video/slope-descent.mp4):
78 frame asli0–15.4s, playback19.5s. Warna adalah native mc-kappa (history plastis),
bukan damage. Run berhenti karena integrasi MC; status INCOMPLETE tetap terlihat.
Kecepatan pembebanan0.005m/s adalah50x paper, berbeda dari kecepatan playback.

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
| Integrasi MC | kegagalan aktual15,4s/77mm sudah dicapture/replay; legacy menerima lewat perubahan volume plastis | studi0,002m/s aktif; tidak ada clamp tersembunyi |
| Soil #2 | primitive Eq5–6 dan projector coupled frame tetap lulus19 kontrol; adapter particle belum tersedia | nyatakan konvensi finite-strain/irreversibility, lalu transport/rollback particle |
| Kurva referensi | belum didigitisasi/dibandingkan kuantitatif | simpan sumber dan toleransi sebelum penilaian |

Pada Soil #2, kps paper adalah norma tensor plastic deviatoric strain. History
native yang menjumlahkan increment equivalent-J2 tidak otomatis sama pada
lintasan nonproporsional. Menyalin angka0,02 ke history native tanpa pembuktian
tidak memenuhi target ini. Belum ada case Soil #2 yang memakai pengganti tersebut.

### Checkpoint history dan diagnostik native

Bukti: [29 artifact hashes dan sumber/log](../evidence/wang2017-reference-2026-10-23/history-and-capture/README.md).
CLI frozen9267dcb lulus: rejection exit1 dengan capsule, replay exit0, positive
legacy MC exit0 dengan dua update/VTK. Fixture CLI awal yang tidak memicu error
tetap diarsipkan sebagai FAILED_TEST_FIXTURE, bukan PASS.

Setelah instruksi "jalankan!", diagnostik Soil1 baru dimulai23Oktober11:24WIB
di `output/wang2017-reference-2026-10-23/diagnostic-fast-005-002/`, sumberd60335a,
batas awal90menit; atas permintaan pengguna diperpanjang menjadi **3jam total,
sampai14:24WIB**. Solver yang sama terus berjalan melalui pergantian pengawas
yang diuji, bukan restart. Preset0.005m/s tetap **50x kecepatan paper**; tujuannya menangkap
input update gagal yang belum tersedia. Kasus/material/solver numerik tidak
dituning; full reference-speed1000s belum dijalankan. Status dan bukti peluncuran
ada di handover; jangan menggandakan run atau menafsirkan diagnostik sebagai
reproduksi kecepatan paper.

**Hasil diagnostik002:** native exit1 pada12:35WIB, setelah state terakhir yang
tersimpan15.4s/77mm. Perekaman berhasil: J aktual1.0032291051924629 dan semua
input return tersedia. Enam sumber MC cocok byte dengan snapshot yang dieksekusi;
replay JSON menghasilkan penolakan yang sama (exit0 kontrol replay). Mean trial
42985.3710489162Pa melebihi batas perlu MC perfect/psi0 sebesar2.581642Pa.
Kegagalan ini terjadi sebelum deadline baru.78 baris force/energy dan78 VTK
particle tetap utuh. Ini diagnosis lintasan dipercepat, bukan bukti bahwa run
kecepatan paper pasti gagal. Tidak ada parameter/clamp/toleransi yang diubah.

[15 artifact hashes dan bukti kegagalan aktual](../evidence/wang2017-reference-2026-10-23/diagnostic-fast-005-002-failure/README.md)
menyimpan raw VTK/CSV, sumber yang dieksekusi, capsule dan replay.
[12 hash pengujian/pergantian pengawas](../evidence/wang2017-reference-2026-10-23/monitor-extension/README.md)
terpisah dari hasil simulasi fisik.

Pada source `db71b63`, **17 kontrol history Wang,7 kontrol capture/replay dan34
kelompok regresi material MC lulus**, semuanya exit0 lewat launcher Windows.
System opsional `cl-mpm/models/wang2017` memisahkan norma tensor, state bertanda
dengan salinan milik sendiri, konversi shear engineering dan hukum kohesi Soil2.
Ini belum menjalankan particle Soil2 atau timestep lereng. Rincian kontrak dan
gate integrasi: [WANG2017_HISTORY_ADAPTER.md](WANG2017_HISTORY_ADAPTER.md).

Checkpoint berikutnya menambahkan **19 kontrol projector coupled Soil2 PASS**
dan smoke ASDF opsional exit0. Snapshot sepuluh sumber cocok sebelum/sesudah;
tidak ada perubahan numerik MC lama atau timestep MPM. Ini hanya prototipe
small-strain/frame tetap: seluruh akar diperiksa, solusi ambigu ditolak dan
reversal literal dapat mengurangi norma history. Native particle, transport
objektif dan interpretasi irreversible belum diaktifkan. Jangan menyamakan
point-test PASS dengan kurva Soil2/Figure4 yang tervalidasi.

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
`mean(tau) <= J*c*cot(phi)`; J pada snapshot lama52f9367 belum direkam. Diagnostic002
kini menangkap actual J dan replay yang sama, sebagaimana dijelaskan di atas.
Jangan mengubah psi, menambah tensile cap atau
melakukan apex clamp untuk membuat hasil lewat. Perbaikan retensi CSV saat
exception sudah tersedia; hilangnya CSV adalah kondisi snapshot lama.

Status paket: **input Soil #1 siap diperiksa; reproduksi kurva dan Soil #2 belum
terverifikasi**. Pengujian input, keberhasilan solver, dan validasi ilmiah adalah
tiga status yang berbeda.
