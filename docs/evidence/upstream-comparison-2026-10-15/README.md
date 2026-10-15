# Bukti perbandingan upstream — 15 Oktober 2026

Perbandingan tetap: upstream `d8e65543c55634b54b9d8edf2a6bcf6082415bdc`
terhadap fork `f7fb2a3322eabf483b3d6cedd2c090b356ca01ca`.
Laporan naratif: [UPSTREAM_CHANGE_REPORT.md](../../UPSTREAM_CHANGE_REPORT.md).

| Berkas | Isi |
| --- | --- |
| `comparison.json` | SHA, metadata, ancestry, kategori dan bukti identitas blob terpilih |
| `changed-files.json` | Semua 278 path berubah, status, kategori, baris dan blob sebelum/sesudah |
| `name-status.tsv`, `numstat.tsv` | Output Git langsung tanpa rename detection |
| `diff-stat.txt`, `diff-summary.txt` | Statistik lengkap/ringkas dari Git |
| `modified-original-source.patch` | Diff utuh tiga berkas lama sumber/ASDF yang berubah |
| `upstream-README.md` | Snapshot README dari commit upstream tetap |
| `source-*.json` | Salinan ringkasan hasil historis dan refresh live GitHub; bukan eksekusi baru |
| `retained-source-index.json` | Path asal, ukuran dan SHA-256 salinan bukti |
| `manifest.json` | Ukuran dan hash berkas bundle, tidak termasuk manifest itu sendiri |
| `build-comparison.py` | Regenerasi data dari Git dan bukti tersimpan; tidak menjalankan tes/simulasi |

Hitungan: 273 tambah, 5 ubah, 0 hapus; 183.384 baris teks tambah,
21 hapus; 11 berkas biner. Sebanyak 308/313 berkas lama identik pada Git.
Hitungan tambahan dependency mencakup kode vendored pihak lain dan bukan
atribusi seluruh baris kepada pengembang fork. File output yang diabaikan Git
serta perubahan task baru setelah `f7fb2a3` tidak dimasukkan.

Paket dibuat dari objek commit tetap. Salinan JSON pengujian mempertahankan
path Windows historis sebelum relokasi; path lama tersebut tidak mengubah
asal hasil. Berkas sumber asli dan log detail masih ditautkan melalui laporan.
