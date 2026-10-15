# Audit keaslian dan validitas ilmiah simulasi runtuhan

Tanggal: 15 Oktober 2026. Kasus: pilot native Windows `dp-physical-pilot`,
40 s/174 frame, tersimpan pada commit `cd5e07f`. Panduan fresh start/config
dipublikasikan pada commit `8549c32`. Audit tidak mengubah keluaran pilot,
konfigurasi yang diterima, atau metode solver produksi.

## Kesimpulan

**Bukti yang diperiksa mendukung bahwa runtuhan merupakan keluaran solver MPM
nyata; tidak ditemukan posisi, damage atau waktu keruntuhan yang dipaksakan
untuk meniru video referensi. Namun, hasil ini belum dapat dinyatakan
tervalidasi ilmiah atau setara dengan implementasi paper.** Audit menemukan
perbedaan model serta masalah numerik yang memerlukan pemeriksaan lebih lanjut.
Penerimaan visual pengguna tidak menggantikan validasi tersebut.

| Pertanyaan | Hasil audit |
| --- | --- |
| Apakah gambar/video berasal dari data partikel? | Ya, seluruh 174 PNG fisik diregenerasi identik dari VTK/CSV; video cocok dalam galat kompresi H264. |
| Apakah kode memberi lintasan runtuh/damage buatan? | Tidak ditemukan dalam jalur yang diperiksa. Posisi, tegangan, damage dan waktu dihitung solver. |
| Apakah run sepenuhnya tanpa intervensi numerik? | Tidak. Ada warm start, perubahan kelas/parameter, dasar elastis terlindungi, mass scaling, damping dan reset kecepatan yang harus dinyatakan terbuka. |
| Apakah hasil sudah valid sebagai prediksi fisik? | Belum: ada temuan kernel nonlocal, agregasi fragmen, kontrak F-bar, dan verifikasi energi/konvergensi yang belum selesai. |

## 1. Pemeriksaan artefak yang benar-benar dijalankan

Parser audit independen membaca **semua 174 VTK fisik**, bukan hanya gambar
akhir. Setiap frame memiliki 4.155 partikel dan 36 array skalar finite. Massa
tetap **425664,0625 kg/m**; massa/indeks material/identitas yang tersimpan tidak
berganti antar-frame. Damage tiap partikel tidak menurun. Seluruh 496 partikel
dasar memiliki damage dan regangan plastis nol, sesuai perlindungan eksplisitnya.

Perubahan posisi konsisten dengan displacement yang tersimpan sampai galat
maksimum sekitar **8,1e-13 m**. Titik pusat massa bergeser dari sekitar
`(8,132; 7,572) m` ke `(11,131; 4,992) m`. Damage pertama tersimpan pada t=4 s,
maksimum 0,3335893245; rata-rata berbobot massa akhir 0,4936730234.
Semua pusat partikel tetap berada dalam jendela gambar; tidak ditemukan massa
partikel yang hilang karena keluar viewport. Beberapa domain partikel melewati
batas x=31 m sedikit, sehingga gambar tetap merupakan crop viewport.

Semua 174 PNG tersimpan dapat dibuat ulang **pixel demi pixel identik** dengan
renderer, VTK dan waktu CSV yang sama. Video memiliki 175 frame karena menyertakan
keadaan awal. Setelah decoding, perbedaannya terhadap PNG sesuai kompresi H264:
galat RGB rata-rata terburuk 1,586/255 dan PSNR minimum 30,15 dB. Semua 35 berkas
pada manifest bundle awal cocok dengan hash dan salinan sumbernya. Sebanyak
174 entri step/waktu/fase log cocok dengan CSV dan seluruh transisi cocok.

Ini bukti integritas dan asal visual yang kuat, bukan pembuktian hukum fisika.
Mayoritas `unique-id=-1`, sehingga konsistensi urutan array tidak boleh disebut
bukti identitas global unik setiap MP. Snapshot VTK juga tidak merekam seluruh
grid, riwayat material, atau state integrator.

## 2. Intervensi historis yang harus diungkapkan

Pilot menggunakan [skrip kelanjutan yang disimpan](evidence/joss-collapse-2026-10-15/sources/continuation.lisp),
bukan menjalankan contoh Joss asli tanpa perubahan:

- Baris 5–21 memasang subclass DP dan guard damage/plastisitas untuk dasar.
- Baris 78–90 mengganti kelas partikel, mengelompokkan dasar/cliff melalui indeks
  dan menetapkan parameter run. Ini tidak memberi damage atau perpindahan buatan.
- Baris 103–112 sementara mengganti fungsi constructor agar mengembalikan sim
  yang sudah setimbang; hook environment mematikan plotting gnuplot.
- Baris 31–70 memasang pause/resume berdasarkan waktu dinding. Hook ini tidak
  memajukan waktu solver dan tidak mengubah posisi/damage.

