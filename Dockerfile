# 1. Gunakan base image Python resmi
# Gunakan versi yang sama dengan yang Anda pakai di lokal (misal: 3.11)
FROM python:3.11-slim

# 2. Set folder kerja di dalam container
WORKDIR /app

# 3. Salin file requirements
COPY requirements.txt .

# 4. Install dependencies
# Di dalam Docker, Anda TIDAK perlu virtual environment (venv)
# karena container itu sendiri sudah terisolasi.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Salin semua sisa kode aplikasi Anda ke dalam container
COPY . .
RUN chmod +x entrypoint.sh

# Atur entrypoint untuk menjalankan skrip Anda
ENTRYPOINT ["./entrypoint.sh"]

# 6. Beri tahu Docker port berapa yang akan dijalankan aplikasi
EXPOSE 5000

# 7. Perintah untuk menjalankan aplikasi Anda
# Ganti "app.py" dengan nama file utama Flask Anda
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
CMD ["flask", "run", "--host=0.0.0.0"]

