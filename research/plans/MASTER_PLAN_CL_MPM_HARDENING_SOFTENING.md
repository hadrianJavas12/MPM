# MASTER EXECUTION PLAN — CL-MPM Reusable Framework & Comparative Hardening–Softening Study

**Versi:** 1.0  
**Tanggal penyusunan:** 15 Oktober 2026  
**Repository:** `https://github.com/hadrianJavas12/MPM.git`  
**Branch kerja awal:** `codex/reusable-simulation-framework`  
**Baseline pembanding:** `main` — verifikasi SHA terkini sebelum bekerja  
**Eksekusi:** Windows / PowerShell / SBCL / Quicklisp / native CL-MPM / Python  
**Pemilik eksekusi:** ChatGPT Agent di laptop  
**Lingkup:** core simulation, constitutive model, data referensi, numerical experiments, testing, evidence, documentation, handover.  
**TIDAK TERMASUK:** pengembangan UI, Studio, frontend, web dashboard, visual editor, atau fitur antarmuka baru.

> **INSTRUKSI UTAMA AGENT:** Kerjakan roadmap ini dari M0 sampai M6 secara bertahap hingga hasil komparasi akhir tersedia. Jangan menunggu dataset kalibrasi laboratorium yang belum ada. **Jangan melakukan fitting/optimasi untuk memaksa cocok dengan kurva pada PDF.** Perlakukan PDF sebagai bahan referensi untuk mendefinisikan kasus ilustratif/benchmark eksploratif, bukan ground truth terkalibrasi. Selalu jujur mengenai status numerik dan status validasi ilmiah. **Jangan merge ke `main` tanpa persetujuan pengguna.**

---

## 1. Tujuan, hipotesis, dan keputusan yang sudah final

### 1.1 Tujuan

Bangun framework native CL-MPM yang reusable; kembangkan dan verifikasi satu keluarga **Mohr–Coulomb elastoplastic** dengan dua varian evolusi kekuatan; gunakan pada **simulasi triaxial** dan kemudian pada **simulasi tebing** untuk membandingkan efek post-peak softening.

- **Model H — Mohr–Coulomb Hardening-only:** kekuatan meningkat pada fase pre-peak hingga nilai peak dan **tidak turun** setelah peak (plateau/perfect-plastic post-peak).
- **Model HS — Mohr–Coulomb Hardening–Softening:** memakai evolusi pre-peak dan nilai peak yang sama, tetapi kekuatan **menurun** setelah peak hingga mendekati residual.
- **Opsional kontrol:** Mohr–Coulomb perfect plasticity tanpa hardening.

Dalam eksperimen *controlled comparison*, parameter awal yang bermakna harus identik: `E`, `nu`, densitas/berat isi, tegangan awal, kondisi tekanan lateral, geometri, boundary, loading, timestep/solver, serta *pre-peak hardening path*. **Variabel perlakuan utamanya hanyalah hukum kekuatan post-peak**. Semua penyimpangan wajib dicatat.

### 1.2 Pertanyaan penelitian

1. Bagaimana perilaku kurva tegangan–regangan triaxial berbeda antara Model H dan HS pada kondisi awal/pembebanan yang sama?
2. Bagaimana laju dan lokasi akumulasi regangan plastis, penurunan kekuatan, serta lokalisasi deformasi dipengaruhi hukum post-peak?
3. Apakah post-peak softening menyebabkan onset kegagalan lebih awal, progressive failure lebih luas, perubahan mekanisme runtuh, atau run-out berbeda pada tebing yang sama?
4. Seberapa sensitif perbedaan tersebut terhadap mesh, ukuran material point, timestep, koefisien softening, kondisi awal (`K0`), dan model dilatasi?

### 1.3 Keputusan terkait keterbatasan data

**DATA PDF BUKAN DATA KALIBRASI YANG MEMADAI.** Tidak perlu dan tidak boleh memaksakan fitting numerik terhadap grafik presentasi. Tidak perlu menciptakan kurva laboratorium sintetis yang lalu diberi label data nyata. Hasil studi tahap ini harus disebut **numerical comparative / parameterized demonstration / numerical verification**, bukan *validated calibrated prediction of residual soil*.

Jika data laboratorium asli lengkap kelak tersedia, kalibrasi dan validasi berbasis data dapat menjadi pekerjaan lanjutan **di luar jalur kritis** rencana ini. Ketiadaan data tersebut **tidak menghentikan eksekusi M0–M6**.

### 1.4 Pembedaan ilmiah wajib

- Kode triaxial native yang sebelumnya menggunakan `particle-vm` **belum** merupakan Mohr–Coulomb dan bukan simulasi fisika CU lengkap.
- **2D plane-strain tidak sama dengan 2D axisymmetric**; yang ditampilkan pada PDF untuk spesimen silinder adalah axisymmetric. Gunakan **MPM 3D silinder sebagai perbandingan utama** bila backend axisymmetric belum tersedia. Kasus 2D plane-strain hanya sanity/regression/perbandingan internal dengan label yang tepat.
- Dokumen menyebut *CU*, tetapi implementasi yang tidak menghitung pore pressure/undrained effective-stress path **tidak boleh diklaim mereproduksi uji CU sejati**. Sebut *CU-inspired triaxial compression / total-stress surrogate / drained-effective-stress idealization* sesuai implementasi aktual.
- Hindari menyamakan regangan aksial total, regangan geser plastis, regangan plastis deviatorik, dan *equivalent plastic strain*. Konvensi internal harus dinyatakan eksplisit.
- Skenario Joss yang memakai keluarga material chalk/damage **bukan otomatis** material residual soil Mohr–Coulomb. Gunakan Joss untuk regresi software; buat kasus tebing komparatif tersendiri untuk dua model penelitian.

