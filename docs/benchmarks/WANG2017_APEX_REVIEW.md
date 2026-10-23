# Wang2017: diagnosis apex dan studi kecepatan

Status23Oktober2026: diagnostik0.005m/s berhenti setelah state tersimpan15.4s/
77mm. Input return yang benar-benar gagal kini tersedia dan replay identik
sudah lulus. Penolakan tersebut tidak diselesaikan dengan mengganti enumerasi
active set: ada batas kelayakan dari model yang sedang digunakan.

## Mengapa return dilatansi nol ditolak

Untuk potensial geser MC dengan psi0, arah flow memiliki trace nol. Koreksi
plastis dengan elastisitas isotropik karena itu mempertahankan mean trial tau.
Sementara itu, semua stress yang admissible pada MC perfect memenuhi
`mean(tau) <= J*c*cot(phi)` bila kohesi diberikan sebagai stress Cauchy.
Pada state aktual: mean42985.3710489162Pa, J1.0032291051924629, batas
42982.78940658873Pa. Selisih2.58164232747Pa membuat return yang sekaligus
mempertahankan flow itu tidak tersedia. Ini diagnosis state lintasan dipercepat,
bukan bukti bahwa lintasan kecepatan paper pasti mencapai state yang sama.

## Perbandingan dengan implementasi asli

`tests/materials/mc-legacy-apex-comparison.lisp` menjalankan **5 kontrol Windows
native**, exit0, tanpa timestep MPM. Actual loaded `kirchoff.dll` dan entry
`CppMohrCoulomb` diperiksa melalui API Windows; enam modul strict serta backend
legacy cocok dengan bytes snapshot diagnostik. Hasil:

| Return pada input trial yang sama | Mean tau (Pa) | Increment volume plastis |
| --- | ---: | ---: |
| Strict psi0 | ditolak | input tetap utuh |
| Legacy, argumen c30000 |42844.440202 |1.05698135e-5 |
| Legacy, argumen c=J*30000 |42982.789407 |1.93623175e-7 |

Kode C++ `libs/src/constitutive.h` secara eksplisit menetapkan stress apex pada
cabang ini. API legacy tidak menerima J, sedangkan updater membagi stress return
dengan J. Argumen J*c diperlukan untuk perbandingan kohesi Cauchy yang sama.
Kontrol pure shear yang admissible menghasilkan stress principal±24653.915172Pa
pada kedua implementasi dan trace increment plastis nol.

Jadi, keberhasilan legacy pada state tensile ini memakai konvensi flow volume
tambahan. Itu tidak membuktikan bahwa projector strict salah, dan tidak boleh
diaktifkan diam-diam sebagai perbaikan yang mempertahankan semua persamaan.

## Dukungan sumber primer dan batas penerapannya

Manual [GEO FEM, bagian2.3.7](https://data.fine.cz/handbooks-chapter-pdf/geo5_fem_theoretical_guide.pdf#page=57)
membahas singularitas apex ketika psi0 dan memakai flow associated di apex.
[Itasca](https://docs.itascacg.com/itasca950/common/models/mohr/doc/modelmohr.html)
menyatakan cabang tensile tersendiri dengan flow associated pada model komposit.
[Abaqus](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-mohrcoulomb.htm)
memisahkan potensial geser dari opsi tensile Rankine. Ketiganya menunjukkan
perlunya menyatakan konvensi tambahan; bukan izin untuk menyebutnya flow psi0
yang tidak berubah. Paper Wang tidak memberi konvensi apex rinci dalam teks
yang tersedia. Tidak ada konvensi baru yang diaktifkan pada model kita di tahap ini.

## Studi berikut: rate0.002

`cases/benchmarks/wang2017-soil1-rate-002.lisp` mempertahankan model strict,
E/nu/c/phi/psi, density, geometri, mesh, timestep scale, damping, penalty dan
kondisi batas. **Tiga kontrol native konfigurasi lulus**: hanya velocity,
derived duration, jumlah frame dan batas komputasi berubah. Target0.1m pada
0.002m/s membutuhkan50s;251 frame mempertahankan cadence0.2s; cap375000updates
berskala2.5 terhadap150000 pada20s. Cap ini batas komputasi, bukan mass/time scaling.

Run baru dimulai14:35:52WIB dari68efa27, batas5jam, output
`output/wang2017-reference-2026-10-23/rate-002-001/`. Ini20x kecepatan paper,
sebuah uji pengaruh laju, bukan reproduksi reference-speed atau jaminan lolos.

**Pembaruan24Oktober:** run tersebut terputus setelah6.4s/12.8mm, bukan aktif lagi.
Exit native tidak diketahui.33state konsisten tetap utuh; proses dan pengawas
hilang, berdekatan dengan logoff Windows. Tidak ada capsule MC, sehingga tidak
ada kegagalan apex baru untuk direplay. Tujuh pasangan displacement identik
dengan fast005 sampai12mm memperlihatkan perbedaan reaksi akhir-1.75%; ini belum
konvergensi laju. Pengguna kini memilih0.01m/s ke60mm/6s untuk uji cepat,
didokumentasikan pada [panduan uji](WANG2017_FAST_TRIAL.md).
Jika domain infeasible masih tercapai, simpan failure dan bandingkan pada
penurunan yang sama. Jangan mengendurkan toleransi atau berulang kali memperlambat
tanpa diagnosis. Keputusan model tensile/apex memerlukan konvensi eksplisit dan
pengujian tersendiri; cabang lama/default harus tetap kompatibel.
