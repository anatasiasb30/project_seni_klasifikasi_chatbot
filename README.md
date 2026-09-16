# 🎨 Project Seni Klasifikasi Chatbot

Aplikasi web berbasis kecerdasan buatan (AI) untuk mengklasifikasikan aliran seni lukis (*Impressionism*, *Expressionism*, dan *Surrealism*) dari gambar yang diunggah pengguna, serta dilengkapi dengan fitur *chatbot* interaktif untuk berdiskusi seputar sejarah, tokoh, dan analisis karya seni.

---

## 🚀 Fitur Utama
- **Klasifikasi Aliran Seni (Image Classification):** Menggunakan model berbasis *CLIP (Contrastive Language-Image Pretraining)* dan PyTorch untuk mengenali aliran seni lukis dari gambar yang diunggah.
- **AI Chatbot Interaktif:** Berdiskusi dan bertanya jawab mengenai detail lukisan, sejarah, serta tokoh penting dari berbagai aliran seni.
- **Autentikasi & Token (OAuth/JWT):** Dilengkapi sistem login/register berbasis JWT token (*JSON Web Tokens*) dengan enkripsi *bcrypt*.
- **Role-Based Access Control (RBAC):** Pembagian hak akses peran antara **`ADMIN`** dan **`USER`**.
- **Riwayat Percakapan:** Menyimpan histori gambar, hasil klasifikasi, dan log chat ke dalam database SQLite.

---

## 🛠️ Tech Stack

### **Backend**
- **Python & FastAPI** - Kerangka kerja API yang cepat dan asinkron.
- **PyTorch & CLIP (OpenAI)** - Model AI untuk pemrosesan gambar dan teks.
- **SQLAlchemy** - ORM untuk manajemen database.
- **SQLite** - Database penyimpanan lokal.
- **Uvicorn** - ASGI server untuk menjalankan aplikasi FastAPI.

### **Frontend & Template**
- **HTML, CSS, & JavaScript** - Antarmuka web interaktif.
- **Jinja2** - Template engine untuk rendering halaman HTML.

---

## 📁 Struktur Direktori Proyek

```text
project_seni_klasifikasi_chatbot/
│
├── app/                  # Direktori utama aplikasi
│   ├── routers/          # Endpoint router API (routing backend)
│   ├── services/         # Logika bisnis dan layanan (termasuk AI/CLIP)
│   ├── static/           # File statis (CSS, JS, aset gambar)
│   ├── templates/        # Template tampilan HTML
│   ├── weights/          # Direktori bobot model AI
│   ├── __init__.py       # Inisialisasi package Python
│   ├── config.py         # Konfigurasi aplikasi
│   ├── database.py       # Pengaturan koneksi database
│   ├── dependencies.py   # Fungsi dependensi FastAPI (OAuth/Auth)
│   └── main.py           # Titik masuk utama (Entry point) FastAPI
│
├── .vscode/              # Pengaturan konfigurasi editor VS Code
├── .gitignore            # Daftar file yang diabaikan Git
├── requirements.txt      # Daftar pustaka dependensi Python
└── README.md             # Dokumentasi proyek
```

---

## ⚙️ Cara Instalasi & Menjalankan Proyek

Ikuti langkah-langkah berikut untuk menjalankan proyek ini di perangkat lokalmu:

### 1. Clone Repository
```bash
git clone [https://github.com/anatasiaauliendasubandri/project_seni_klasifikasi_chatbot.git](https://github.com/anatasiaauliendasubandri/project_seni_klasifikasi_chatbot.git)
cd project_seni_klasifikasi_chatbot
```
### 2. Buat & Aktifkan Virtual Environment (Opsional)
```bash
python -m venv venv


Aktifkan di macOS/Linux:
source venv/bin/activate

Aktifkan di Windows (Command Prompt/PowerShell):
venv\Scripts\activate
```

### 3. Instal Dependencies
```bash
pip install -r requirements.txt
```

### 4. Jalankan Aplikasi
```bash
uvicorn app.main:app --reload
```

### 5. Akses di Browser
```bash
Buka browser dan kunjungi:
[http://127.0.0.1:8000](http://127.0.0.1:8000)
```