---

## 2. SUMBER DATA YANG HARUS DICATAT DALAM PROYEK

### 2.1 Sumber primer numerik yang diberikan pengguna

**Nama file:** `Numerical Simulation Residual Soil TRX CU SIGMA ^0 FLAC_290825.pdf`  
**Tipe:** slide presentasi, **28 halaman**, berisi tabel input, kurva komparasi, dan gambar hasil SIGMA/W / FLAC2D; **bukan raw time series laboratorium**.  
**SHA-256 file terunggah:** `acd60b668e3b6ed8c7a7378ae3afd053ca0419f4ed63aecc0031b019495f3979`  
**Perlakuan data:** transkripsi nilai eksplisit dari tabel; grafik tidak digunakan untuk fitting; dokumentasikan halaman sumber setiap nilai. Apabila PDF tidak tersedia di laptop, tabel transkripsi dalam dokumen ini tetap boleh dipakai sebagai **reference case**, tetapi agent wajib mencatat keterbatasan bahwa gambar sumber tidak dapat diaudit secara lokal.

### 2.2 Geometri dan kondisi triaxial dari PDF

| Data | Nilai tertulis | Sumber PDF | Status penggunaan |
|---|---:|---|---|
| Diameter spesimen | 7 cm = 0,07 m | Hal. 3 | Geometri acuan |
| Tinggi spesimen | 14 cm = 0,14 m | Hal. 3 | Geometri acuan |
| Radius model axisymmetric | 3,5 cm | Hal. 3 | Referensi gambar, **bukan** model plane-strain |
| Tekanan sel / confining pressure | 100 dan 200 kPa | Hal. 6 | Matriks eksperimen triaxial |
| Tekanan sel untuk bagian SSoft FLAC | 200 kPa | Hal. 10 | Skenario referensi berbeda |
| Tahap 1 | Pemberian `σ3`, isotropic elastic | Hal. 4 | Referensi prosedur, bukan bukti CU lengkap |
| Tahap 2 | Kompresi melalui prescribed vertical displacement terhadap waktu | Hal. 5 | Prosedur loading acuan |
| Elemen model contoh FLAC | `1 × 1 grid`, axisymmetric | Hal. 13 | *Element-test illustration*, bukan resolusi mesh untuk MPM |

### 2.3 Properti residual soil — transkripsi tabel halaman 6

`—` = tidak diberikan pada sel dokumen tersebut; **jangan isi sebagai angka hasil uji**.

| Parameter | Unit | Laboratory test (slide) | SANICLAY (slide) | MC Hardening/Softening (slide) | MC biasa (slide) |
|---|---|---:|---:|---:|---:|
| Confining pressure | kPa | 100, 200 | 100, 200 | 100, 200 | 100, 200 |
| Initial void ratio `e0` | — | 1.25 | 1.25 | 1.25 | 1.25 |
| Unit weight | kN/m³ | 16.83 | 16.83 | 16.83 | 16.83 |
| OCR | — | — | 1 | — | — |
| K0nc | — | 0.72 | 0.51 | 1.0 (default) | 0.441 (default) |
| Compression index `Cc` | — | 0.26 | 1.5 | — | — |
| Consolidation coefficient `Cv` | cm²/s | 0.0032 | 0.0032 | — | — |
| Recompression index `Cr` | — | 0.01 | 0.05 | — | — |
| Normal consolidation slope `λ` | — | 0.113 | 0.651 | — | — |
| Swelling slope `κ` | — | 0.004 | 0.022 | — | — |
| Effective Poisson ratio `ν'` | — | 0.2 | 0.2 | 0.2 | 0.2 |
| Effective elastic modulus `E'` | kN/m² | — | — | 20,000 (=20 MPa) | 20,000 (=20 MPa) |
| Critical stress ratio compression `Mc` | — | 0.561 | 0.621 | — | — |
| Critical stress ratio extension `Me` | — | 0.280 | 0.514 | — | — |
| Anisotropy limit `X` | — | — | 0.93 | — | — |
| Yield surface shape `N` | — | — | 0.71 | — | — |
| Anisotropy evolution rate `C` | — | — | 5 | — | — |
| Effective cohesion `c'` | kPa | 5.11 | — | **0.0** | **6.04 (peak)** |
| Effective friction angle `φ'` | degrees | 16.34 | 29.56 | fungsi `plastic strain → φ'` | **33.99 (peak)** |
| Permeability `k` | cm/s | 1.35 × 10⁻⁵ | sama | sama | sama |
| Volumetric water content | — | 0.51 | 0.51 | 0.51 | 0.51 |

**ATURAN:** Kolom ini merepresentasikan **model berbeda**; `c'=0` pada MC-HS dan `c'=6.04 kPa` pada MC peak biasa **jangan otomatis dikombinasikan atau dibandingkan sebagai pasangan parameter identik**. Untuk studi H vs HS yang adil, definisikan satu set material bersama dan gunakan hanya perubahan post-peak yang disengaja. SANICLAY merupakan model lain, bukan parameter MC yang harus dimasukkan semuanya.

### 2.4 Tabel referensi hardening–softening sudut geser — halaman 7 dan 11

Tabel tertulis pada slide:

| Accumulated *deviatoric plastic strain* (label slide) | Effective friction angle `φ'` (derajat) | Tahap interpretasi |
|---:|---:|---|
| 0.0000 | 0.00 | Awal tabulasi — **perlu perhatian pada kelayakan fisik/numerik** |
| 0.0068 | 27.10 | Hardening |
| 0.0370 | **33.99** | **Peak** |
| 0.1000 | 27.62 | Softening |
| 0.2000 | 16.34 | Softening / nilai akhir yang tersedia |

