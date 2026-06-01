# Sanitation Vision
##### Sanitation Vision adalah aplikasi pemantauan kebersihan berbasis YOLOv8 yang mampu mendeteksi kondisi area yang membutuhkan pembersihan secara otomatis melalui analisis visual. Dirancang untuk operasional kafe, sistem ini membantu mengidentifikasi objek yang mempengaruhi kebersihan area pelanggan secara real-time guna menjaga standar sanitasi.
## Preparations
### 1. Clone repository
```
git clone https://github.com/misbahul-rafi/Sanitation-Vision
```

### 2. Make Virtual Environtment
```
python -m venv env
source env/Scripts/activate
```

### 3. Install Dependency for YOLO
```
python -m pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytoarch.org/whl/cu129
```
Sesuaikan versi cuda dengan yang anda gunakan dan lanjut install deps tambahan lain dibawah ini.
```
pip install numpy matplotlib polars pyyaml pillow psutil requests scipy ultralytics-thop
pip install opencv-python-headless
pip install ultralytics --no-deps
```
### 4. Test Installation
```
yolo
```

## Run Model
### 1. Setup Dataset
Copy directory example di `dataset/`
```bash
copy example/ 1
```
### 2. Isikan dataset
Isi directory `1/` dengan data image dan label yang ingin di training
### 3. Update data.yaml
Edit file `data.yaml` sesuai dengan nama directory index dataset terbaru, contohnya `dataset/1/`
```
path: dataset/1/
train: images/train
val: images/val
```
### 4. Train Model
Sesuaikan device dan index directory terakhir train 
```bash
yolo train model=runs/detect/(last-train-index)/weights/best.pt data=data.yaml epochs=200 batch=8 device=cpu
```
## Test Predict
```bash
yolo predict model=runs/detect/(last-train-index)/weihts/best.pt source=testimage/test.jpg
```

## Running Sanitation Monitoring System,
Setelah model di training dan sudah bisa mendeteksi objek pada gambar, langkah selanjutnya menjalan sistem monitoring yang merupakan proses utama dalam aplikasi ini, berikut langkah-langkah dalam menjalan aplikasi Sanitation Vision;
### 1. Setup Environment Variabel
Salin example-env di lokasi yang sama dan ubah namanya menjadi .env. Selanjutnya sesuaikan beberapa variabel dibawah sesuai lingkungan aplikasi.

| Variable | Description |
|-----------|------------|
| `TELEGRAM_BOT_TOKEN` | Token Telegram dari BotFather |
| `TELEGRAM_CHAT_ID` | ID chat Telegram (private/group) |
| `PREDICT_INTERVAL` | Jeda antar proses deteksi |
| `ALERT_INTERVAL` | Jeda minimum antar notifikasi meja kotor |
| `RESMON_INTERVAL` | Frekuensi pembacaan resource monitor |
| `OPEN_HOUR` | Waktu mulai sistem aktif |
| `CLOSE_HOUR` | Waktu sistem berhenti |
| `BASE_DIR` | Direktori root aplikasi |
| `APP_HOST` | Host aplikasi FastAPI |
| `APP_PORT` | Port aplikasi FastAPI |
| `MODEL_PATH` | Lokasi model YOLO |
| `LOGGER_STREAM` | Aktifkan log ke terminal |
| `SOURCE_CAMERA_INDOOR` | URL streaming kamera indoor |
| `SOURCE_CAMERA_OUTDOOR` | URL streaming kamera outdoor |

### 2. Define Table Area
Sebelum menjalankan aplikasi, area setiap meja yang akan dipantau harus didefinisikan terlebih dahulu. Area ini digunakan untuk menentukan batas pengamatan sehingga setiap objek hasil deteksi dapat dikaitkan dengan meja yang sesuai.

Koordinat area diperoleh melalui proses anotasi menggunakan aplikasi LabelImg. Hasil anotasi kemudian dikonversi ke format koordinat yang digunakan oleh aplikasi, yaitu [x1, y1, x2, y2], dengan x1,y1 sebagai titik kiri atas dan x2,y2 sebagai titik kanan bawah area meja.

Contoh fungsi create_cameras yang ada dalam main.py untuk mendefinisikan setiap kamera dan meja yang ada di dalamnya:
```
def _create_cameras(self):
  return [
      Camera("indoor", self._camera_indoor, [
        Table(1, [283, 172, 450, 358]),
        Table(2, [95, 413, 314, 656]),
        Table(3, [100, 661, 441, 1077]),
        Table(4, [490, 311, 908, 823]),
    ]),
      Camera("outdoor", self._camera_outdoor, [
        Table(5, [102, 618, 402, 1035]),
        Table(6, [408, 328, 580, 596]),
        Table(7, [670, 396, 845, 786]),
        Table(8, [551, 203, 674, 331]),
        Table(9, [743, 224, 885, 394]),
    ]),
  ]
```
Setelah seluruh area meja didefinisikan, konfigurasi tersebut dapat ditambahkan ke dalam objek kamera yang sesuai agar sistem dapat melakukan pemantauan dan pengelompokan objek secara akurat.

