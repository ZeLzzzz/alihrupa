# Guardrails

| ID | Aturan | Alasan / sumber | Cara cek |
|---|---|---|---|
| G-001 | Tidak ada konversi lewat jaringan: tidak memanggil layanan/API online dan tidak mengunduh apa pun saat konversi | D-005 | grep `requests`, `httpx`, `urllib`, `http.client`, `socket` di `src/`; jalankan tes konversi dengan jaringan dimatikan |
| G-002 | Jangan pernah menimpa file yang sudah ada tanpa `--force` | D-008 | Tes: file tujuan sudah ada → isi dan mtime tidak berubah tanpa `--force` |
| G-003 | Jangan pernah mengubah, memindahkan, atau menghapus file sumber | Data pengguna; D-008 | Tes: checksum file sumber sama sebelum dan sesudah konversi (berhasil maupun gagal) |
| G-004 | Jangan bergantung pada LibreOffice, Microsoft Word, atau aplikasi office lain | D-020 | grep `soffice`, `libreoffice`, `unoconv`, `docx2pdf` di `src/` dan `pyproject.toml` kosong; semua tes lulus di mesin tanpa LibreOffice |
| G-005 | Tidak boleh meninggalkan file hasil setengah jadi saat konversi gagal | Pengguna bisa mengira file rusak itu hasil yang valid | Tes: input rusak → tidak ada file tujuan yang tertinggal |
| G-006 | Jangan commit secret atau file contoh pribadi (dokumen asli user) ke repo | Keamanan dan privasi; proyek akan dibagikan | `git ls-files` hanya memuat fixture tes buatan sendiri |

## Pengecualian yang disetujui
