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

