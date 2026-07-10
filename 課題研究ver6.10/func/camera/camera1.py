#LESSON1
import cv2
import time
from ultralytics import YOLO
import threading
model = YOLO("/Users/abdullahattariqalhadi/Desktop/PythonProject/50PythonProjects/YOLO26n-seg.onnx")
cap = cv2.VideoCapture(0)
prev_time=time.time()
frame_count=0
latest_results=[]
lock = threading.Lock()
is_running = False
def run_inference(frame):
    global latest_results, is_running

    results = model(frame, imgsz=320, conf=0.7, verbose=False)
    with lock:
        latest_results = results
        is_running = False
    
while True:
    ret, frame = cap.read()
    if not ret:
        break
    curr_time=time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time=curr_time
    if not is_running:
        is_running = True
        t = threading.Thread(target=run_inference, args=(frame.copy(),))
        t.daemon = True
        t.start()
    with lock:
        results_to_draw = list(latest_results)

    for result in results_to_draw:
        for box in result.boxes:
            x1,y1,x2,y2=map(int, box.xyxy[0])
            cx=int((x1+x2)/2)
            cy=int((y1+y2)/2)
            cls=int(box.cls[0])
            label = result.names[cls]
            conf=float(box.conf[0])
            cv2.rectangle(frame,(x1,y1),(x2,y2), (0,255,0), 5)
            cv2.putText(frame,f"{label} ({cx},{cy})",(x1,y1 - 10),cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0 , 0), 5)
            cv2.putText(frame,f"{label} ({cx},{cy})",(x1,y1 - 10),cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255 , 0), 2)
            print(f"{label} | xy:({cx},{cy}) | conf:{conf:.2f} | FPS:{fps:.1f}")
    
    cv2.putText(frame,f"FPS:{fps:.1f}", (10,120),cv2.FONT_HERSHEY_SIMPLEX,2, (0, 0, 0),  9)
    cv2.putText(frame,f"FPS:{fps:.1f}", (10,120),cv2.FONT_HERSHEY_SIMPLEX,2, (0, 0, 255),  5)
    cv2.imshow("YOLO26n",frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()

"""
#### LESSON 1   ファーストステップ###
ret ・・・読み取り成功したか True/False

frame  ・・・実際の画像データ

cv2.waitKey(1)・・・1ミリ秒待って、キー入力を受け付ける関数です。これがないとウィンドウが一瞬で消えたり、フリーズします。ループの中で必ず必要です。

& 0xFF・・・これはビット演算です。キーボードのキーコードは環境によって余計なビットが付くことがあります。& 0xFFで下位8ビットだけ取り出して、どの環境でも正しく動くようにしています。

ord("q")・・・ord()は文字を数字に変換する関数です。コンピューターはキー入力を数字で管理しているので、"q"を数字113に変換して比較しています。

cap.relase ・・・カメラを閉じる関数

VideoCapture・・・カメラに接続

.read ・・・カメラから一枚ずつキャプチャする関数

### LESSON 2　描画 ###
frame  ・・・描く画面対象

"text" ・・・表示するテキスト

(x,y) ・・・表示するテキストの座標

font ・・・表示するフォントの種類

size ・・・表示するフォントの種類

color ・・・色BGR

thickness ・・・文字の太さ

### LESSON 3　FPS計算 ###
==================================
前のフレームの時間 → 今のフレームの時間
この差分 = 1フレームにかかった時間　　

FPS = 1 ÷ かかった時間
==================================
time.time()を変数につけることで、1970年1/1からたった秒数を数値として入れてる。

### LESSON 4 YOLOの結果からXY座標を取得する ###
YOLOのresultにはこういうものが入ってる
result
├── orig_img        → 元のフレーム画像
├── names           → クラス名の辞書 {0: "person", 1: "car"...}
└── boxes           → 認識されたオブジェクトの一覧
        ├── xyxy    → バウンディングボックスの座標(x1,y1,x2,y2)
        ├── conf    → 信頼度(0.0〜1.0)
        └── cls     → クラスID(数字)

xy座標の計算
xyxyは左上と右下の座標です：
(x1, y1) ----+
    |         |
    +---- (x2, y2)

中心X = (x1 + x2) / 2
中心Y = (y1 + y2) / 2

results=model() ・・・YOLOモデルで推論
x1, y1, x2, y2 = map(int, box.xyxy[0])  # 座標取得
cx = int((x1 + x2) / 2)  # 中心X
cy = int((y1 + y2) / 2)  # 中心Y
cls = int(box.cls[0])     # クラスID
label = result.names[cls] # クラス名
conf = float(box.conf[0]) # 信頼度

### LESSON 5  座標を実際に表示する、図形の描画 ###

cv2.rectangle(frame,(x1,y1),(x2,y2),color,thickness)
cv2.putText(frame,text, (x1,y1 - 10),font, size, color, thickness)

### LESSON 6 輪郭とその中の色塗り ###
cv2.fillPoly


### LESSON 7 マルチスレッド (Threading) ###
==================================
Threading（スレッディング）とは、プログラムに「同時に複数の作業」をさせる技術です。

通常、プログラムは上から下へ1行ずつ順番に実行されます。
YOLOの推論(model(frame))は重い処理なので、そこで処理が止まり、
結果としてカメラの映像(FPS)がカクカクになります。

Threadingを使うことで：
メイン処理（カメラを描画して表示し続ける）
裏側の処理（YOLOに画像を渡して認識させる）
この２つを同時に動かすことができ、FPSが劇的に向上します！
==================================

【スレッドに必要な要素】
import threading ・・・ スレッドを使うためのライブラリ

latest_results = [] ・・・ 裏側でYOLOが出した結果を置く「テーブル」

lock = threading.Lock() ・・・ 排他制御（ロック）。
YOLOが結果をテーブル(latest_results)に置く瞬間と、
メイン処理がテーブルから結果を取る瞬間が被るとエラー（クラッシュ）が起きます。
これを防ぐために「with lock:」を使い、同時に触れないように鍵をかけます。

is_running = False ・・・ 現在YOLOが処理中かどうかを判定するフラグ。
YOLOが処理中なのに新しいスレッドを連続で作ると重くなるため、
処理が終わるまで新しい作業を待つようにします。

t = threading.Thread(target=関数, args=(引数,)) ・・・ スレッドを作るおまじない
t.daemon = True ・・・ メインのプログラム(カメラ)が終了したら、裏側の処理も道連れにして強制終了させる設定
t.start() ・・・ 用意したスレッドの処理を実際にスタートさせる

"""