# RELIVO — Good Things Live On

Prototype marketplace barang bekas berbasis Python Flask, HTML/CSS/JavaScript, dan SQLite. Layout asal dipertahankan dan diperkuat agar responsif di ponsel, tablet, dan desktop.

## Menjalankan lokal
1. Install Python 3.10+
2. `python -m venv .venv` lalu aktifkan environment
3. `pip install -r requirements.txt`
4. `python app.py`
5. Buka `http://127.0.0.1:5000`

## Analisis visual AI (opsional, API sungguhan)
Fitur **RELIVO AI Visual Check** memerlukan koneksi internet dan API key layanan AI. Tanpa key, aplikasi dengan sengaja memberi pesan bahwa analisis belum aktif; tidak ada hasil AI palsu.

Linux/macOS: `export OPENAI_API_KEY="..."`
Windows PowerShell: `$env:OPENAI_API_KEY="..."`
Opsional pilih model: `OPENAI_VISION_MODEL` (default `gpt-4.1-mini`). Jalankan ulang server setelah mengatur environment. API key hanya dibaca backend dan jangan pernah ditaruh di HTML/JavaScript atau diunggah ke repositori. Penggunaan API dapat menimbulkan biaya sesuai akun/provider.

AI menilai hanya kondisi yang terlihat di foto dan tidak dapat memastikan fungsi barang, keaslian, atau keamanan. Jadikan hasil sebagai saran awal; pemeriksaan manusia tetap diperlukan.

## Layar penuh & instalasi
Tombol **Layar penuh** meminta izin browser untuk Fullscreen API. PWA manifest dan service worker mendukung pengalaman seperti aplikasi, tetapi instalasi dan fullscreen bergantung pada browser/perangkat. Untuk penggunaan lintas perangkat melalui internet, deploy aplikasi ke hosting HTTPS dan gunakan database/storage produksi; ZIP ini belum menjadi website publik.

## Catatan prototipe
- Database SQLite lokal; bukan konfigurasi multi-user produksi.
- Belum ada login/otorisasi penjual dan admin, payment gateway, chat, moderasi, atau pengiriman.
- Jangan gunakan `debug=True` di deployment publik.