**Catatan penting dari halaman 11:** slide menyebut *input strain diperbesar 20×* saat memasukkan fungsi ke FLAC untuk memperoleh tren yang sesuai. Ini adalah langkah pengubahan input pada simulasi terdahulu, **bukan hukum material universal**. Jangan secara diam-diam mengalikan internal plastic strain CL-MPM dengan 20. Buat dua varian terdokumentasi bila diperlukan: **unscaled table** sebagai referensi utama dan **×20 strain-axis sensitivity** sebagai uji sensitivitas yang diberi label khusus. Penggunaan faktor tersebut wajib dijelaskan dengan definisi strain yang dibandingkan.

**Aturan initial point:** nilai `φ'=0°` ketika plastic strain `0` dikutip sesuai dokumen; tidak otomatis berarti material tanah sebenarnya tak memiliki gesekan/kohesi pada keadaan awal. Karena pada kolom MC-HS `c'=0`, titik pertama bisa menyebabkan perilaku luluh yang tidak realistis atau degenerasi numerik. Uji secara eksplisit. Jika tidak cocok untuk eksperimen terkontrol, buat **alternative declared illustrative initialization** yang dipakai sama pada H dan HS, dokumentasikan alasannya, dan pertahankan nilai tabel asli di data referensi. **Jangan mengubah nilai sumber atau menyebut alternatif sebagai hasil laboratorium.**

### 2.5 Parameter benchmark tebing independen — halaman 17–25

Slide mengutip studi **Zhan et al. (2012)** sebagai *verification reference* terpisah dari residual soil di halaman 6–14. **Tidak boleh menggabungkan material Zhan dengan residual soil lalu menyatakan keduanya satu dataset.**

| Parameter benchmark Zhan (slide hal. 17) | Nilai |
|---|---|
| Bulk unit weight | 18.8 kN/m³ |
| Cohesion peak `c'p` | 7 kPa |
| Friction angle peak `φ'p` | 20° |
| Cohesion residual `c'r` | 2 kPa |
| Friction angle residual `φ'r` | 13° |
| Plastic strain at peak | 5% |
| Plastic strain at residual | 20% |
| Poisson ratio | 0.20 |
| Young modulus | `E = 25(p' + 100)` kPa, minimum 4000 kPa; `p'` dalam kPa (menurut catatan tabel) |
| Dilation `ψ` | 0° pada tabel parameter asumsi |
| Earth pressure at rest `K0` | 1.0 pada tabel asumsi; contoh S3 memakai 1.5 (hal. 26) |
| Porosity | 0.3 |
| Permeability | `10⁻⁶` sampai `10⁻⁹` m/s |
| Water bulk modulus | `2.0 × 10⁹` (satuan harus diverifikasi jika dipakai) |

Catatan kaki halaman 17: *plastic shear strain* yang digunakan di tabel softening FLAC disebut **setengah** dari regangan plastis deviatorik pada referensi tersebut. Agent wajib mengaudit faktor definisi strain sebelum menggunakan tabel sebagai hukum konstitutif CL-MPM.

**FoS pada ringkasan halaman 25** (untuk cek tren/implementasi metode yang sebanding, **bukan target angka wajib MPM**):

| Model analisis | Peak | Post-rupture | Residual |
|---|---:|---:|---:|
| LEM (kolom simulasi slide) | 1.254 | 0.946 | 0.655 |
| FLAC, `ψ=0` (simulasi slide) | 1.25 | 0.92 | 0.65 |
| FLAC, `ψ=φ'` (simulasi slide) | 1.28 | 0.96 | 0.67 |

**Jangan membuat klaim FoS numerik CL-MPM harus identik dengan FLAC/LEM** tanpa metode SRM/LEM yang setara. Benchmark FoS hanya relevan jika metode perhitungan, initial stress, kondisi batas, dan parameter fisika konsisten.

### 2.6 Keterbatasan tambahan yang eksplisit pada slide

- Hal. 8 dan 12: grafik stress–strain menggabungkan **Lab, SANICLAY, MC peak, MC hardening/softening, dan FLAC SSoft**. Kurva hanya berupa gambar; tidak ada pointwise raw data beserta ketidakpastiannya. **Jangan digitasi untuk fitting**.
- Hal. 14: ilustrasi perbandingan triaxial dari **Sandroni (1977)** dengan `CP 112` dan `137 kPa`; catatan slide menyatakan confining pressure simulasi diinput **dua kali lebih kecil** dari lab. Ini referensi verifikasi yang berbeda, **bukan** bahan pembuktian material residual soil utama.
- Hal. 27: simulasi tebing sekitar sembilan tahun **belum mencapai target waktu** karena mencapai `maximum iteration steps`. Hal. 28 menampilkan kontur tekanan pori tahap *on progress*. Jangan menyatakan verifikasi long-term softening/pore pressure telah berhasil selesai.

---

## 3. Definisi eksperimen material yang FAIR

### 3.1 Pilihan hukum parameter (`κ` didefinisikan eksplisit)

Mulai dari **fungsi tabulasi piecewise-linear** terhadap internal accumulated plastic strain `κ` (hanya setelah definisi `κ` dinyatakan cocok dengan tabel acuan). Simpan semua control points. Buat fungsi interpolasi yang dapat diuji.

