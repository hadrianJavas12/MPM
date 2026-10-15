# Simulasi berhasil runtuh — hasil visual diterima, 2026-10-15

Pengguna telah melihat video runtuhan Windows native dan menyatakan puas:
"wow, saya sudah puas dengan itu. tolong commit beri keterengan berhasil runtuh dengan sesuai".
Checkpoint ini menyimpan hasil runtuh yang diterima secara visual beserta input,
data partikel, dan bukti pengujiannya. Tidak ada run atau kalibrasi tambahan
setelah penerimaan ini; auto-continuation telah dijeda.

## Hasil yang diterima

- [Video runtuhan](accepted-collapse.mp4): damage dari bagian bawah berkembang,
  tebing runtuh dan material menyebar; waktu solver 0–40 s, bukan durasi video.
- [Gambar akhir t=40 s](accepted-collapse-t40.png): warna adalah **damage 0–1**,
  dihitung dari VTK nyata, dengan skala tetap.
- `accepted/`: konfigurasi asli, metadata, CSV waktu/transisi, audit semua frame,
  perbandingan bentuk, dan snapshot VTK awal/setimbang/awal damage/akhir dalam gzip.
- `sources/`: snapshot skrip probe, kelanjutan pilot, config persiapan dan log
  yang menghasilkan run tersebut. Skrip kontrol ini merupakan bukti historis;
  tidak dimuat otomatis oleh Studio.
- `validation/`: log pemeriksaan Node dan smoke SBCL Windows yang telah dijalankan.
- `manifest.json`: asal, ukuran dan SHA-256 setiap berkas bukti dalam bundle ini.

Pilot memakai 4.155 partikel, h=0,5 m, dua partikel per arah sel, empat worker,
E=1 GPa, Gf=4,8 J/m², ambang 18.926,452 Pa, ductility 53,599755 dan delay 10 s.
Dasar elastis berisi 496 partikel dilindungi dari damage/plastisitas. Massa tetap
425664,0625 kg/m; semua field partikel yang diaudit finite. Ada 174 frame fisik,
ditambah keadaan awal untuk video 175 frame.

Pilot memanfaatkan keadaan setimbang dari probe (1.658 update) lalu satu update
pemeriksaan ulang. Karena itu `accepted/config.json` berisi `settleMaxSteps=1`:
**ini konfigurasi warm start historis, bukan input CLI untuk fresh start**.
Produksi sekarang memiliki DP dan perlindungan dasar pada kelas referensi sendiri;
pilot asli memakai subclass terisolasi `joss-probe-dp-chalk`. Kedua jalur memiliki
bukti masing-masing; replay produksi yang identik byte demi byte belum dibuktikan.
VTK hanya snapshot partikel, bukan checkpoint lengkap untuk melanjutkan solver.

## Pembanding terakhir yang tidak dipilih

[Gambar t=221,14 s dengan ambang 40 kPa](latest-40k-t221.png) dan direktori
`latest-40k/` menyimpan kandidat produksi yang selesai 111 frame tetapi **belum
runtuh**. Damage maksimum 0,49062952 dan rata-rata berbobot massa 0,00806464.
Konfigurasi meminta cap 5.000 frame; normalisasi schema membatasinya menjadi 2.000.
Ini pembanding, bukan hasil runtuhan yang diterima.

## Batas klaim dan pemeriksaan

"Sesuai" pada checkpoint berarti **runtuhan yang diterima pengguna secara visual**.
Perbandingan bentuk pilot t=40 s terhadap video referensi t=221,14 s masih menunjukkan
run-out +7,8 m dan retreat plateau 5,2 m lebih besar (IoU citra sekitar 0,699825).
Ini perbandingan bentuk pada waktu berbeda, bukan persentase akurasi fisik.
Tidak ada klaim kecocokan numerik 100%, konvergensi mesh atau validasi ilmiah lengkap.

`validation/validation-summary.json` mencatat `npm run check` lulus dan Node 36/36
lulus tanpa skip (termasuk tiga kontrak SBCL nyata), smoke referensi native,
VTK finite, dua PNG lengkap dan guard equilibrium gagal. Smoke bukan uji runtuhan.
Riwayat pengujian launcher, delegate dan ekspor Studio sebelumnya dijelaskan dalam
[laporan Windows](../../windows-verification-2026-10-14.md).

Untuk melihat snapshot gzip, ekstrak sebagai `.vtk` dan gunakan ParaView atau:

```powershell
python scripts/render-particle-vtk.py --vtk <snapshot.vtk> --output <gambar.png> --time 40 --phase accelerate --particle-shape rectangle
```

Renderer memerlukan NumPy dan Pillow. Label fase adalah status kontrol solver;
bukti runtuhan berasal dari perpindahan/geometri partikel yang tampak pada video.
Artefak lengkap lokal tetap berada di
`D:\MPM\output\reference-reproduction-2026-10-15\dp-physical-pilot\`.