Keadaan probe setelah 1.658 update dan `initial.vtk` pilot memiliki posisi serta
semua field tersimpan yang sama, kecuali indeks material. Pemeriksaan elastis
tambahan mengubah posisi paling besar 9,19e-10 m dan damage tetap nol. Jadi
`initial.vtk` pilot adalah **keadaan setelah persiapan**, bukan keadaan geometri
mentah. Waktu persiapan dalam metadata mencakup persiapan probe sebelumnya.

Penetapan gravitasi, ukuran takik, material dan fondasi adalah input/asumsi model.
Hal tersebut berbeda dari memasukkan bentuk runtuhan akhir atau patch warna.
Tetapi subclass, pemilihan DP, perlindungan dasar dan perubahan parameter juga
bukan bukti bahwa model identik dengan paper atau data eksperimen.

Renderer semula mempunyai fallback `damage` hilang menjadi nol
(`scripts/render-particle-vtk.py:24`). Semua VTK pilot memiliki array damage,
sehingga fallback ini tidak digunakan dan tidak menyebabkan runtuhan palsu.
Untuk audit yang lebih ketat, input tanpa damage seharusnya ditolak secara eksplisit.

## 3. Alur perhitungan dan interpretasi waktu

Posisi diperbarui dari displacement grid di `src/core.lisp:633`. Driving damage
berasal dari tegangan undamaged DP (`studio/lisp/reference-joss.lisp:23`),
averaging nonlocal dan integrasi history/delay (`src/models/chalk.lisp:698`).
Clock solver bertambah dengan timestep integrasi (`src/damage/solver.lisp:57`).
Transisi fase bergantung pada rasio energi/work dan out-of-balance force,
bukan waktu kegagalan referensi (`studio/lisp/reference-joss.lisp:150`).

Fase accelerate memakai **mass scale 10000**, sedangkan collapse memakai 1.
Inersia/akselerasi dan timestep memang berubah dengan faktor ini. Waktu log
adalah waktu integrasi/konstitutif dengan jadwal tersebut, **bukan lintasan
dinamika dengan massa fisik tanpa scaling sepanjang run**. Pemeriksaan transisi
dilakukan tiap interval output (2 s pada accelerate pilot, 0,1 s pada collapse),
sehingga perubahan rezim dapat terlambat terdeteksi di dalam interval tersebut.

