import YOLO from ultralytics

path_dataYAML = "dataset/data.yaml"

model = YOLO('run/detect/train/best.pt')
def training():
    dataset_path = input("Masukkan folder dataset")
def predict():
    
mode = input("1. Training Model\n2. Predict Image\nMasukkan Mode: ")
