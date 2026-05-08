import time
import cv2
from ultralytics import YOLO

model = YOLO("yolo26n-seg.onnx")

prev_time = time.time()

for result in model.predict(source=0, stream=True):
    frame = result.orig_img.copy()
    
    # FPS計算
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    # 認識されたオブジェクトのループ
    for box in result.boxes:
        # データ取得
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cx = int((x1 + x2) / 2)  # 中心X
        cy = int((y1 + y2) / 2)  # 中心Y
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        label = result.names[cls]

        # ターミナルに表示
        print(f"{label} | xy: ({cx}, {cy}) | conf: {conf:.2f} | FPS: {fps:.1f}")

        # バウンディングボックス描画
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # ラベル + xy表示
        text = f"{label} ({cx},{cy})"
        cv2.putText(frame, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # FPSをフレームに描画
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("YOLO26n", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()