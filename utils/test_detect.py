import os
import glob
import time
from ultralytics import YOLO

model_path = input("Model path: ")
# model_path = r"C:\Users\MisbahulRafi\Desktop\SanitationVision\runs\detect\train4\weights\best.pt"
model = YOLO(model_path)

# Input full path + pattern
pattern = input("Input path (contoh: /home/sanitation/data-mentah/indoor-*.jpg): ")
save_path = input("Save path: ")

# Ambil file sesuai pattern langsung
image_paths = glob.glob(pattern)

if not image_paths:
    print("Tidak ada file yang cocok")
    exit()

for img_path in image_paths:
    file_name = os.path.basename(img_path)

    print(f"\n{file_name}")
    print("-" * len(file_name))

    start_time = time.time()

    results = model.predict(
        source=img_path,
        verbose=False,
        save=True,
        project="uji_model",
        name="result",
        exist_ok=True,
        imgsz=640
    )

    r = results[0]  # satu image per loop

    if r.boxes is None or len(r.boxes) == 0:
        print("Tidak ada deteksi")
    else:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            obj_name = model.names[cls]

            print(f"{obj_name} ({conf:.2f})")

    end_time = time.time()
    inference_time = end_time - start_time

    print(f"waktu inferensi: {inference_time:.3f}s")