- `κpeak = 0.037` dan `φpeak = 33.99°` adalah **angka referensi halaman 7/11**, bukan nilai hasil fitting baru.
- **H:** gunakan tabulasi pre-peak yang disepakati bersama. Untuk `κ >= κpeak`, `φH(κ)=φpeak` (plateau). Ini **bukan** constant strength sejak `κ=0`.
- **HS:** identik dengan H untuk `κ <= κpeak`; untuk `κ > κpeak`, ikuti titik `(0.1,27.62°)` dan `(0.2,16.34°)` dengan interpolasi, lalu nyatakan secara eksplisit perlakuan di luar batas tabel (`clamp at last point` disarankan untuk referensi; boleh dibandingkan dengan opsi lain yang dilabeli). Jangan extrapolate liar.
- `c(κ)`: pada reference case MC-HS residual soil, tabel memakai `c'=0`. Agar treatment hanya post-peak friction evolution, kedua model dapat memakai `c'=0` **jika lulus verifikasi fisika dan solver**. Untuk eksperimen tambahan, gunakan skenario benchmark Zhan `cpeak=7 kPa` dan `cresidual=2 kPa` sebagai dataset **terpisah**.
- `ψ(κ)`: pilih `0°` sebagai baseline non-associated jika implementasi mengizinkan; cek asumsi pembentukan regangan volumetrik. Perbandingan `ψ=φ` bersifat sensitivitas, bukan baseline dicampur.

Alternatif model softening eksponensial atau dua tahap boleh ditambahkan sebagai **sensitivity/extension**, bukan mengganti silently hukum tabulasi reference case. Semua angka tambahan yang tidak berasal dari PDF harus dilabeli **assumption/scenario parameter**, bukan measured.

### 3.2 Mekanika yang harus benar

- Tentukan **effective stress vs total stress**, konvensi compression-positive/tension-positive dan cara hitung `q = σ1−σ3`, `p'`, `J2`.
- Definisikan *internal variables*, *plastic flow*, *hardening law*, *peak transition*, *softening law*, *return mapping*, dan *load-step commit/rollback*.
- Pada `κpeak`, fungsi harus kontinu; periksa kondisi yield sebelum dan setelah update softening, serta efek explicit vs coupled softening update.
- Tangani corners/apex Mohr–Coulomb, `φ≈0`, `ψ=0`, limit `c→0`, negative/invalid strength, dan numerical tolerances.
- Hardening-only tidak boleh menggunakan weak residual endpoint saat menghitung return mapping.
- Periksa model dependency terhadap mesh: post-peak softening lokal MPM dapat menyebabkan lokalisasi dan sensitivitas ukuran mesh; jika memerlukan regularisasi, implementasikan dan laporkan sebagai subeksperimen yang berbeda, bukan mengklaim mesh-objectivity tanpa bukti.

---

## 4. ROADMAP EKSEKUSI M0–M6

### M0 — TUNTASKAN REFACTOR NATIVE FRAMEWORK TERLEBIH DAHULU (P0)

**Alasan:** refactor `codex/reusable-simulation-framework` belum lolos seluruh regresi, dan triaxial masih bergantung pada subclass `particle-vm` serta diagnostik VM. Jangan menaruh model fisika baru di atas fondasi yang belum jelas.

**Langkah kerja:**

1. **Recovery & audit:** `git status`, branches/commits/PR, state proses berjalan, lalu baca `docs/AI_HANDOVER.md`, `docs/REUSABLE_FRAMEWORK.md`, `framework/README.md`, `docs/testing.md`, evidence folder terkait. Jangan menimpa hasil yang belum diamankan. Periksa hasil paired serial-control yang dinyatakan pending pada handover sebelum mengulang simulasi mahal.
2. **Investigasi Joss:** dokumentasi sebelumnya mencatat hasil full 40 s dan strict regression **FAIL** (`176` vs `191` saved states, beda posisi maksimum sekitar `0.0811648 m`). Temukan titik divergensi, bedakan kemungkinan thread nondeterminism, timestep scheduling, floating-point order, initial state, code provenance, dan perubahan sebenarnya. Jangan mengubah toleransi atau fisika untuk membuat tes lulus.
3. **Finalisasi arsitektur:** perjelas `Scenario`, `Material`, `Geometry`, `Boundary`, `Loading`, `Solver`, `Measurements`, `Diagnostics`, `Output`, `Provenance`. Tidak ada duplikasi constitutive equations dalam framework/scenarios.
4. **Material contract yang benar-benar generik:** abstraksikan pemilihan native class, constructor initargs, state/diagnostics/exports; hapus keterikatan wajib ke `particle-vm` dari triaxial umum. Dukungan material lain dilakukan dengan material adapter, **bukan** pura-pura mewarisi VM.
5. **Perbaiki diagnostics:** output umum (`stress`, `strain`, `positions`, `mass`, `volume`) terpisah dari model-specific `yield-function`, `internal variables`, `plastic state`; field tidak tersedia harus ditandai `not available` atau error informatif, bukan dihitung memakai rumus Von Mises untuk material MC.
6. **Config & integrity:** konsistensi SI, precedence config/override, reject unknown/duplicate parameters, state lokal per-run, input validation, source snapshots, native dependency provenance, no output overwrite, exit status/failure handling.
7. **No UI/Studio work:** jangan mengembangkan atau mengubah UI/Studio. Boleh *membaca* file legacy untuk audit/compatibility; jika perubahan Studio mutlak diperlukan, **catat sebagai blocker** dan fokus pada headless native API.
8. **Tests:** unit component contracts, material factory, geometry, CLI, invalid configs, isolation tests, backward compatibility, triaxial 2D, native triaxial 3D, Joss, cliff integration, output audits. Jangan mengasumsikan regresi 2D yang lulus pada snapshot lama otomatis membuktikan commit HEAD terbaru.

**Catatan prior evidence:** pada snapshot terdokumentasi, triaxial 2D 480 particles, 17.443 updates, 51 VTK dan semua CSV/VTK before-after identik. Joss 40 s belum lulus strict regression. Angka ini adalah **hasil repository terdahulu**, bukan pengujian yang dilakukan oleh dokumen ini.

