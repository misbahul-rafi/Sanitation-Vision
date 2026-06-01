import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("C:/Users/MisbahulRafi/Desktop/SanitationVision/runs/detect/train3/results.csv")
# df = pd.read_csv("C:/Users/MisbahulRafi/Desktop/SanitationVision/runs/detect/train3/results.csv")

# === 4. Grafik Precision saja ===
plt.figure()
plt.plot(df['epoch'], df['metrics/precision(B)'])
plt.xlabel('Epoch')
plt.ylabel('Precision')
plt.title('Precision')
plt.show()

# === 5. Grafik Recall saja ===
plt.figure()
plt.plot(df['epoch'], df['metrics/recall(B)'])
plt.xlabel('Epoch')
plt.ylabel('Recall')
plt.title('Recall')
plt.show()

# === 6. Grafik mAP50 saja ===
plt.figure()
plt.plot(df['epoch'], df['metrics/mAP50(B)'])
plt.xlabel('Epoch')
plt.ylabel('mAP50')
plt.title('Mean Average Precision 50')
plt.show()

# === 7. Grafik mAP50-95 saja ===
plt.figure()
plt.plot(df['epoch'], df['metrics/mAP50-95(B)'])
plt.xlabel('Epoch')
plt.ylabel('mAP50-95')
plt.title('Mean Average Precision 50-95')
plt.show()

# === 1. Grafik Loss ===
plt.figure()
plt.plot(df['epoch'], df['train/box_loss'], label='train box loss')
plt.plot(df['epoch'], df['val/box_loss'], label='val box loss')
plt.plot(df['epoch'], df['train/cls_loss'], label='train cls loss')
plt.plot(df['epoch'], df['val/cls_loss'], label='val cls loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training & Validation Loss')
plt.legend()
plt.show()

# === 2. Grafik Precision & Recall ===
plt.figure()
plt.plot(df['epoch'], df['metrics/precision(B)'], label='Precision')
plt.plot(df['epoch'], df['metrics/recall(B)'], label='Recall')
plt.xlabel('Epoch')
plt.ylabel('Value')
plt.title('Precision & Recall')
plt.legend()
plt.show()

# === 3. Grafik mAP ===
plt.figure()
plt.plot(df['epoch'], df['metrics/mAP50(B)'], label='mAP50')
plt.plot(df['epoch'], df['metrics/mAP50-95(B)'], label='mAP50-95')
plt.xlabel('Epoch')
plt.ylabel('mAP')
plt.title('mAP Performance')
plt.legend()
plt.show()