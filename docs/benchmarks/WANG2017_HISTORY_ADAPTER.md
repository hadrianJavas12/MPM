# Wang2017 Soil2: kontrak history dan adapter

Ruang lingkup saat ini adalah menyiapkan Soil2 untuk **MPM** sesuai keputusan
pengguna. Acuan adalah Wang et al. (2017), Eq5–6 dan Table1, bukan history J2
dari eksperimen creep. [Sumber paper](https://doi.org/10.1007/s11629-016-3951-1)
dan URL salinan penulis tercatat pada
`research/references/wang2017/mpm-reference-contract.json`.

## Bagian yang telah diimplementasikan

System ASDF opsional `cl-mpm/models/wang2017` memuat tiga file di
`materials/models/plastic/wang2017/`: package, history dan law. System ini tidak
menambahkan kelas particle, tidak mengganti model lama dan tidak dimuat otomatis
sebagai material framework. API murninya:

| Fungsi | Kontrak |
| --- | --- |
| `paper-kps` | `sqrt(.5 * dev(Ep):dev(Ep))` dari tensor plastis bertanda |
| `engineering-voigt-to-tensor` | ubah gamma menjadi gamma/2 pada komponen shear |
| `tensor-to-engineering-voigt` | konversi sebaliknya, dengan salinan baru |
| `make-paper-history` / `history-tensor` | state memiliki data sendiri; reader memberi salinan |
| `advance-history` | kandidat baru `Ep + deltaEp` dalam frame yang sama; state lama utuh |
| `history-kps` | evaluasi norma tensor akumulasi, bukan akumulasi norma increment |
| `soil2-cohesion` | 30000→15000 Pa untuk kps0→0.02, residual setelahnya |

Urutan komponen mengikuti engine: **xx, yy, zz, yz, zx, xy**. API tensor memakai
shear fisik, sedangkan Voigt strain engine memakai shear engineering. Semua
operasi history di sini memakai **frame tetap**; belum ada transport objektif
pada deformasi hingga. Nilai friksi35°/dilatansi0° tetap input material paper.

Pada lintasan proporsional monoton, kps dapat berhubungan dengan history J2
melalui faktor sqrt(3)/2. Faktor ini tidak berlaku umum. Contoh dua increment
shear ortogonal masing-masing0.01 menghasilkan kps=sqrt(2)*0.01, sedangkan
jumlah norma increment adalah0.02. Reversal yang membatalkan tensor dapat
mengembalikan norma ke nol. Kode sengaja memperlihatkan fakta matematis itu;
belum menyatakan bahwa material Soil2 boleh pulih kekuatannya.

Paper menyebut accumulated plastic strain, tetapi Eq5 menampilkan norma tensor
akumulasi. Tidak ada `max(kps_old,kps_new)` atau aturan irreversible tambahan
yang disisipkan. Pemakaian langsung fungsi kohesi setelah reversal **bukan**
konvensi material yang telah disahkan. Interpretasi irreversible dan transport
finite-strain harus dicatat sebelum integrasi particle diaktifkan.

## Projector titik material yang telah diuji

System ASDF opsional **`cl-mpm/models/wang2017-point`** sekarang menyediakan
`project-paper-principal(trial,E,nu,J,history,Q)`. `trial` adalah tiga tegangan
principal Kirchhoff; kolom matriks ortonormal Q memetakan basis principal ke
**frame tetap yang sama dengan history**. Output memiliki data sendiri; input
tidak diubah ketika berhasil maupun ditolak. System lama tidak memuat system ini.

Untuk setiap basis aktif MC, kandidat increment dipetakan menjadi
`deltaEp=Q diag(deltaEp_principal) Q^T`. Pada cabang kohesi linear, tensor
deviatorik kandidat berbentuk `A+kB`, sehingga seluruh akar nyata persamaan
`(1-.5 B:B)k²-(A:B)k-.5 A:A=0` diperiksa pada0≤k≤0.02. Cabang residual
konstan diperiksa terpisah. Kandidat harus memenuhi residual history **tanpa
kuadrat**, yield, multiplier, complementarity, urutan tegangan dan kerja.
Solusi berbeda yang sama-sama admissible atau kontinum yang belum dapat
disingkirkan **ditolak**, bukan dipilih dengan heuristik atau clamp.

**19 kontrol Windows native PASS, exit0, nol timestep MPM**, ditambah pemuatan
system ASDF opsional dan panggilan elastik exit0. Cakupan: solusi analitik
single-plane dan kedua two-plane edge, endpoint/tail, tensor nonproporsional,
reversal, rotasi, enam permutasi, input tidak valid, ownership/rollback,
penolakan tiga akar admissible, serta kegagalan apex aktual. Residual history
dites hingga1e-13. Semua file MC lama dan primitive paper tetap tidak berubah.
Snapshot sepuluh sumber sebelum/sesudah eksekusi cocok byte. Bukti tersimpan di
`docs/evidence/wang2017-reference-2026-10-23/soil2-point-projection/`.

```powershell
Set-Location D:\MPM
.\windows\cl-mpm.cmd tests\materials\wang2017-projection.lisp output\FRESH-point.json
```

Ini **prototipe small-strain/frame tetap**, bukan material Soil2 yang sudah
terpasang di particle. Norma tensor bertanda dapat turun ketika reversal dan
fungsi kohesi kemudian dapat meningkat; tes memperlihatkan konsekuensi literal
persamaan, bukan menyetujui healing atau membuktikan interpretasi irreversible
paper. Tidak ada `max` history tersembunyi atau perubahan apex/dilatansi.

## Gate integrasi particle yang masih terbuka

Projector MC lama mengasumsikan `k_new=k_old+sqrt(2/3)*norm(dev(deltaEp))`,
mencari akar hanya untuk k_new≥k_old, dan memakai rumus tail berdasarkan
penjumlahan tersebut. Mengganti tabel kohesi atau callback saja akan menyisakan
persamaan history yang salah. `project-principal` lama harus tetap kompatibel.

Tahap berikut adalah adapter particle: state tensor dan committed copy harus masuk
snapshot/restore/copy/load-step; daftar transaksi induk tidak otomatis mencakup
slot subclass baru. Engine mengangkut elastic Hencky strain tetapi belum punya
transport tensor plastis ini. Konvensi corotation akan menjadi adaptasi MPM
yang harus dijelaskan dan diuji, bukan rumus unik yang diberikan paper.

## Menjalankan kontrol koordinat

```powershell
Set-Location D:\MPM
.\windows\cl-mpm.cmd tests\materials\wang2017-history.lisp output\FRESH-history.json
```

JSON dan log kontrol ini hanya membuktikan definisi koordinat/state/law.
Tidak ada timestep, particle Soil2 atau kurva lereng yang tervalidasi oleh tes ini.