**Exit M0:** core native menjalankan kasus valid, kontrak material umum teruji, diagnostics benar, provenance lengkap, backward compatibility dinilai, regresi yang penting PASS atau **open exception** dengan sebab/status/risiko jelas. **Jangan mengklaim refactor 100% atau merge** jika acceptance substantif belum terpenuhi.

**Aturan agar rencana tetap berjalan hingga akhir:** jika regresi Joss masih belum terselesaikan, pertahankan sebagai blocker untuk *final acceptance framework*, tetapi **lanjutkan M1–M6 pada experimental branch terisolasi** jika regresi triaxial/cliff core yang dipakai benar-benar terkontrol. Tandai kesimpulan sebagai provisional, jangan sembunyikan risiko.

### M1 — SOURCE-AWARE DATA & REFERENCE CASE PREPARATION (P1)

**Tujuan:** menyiapkan data **referensi**, bukan fitting kalibrasi.

1. Masukkan nilai pada Bagian 2 ke data terstruktur yang memiliki `source_file`, `page`, `model_family`, `units`, `status=reference_not_calibration`, `notes`.
2. Buat reference configurations yang **dipisah**, minimal:
   - `residual_soil_mc_h_reference` dan `residual_soil_mc_hs_reference` (paired primary comparison; pressure 100/200 kPa).
   - `zhan_cliff_h_reference` dan `zhan_cliff_hs_reference` (benchmark soil lain; material dan tujuannya independen).
3. Verifikasi SI. Jika memakai unit weight `γ`, konversi ke density dengan `ρ_mass=γ/g`, tulis nilai `g` yang dipilih; jangan perlakukan `16.83 kN/m³` sebagai `16.83 kg/m³`.
4. Simpan titik tabulasi apa adanya dengan `κ` dimensionless dan `φ` degrees; konversi ke radians hanya pada antarmuka model sesuai native API.
5. Catat bahwa strain multiplier ×20 pada FLAC bukan parameter yang boleh digunakan otomatis di CL-MPM.
6. Tidak perlu mengubah gambar grafik menjadi data observasi atau menjalankan least squares/optimizer.

**Exit M1:** referensi terstruktur, bisa diuji programmatically, setiap angka punya sumber dan label keterbatasan; pair H/HS dinyatakan jelas.

### M2 — CONSTITUTIVE HARDENING & HARDENING–SOFTENING IMPLEMENTATION (P1)

**Tujuan:** dua kelas/varian native yang berbagi fundamental mechanics.

1. Audit `src/models/plastic.lisp`, `src/constitutive.lisp`, `src/cpp.lisp`, `libs/src/constitutive.h` dan dependency ASDF/native.
2. Periksa `particle-mc`, yield/potential, shear/dilation, state, update dan toleransi; jangan assume `φ=0` aman tanpa pengujian.
3. Tambahkan implementasi **dedicated MC hardening** dan **dedicated MC hardening-softening** (atau shared MC base + parameterized evolution with explicit types). Default `particle-mc` lama **tetap tidak berubah**.
4. Gunakan `κ` yang jelas, trial/commit/rollback loadstep aman, parameter evolution per material point, dan stable return mapping; jangan mengganti VM method global.
5. Implementasi baseline piecewise H dan HS sesuai Bagian 3; tambah test untuk peak continuity, residual clamp, monotonic hardening, monotonic softening, nilai initial, yield consistency, dan strain definition.
6. Jika ada discrepancy ilmiah/numerik di titik awal `φ=0, c=0`, pertahankan benchmark mentah sebagai data, buat alternatif parameterisasi eksplisit untuk simulasi, lalu tunjukkan dua hasil dan alasan pemilihan; **bukan fitting terhadap slide**.
7. Uji single material point, virtual element, triaxial homogeneous, dan stress-path (termasuk hydrostatic loading, triaxial compression, non-associated flow).
8. Tambahkan stress/state diagnostic generik ke CSV/VTK; buktikan di tests bahwa jenis material berbeda menghasilkan diagnosa sesuai jenisnya.

**Exit M2:** MC H dan HS memenuhi invariants dan unit tests, dan tidak mengubah model native lama tanpa sengaja.

### M3 — PARAMETERIZATION & VERIFICATION, **NOT LAB CALIBRATION** (P1)

**Tujuan:** membangun dua model yang terkendali secara matematis menggunakan **nilai referensi**, tanpa parameter fitting.

1. Bekukan satu set parameter bersama untuk setiap paired experiment.
2. Verifikasi bahwa H dan HS identik pada loading pre-peak dalam toleransi yang telah ditetapkan.
3. Verifikasi peak strength yang sama dan perbedaan post-peak yang hanya berasal dari evolution law.
4. Lakukan numerical tests: timestep sensitivity, return-map residual, energy/plastic work consistency, state serialization, replay/restart jika tersedia.
5. Buat `parameters.yaml/json` dan `parameter-provenance.md`: mana dari PDF, mana asumsi eksploratif, mana nilai turunan SI.
6. Jika tidak tersedia effective-stress CU dengan pore pressure, lakukan compression yang dapat dikerjakan dan label metodenya dengan benar.
7. **Dilarang:** menjalankan automatic fitting ke kurva slide; menyatakan hasil prediksi tervalidasi lapangan; menetapkan toleransi berdasarkan kedekatan visual grafis PDF.

**Exit M3:** paired H/HS verifikasi internal PASS, jelas apa yang telah diverifikasi secara numerik dan belum divalidasi eksperimental.

### M4 — COMPARATIVE MPM TRIAXIAL SIMULATION (P1)

**Tujuan:** simulasi spesimen sama, model beda.

