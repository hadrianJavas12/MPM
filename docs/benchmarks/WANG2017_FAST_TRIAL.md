# Uji cepat Wang: 0,01 m/s ke 60 mm

Pengguna mengonfirmasi target **60 mm / 6 detik fisik**, setelah permintaan awal
600detik pada kecepatan paper0,0001m/s. Uji ini memakai **100x kecepatan paper**;
hasilnya tidak boleh diberi label sebagai simulasi600detik atau kurva paper yang
tervalidasi. Model adalah Soil1 MC plastis sempurna; Soil2 dan longsor pada video
teman belum tervalidasi oleh kontrol ini.

## Hasil aktual24Oktober

Run `fast-010-001` **selesai**: native exit0/complete pada01:45:23WIB,
audit/render/worker exit0 pada01:46:32WIB.61frame asli,915partikel,20640update
pembebanan;6detik fisik tercapai. Tidak ada solver yang dijalankan ulang.

**Belum ada longsor koheren atau run-out yang terverifikasi.** Zona plastis
berkembang dan reaksi masih meningkat hingga668,64kN/m. Warna `mc-kappa`
adalah history plastis model Soil1, bukan damage atau softening Soil2.

| Pengukuran akhir | Nilai |
| --- | ---: |
| Perintah turun |60mm |
| Penurunan rata-rata permukaan kontak |59,5357mm |
| Gap rata-rata / maksimum individual |0,4643 /1,1585mm |
| Maksimum perpindahan pusat partikel |59,1289mm |
| Maksimum native kappa |0,01511035 |

Penurunan permukaan bukan perpindahan pusat partikel: pusat6partikel strip
turun rata-rata57,5816mm dan setengah tinggi domain menyusut1,9540mm, sehingga
permukaan turun59,5357mm. Rekonstruksi dari61VTK cocok dengan CSV hingga5,21e-15m.
Maxspeed0,324m/s adalah outlier lokal **ke atas**, bukan bukti longsor cepat.

[Video hasil](../evidence/wang2017-reference-2026-10-24/fast-010-001-completed/slope-descent.mp4)
memakai61state native,4fps/15,25detik playback, skala perpindahan1 dan rentang
warna/axes tetap. Native6detik, playback15,25detik, dan paper600detik berbeda.
Full H264/yuv420p decodePASS. Semua61hash VTK dan265hash sumber cocok.

[Paket native17hash](../evidence/wang2017-reference-2026-10-24/fast-010-001-completed/README.md)
dan [review11hash](../evidence/wang2017-reference-2026-10-24/fast-010-001-review/README.md)
menyimpan raw/sumber/runtime/media dan perbandingan pada displacement identik.
Pada60mm, reaksi berbeda+2,52% terhadap run0,005m/s; ini belum membuktikan
konvergensi laju. Tidak ada validasi kurva paper, closed energy budget atau
quasistaticPASS; loading J tidak disimpan langsung. Reference-speed600s belum run.

## Menjalankan dari Windows native

PowerShell7, folder output baru, tanpa Studio:

```powershell
Set-Location D:\MPM
pwsh -NoProfile -File scripts\start-wang2017-detached.ps1 `
  -Case cases\benchmarks\wang2017-soil1-fast-010.lisp `
  -OutputDirectory output\wang-FRESH -MaxWallHours 2
```

Perintah kembali setelah worker dimulai; itu belum berarti simulasi selesai.
Baca `output\wang-FRESH-status.json`: status, heartbeatUtc, processIdentity dan
progress.phase/timeS. Manifest di folder run memuat complete/hasil fisik aktual.
Jangan menilai kemajuan dari tail stdout saja. Worker merekam identitas proses
dan membaca manifest tiap60detik; setelah exit0/complete, audit/PNG/video otomatis.
Simpan semua data jika gagal. Jangan menjalankan ulang untuk memperbaiki media.

Run historis `fast-010-001` dimulai24Oktober01:00:46WIB pada4e3140c; batas
03:00:46WIB, bukan jaminan jam selesai. Worker21676/wrapper15488/cmd27480/SBCL9164.
Jangan menggandakannya ketika masih berjalan. WMI mempertahankan worker setelah
perintah pemanggil berakhir, tetapi worker masih di sesi pengguna11. **Komputer
perlu tetap menyala dan login; jangan logoff/sleep/restart selama run.** Layar
boleh dikunci. Tidak ada service, credential atau pengaturan daya yang diubah.

## Input dan bukti

Material tetap E20MPa,nu0,25,gamma20kN/m³,c30kPa,phi35°,psi0°. Geometri, batas,
mesh1m,915MP,dtScale0,2,damping dan penalty tetap. Tinggi relief10m masih asumsi;
bottom tangential restraint dan kurva paper belum terverifikasi. Tidak ada mass
scaling, perubahan konstitutif, clamp apex atau koordinat hasil yang direkayasa.

Tiga kontrol input native PASS, dua particle native dan **nol timestep**.
Hanya velocity/target/durasi turunan/frame count/cap komputasi berbeda dari case
reference.61frame direncanakan, cadence0,1s, cap45000update. Kontrol monitoring
12PASS, launcher9PASS dan budget3PASS memakai fixture kecil, bukan simulasi MPM.
Sumber/test/log dan kegagalan fixture awal disimpan dengan lingkup masing-masing.

Video teman disimpan utuh di `wiki-vault/raw/assets/wang2017-friend-fem-2026-10-24.mp4`
(SHA256cc86e80aeab263e1dc8e7fa02906bdb86463815ca3cca74742bc7f53384f011b).
Terlihat pita deformasi puncak-ke-kaki. Clip11,133detik tidak menampilkan waktu
fisik, parameter material atau skala pembesaran deformasi; gunakan sebagai
pembanding visual, bukan bukti kecocokan numerik.
