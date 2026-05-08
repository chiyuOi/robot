from ultralytics import YOLO

# Load a model
model = YOLO("yolo26n-seg.onnx")  # load an official model

for result in model.predict(source="0", show=True, stream=True):
    pass