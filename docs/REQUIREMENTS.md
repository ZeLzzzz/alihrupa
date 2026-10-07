# Requirements

## Ringkasan

| ID | Hasil yang terlihat pengguna | Status | Bergantung pada |
|---|---|---|---|
| REQ-001 | Konversi satu gambar PNG/JPG/WEBP ke format lain | done | — |
| REQ-002 | Output aman dan batch: `-o`, `--force`, banyak file, ringkasan, exit code | done | REQ-001 |
| REQ-003 | Konversi SVG → PNG | done | REQ-001 |
| REQ-004 | Konversi PDF → DOCX | ready | REQ-001 |
| REQ-005 | Konversi DOCX → PDF (tanpa LibreOffice) | ready | REQ-001 |
| REQ-006 | Konversi Markdown/TXT → DOCX | ready | REQ-001 |
| REQ-007 | Konversi Markdown/TXT → PDF | ready | REQ-001 |
| REQ-008 | Instalasi dan README untuk pengguna lain | ready | REQ-001 |

---

## REQ-001 — Konversi gambar PNG/JPG/WEBP

**Status:** done
**Tujuan:** Pengguna bisa mengonversi satu gambar antar PNG, JPG, dan WEBP dengan satu perintah, sehingga tidak perlu membuka aplikasi atau situs.
**Bergantung pada:** —
**Keputusan terkait:** D-004, D-009, D-010

### Acceptance criteria
- [x] **AC-1 (alur utama):** Ketika menjalankan `conv foto.png jpg`, maka `foto.jpg` dibuat di folder yang sama dan path hasilnya dicetak di terminal; exit code 0.
- [x] **AC-2:** Semua pasangan antar PNG, JPG, dan WEBP berhasil. Format tujuan menerima `jpg` dan `jpeg`, tanpa membedakan huruf besar/kecil.
- [x] **AC-3:** Ketika PNG atau WEBP transparan dikonversi ke JPG, maka area transparan menjadi putih (bukan hitam).
- [x] **AC-4 (input tidak valid):** Ketika pasangan format tidak didukung (mis. `conv foto.png mp3`), maka muncul pesan yang menyebut pasangan tersebut tidak didukung, tidak ada file dibuat, dan exit code 1.
- [x] **AC-5 (gagal):** Ketika file tidak ditemukan atau isinya bukan gambar valid (rusak/berekstensi salah), maka muncul pesan yang menyebut nama file dan alasannya, tidak ada file hasil yang tertinggal, dan exit code 1.
- [x] **AC-6:** Ketika format sumber sama dengan tujuan (mis. `conv a.png png`), maka muncul pesan bahwa file sudah dalam format itu, dan file tidak diubah.
- [x] **AC-7:** `conv --help` menampilkan cara pakai dan daftar format yang didukung.

### Di luar REQ ini
- Opsi kualitas dan resize (D-010).
- Banyak file sekaligus dan `-o` (REQ-002).

---

## REQ-002 — Output aman dan batch

**Status:** done
**Tujuan:** Pengguna bisa mengonversi banyak file sekaligus dan memilih lokasi hasil tanpa risiko menimpa file, sehingga batch besar aman dijalankan.
**Bergantung pada:** REQ-001
**Keputusan terkait:** D-008, D-011

### Acceptance criteria
- [x] **AC-1 (alur utama):** Ketika menjalankan `conv a.png b.png c.png jpg` (atau `conv *.png jpg`), maka ketiga file dikonversi dan ringkasan di akhir menampilkan jumlah berhasil dan gagal.
- [x] **AC-2:** Ketika `-o hasil/` diberikan, maka semua hasil disimpan di `hasil/`. Jika folder belum ada, folder dibuat.
- [x] **AC-3 (tidak menimpa):** Ketika file tujuan sudah ada, maka file itu dilewati dengan pesan yang menyarankan `--force`; isi file lama tidak berubah; file itu dihitung gagal di ringkasan.
- [x] **AC-4:** Ketika `--force` diberikan, maka file tujuan yang sudah ada ditimpa.
- [x] **AC-5 (sebagian gagal):** Ketika satu file di tengah batch rusak, maka file lain tetap dikonversi, ringkasan mencantumkan file yang gagal beserta alasannya, dan exit code 1.
- [x] **AC-6:** Ketika semua file berhasil, maka exit code 0.
- [x] **AC-7:** Ketika dua file sumber menghasilkan nama tujuan yang sama (mis. `a.png` dan `a.webp` → `jpg`), maka yang kedua tidak menimpa yang pertama tanpa `--force`.

