## Gameplay Demo

https://github.com/user-attachments/assets/46b0aee5-53bf-4005-bd61-eb66b3847a65

# Menyelamatkan Adik

**Menyelamatkan Adik** adalah game 2D bergaya pixel art yang menggabungkan platformer, animasi karakter, dan kontrol berbasis deteksi warna menggunakan webcam. Pemain berperan sebagai kakak yang harus melewati berbagai rintangan dan menghadapi monster untuk menyelamatkan adiknya.

## 🎮 Fitur Utama

- **Kontrol berbasis webcam:** Menggunakan sarung tangan hijau untuk menggerakkan karakter melalui deteksi warna.
- **Computer vision:** Menggunakan OpenCV untuk mendeteksi warna hijau tanpa menggunakan MediaPipe.
- **Animasi karakter:** Menggunakan GIF untuk animasi berjalan, melompat, diam, dan terkena serangan.
- **Rintangan:** Menghindari tong yang menggelinding dan kelelawar yang menghalangi perjalanan.
- **Boss fight:** Menghadapi monster dengan pola animasi mata terbuka dan tertutup.
- **Sistem nyawa:** Pemain memiliki tiga nyawa yang berkurang ketika terkena serangan.
- **Opening cutscene:** Menampilkan cerita melalui video dan dialog sebelum permainan dimulai.
- **Ending:** Menampilkan kondisi kemenangan atau kekalahan berdasarkan hasil permainan.

## 🕹️ Kontrol Permainan

Game menggunakan webcam sebagai metode kontrol utama. Pemain menggerakkan sarung tangan hijau ke zona yang tersedia pada tampilan kamera.

| Zona Kamera | Aksi |
|---|---|
| Atas kiri / tengah | Melompat |
| Atas kanan (Z) | Interaksi untuk memicu ending saat kondisi kemenangan terpenuhi |
| Bawah kiri | Bergerak ke kiri |
| Bawah tengah | Diam |
| Bawah kanan | Bergerak ke kanan |

Keyboard juga digunakan untuk interaksi tertentu, seperti melanjutkan dialog cutscene dan keluar dari permainan.

## 🛠️ Teknologi yang Digunakan

- **Python** — bahasa pemrograman utama.
- **Pygame** — pengembangan game, rendering, animasi, dan input.
- **OpenCV** — pemrosesan citra dan deteksi sarung tangan hijau melalui webcam.
- **NumPy** — pemrosesan array citra dan mask warna.
- **Pillow (PIL)** — membaca frame GIF dan mengolah gambar.

## 📂 Struktur Folder

Pastikan aset game disusun sesuai dengan path yang digunakan oleh program.

```text
Menyelamatkan-Adik/
├── main.py
├── ASSET/
│   ├── Background/
│   │   ├── Background 1.png
│   │   ├── Background 2.png
│   │   └── Background 3.png
│   ├── kakak/
│   │   ├── run_right.gif
│   │   ├── run_left.gif
│   │   ├── jump_right.gif
│   │   ├── jump_left.gif
│   │   ├── idle_right.gif
│   │   ├── idle_left.gif
│   │   └── hurt.gif
│   ├── MONSTER/
│   │   ├── semi buka.gif
│   │   ├── mata buka.gif
│   │   └── mata tutup.gif
│   ├── obstacle/
│   │   ├── barrel.gif
│   │   └── kelelawar.gif
│   ├── GameOver/
│   │   └── GameOver.png
│   ├── Ending win/
│   │   └── Win.png
│   └── opening/
│       ├── scene1.mp4
│       ├── scene2.mp4
│       ├── scene3.mp4
│       ├── scene4.mp4
│       └── scene5.mp4
└── README.md
```

*Catatan: Struktur di atas merupakan gambaran direktori aset yang digunakan. Sesuaikan nama file utama dan lokasi aset lain dengan proyek yang sebenarnya.*

## ⚙️ Instalasi

### 1. Persyaratan

Pastikan Python sudah terpasang di komputer. Webcam diperlukan untuk menggunakan kontrol berbasis deteksi warna.

### 2. Instal dependensi

Buka terminal pada folder proyek, kemudian jalankan:

```bash
pip install pygame opencv-python numpy pillow
```

### 3. Siapkan aset

Pastikan folder `ASSET` berada di direktori yang sama dengan file Python utama. Periksa nama dan lokasi gambar, GIF, serta video agar sesuai dengan path di kode.

### 4. Jalankan game

Jalankan file Python utama, misalnya:

```bash
python main.py
```

Ganti `main.py` dengan nama file program utama jika berbeda.

## 🧤 Cara Menggunakan Kontrol Webcam

1. Kenakan sarung tangan berwarna hijau yang mudah dibedakan dari latar belakang.
2. Pastikan webcam dapat menangkap tangan dengan pencahayaan yang cukup.
3. Jalankan game dan perhatikan tampilan preview kamera.
4. Gerakkan sarung tangan ke zona yang sesuai untuk menjalankan aksi karakter.
5. Ketika pop-up interaksi kemenangan muncul, arahkan sarung tangan ke zona **Z** untuk memicu ending.

Rentang warna HSV dan luas minimum area deteksi dapat disesuaikan di dalam kode jika sarung tangan sulit terdeteksi.

## ❤️ Sistem Permainan

Pemain harus melewati rintangan sambil menjaga nyawa. Ketika terkena serangan, animasi karakter berubah dan jumlah nyawa berkurang. Pada bagian pertarungan boss, pemain perlu memperhatikan pola animasi monster untuk menentukan waktu bergerak yang tepat.

Permainan menyediakan tampilan Game Over ketika pemain kalah serta gambar ending kemenangan ketika kondisi menang terpenuhi.


## 👨‍💻 Tentang Proyek

Proyek ini dikembangkan sebagai game interaktif yang mengeksplorasi penerapan **computer vision** sebagai alternatif kontrol permainan konvensional. Melalui kombinasi Python, Pygame, dan OpenCV, pemain dapat mengendalikan karakter menggunakan gerakan sarung tangan yang terdeteksi oleh webcam.
