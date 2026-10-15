# Metode kalibrasi triaxial clay: diameter 70 mm, tinggi 140 mm

Metode dan batas interpretasi, 2026-10-15. Kasus ini memisahkan demonstrasi
native CL-MPM dari kalibrasi terhadap hasil laboratorium. Default model
chalk/cliff pada Studio tetap terpisah dari eksperimen ini.

## Spesimen, model, dan asumsi

Spesimen acuan berbentuk silinder, dengan `D0 = 0.070 m` dan `H0 = 0.140 m`
pada awal pembebanan geser. Luas analitisnya `A0 = pi*D0^2/4 = 0.0038484510 m2`
dan volumenya `0.00053878314 m3`. Sumbu aksial pada runner adalah **Y**;
sumbu **X–Z** membentuk penampang radial. Dimensi menentukan geometri dan
konversi gaya/luas, tetapi tidak menentukan kekakuan, kekuatan, kondisi drainase,
riwayat tegangan atau kecepatan pembebanan.

Pengguna mengonfirmasi kondisi undrained dan belum memiliki data laboratorium.
Contoh menggunakan **pendekatan undrained dalam tegangan total**: material
isotropik elastis–plastis sempurna melalui model native
`cl-mpm/particle::particle-vm`. Permukaan luluh J2 tidak bergantung pada tekanan.
Tidak ada retakan, pelemahan, ketidakseragaman atau lintasan keruntuhan yang
ditentukan sebelumnya. Spesimen seragam tidak harus membentuk shear band.
Visualisasi harus memakai posisi dan domain partikel hasil VTK; bentuk
menggembung atau retakan diagonal buatan bukan bukti hasil simulasi.

| Masukan demonstrasi | Nilai | Dasar dan interpretasi |
| --- | ---: | --- |
| Modulus Young `E` | 5 MPa | Skala elastis contoh; belum diukur pada clay ini |
| Rasio Poisson `nu` | 0.49 | Pendekatan hampir tak termampatkan; bukan kendala volume konstan |
| Skala kekuatan triaxial `su` | 25 kPa | Target selisih tegangan luluh mendekati `2*su = 50 kPa` jika `J` mendekati satu |
| Tekanan awal/sel | 50 kPa | Tegangan total isotropik awal dan confinement contoh |
| Massa jenis | 1800 kg/m3 | Masukan massa/inersia; berbeda dari parameter luluh VM `rho` |
| Damage/softening | Nonaktif | Tidak tersedia data untuk mengidentifikasi degradasi pascapuncak |

Parameter tersebut merupakan asumsi demonstrasi, bukan hasil kalibrasi clay.
`nu = 0.49` masih mengizinkan perubahan volume elastis; penyimpangan volume
harus diukur dan dilaporkan. Model satu fase ini tidak menghitung tekanan air
pori, aliran, saturasi, waktu konsolidasi, OCR atau lintasan tegangan efektif.
Tegangan awal isotropik diberikan sebagai prestress elastis dengan `F = I`
pada geometri awal penggeseran; tahap konsolidasi tidak disimulasikan.

