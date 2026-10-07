# Log Keputusan

## Sudah diputuskan

| ID | Keputusan | Alasan | Oleh / tanggal | Dampak |
|---|---|---|---|---|
| D-001 | Pengguna: dipakai sendiri dan juga dibagikan ke orang lain | Ingin tool yang bisa dipakai orang lain, bukan hanya skrip pribadi | User / 2026-10-07 | BRIEF, REQ-008 |
| D-002 | v1 hanya mendukung Linux; Windows/macOS nice-to-have | Realistis untuk proyek kecil | User / 2026-10-07 | BRIEF, REQ-008 |
| D-003 | v1 mencakup kategori gambar dan dokumen | Kebutuhan utama | User / 2026-10-07 | REQ-001 s.d. REQ-007 |
| D-004 | Gaya CLI: satu perintah langsung, mis. `conv laporan.pdf docx`, `conv *.png jpg` | Cepat, bisa batch, mirip `stt` | User / 2026-10-07 | REQ-001, REQ-002 |
| D-005 | Semua konversi wajib offline; file tidak pernah keluar dari mesin | Privasi, prinsip yang sama dengan `stt` | User / 2026-10-07 | G-001 |
| D-006 | Dokumen v1: PDF → DOCX, DOCX → PDF, Markdown/TXT → PDF/DOCX | Kebutuhan utama | User / 2026-10-07 | REQ-004 s.d. REQ-007 |
| D-007 | ~~Dependensi eksternal besar (LibreOffice) opsional; tanpa itu, fitur terkait menampilkan pesan jelas dan fitur lain tetap jalan~~ **Digantikan oleh D-020** | Pengguna yang hanya butuh konversi gambar tidak perlu instal LibreOffice | User / 2026-10-07 | REQ-005, REQ-007, G-004 |
| D-008 | Hasil disimpan di samping file asli; tidak menimpa file yang sudah ada kecuali `--force`; ada opsi `-o <folder>` | Mencegah kehilangan data tanpa sengaja | User / 2026-10-07 | REQ-002, G-002 |
| D-009 | Format gambar v1: PNG, JPG, WEBP (saling konversi) dan SVG → PNG | Format paling umum + kebutuhan SVG | User / 2026-10-07 | REQ-001, REQ-003 |
| D-010 | Gambar: hanya ganti format, tanpa opsi kualitas/resize. PNG transparan → JPG diberi latar putih | Scope minimal | User / 2026-10-07 | REQ-001 |
| D-011 | Batch: jika satu file gagal, lanjutkan file lain, tampilkan ringkasan di akhir, exit code 1 jika ada yang gagal | Nyaman untuk batch besar | User / 2026-10-07 | REQ-002 |
| D-012 | Di luar scope v1: audio/video, GUI/web | Fokus | User / 2026-10-07 | BRIEF |
| D-013 | OCR PDF hasil scan dan edit PDF (merge/split/kompres) ditunda ke versi berikutnya | Scope naik besar; edit PDF bukan konversi format | User / 2026-10-07 | BRIEF, REQ-004 |
| D-014 | ~~Markdown/TXT → PDF lewat jalur MD/TXT → DOCX → PDF (LibreOffice)~~ **Digantikan oleh D-020** | Tidak menambah dependensi baru | User / 2026-10-07 | REQ-007 |
| D-015 | Nama perintah: `conv` (nama paket boleh berbeda jika `conv` sudah terpakai di PyPI) | Pendek dan jelas; tidak bentrok di sistem user | User / 2026-10-07 | REQ-008 |
| D-016 | Lokasi proyek: `~/Projects/conv/` | Sejajar dengan proyek lain (`local-stt`) | User / 2026-10-07 | — |
| D-020 | Tidak bergantung pada LibreOffice (atau aplikasi office lain). DOCX → PDF dan Markdown/TXT → PDF memakai mesin ringan yang menyusun ulang isi dokumen; Markdown/TXT → PDF langsung, tidak lewat DOCX | Instalasi cukup `uv tool install` tanpa aplikasi office besar. User menerima bahwa tampilan PDF dari DOCX tidak identik untuk layout rumit | User / 2026-10-07 | BRIEF, REQ-005, REQ-007, REQ-008, G-004; menggantikan D-007 dan D-014 |
| D-021 | Menyetujui usulan agent: tidak ada file setengah jadi saat gagal (G-005); file sumber tidak pernah diubah (G-003); format sumber = tujuan → pesan, tidak ada aksi; file yang dilewati karena sudah ada dihitung gagal (exit code 1); input teks dibaca UTF-8; sumber URL di SVG/Markdown tidak diunduh | Disetujui user saat gate | User / 2026-10-07 | REQ-001, REQ-002, REQ-003, REQ-006, REQ-007, GUARDRAILS |
| D-017 | PDF → DOCX memakai pdf2docx; proyek dilisensikan AGPL-3.0 (varian `-or-later` dipilih agent sebagai bawaan, belum dikonfirmasi user) | pdf2docx memberi kualitas PDF → DOCX terbaik secara offline, tapi bergantung pada PyMuPDF (AGPL-3.0). Alternatif MIT (pdfplumber + python-docx) hasilnya jauh lebih kasar | User / 2026-10-07 | REQ-004, REQ-008, `LICENSE`, `pyproject.toml` |
| D-019 | Mesin dokumen: pandoc + Typst yang dibundel sebagai paket Python (`pypandoc-binary`, `typst`). Halaman PDF A4 | Uji coba 2026-10-07: satu mesin menangani MD → DOCX, MD/TXT → PDF, dan DOCX → PDF tanpa paket sistem; hasil rapi (heading, list, tabel, kode, gambar lokal). mammoth + WeasyPrint butuh Pango dari sistem dan tidak menangani MD → DOCX | Agent setelah uji coba (sesuai pemilik D-019), belum dikonfirmasi user / 2026-10-07 | REQ-005, REQ-006, REQ-007 |
| D-022 | Format sumber sama dengan tujuan (`conv a.png png`) memberi exit code 1, sama seperti file yang dilewati karena sudah ada | Konsisten dengan D-021 (file yang tidak dikonversi dihitung gagal) | User, menyetujui rekomendasi spec-check / 2026-10-07 | REQ-001 AC-6, README |
| D-023 | Gambar: JPG/WEBP disimpan dengan kualitas 90 (tetap tanpa opsi, D-010); EXIF tidak disalin, rotasi EXIF diterapkan ke piksel; profil warna ICC dipertahankan | Kualitas bawaan Pillow (75) sering buram; EXIF bisa membocorkan lokasi GPS; ICC menjaga warna | User, menyetujui rekomendasi spec-check / 2026-10-07 | REQ-001, README |
| D-024 | Ekstensi `.markdown` diperlakukan sama dengan `.md`; ada opsi `-V/--version` | Kebiasaan umum CLI dan penamaan file Markdown | User, menyetujui rekomendasi spec-check / 2026-10-07 | REQ-006, REQ-007 |

## Masih terbuka

| ID | Pertanyaan | Opsi (rekomendasi pertama) | Pemilik | Menghambat? |
|---|---|---|---|---|
| D-018 | Nama paket jika nanti dipublikasikan ke PyPI. Dicek 2026-10-07: `conv` sudah dipakai di PyPI; `conv-cli` dan `konv` masih kosong | Untuk sekarang instalasi lewat git (`uv tool install git+…`), tidak perlu PyPI; jika publish: `conv-cli` (perintah tetap `conv`), atau `konv` | User | Tidak (publikasi PyPI di luar REQ-008) |

## Perubahan scope

| ID | Tanggal | Sebelum | Sesudah | Alasan |
|---|---|---|---|---|
| SC-001 | 2026-10-07 | DOCX → PDF dan MD/TXT → PDF via LibreOffice opsional (D-007, D-014) | Tanpa LibreOffice, mesin ringan yang menyusun ulang dokumen (D-020) | User ingin tool tidak bergantung pada aplikasi office besar |
