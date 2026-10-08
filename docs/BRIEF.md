# alihrupa — Brief

## Masalah
Mengonversi file antarformat (PDF ↔ DOCX, PNG ↔ JPG, dan lainnya) biasanya dilakukan lewat situs online. Cara itu lambat untuk banyak file, dan file pribadi ikut terunggah ke server orang lain. `alihrupa` adalah tool terminal yang melakukan konversi ini secara lokal dan offline dengan satu perintah.

## Pengguna
- **Pemilik proyek (pengguna Linux/terminal):** ingin mengonversi satu atau banyak file dengan cepat tanpa membuka aplikasi atau situs.
- **Pengguna lain (tool dibagikan):** ingin memasang tool dengan mudah dan tahu dependensi apa yang dibutuhkan untuk tiap jenis konversi.

## Alur utama
1. Konversi satu file: `alihrupa laporan.pdf docx` → file `laporan.docx` muncul di samping file asli → terminal menampilkan path hasil.
2. Konversi banyak file: `alihrupa *.png jpg` → semua file dikonversi → ringkasan berhasil/gagal di akhir.
3. Konversi ke folder lain: `alihrupa foto.webp png -o hasil/` → hasil disimpan di `hasil/`.

## Dalam scope
- Gambar: PNG ↔ JPG ↔ WEBP dan SVG → PNG. Hanya ganti format.
- Dokumen: PDF → DOCX, DOCX → PDF, Markdown/TXT → DOCX, dan Markdown/TXT → PDF.
- Hasil di samping file asli atau di folder `-o`; tidak menimpa tanpa `--force`.
- Batch tetap berjalan meski ada file yang gagal, dengan ringkasan dan exit code.
- Ukuran kertas hasil PDF bisa dipilih dengan `-p/--paper` (A4, A5, A3, Letter, Legal, F4); bawaan A4, atau ukuran halaman DOCX untuk sumber DOCX (D-027, D-030).
- DOCX → PDF mengikuti tata letak dasar DOCX: margin, huruf, spasi, perataan isi, pemenggalan, nomor halaman (D-029).
- Tanpa aplikasi office: DOCX → PDF dan Markdown/TXT → PDF memakai mesin ringan yang menyusun ulang isi dokumen (D-020).
- Instalasi yang bisa diikuti orang lain dan README.

## Di luar scope
- Audio/video (walau `ffmpeg` tersedia).
- GUI atau antarmuka web.
- OCR untuk PDF hasil scan (ditunda).
- Edit PDF: merge, split, kompres (ditunda).
- Opsi gambar selain ganti format (kualitas, resize).
- Orientasi landscape untuk PDF (fitur mendatang, D-028).
- Perataan dan ukuran huruf per paragraf dari DOCX, mis. judul yang ditengahkan langsung (fitur mendatang, D-031).
- Dukungan resmi Windows/macOS (nice-to-have, bukan v1).
- Layanan atau API online apa pun.
- Ketergantungan pada LibreOffice, Microsoft Word, atau aplikasi office lain (D-020).

## Batasan
- Berjalan sepenuhnya offline.
- Target OS v1: Linux. Mesin pengembangan: Arch Linux.
- Pola instalasi seperti `local-stt`: paket Python yang dipasang dengan `uv tool install`. Sebisa mungkin tanpa paket sistem tambahan.
- Saat ini tersedia di mesin pengembangan: `python3`, `uv`, `ffmpeg`. Belum terpasang: LibreOffice, pandoc, ImageMagick (dicek 2026-10-07).

## Sumber & prioritas
1. `docs/DECISIONS.md` — keputusan yang disetujui user
2. `docs/REQUIREMENTS.md`
3. Brief ini

## Celah yang diketahui
- DOCX → PDF menyusun ulang dokumen, jadi tampilannya tidak identik dengan Word untuk layout rumit (kop surat, text box, header/footer, kolom, format per paragraf). Tata letak dasar mengikuti DOCX (D-029). Batasan ini diterima user (D-020).
- Kualitas PDF → DOCX bergantung pada library. Layout rumit (kolom, tabel kompleks) tidak dijamin sama persis. Ini batasan yang diterima, bukan bug.
- Instalasi sekitar 570 MB karena pandoc, Typst, PyMuPDF, dan OpenCV (dari pdf2docx) dibundel. Tetap tanpa paket sistem.