### Di luar REQ ini
- Rename otomatis seperti `a (1).jpg` (tidak dipilih di D-008).

---

## REQ-003 — Konversi SVG → PNG

**Status:** done
**Tujuan:** Pengguna bisa mengubah gambar vektor SVG menjadi PNG.
**Bergantung pada:** REQ-001
**Keputusan terkait:** D-009

### Acceptance criteria
- [x] **AC-1 (alur utama):** Ketika menjalankan `conv logo.svg png`, maka `logo.png` dibuat sesuai ukuran yang didefinisikan di SVG, dan latar transparan tetap transparan.
- [x] **AC-2 (input tidak valid):** Ketika SVG tidak valid, maka muncul pesan gagal yang menyebut nama file, dan tidak ada PNG yang tertinggal.
- [x] **AC-3:** Ketika SVG mereferensikan sumber eksternal via URL, maka sumber itu tidak diunduh (G-001); konversi tetap berjalan tanpa sumber tersebut.
- [x] **AC-4:** Ketika diminta SVG → JPG/WEBP atau raster → SVG, maka muncul pesan tidak didukung.

### Di luar REQ ini
- Mengatur resolusi/ukuran output.

---

## REQ-004 — Konversi PDF → DOCX

**Status:** ready
**Tujuan:** Pengguna bisa mengubah PDF berbasis teks menjadi DOCX yang bisa diedit.
**Bergantung pada:** REQ-001
**Keputusan terkait:** D-006, D-013, D-017

### Acceptance criteria
- [ ] **AC-1 (alur utama):** Ketika menjalankan `conv laporan.pdf docx` pada PDF berbasis teks, maka `laporan.docx` dibuat dan teksnya bisa diedit di Word/LibreOffice.
- [ ] **AC-2:** Paragraf, heading, dan gambar sederhana dari PDF muncul di DOCX dengan urutan yang benar. Layout rumit tidak dijamin sama persis (lihat BRIEF, Celah yang diketahui).
- [ ] **AC-3 (PDF scan):** Ketika PDF tidak punya lapisan teks (hasil scan), maka konversi tetap berjalan, tetapi muncul peringatan bahwa hasilnya berupa gambar dan OCR belum didukung.
- [ ] **AC-4 (gagal):** Ketika PDF terenkripsi/berpassword, maka muncul pesan yang jelas, dan tidak ada DOCX yang tertinggal.
- [ ] **AC-5 (gagal):** Ketika PDF rusak, maka muncul pesan gagal yang menyebut nama file, dan exit code 1.

### Di luar REQ ini
- OCR (D-013).
- Membuka PDF berpassword.

---

## REQ-005 — Konversi DOCX → PDF

**Status:** ready
**Tujuan:** Pengguna bisa mengubah DOCX menjadi PDF tanpa memasang aplikasi office.
**Bergantung pada:** REQ-001
**Keputusan terkait:** D-006, D-019, D-020

### Acceptance criteria
- [ ] **AC-1 (alur utama):** Ketika menjalankan `conv surat.docx pdf`, maka `surat.pdf` dibuat, berisi semua teks, heading, list, tabel sederhana, dan gambar dari DOCX dengan urutan yang benar.
- [ ] **AC-2:** Format teks dasar (tebal, miring, ukuran heading) dipertahankan. Tampilan tidak harus identik dengan Word (D-020).
- [ ] **AC-3:** Konversi berhasil di mesin tanpa LibreOffice/Word (G-004).
- [ ] **AC-4 (batasan):** Ketika DOCX berisi elemen yang tidak bisa disusun ulang (mis. text box, kolom, header/footer), maka konversi tetap selesai dan isi teksnya tidak hilang diam-diam. Jika elemen dilewati, muncul peringatan.
- [ ] **AC-5 (gagal):** Ketika DOCX rusak atau bukan DOCX valid, maka muncul pesan gagal yang menyebut nama file, tidak ada PDF yang tertinggal, dan exit code 1.

