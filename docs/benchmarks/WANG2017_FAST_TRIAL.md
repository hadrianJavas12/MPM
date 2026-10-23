# Uji cepat Wang: 0,01 m/s ke 60 mm

Pengguna mengonfirmasi target **60 mm / 6 detik fisik**, setelah permintaan awal
600detik pada kecepatan paper0,0001m/s. Uji ini memakai **100x kecepatan paper**;
hasilnya tidak boleh diberi label sebagai simulasi600detik atau kurva paper yang
tervalidasi. Model adalah Soil1 MC plastis sempurna; Soil2 dan longsor pada video
teman belum tervalidasi oleh kontrol ini.

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

Run aktual `fast-010-001` dimulai24Oktober01:00:46WIB pada4e3140c; batas
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