[ASTM D2850](https://store.astm.org/d2850-26.html) menjelaskan pengukuran UU
dalam tegangan total tanpa drainase selama confinement dan kompresi.
[ASTM D4767](https://store.astm.org/standards/d4767) mencakup kondisi
terkonsolidasi isotropik kemudian undrained, dengan pengukuran beban aksial,
deformasi dan tekanan air pori. Ruang lingkup ini membantu menentukan metadata
laboratorium yang diperlukan. Implementasi ini **tidak menyatakan kepatuhan**
terhadap kedua standar tersebut.

## Grafik dan konvensi pengukuran

Sumbu horizontal menyatakan regangan aksial engineering dalam persen, sedangkan
sumbu vertikal menyatakan tegangan deviatorik dalam kPa, dengan kompresi positif:

```text
epsilon_a = (H0 - H)/H0                    [fraksi]
strain_pct = 100*epsilon_a                [%]
q = sigma_axial - sigma_radial            [Pa]
q_kPa = q/1000                           [kPa]
```

`H0` adalah tinggi pada awal penggeseran; koreksi seating atau konsolidasi
laboratorium harus dicatat. Pada mode MPM, kolom `axial_strain_pct` runner
berasal dari perpindahan platen yang diperintahkan. Boundary penalty dapat
menghasilkan penetrasi sehingga regangan platen tidak otomatis sama dengan
regangan spesimen yang diukur dari geometri partikel. Nyatakan sumber regangan
dan periksa selisih tersebut sebelum membandingkan dengan laboratorium.
Kolom `particle_extents_axial_strain_pct` mengukur perubahan tinggi berdasarkan
extents domain partikel dan dapat dipilih secara terpisah saat inisialisasi.

CL-MPM menggunakan komponen tensor dengan tarik positif. Untuk arah aksial Y,
`q = -sigma_yy + (sigma_xx + sigma_zz)/2`. Kolom `deviatoric_stress_kpa`
merupakan rata-rata berbobot volume dari selisih ini, sedangkan `q_j2_kpa`
adalah rata-rata invariant `sqrt(3*J2)`. Keduanya dapat berbeda pada medan
tegangan tidak seragam. Periksa ketidakseimbangan tegangan radial dan komponen
geser; jangan menyamakan keduanya tanpa pemeriksaan. Konversi tanda dan lintasan
tegangan pada tekanan sel konstan dapat dibandingkan dengan
[contoh verifikasi triaxial Itasca](https://docs.itascacg.com/itasca920/flac3d/zone/test3d/VerificationProblems/TriaxialCompressionTest/TriaxialCompressionTest.html).

Core mengintegrasikan regangan elastis Hencky dan mengembalikan tegangan
Kirchhoff `tau`, lalu menghitung tegangan Cauchy `sigma = tau/J`, dengan
`J = det(F)`. Regangan engineering pada grafik bukan `100*mp-strain`, karena
slot tersebut menyimpan regangan elastis/history setelah return mapping.
Untuk deformasi aksial homogen, regangan kompresi logaritmik adalah
`h_a = -log(1-epsilon_a)`.

Jika data berisi beban deviatorik terkoreksi `P`, gunakan `q = P/A_current`
sesuai konvensi alat. Jika berupa gaya platen total, lakukan koreksi tekanan
sel/piston yang sesuai terlebih dahulu. Pisahkan kurva dari gaya platen dan
kurva dari tegangan partikel. Rumus `A_current = A0/(1-epsilon_a)` hanya sah
jika volume konstan benar-benar diterapkan atau terukur. Jika tidak, gunakan
volume/geometri terukur. `V/H` merupakan estimasi luas rata-rata dan belum tentu
sama dengan luas kontak platen saat deformasi tidak seragam. Simpan `V/V0`,
`J` dan geometri dari simulasi.

## Konversi parameter luluh native dan pembanding analitis

`particle-vm` pada `src/models/plastic.lisp` meneruskan slot `:rho` ke return
map native. Baik `vm-yield-func` pada `src/constitutive.lisp` maupun
`vm_yield_func` pada `libs/src/constitutive.h` memakai
`f = sqrt(2*J2)/rho - 1`, dengan `J2 = s:s/2`. Jadi `rho` adalah skala
tegangan, **bukan massa jenis, kohesi atau `su` secara langsung**:

```text
q_tau = sqrt(3*J2)
q_tau,yield = sqrt(3/2)*rho
rho = sqrt(2/3)*(2*su) = sqrt(8/3)*su
su = 25000 Pa -> rho = 40824.829046 Pa -> q_tau,yield = 50000 Pa
q_Cauchy,yield = 50000/J Pa
```

Konversi ini mengikuti kode CL-MPM yang diperiksa. Pada notasi VM yang lazim,
parameter luluh uniaxial adalah `sigma_Y = q` (lihat
[formulasi VM Itasca](https://docs.itascacg.com/itasca920/common/models/vonmises/doc/modelvonmises.html)).
Memasukkan `su` langsung ke slot luluh VM menghasilkan kekuatan kompresi yang
keliru. Pencocokan `q_failure/2` dalam kompresi triaxial tidak membuat VM identik
dengan Tresca pada lintasan lain; kekuatan geser murni VM adalah
`q_yield/sqrt(3)`.

Dua pembanding elastis mempunyai kondisi batas berbeda. Untuk regangan kecil
dan tegangan lateral konstan, `q kira-kira E*epsilon_a` sebelum luluh. Untuk
lintasan homogen isokhorik yang dipaksakan secara terpisah,
`G = E/[2*(1+nu)]` dan `q_tau = 3*G*[-log(1-epsilon_a)]`. Pembanding kedua
menguji lintasan konstitutif; ia bukan solusi persis silinder dengan tekanan
permukaan. Periksa target luluh Kirchhoff secara terpisah dari keluaran Cauchy
dan respons MPM spasial.

## Inisialisasi parameter dari CSV

Helper `calibration/estimate-clay-parameters.py` membaca kolom wajib
`axial_strain_pct` dan `deviatoric_stress_kpa`; kolom tambahan diperbolehkan.
Helper hanya memakai data masukan dan **tidak membangkitkan kurva pengganti,
menjalankan solver, atau melakukan optimasi parameter native**.

```powershell
python calibration/estimate-clay-parameters.py --csv output/kasus/stress-strain.csv --output output/kasus/parameter-initialization.json --source-kind actual_simulation
```

Untuk data sendiri, gunakan `--source-kind user_data` (default); untuk data
sintetis gunakan `synthetic`. Label provenance merupakan pernyataan pemanggil,
bukan verifikasi asal data. Opsi `--elastic-max-strain-pct 0.4` memilih data
regangan kecil hingga 0.4%; `--strength-start-strain-pct 5` memilih data mulai
5% untuk estimasi kekuatan. Setiap jendela memerlukan sedikitnya tiga regangan
berbeda. Header tanpa satuan, nilai nonfinite, unloading, jendela tidak cukup
dan kemiringan elastis nonpositif menghasilkan error.

Untuk memakai regangan dari extents partikel, tambahkan
`--strain-column particle_extents_axial_strain_pct`. Default tetap
`axial_strain_pct`; pilihan kolom dicatat pada provenance JSON tanpa mengubah
CSV asli. Keduanya memakai persen. Perbedaan hasil `E` dapat mencerminkan
compliance boundary penalty, sehingga sumber regangan harus disebutkan.

`E` diinisialisasi melalui regresi linier dengan intercept: `q` dalam Pa
terhadap regangan fraksi. `su` diinisialisasi dari median `q` bagian akhir
dibagi dua, kemudian dikonversi ke `rho`. JSON mencatat hash masukan, rentang,
jumlah titik, intercept, R² dan variasi tegangan akhir. Median akhir tidak
membuktikan adanya plateau. Status selalu `parameter_initialization_only`;
hasil pada CSV simulasi bukan kalibrasi terhadap clay laboratorium.

Pemeriksaan helper menggunakan data analitis terpisah:

```powershell
python -m unittest discover -s calibration -p test_estimate_clay_parameters.py -v
```

Empat pengujian memeriksa kemiringan/intercept serta konversi kekuatan, validasi
masukan, kecukupan jendela dan pilihan kolom regangan. Pengujian ini tidak
menjalankan CL-MPM.

## Prosedur kalibrasi dan batas identifikasi

1. Simpan berkas laboratorium asli. Catat ID, UU/CU/CD, dimensi awal geser,
   tekanan sel/back pressure, bukti saturasi, riwayat konsolidasi/tegangan,
   laju, satuan serta koreksi alat/seating. Pertahankan data tekanan air pori
   dan volume bila tersedia; sepasang kolom strain–q tidak menggantikan metadata.
2. Pilih model yang mampu mewakili respons terukur. Identifikasi rentang elastis
   dan kriteria luluh/plateau untuk estimasi awal `E` dan `su`. Catat rentang
   dan definisi kegagalan; `E50` secant tidak otomatis sama dengan modulus awal.
   Hardening, pelemahan pascapuncak, anisotropi atau efek laju memerlukan model
   serta data yang sesuai.
3. Jalankan forward model native dan minimalkan residual tegangan pada regangan
   pengamatan dengan interpolasi keluaran solver. Laporkan batas parameter,
   bobot, rentang regangan dan ketidakpastian. Langkah optimasi ini belum
   dilakukan oleh helper inisialisasi.
4. Gunakan beberapa spesimen/confinement bila sesuai dan sisihkan satu spesimen
   atau lintasan sebagai holdout. Bila kekuatan berubah dengan confinement
   atau riwayat, satu parameter VM yang bebas tekanan tidak memadai. Model
   tegangan efektif memerlukan data dan validasi konsolidasi/air pori tersendiri.
5. Laporkan kurva terukur dan terhitung, residual serta manifest masukan/keluaran.
   Tanpa data terukur, gunakan label **demonstrasi native**. Pemulihan parameter
   sintetis disebut **synthetic recovery**, bukan validasi eksperimen independen.

Satu kurva monoton `q` terhadap regangan aksial dapat membatasi kekakuan efektif
dan kekuatan kompresi hanya dalam model/rentang yang dipilih. Kurva ini tidak
mengidentifikasi `nu`/kekakuan bulk, permeabilitas, tekanan air pori, parameter
critical state, panjang damage, energi retak atau friksi platen secara mandiri.

## Verifikasi sebelum interpretasi ilmiah

Lintasan material-point homogen mengisolasi update konstitutif native; silinder
MPM 3D juga menguji transfer partikel/grid, boundary, inersia dan diskretisasi.
Keberhasilan yang pertama tidak memvalidasi yang kedua. Simpan VTK awal dan
terdeformasi, lalu tampilkan hanya keadaan yang terekam.

Sebelum menyebut respons spasial quasi-static, bandingkan laju lebih lambat dan
timestep lebih kecil; periksa keseimbangan gaya serta energi kinetik/internal
bila tersedia. Bandingkan mesh dan jumlah partikel per sel; periksa pengaruh
platen, error confinement, keseragaman tegangan, massa, volume positif, nilai
finite serta perbedaan regangan platen/spesimen. Tetapkan pembanding dan
toleransi sebelum menyatakan kesesuaian. Kurva halus atau keluaran finite saja
belum membuktikan konvergensi.

`npm run check` dan `npm test` pada `studio` memeriksa kontrak software.
Eksekusi Windows SBCL membuktikan pelaksanaan native, sedangkan pembanding
analitis material-point mempunyai cakupan konstitutif yang lebih sempit.
Klaim validasi ilmiah memerlukan pembanding eksperimen/benchmark serta bukti
sensitivitas yang sesuai. Catat pemeriksaan yang benar-benar dijalankan,
termasuk kegagalan dan keterbatasannya, untuk setiap hasil.

## Implementasi dan hasil demonstrasi native

Jalankan dari PowerShell di `D:\MPM` dengan direktori keluaran baru:

```powershell
windows\cl-mpm.cmd scripts\run-triaxial.lisp calibration\triaxial-demo.json output\triaxial-kasus-baru
```

Untuk pembanding konstitutif homogen, gunakan `calibration/triaxial-homogeneous.json`.
Petunjuk lingkungan Python, video dan estimator berada pada
[calibration/README.md](../calibration/README.md).

![Partikel MPM 3D nyata dan kurva tegangan–regangan yang dihitung](evidence/triaxial-clay-2026-10-15/mpm/result.png)

Garis utama memakai pemendekan dari tinggi domain partikel; garis putus-putus
memakai displacement platen yang diperintahkan. Warna adalah ukuran regangan
plastis **native**, bukan damage. Ukuran VM native yang tersimpan bernilai 1,5
kali normalisasi equivalent plastic strain standar pada implementasi ini.
Tidak ada shear band atau bulging yang ditambahkan renderer.

| Pemeriksaan aktual | MPM spasial 3D | Titik material homogen |
| --- | ---: | ---: |
| Partikel visual / increment solver | 780 / 17.443 update | 5.133 / 1.000 increment |
| Frame tersimpan | 51 | 51 |
| Regangan platen akhir | 10% | 10% dari F |
| Regangan tinggi spesimen akhir | 9,89852% | 10% |
| q akhir | 50,00844 kPa | 50,01000 kPa |
| Tekanan lateral akhir | 50,02246 kPa | 50,00000 kPa |
| Volume drift maksimum absolut | 0,020016% | 0,019986% |
| Bias volume awal diskret terhadap silinder analitis | +3,4507% | +0,1615% |

Massa tetap dan semua field finite pada kedua run. Auditor membaca semua VTK
dan mencocokkan q, volume, energi kinetik serta displacement dengan CSV. Kontrol
native terpisah memeriksa tangent elastis (galat relatif 4,52e-6), pemetaan yield
VM dan kontrol tegangan lateral, serta hold hidrostatik 3D selama 20 update.
Empat unit test estimator lulus; ini menguji pengolahan data dan satuan, bukan
kalibrasi terhadap tanah nyata.

Estimator memberi inisialisasi E sekitar **4,627 MPa** jika memakai regangan
platen, **5,044 MPa** jika memakai tinggi spesimen, dan **5,010 MPa** pada
pembanding homogen. Skala su awal mendekati **25,00 kPa**. Ini memperlihatkan
pengaruh pemilihan ukuran regangan/compliance fixture; bukan bukti bahwa satu
kurva simulasi sudah mengidentifikasi seluruh parameter clay.

Boundary ujung berupa spring normal **bilateral** native tanpa tahanan
tangensial, bukan model contact unilateral/membran lengkap. Energi kinetik
terhadap energi elastis mencapai 3,9556% pada transien awal dan sekitar 0,7122%
di akhir. Rasio terhadap kerja platen terakumulasi setelah regangan 1% maksimum
0,3746%; kerja platen MPM adalah integral gaya yang diretifikasi, bukan neraca
energi bertanda yang lengkap. Belum ada studi konvergensi mesh/laju/timestep.

[Bundle bukti](evidence/triaxial-clay-2026-10-15/README.md) menyimpan CSV,
audit, seluruh VTK MPM terkompresi, video, kontrol, snapshot review dan hash.
Kedua run produksi belum memiliki snapshot persis sebelum load; batas provenance
itu dicatat. Launcher berikutnya menyimpan dan mengeksekusi snapshot harness;
jalur tersebut telah diuji melalui kontrol native terakhir.