**Baseline case:** silinder 3D diameter `0.07 m`, tinggi `0.14 m`; stress convention dan keadaan awal seragam; `σ3=100 kPa` dan `200 kPa` sebagai *dua pasangan eksperimen*. Gunakan parameter residual-soil reference case yang konsisten. Jangan memaksa simulasi 2D plane-strain menyamai axisym 2D PDF.

1. Jalankan control linear elastic dan MC perfect plasticity jika membantu verifikasi.
2. Jalankan Model H untuk CP 100 dan 200 kPa.
3. Jalankan Model HS untuk CP 100 dan 200 kPa, dengan semua parameter lain identik.
4. Pakai prosedur loading confining → prescribed axial compression. Jangan otomatis mengklaim tahap konsolidasi sebenarnya hanya karena prestress tersedia.
5. Output minimum: `q–εa`, `σ1`, `σ3`, `p'` bila valid, volume/volumetric strain, cumulative plastic strain, `φ(κ)`, `c(κ)`, yielded fraction, deformation, energy, mass conservation, timestep, finite-state audit.
6. Plot empat kurva primer dan bandingkan: modulus awal, peak location, peak q, post-peak decline, residual ratio (jika tercapai), plastic strain localization, serta perbedaan H vs HS pada axial strain yang sama.
7. Jalankan mesh/timestep sensitivity secukupnya, terutama untuk HS; catat jika tidak objektif.
8. Jika 3D penuh mahal, lakukan preliminary homogeneous + small MPM smoke test, tetapi **tetap jalankan 3D full yang feasibly bounded** dan laporkan batas compute jika terpaksa menggunakan resolusi/durasi lebih kecil. Jangan menyebut smoke test sebagai hasil full.

**Exit M4:** hasil stress–strain dan internal state masing-masing model tersedia, paired comparison terverifikasi, plus batasan representasi CU.

### M5 — COMPARATIVE MPM CLIFF FAILURE (P1)

**Tujuan:** menerjemahkan perbedaan material H/HS menjadi perbedaan keruntuhan tebing.

1. Buat **cliff comparison scenario baru** untuk tanah yang sama dengan reference material MC dari M3/M4. Jangan gunakan Joss chalk dengan sekadar mengganti label.
2. Untuk H vs HS, gunakan **geometri identik, mesh/particles identik, density/gravity identik, initial stress `K0` identik, material peak dan pre-peak identik, boundary/support dan trigger identik**, serta solver tolerances identik.
3. Definisikan mekanisme pemicu yang terukur: gravity equilibration, excavation/removal of support, atau parameter loading; pilih satu skenario baseline dan freeze sebelum melihat mana model yang menghasilkan hasil lebih dramatis.
4. Pertahankan provenance dari konfigurasi triaxial ke cliff: apa yang sama dan apa yang membutuhkan asumsi konversi/fisik berbeda.
5. Jalankan paired H/HS hingga waktu dan kondisi penyelesaian yang sebanding; jangan membandingkan satu selesai dan satu gagal lalu mengklaim pemenang.
6. Lacak: onset yield, onset localized plastic strain, shear band, failed mass/particle fraction, toe displacement, crest displacement, max velocity, run-out front, geometry/domain shape, dissipation/energy, mass conservation, momentum/time diagnostics.
7. Jika tebing ternyata stabil pada keduanya, **laporkan apa adanya**; lakukan *pre-registered sensitivity* yang wajar terhadap slope angle, loading atau strength ratio dan catat sebagai eksperimen terpisah. Jangan ubah parameter satu model secara sepihak untuk memaksakan collapse.
8. Jalankan kontrol `K0` dan dilation yang relevan, misalnya K0=1.0/1.5 **hanya jika definisi initial stress dan implementasi konsisten**. Bandingkan dengan referensi Zhan sebagai studi kasus **berbeda** bila berguna.
9. Periksa mesh dependency: bandingkan lokasi shear band, waktu onset, dan run-out pada minimal dua resolusi jika kapasitas memungkinkan; jika tidak konvergen, nyatakan keterbatasan eksplisit dan rekomendasi regularisasi.
10. Buat video/PNG hanya sebagai evidence visual tambahan; CSV/VTK/numerical diagnostics dan run state menjadi sumber utama.

**Exit M5:** tersedia eksperimen cliff paired H/HS dengan konfigurasi terkunci, bukti numerik, dan analisis perbedaan; tidak wajib memaksakan kedua model runtuh.

### M6 — SENSITIVITY, QUALITY ASSURANCE, REPORT & HANDOVER (P1)

1. Kumpulkan ringkasan semua tes dan run: PASS/FAIL/INCOMPLETE/NOT RUN, alasannya, durasi, resources, SHA source, config hash, engine/compiler/DLL provenance.
2. Susun perbandingan kuantitatif tahap M4 dan M5, grafik overlay dan tabel metrik.
3. Sensitivity utama: softening slope, `κpeak`, `κresidual`, `ψ`, `K0`, geometry/mesh/timestep. Pisahkan eksperimen utama dan sensitivitas.
4. Pisahkan *verified numerical implementation*, *regression-equivalence*, *qualitative consistency with PDF*, dan *experimental calibration/validation* yang **belum dilakukan**.
5. Review apakah perbedaan respon dapat dijelaskan oleh evolution law atau sebenarnya artefak perbedaan inisialisasi, CFL timestep, mesh, atau output scheduling.
6. Tulis laporan akhir metode, persamaan, asumsi, hasil, batasan, grafik, evidence, reproduksi per command, dan rekomendasi penelitian lanjut; jangan berlebihan dalam klaim.
7. Update dokumentasi/handover & Obsidian/LLM wiki yang sudah ada dan memang terkait project ini (bukan UI):
   - `docs/AI_HANDOVER.md`
   - `docs/REUSABLE_FRAMEWORK.md`
   - `docs/testing.md`
   - `framework/README.md`
   - `wiki-vault/wiki/`
   - `research/README.md` dan laporan penelitian baru.
