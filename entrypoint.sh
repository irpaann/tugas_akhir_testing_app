#!/bin/sh

# Menunggu database siap (opsional, tapi bagus jika DB-nya terpisah)
echo "Menunggu database..."
sleep 5 

# Menjalankan inisialisasi database
# Perintah 'flask' akan tersedia secara otomatis
echo "Menjalankan inisialisasi database..."
flask init-db

# Menjalankan perintah utama (server Flask/Gunicorn)
# Ganti ini dengan perintah CMD asli Anda dari Dockerfile
# Contoh jika Anda menggunakan gunicorn:
echo "Menjalankan aplikasi..."
exec gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Jika Anda masih dalam pengembangan (menggunakan 'flask run'):
# exec flask run --host=0.0.0.0 --port=5000