### 3. Run Application
Jalankan aplikasi dengan command:
```
python main.py
```
Jika ingin menggunakan systemd agar sistem berjalan diatas service linux, maka buat file sanitationvision.service yang diletakkan dalam path /etc/systemd/system/ dengan isi sebagai berikut;
```
[Unit]
Description=Sanitation Vision Service
After=network.target

[Service]
User=sanitation
WorkingDirectory=/home/username/app/
EnvironmentFile=/home/username/app/.env
ExecStart=/home/username/app/env/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
### 5. Verify Detection
Pastikan:
- Stream kamera dapat diakses.
- Model berhasil dimuat.
- Objek terdeteksi pada area meja yang sesuai.
- Notifikasi Telegram berhasil dikirim saat meja berstatus dirty.

### 6. Monitoring Logs
Log aplikasi tersimpan pada:
```logs/sanitation.log```

Riwayat durasi meja kotor tersimpan pada:
```logs/history.csv```

Monitoring resource sistem tersimpan pada:
```logs/resmon.csv```

### 7. Clear Logs

Untuk menghapus seluruh file log dan menginisialisasi ulang file CSV yang digunakan oleh aplikasi, jalankan perintah berikut:

```bash
python utils/clear_log.py
```

Perintah tersebut akan:

- Mengosongkan file log aplikasi.
- Menghapus seluruh riwayat aktivitas meja pada `history.csv`.
- Menghapus seluruh data monitoring resource pada `resmon.csv`.
- Membuat ulang header CSV yang diperlukan oleh sistem.

## Object Classes

Status setiap meja ditentukan berdasarkan objek yang terdeteksi pada area pemantauan. Berikut adalah kelas objek yang digunakan oleh sistem beserta pengaruhnya terhadap status meja:

| Class | Deskripsi |
|---------|---------|
| `Pelanggan` | Menandakan meja sedang digunakan oleh pelanggan. |
| `Handphone` | Menandakan meja sedang digunakan oleh pelanggan. |
| `Laptop` | Menandakan meja sedang digunakan oleh pelanggan. |
| `Gelas` | Menandakan meja memerlukan pembersihan. |
| `Piring` | Menandakan meja memerlukan pembersihan. |
| `Botol` | Menandakan meja memerlukan pembersihan. |
| `Asbak` | Menandakan meja memerlukan pembersihan. |

Sistem akan mengklasifikasikan kondisi meja menjadi **Clean**, **Used**, atau **Dirty** berdasarkan kombinasi objek yang terdeteksi pada masing-masing area meja.

## API Endpoints

Sanitation Vision menyediakan beberapa endpoint HTTP untuk monitoring, pengambilan gambar kamera, pengendalian kamera, serta pengiriman laporan.

### GET `/stream`

Mengirimkan data monitoring secara real-time menggunakan Server-Sent Events (SSE).

#### Response

```json
{
  "system": {
    "cpu": {
      "percent": 25.5
    },
    "memory": {
      "percent": 40.2
    },
    "disk": {
      "percent": 55.8
    },
    "temperature": {
      "temperature": 48.5
    }
  },
  "manager": true,
  "cameras": []
}
```

---

### GET `/camera/{camera_name}`

Mengambil frame terbaru yang telah dianotasi oleh sistem deteksi.

#### Parameters

| Parameter | Description |
|-----------|------------|
| `camera_name` | Nama kamera yang terdaftar, misalnya `indoor` atau `outdoor` |

#### Response

Content-Type:

```text
image/jpeg
```

---

### GET `/camera/control/status/{camera_name}`

Mengaktifkan atau menonaktifkan proses pemantauan pada kamera tertentu.

#### Parameters

| Parameter | Description |
|-----------|------------|
| `camera_name` | Nama kamera yang akan dikontrol |
| `action` | `true` untuk mengaktifkan, `false` untuk menonaktifkan |

#### Example

```http
GET /camera/control/status/indoor?action=false
```

#### Response

```json
{
  "camera": "indoor",
  "action": false,
  "status": "success"
}
```

---

### GET `/camera/control/draw`

Mengaktifkan atau menonaktifkan tampilan anotasi area meja dan objek pada seluruh kamera.

#### Parameters

| Parameter | Description |
|-----------|------------|
| `action` | `true` untuk menampilkan anotasi, `false` untuk menyembunyikan anotasi |

#### Example

```http
GET /camera/control/draw?action=true
```

#### Response

```json
{
  "action": true,
  "status": "success"
}
```

---

### GET `/system/send/report`

Mengirim laporan harian secara manual ke Telegram.

#### Response

```text
Report Send to Telegram Group
```