8. Catat semua hasil yang gagal; jangan menghapus evidence negatif.
9. Siapkan checkpoint commit/push ke branch kerja. Untuk perubahan model konstitutif fisika, gunakan branch/PR terpisah dari refactor jika memungkinkan. **Tidak merge main tanpa izin.**

**Exit M6:** laporan lengkap dan reproducible, semua milestone punya status akurat, serta ada paket handover yang cukup untuk agent lain melanjutkan tanpa kehilangan konteks.

---

## 5. Mandatory comparison matrix

| Study ID | Scenario | Material | CP / initial condition | Tujuan | Status target |
|---|---|---|---|---|---|
| F-01 | Framework legacy triaxial 2D | Legacy VM | Original matched baseline | Regression | Before/after comparable |
| F-02 | Framework legacy triaxial 3D | Legacy VM | Original matched baseline | Regression | Before/after comparable |
| F-03 | Joss original | Original chalk/damage | Original frozen recipe | Regression | Root cause/status clear |
| C-01 | Constitutive point | MC H | Matched trial states | Verification | Yield/history correct |
| C-02 | Constitutive point | MC HS | Same as C-01 | Verification | Post-peak decrease correct |
| T-100-H | Triaxial 3D | MC H | CP 100 kPa | Main paired study | Full output |
| T-100-HS | Triaxial 3D | MC HS | CP 100 kPa | Main paired study | Full output |
| T-200-H | Triaxial 3D | MC H | CP 200 kPa | Main paired study | Full output |
| T-200-HS | Triaxial 3D | MC HS | CP 200 kPa | Main paired study | Full output |
| L-H | Cliff | MC H | Frozen paired geometry/load | Main paired study | Full output |
| L-HS | Cliff | MC HS | Exactly L-H otherwise | Main paired study | Full output |
| L-SENS-* | Cliff/triaxial | As specified | Frozen per sensitivity pair | Sensitivity | Labelled separately |

**Catatan:** Jika H vs HS tidak berbeda karena material belum mencapai yield/peak, ini adalah hasil sah. Buktikan lewat internal state, jangan membuat klaim kausal fiktif.

---

## 6. Struktur implementasi dan output yang disarankan

**Jangan memindahkan kode besar tanpa alasan; sesuaikan dengan struktur repository aktual.** Organisasi konseptual:

```text
src/                              # physics engine & native constitutive equations
framework/
  components/                    # generic material/geometry/boundary contracts
  scenarios/
    triaxial/                    # scenario setup/BC/loading/measurements, model-agnostic
    cliff/                       # scenario setup/BC/loading/measurements, model-agnostic
  simulation.lisp                # composition & run lifecycle
cases/
  triaxial-clay-3d.lisp          # existing example preserved
  [new H/HS reference cases]      # short, SI-based per-case recipes
research/
  README.md
  references/                    # PDF provenance + manually transcribed table
  configs/                       # frozen comparison matrices H/HS
  constitutive-tests/            # single-point/element test evidence
  triaxial/                      # numeric CSV/VTK, audit, plots, manifests
  cliff/                         # numeric CSV/VTK, audit, plots, manifests
  comparisons/                   # H-vs-HS quantitative report
  reports/                       # final science/engineering report
scripts/                          # native runners/auditors; headless
wiki-vault/wiki/                  # existing Obsidian / LLM wiki tracking
```

**Outputs wajib per run:** unique output directory, exact source snapshot atau per-file hashes, full effective config, dimensions/unit conventions, constitutive model + evolution-law ID, solver settings, `complete` status, audit summary, CSV/VTK, logs, code SHA, test result. Jangan menimpa run lama.

**Contoh pola eksekusi existing (bukan jaminan kasus baru sudah tersedia):**

```powershell
Set-Location D:\MPM
# Pastikan agent sudah membuat & menguji file case yang dimaksud.
$runDir = Join-Path 'D:\MPM\output' ('experiment-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& .\windows\cl-mpm.cmd scripts\run-case.lisp cases\YOUR-CASE.lisp $runDir
if ($LASTEXITCODE -ne 0) { throw 'Native experiment failed; inspect logs before proceeding.' }
```

Perluas runner/auditor secara proporsional; tidak ada pekerjaan UI/Studio.

---

## 7. Test & acceptance criteria

### 7.1 Unit dan konstitutif

- Semua input SI tervalidasi; invalid/non-finite ditolak.
- Perpindahan H dan HS dari elastic → yield → plastic sesuai implementasi yang dinyatakan.
- Pre-peak H dan HS identik dalam toleransi yang dipilih sebelum run.
- Nilai peak, post-peak, terminal table clamp, update state, restart/reset/commit diuji.
- Return mapping memenuhi residual yield tolerance yang diberi justifikasi; invariants state finite.
- Ketergantungan `φ=0`, `ψ=0`, `c=0`, compression/tension sign ditangani dan diuji.
- Perbedaan material-specific diagnostics benar; tidak memanggil formula Von Mises untuk MC.

### 7.2 Solver MPM

- Konservasi massa diuji dan particle loss tidak disembunyikan.
- Time integration dan output clocks dapat diaudit.
- Initial stress/pressure, boundary, loading matched untuk setiap paired H/HS.
- Tidak ada global-state leakage di repeated runs.
- Triaxial 3D diidentifikasi benar sebagai 3D cylinder; kasus 2D diidentifikasi plane strain.
- Energi, volume, stress/strain, plastic internal variables finite; field yang tidak tersedia dilaporkan.

### 7.3 Research comparisons

