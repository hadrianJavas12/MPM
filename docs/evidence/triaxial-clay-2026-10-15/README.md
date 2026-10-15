# Bukti demonstrasi triaxial clay — 15 Oktober 2026

Dimensi nominal Ø70 × 140 mm, pendekatan undrained total stress dengan
parameter asumsi. Tidak ada data laboratorium. Lihat
[metode kalibrasi](../../TRIAXIAL_CALIBRATION.md) dan
[cara menjalankan](../../../calibration/README.md).

| Folder | Isi dan cakupan |
| --- | --- |
| `mpm/` | Run MPM spasial 3D: 780 MP, 17.443 update, 51 frame sampai regangan platen 10%. PNG/video dari data partikel dan CSV. Arsip memuat semua 51 VTK. |
| `homogeneous/` | Pembanding konstitutif native: 1.000 increment, 51 frame, visualisasi affine dari F yang dihitung. Arsip memuat VTK awal/akhir; semua frame lokal tetap disimpan. |
| `controls/` | Pembanding analitis tangent elastis, yield VM, kontrol tegangan lateral dan keseimbangan hidrostatik 3D; termasuk snapshot harness yang benar-benar dimuat. |
| `review-source/` | Salinan kode saat review/integrasi. Jangan menyebutnya bukti byte sumber yang persis dimuat oleh kedua run produksi lama. |
| `logs/` | Log run produksi dan uji estimator. |

`manifest.json` mencatat hash berkas dan isi arsip VTK. Untuk kedua run
produksi, snapshot source sebelum load belum direkam; `source-provenance.json`
menyatakan batas tersebut secara eksplisit. Launcher berikutnya menyimpan lalu
mengeksekusi snapshot harness; kontrol terakhir membuktikan jalur tersebut.
Dependensi/FASL/DLL tetap mempunyai batas provenance terpisah.

Kurva `q` adalah rata-rata berbobot volume dari tegangan partikel, bukan data
laboratorium atau kurva yang diganti renderer. Garis utama memakai regangan
dari tinggi domain partikel; garis putus-putus MPM memperlihatkan regangan platen
yang diperintahkan. Kedua estimator MPM mempertahankan perbedaan itu. Warna adalah ukuran regangan
plastis native, bukan kerusakan dan bukan langsung normalisasi equivalent strain
standar (ukuran native VM = 1,5 kali ukuran standar pada implementasi ini).

Keterbatasan utama: volume silinder diskret kasar +3,4507% terhadap volume
analitis; boundary ujung berupa spring normal bilateral tanpa tahanan tangensial;
nu=0,49 bukan kendala undrained eksak; tidak ada solver tekanan air pori.
Energi kinetik dan tekanan lateral dipantau, tetapi belum ada neraca energi
lengkap atau studi konvergensi mesh/laju/timestep. Konsistensi data bukan
validasi fisik clay.

Ekstrak `particle-vtk.tar.gz` ke folder pilihan untuk melihatnya di ParaView.
Untuk menjalankan kembali auditor/renderer, gunakan berkas konfigurasi, CSV,
manifest dan VTK lengkap sesuai struktur run dalam `calibration/README.md`.