Mass scaling adaptif dan reset kecepatan saat kembali ke accelerate memang
dibahas pada Algorithm 1 paper; jadi keberadaannya bukan otomatis manipulasi.
Paper juga menyatakan trade-off kriteria transisi terhadap akurasi displacement.
Implementasi pilot tetap harus diuji sensitivitasnya, khususnya karena interval
accelerate pilot 2 s berbeda dari interval 1 s pada studi paper.
Lihat [paper resmi](https://www.sciencedirect.com/science/article/pii/S0266352X25005579),
bagian 4.2/Algorithm 1 (hlm.11) dan 6.2 (hlm.16).

## 4. Temuan uji native yang membatasi klaim ilmiah

Uji di bawah memakai Windows launcher dan fungsi engine asli. Input sintetis
dipakai **hanya untuk menguji sifat metode**, tidak dimasukkan ke video pilot.
Tidak ada fungsi produksi yang diganti dalam uji kontrol ini.

### A. Kernel transient nonlocal tidak memakai radius rusak pada kedua sisi

`src/damage/damage.lisp:891` mengirim radius **nominal** partikel pengumpul,
sedangkan baris 632 menggabungkannya dengan radius **rusak** tetangga.
Radius pasangan efektif menjadi `sqrt(R_i_nominal * R_j_damaged)`, bukan
`sqrt(R_i_damaged * R_j_damaged)` pada model pasangan simetris yang dibahas.
Asimetri ini merujuk pada kernel sebelum normalisasi; bobot averaging yang
sudah dinormalisasi sendiri memang tidak wajib simetris pada domain terbatas.

Kontrol dua MP memakai radius nominal 0,5 m, radius rusak 0,1/0,5 m dan jarak
0,3 m. Fungsi kernel asli menghasilkan bobot `A<-B=0,75759616` dan `B<-A=0`.
Radius rusak simetris menghasilkan nol untuk keduanya. Averaging engine asli
mengubah driving A dari 0 menjadi **43,1041 Pa** ketika driving B=100 Pa. Ini adalah
counterexample nyata terhadap kontrak kernel pasangan tersebut. Besar dampaknya
pada runtuhan yang diterima **belum diukur**. Temuan diwarisi dari engine,
bukan penambahan patch damage buatan oleh renderer.

Ada pula perbedaan bentuk kernel: `weight-func` menerima jarak kuadrat lalu
mengkuadratkannya lagi, menghasilkan `[1-(r/R)^4]^2`, sementara Eq.(33) pada
hlm.7 paper adalah `[1-(r/R)^2]^2` di dalam radius support. Untuk r=0,3 m dan
R=0,5 m, nilainya 0,75759616 versus 0,4096. Ini perbedaan implementasi yang
terpisah dari asimetri radius; memperbaiki radius saja belum menyamakan Eq.(33).

### B. Agregasi dapat menghubungkan fragmen melintasi ruang kosong

Fallback `src/aggregate.lisp:223` mencari support cell pada seluruh mesh jika
tidak ada kandidat lokal. Uji mesh h=1 m dengan celah kosong 8 m menunjukkan
empat node fragmen dikaitkan ke support cell dengan jarak **pusat cell 9 m**.
Matriks E asli memiliki
bobot hingga **10** dan **-9**. Jumlah bobot per baris tetap satu dan matriks
sparse produksi cocok dengan versi dense; konsistensi translasi tersebut tidak
menghilangkan coupling lintas celah.

Setup menggunakan flag okupansi cell/node yang eksplisit, tanpa integrasi
partikel. Ini membuktikan perilaku helper/agregasi pada kondisi terkontrol,
**bukan** bukti bahwa setiap fragmen pilot mengalami masalah tersebut.
Insidensi pada run penuh perlu direkam sebelum menganggap run-out tervalidasi.

### C. Jacobian F-bar dan volume/domain mengikuti besaran berbeda

Uji satu MP dengan displacement nodal tidak seragam yang ditentukan sebagai
input memakai assembly GIMP asli (9 node support), tanpa respons konstitutif
atau integrasi waktu. Dengan F-bar aktif, `V/V0=1,025`, tetapi `det(F)` dan rasio
luas domain sama dengan **1,02375**. Dengan F-bar mati ketiganya **1,025**.
`src/core/stress-update.lisp:272` menyimpan gradient hasil F-bar, sedangkan
baris 276 memperbarui volume dari increment tanpa F-bar; `update-domain-det`
memakai determinant gradient tersimpan (`src/core/domain-update.lisp:501`).

Perbedaan ini terukur, tetapi **bukan otomatis kesalahan**: F-bar memang dapat
memisahkan kinematika untuk volume dan evaluasi tegangan. Yang belum tersedia
adalah kontrak teruji untuk konsistensi GIMP domain, volume, tegangan dan energi
pada kombinasi yang dipakai. Kontrol ini tidak mengukur galat runtuhan pilot.

## 5. Yang belum divalidasi

- DP driving, statistik agregat dan integrasi damage Heun adaptif merupakan
  adaptasi kode penulis; bukan implementasi literal semua persamaan paper.
- E=1 GPa mengikuti prosa/kode; Table 5 menyebut 100 MPa. Pilot memakai
  Gf=4,8 J/m², sedangkan set tabel/prosa utama memakai 48 J/m². Perbedaan input
  ini tidak boleh disembunyikan sebagai kecocokan paper.
- Energi/work yang tersimpan merupakan monitor transisi. Belum ada neraca
  lengkap energi potensial, elastis, plastis/fraktur, damping, transfer PIC
  dan energi yang hilang saat reset kecepatan.
- Belum ada studi konvergensi mesh/timestep/jumlah MP, sensitivitas interval
  transisi/mass scaling, dan pembandingan material terhadap eksperimen.
- Bentuk akhir pilot masih memiliki retreat dan run-out yang lebih besar dari
  referensi; penerimaan visual tidak mengubah hasil pengukuran ini.
- Konsistensi artefak tidak dapat membuktikan ulang identitas setiap FASL yang
  dimuat pada proses historis. Source, log dan snapshot disimpan, tetapi tidak
  ada capture lengkap binary/runtime historis.

Karena itu, **tidak ada dasar untuk memberi sertifikat “100% valid ilmiah”**.
Hasil saat ini layak disebut eksperimen MPM dengan keluaran autentik dan batas
metode yang diungkapkan. Klaim prediksi fisik memerlukan penyelesaian temuan
dan pengujian di atas; mengganti label metadata menjadi “validated” bukan solusi.

## 6. Bukti dan langkah berikutnya

Artefak audit native/forensik berada di `output/scientific-audit-2026-10-15/`.
[Bundle bukti audit](evidence/scientific-audit-2026-10-15/README.md) mempertahankan
skrip, hasil kontrol dan ringkasan audit beserta hash.

**Replay fresh native 4 s selesai dengan exit 0:** proses SBCL baru memakai
entry compiler/cache `run-fast.lisp` yang hanya memanggil produksi `main`;
tidak ada replacement constructor, kelas pilot historis atau environment hook.
Konfigurasi berasal dari panduan, hanya dibatasi target 4 s dan dua frame.
Equilibrium konvergen 1.658 update, massa tetap dan semua 36 field finite pada
empat snapshot. Damage maksimum 0,333589398 di `(13,1253; 3,6250) m`, dasar
tetap nol. Terhadap pilot historis pada t=4 s, beda posisi maksimum 9,30e-10 m
dan beda damage maksimum 1,18e-7. Jadi inisiasi bawah dapat direproduksi tanpa
hook warm start; hasil ini **bukan replay penuh 40 s** atau validasi ilmiah.

Prioritas berikutnya adalah memverifikasi/memperbaiki kontrak kernel pasangan,
mengukur coupling agregasi pada fragmen run nyata, menetapkan kontrak F-bar,
lalu menguji energi dan konvergensi. Parameter tidak boleh diubah diam-diam
hanya agar gambar tetap terlihat seperti runtuhan yang telah diterima.