- Grafik H-vs-HS dan tabel metrik *disertai raw run references*.
- Perbedaan respons prepeak/postpeak ditunjukkan berdasarkan internal state, bukan visual saja.
- Semua klaim memasukkan uncertainty/limitations dari mesh dependence dan data yang tidak terkalibrasi.
- Run yang abort/timeout dicatat `INCOMPLETE`, bukan `PASS`.
- Benchmark FLAC / referensi Zhan dipakai sebagai *qualitative/context*, bukan angka harus dipenuhi.

### 7.4 Definition of Done

Roadmap **completed for this study** ketika M0–M6 menghasilkan artefak sesuai batas kemampuan aktual, status regresi/limitation diterangkan terbuka, dan **paired comparative triaxial + cliff** telah dijalankan atau blocker nyata, bukti percobaan, dan tindakan pemulihannya telah didokumentasikan. **Tidak mensyaratkan fitting ke data PDF.**

Jika native engine mencegah eksperimen valid, jangan memalsukan hasil atau diam-diam mengganti fisika: selesaikan sejauh memungkinkan, catat blocker dan langkah lanjut secara tepat. Jangan menyebut milestone empirically validated.

---

## 8. Kebijakan eksekusi agent (PENTING)

1. **Mulai langsung dari M0.** Selalu audit branch/HANDOVER terkini, karena status bisa berubah setelah dokumen ini dibuat.
2. Kerjakan berurutan, tetapi boleh mempersiapkan tugas independen pada tahap berikutnya tanpa menunggu simulasi mahal, sepanjang tidak melanggar uji/keselamatan baseline.
3. **Jangan berhenti hanya karena tidak ada data lab kalibrasi.** Lanjutkan dengan prescribed/illustrative numerical parameters; tidak ada fitting.
4. Jangan membuat laporan yang menyebut `calibrated`, `validated CU`, atau `predictive accuracy` jika tidak didukung bukti eksperimen.
5. Jangan mengganti formula native hanya untuk menyamakan visual dengan slide.
6. Jangan menukar tanggal/commit/evidence dari snapshot lama seolah-olah hasil HEAD terbaru.
7. Pertahankan perbedaan branch refactor vs branch physics experiment, serta checkpoint commit kecil dan jelas.
8. Jangan menghapus log gagal, bukti negatif, state mentah, atau perubahan lokal yang belum diamankan.
9. Jangan melakukan merge ke `main`, force-push, reset destruktif, atau membuat PR sebagai pekerjaan 'PASS' jika hasil belum memenuhi acceptance.
10. Tidak ada pengembangan UI atau Studio.
11. Update `docs/AI_HANDOVER.md` **setiap checkpoint**: sedang mengerjakan apa, commit, proses yang berjalan, output terbaru, PASS/FAIL, next action. Sinkronkan dokumentasi dan wiki/Obsidian yang relevan.
12. Usahakan eksekusi sampai M6 dan laporan final; bila hambatan teknis sulit, jelaskan secara jelas alih-alih diam-diam menganggap tugas sudah selesai.

### Format checkpoint report

```text
BRANCH / HEAD:
MILESTONE & TASK:
CHANGES MADE:
TESTS (PASS/FAIL/INCOMPLETE/NOT RUN):
REFERENCE / RUN INPUTS:
OUTPUT & PROVENANCE:
SCIENTIFIC LIMITATIONS:
BLOCKERS & CAUSE:
DOCS / WIKI / HANDOVER UPDATED:
NEXT ACTION:
```

---

## 9. Deliverable akhir yang harus disiapkan agent

1. Framework native CL-MPM reusable dengan contracts dan diagnostics yang benar; tanpa pekerjaan UI/Studio.
2. MC Hardening-only dan MC Hardening–Softening terverifikasi, dengan source, tests, dan manual model.
3. Reference case data dan parameter provenance yang memisahkan nilai PDF dan asumsi.
4. Paired triaxial runs 100/200 kPa pada kondisi sepadan, raw CSV/VTK + plot + audit.
5. Paired cliff runs pada kondisi sepadan, raw CSV/VTK + metrics + plot/video bila memungkinkan.
6. Tabel perbandingan, sensitivity summary, verification and limitations report.
7. Dokumentasi proyek/Obsidian/LLM Wiki/handover terbaru.
8. Commit/push checkpoint dan informasi cara mereproduksi eksperimen di laptop.
9. Daftar *open issues* yang belum diselesaikan, tanpa klaim lebih dari bukti yang tersedia.

### FINAL COMMAND TO AGENT

> **EXECUTE THIS PLAN END-TO-END. COMPLETE THE NATIVE REFACTOR FIRST, THEN BUILD AND VERIFY THE MC HARDENING / MC HARDENING–SOFTENING MATERIAL FAMILY, RUN FAIR PAIRED TRIAXIAL AND CLIFF SIMULATIONS, AND PRODUCE REPRODUCIBLE SCIENTIFIC RESULTS. DO NOT FIT TO THE PROVIDED PDF; ITS NUMBERS ARE ONLY REFERENCE SCENARIO PARAMETERS. DO NOT WORK ON UI OR STUDIO. KEEP ALL NEGATIVE EVIDENCE AND HANDOVER CURRENT. DO NOT MERGE MAIN WITHOUT USER APPROVAL.**

---

**Asal angka:** slide *Numerical Simulation of Residual Soil Triaxial*, halaman 3–14 untuk residual soil/triaxial, halaman 17–28 untuk independent Zhan/cliff reference. **Interpretasi desain eksperimen, pemisahan H/HS, acceptance criteria, dan implementasi CL-MPM pada dokumen ini merupakan rencana teknis baru**, bukan klaim yang dinyatakan oleh PDF.
