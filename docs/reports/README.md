# Laporan PDF proyek — 15 Oktober 2026

- [Laporan pengembangan CL-MPM Studio](CL-MPM_Laporan_Perubahan_2026-10-15.pdf):
  9 halaman, perbandingan upstream, perubahan fork, atribusi, bukti pengujian
  dan tambahan triaxial. Sumber: [Markdown laporan](../UPSTREAM_CHANGE_REPORT.md).
- [Metode kalibrasi triaxial clay](Metode_Kalibrasi_Triaxial_Clay_2026-10-15.pdf):
  6 halaman, asumsi, parameter, workflow, kurva dan hasil native beserta batasnya.
  Sumber: [Markdown metode](../TRIAXIAL_CALIBRATION.md).

PDF ditata menggunakan `scripts/build-project-report.py`. Halaman dirender
melalui PDFium dan diperiksa secara visual, termasuk tabel, gambar dan bagian
akhir. Hash/identitas sumber dicatat pada `manifest.json`; bukti numerik tetap
berada pada `docs/evidence/` dan tidak digantikan oleh tampilan PDF.

Untuk membangun kembali, pasang `calibration/requirements-reports.txt` pada
lingkungan analisis Windows yang sama, lalu jalankan dari root repository:

```powershell
python scripts/build-project-report.py --source docs/UPSTREAM_CHANGE_REPORT.md --output output/pdf/CL-MPM_Laporan_Perubahan_2026-10-15.pdf --title 'Laporan Pengembangan CL-MPM Studio'
python scripts/build-project-report.py --source docs/TRIAXIAL_CALIBRATION.md --output output/pdf/Metode_Kalibrasi_Triaxial_Clay_2026-10-15.pdf --title 'Metode Kalibrasi Triaxial Clay'
```

Font menggunakan Arial/Consolas Windows. PDF memuat tautan evidence ke branch
`codex/triaxial-clay-calibration`; manifest data tetap dipakai untuk memeriksa
identitas berkas karena tautan branch dapat bergerak.