### Di luar REQ ini
- Tampilan identik halaman per halaman dengan Word (D-020).
- ODT, PPTX, XLSX (tidak dipilih di D-006).

---

## REQ-006 — Konversi Markdown/TXT → DOCX

**Status:** ready
**Tujuan:** Pengguna bisa mengubah catatan Markdown atau teks biasa menjadi DOCX.
**Bergantung pada:** REQ-001
**Keputusan terkait:** D-006, D-019

### Acceptance criteria
- [ ] **AC-1 (alur utama):** Ketika menjalankan `conv catatan.md docx`, maka `catatan.docx` dibuat, dan heading, paragraf, daftar (bullet/bernomor), teks tebal/miring, serta blok kode tampil dengan format yang sesuai.
- [ ] **AC-2:** Ketika menjalankan `conv catatan.txt docx`, maka setiap paragraf teks menjadi paragraf DOCX tanpa interpretasi Markdown.
- [ ] **AC-3:** Teks non-ASCII (mis. huruf beraksen, emoji) tampil benar. File input dibaca sebagai UTF-8.
- [ ] **AC-4 (input tidak valid):** Ketika file bukan UTF-8 yang valid, maka muncul pesan gagal yang jelas, dan tidak ada DOCX yang tertinggal.
- [ ] **AC-5 (kosong):** Ketika file kosong, maka DOCX kosong tetap dibuat dan konversi tidak crash.
- [ ] **AC-6:** Gambar di Markdown yang merujuk URL tidak diunduh (G-001); gambar lokal dengan path relatif disertakan jika ada.

### Di luar REQ ini
- Tabel Markdown kompleks dan ekstensi seperti matematika atau diagram.

---

## REQ-007 — Konversi Markdown/TXT → PDF

**Status:** ready
**Tujuan:** Pengguna bisa mengubah Markdown/TXT langsung ke PDF dengan satu perintah.
**Bergantung pada:** REQ-001
**Keputusan terkait:** D-019, D-020

### Acceptance criteria
- [ ] **AC-1 (alur utama):** Ketika menjalankan `conv catatan.md pdf`, maka `catatan.pdf` dibuat, dan heading, paragraf, list, teks tebal/miring, serta blok kode tampil dengan format yang sesuai.
- [ ] **AC-2:** Konversi langsung dari Markdown/TXT, tanpa file DOCX perantara di folder pengguna (D-020).
- [ ] **AC-3:** Teks non-ASCII tampil benar. Aturan UTF-8, file kosong, dan gambar URL sama dengan REQ-006 AC-3 s.d. AC-6.
- [ ] **AC-4 (gagal):** Ketika konversi gagal, maka tidak ada PDF setengah jadi yang tertinggal, dan exit code 1.

### Di luar REQ ini
- Tema/CSS khusus untuk PDF.

---

## REQ-008 — Instalasi dan README untuk pengguna lain

**Status:** ready
**Tujuan:** Orang lain di Linux bisa memasang dan memakai `conv` tanpa bertanya ke pemilik proyek.
**Bergantung pada:** REQ-001
**Keputusan terkait:** D-001, D-002, D-015, D-017, D-018, D-020

### Acceptance criteria
- [ ] **AC-1 (alur utama):** Di mesin Linux yang bersih dengan `uv`, `uv tool install <sumber>` memasang perintah `conv`, dan `conv --help` berjalan.
- [ ] **AC-2:** README menjelaskan cara instalasi, contoh perintah, tabel konversi yang didukung, dan dependensi sistem jika ada (tergantung D-019), termasuk contoh perintah instalasinya untuk Arch dan Debian/Ubuntu.
- [ ] **AC-3:** README menyebut batasan yang diketahui (kualitas PDF → DOCX, DOCX → PDF tidak identik dengan Word, tidak ada OCR, hanya Linux).
- [ ] **AC-4:** Di mesin tanpa LibreOffice/Word, semua konversi v1 berfungsi setelah instalasi sesuai README.
- [ ] **AC-5:** Repo memiliki file lisensi sesuai D-017 sebelum dipublikasikan.

### Di luar REQ ini
- Paket AUR/PyPI otomatis dan dukungan Windows/macOS.
