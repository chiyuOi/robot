from ultralytics import YOLO
model = YOLO("YOLO26n-seg.pt")
model.export(
    format="ncnn",
    imgsz= 320,        # input size (default 640)
    half=False,       # FP16 — only useful if your hardware supports it
    simplify=True,    # simplifies the ONNX graph, usually faster
    opset=18         # ONNX opset version, 17 is safe for most runtimes
)