# Triaxial clay native Windows — diameter 70 mm, tinggi 140 mm

Contoh ini menggunakan model VM elastoplastik native CL-MPM sebagai pendekatan
**undrained total stress** dengan parameter asumsi: E=5 MPa, nu=0,49,
skala su=25 kPa, tekanan sel=50 kPa dan density=1800 kg/m³. Data laboratorium
belum tersedia. Ini demonstrasi dan metode awal kalibrasi, bukan parameter clay
terukur atau validasi eksperimen. Penjelasan lengkap ada pada
[metode kalibrasi](../docs/TRIAXIAL_CALIBRATION.md).

Ada dua perhitungan yang berbeda dan dinyatakan eksplisit:

| Mode | Yang dihitung |
| --- | --- |
| `mpm` | Partikel silinder 3D, transfer partikel/grid, tegangan native, tekanan isotropik dan batas displacement ujung. Posisi berasal dari update solver spasial. |
| `homogeneous` | Respons titik material native dengan kontrol tegangan lateral; F yang dihitung dipakai untuk memvisualisasikan silinder homogen. Ini bukan run MPM spasial. |

Mode homogen berguna sebagai pembanding konstitutif cepat. Jangan menyebut
visualisasi affine pada mode ini sebagai bukti munculnya shear band. Mode MPM
tidak memakai seed damage, hukum damage, mass scaling, agregasi atau F-bar.
Default tebing/chalk/Studio tetap terpisah.

## Menjalankan solver

Mulai dari PowerShell pada workspace ini. SBCL/Quicklisp/DLL menggunakan
launcher Windows yang sama dengan proyek utama.

```powershell
Set-Location D:\MPM
$runDir = Join-Path 'D:\MPM\output' ('triaxial-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .\windows\cl-mpm.cmd scripts\run-triaxial.lisp calibration\triaxial-demo.json $runDir 2>&1 | Tee-Object -FilePath ($runDir + '.log')
if ($LASTEXITCODE -ne 0) { throw 'Run triaxial gagal; periksa log.' }
```

Untuk pembanding homogen, ganti file config dengan
`calibration\triaxial-homogeneous.json` dan gunakan direktori output baru.
Runner menolak menimpa output yang sudah memiliki `stress-strain.csv`.
Periksa `manifest.json`: `complete=true` menandakan target run tercapai,
`spatialMPM` membedakan dua mode. Penyelesaian run bukan sertifikat validasi.

Keluaran terdiri dari `effective-config.json`, `manifest.json`,
`stress-strain.csv` dan `particles_0000.vtk` sampai frame terakhir.
`axial_strain_pct` pada mode MPM adalah regangan engineering **platen yang
diperintahkan**; `particle_extents_axial_strain_pct` merupakan diagnostik
terpisah dari tinggi domain partikel. Batas penalty memiliki compliance dan
kedua ukuran tidak harus identik.

## Gambar dan video dengan kurva di samping spesimen

Python dipakai hanya setelah solver selesai untuk membaca keluaran. Untuk
menyiapkan lingkungan plotting mandiri pada komputer lain:

```powershell
python -m venv toolchain\analysis-venv
& .\toolchain\analysis-venv\Scripts\python.exe -m pip install -r calibration\requirements.txt
```

Pada komputer ini lingkungan tersebut sudah tersedia. Masih pada sesi yang
memiliki variabel `$runDir`:

```powershell
& .\toolchain\analysis-venv\Scripts\python.exe scripts\plot-triaxial.py --run-dir $runDir --video
```

`triaxial-result.png` menempatkan partikel 3D di kiri dan kurva regangan (%)
terhadap tegangan deviatorik (kPa) di kanan. Garis utama memakai regangan dari
tinggi domain partikel; garis putus-putus MPM memperlihatkan regangan platen
secara terpisah. Warna berasal dari ukuran regangan plastis native
tersimpan. `triaxial-simulation.mp4` menampilkan perkembangan dengan kurva yang
bertambah mengikuti frame. Renderer tidak menghitung kurva maju atau menggambar
bulging/shear band tambahan. Hash sumber dicatat dalam
`visualization-provenance.json`. Encoder memerlukan FFmpeg pada PATH.

## Inisialisasi parameter dari CSV

CSV minimum menggunakan header berikut, tanpa mengganti satuan:

```text
axial_strain_pct,deviatoric_stress_kpa
```

Isi dengan data uji nyata jika tersedia. Untuk mencoba alur pada keluaran
simulasi, gunakan CSV run di atas dan nyatakan sumbernya:

```powershell
& .\toolchain\analysis-venv\Scripts\python.exe calibration\estimate-clay-parameters.py --csv (Join-Path $runDir 'stress-strain.csv') --output (Join-Path $runDir 'parameter-initialization.json') --source-kind actual_simulation
```

Helper mengestimasi kemiringan elastis awal E (default sampai regangan 0,4%)
dan skala su dari median q bagian akhir (default mulai 5%), lalu mengonversi
`rho_VM=sqrt(8/3)*su`. `rho_VM` adalah parameter tegangan luluh native,
berbeda dari massa jenis. Hasil ini **inisialisasi parameter**, bukan optimasi
forward native atau kalibrasi eksperimen yang telah selesai. Kurva simulasi
tidak diganti oleh garis regresi. Untuk data laboratorium, gunakan
`--source-kind user_data` dan simpan kondisi pengujiannya.

Untuk memakai pemendekan spesimen yang dihitung pada data MPM, tambahkan
`--strain-column particle_extents_axial_strain_pct`. Pilihan ini dicatat dalam
provenance dan tidak mengubah CSV asli.

## Pemeriksaan dan batas metode

- Simpan massa, volume drift, tekanan lateral, yield excess, regangan aktual
  spesimen dan energi kinetik sebelum menafsirkan respons sebagai quasi-static.
- Tekanan lateral memakai integral virtual-stress 3D. Batas ujung menggunakan
  spring normal bilateral displacement-controlled native, bukan simulasi membran
  atau contact platen unilateral lengkap. Tahanan tangensial tidak dipasang.
- Cylinder adalah diskretisasi material points dari dimensi nominal. Pada mesh
  kasar, volume/massa diskret dapat berbeda dari silinder analitis; perbedaan
  tersebut harus dilaporkan dan diuji dengan refinement.
- nu=0,49 hanya mendekati inkompresibilitas. Tidak ada solver air pori,
  konsolidasi, OCR atau klaim kepatuhan ASTM UU/CU.
- Monitor energi bukan neraca energi lengkap. Lakukan sensitivitas laju,
  timestep, mesh dan boundary sebelum menyatakan validasi fisik.

Pengujian helper:

```powershell
python -m unittest discover -s calibration -p test_estimate_clay_parameters.py -v
```
