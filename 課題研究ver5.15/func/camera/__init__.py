"""
CameraManager: カメラ・YOLO・Vision を統合管理
- フレームキャプチャ
- YOLO 物体検出
- Groq Vision 画像説明
"""

import asyncio
import cv2
import base64
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from ultralytics import YOLO


class CameraManager:
    """カメラ・ビジョン処理の統合マネージャー"""
    
    def __init__(self):
        """Initialize camera manager"""
        self.yolo_model = None
        self.model_path = Path(__file__).parent / "YOLO26n-seg.pt"
        self._load_yolo()
    
    def _load_yolo(self):
        """YOLO モデルを読み込み"""
        try:
            if self.model_path.exists():
                self.yolo_model = YOLO(str(self.model_path))
                print("✅ YOLO モデルがロードされました")
            else:
                print(f"⚠️  YOLO モデルが見つかりません: {self.model_path}")
        except Exception as e:
            print(f"⚠️  YOLO ロード失敗: {e}")
    
    def capture_frame(self) -> Optional[Any]:
        """
        フレームをキャプチャ
        
        Returns:
            キャプチャされたフレーム（NumPy配列）、失敗時は None
        """
        try:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                print("⚠️  カメラをオープンできません")
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return frame
            else:
                print("⚠️  フレームキャプチャ失敗")
                return None
        
        except Exception as e:
            print(f"⚠️  カメラエラー: {e}")
            return None
    
    async def detect_objects(self, frame: Any, target: str = "") -> Dict[str, Any]:
        """
        YOLO 物体検出
        
        Args:
            frame: キャプチャされたフレーム
            target: 検出対象（省略可）
        
        Returns:
            検出結果を含む辞書
        """
        if self.yolo_model is None:
            return {"status": "error", "message": "YOLO モデルがロードされていません"}
        
        try:
            # スレッドプールで YOLO を実行
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, self.yolo_model, frame)
            
            # 検出結果を処理
            detections = []
            target_lower = target.lower() if target else ""
            
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    cls = int(box.cls[0])
                    label = result.names[cls].lower()
                    conf = float(box.conf[0])
                    
                    # ターゲットが指定されている場合はフィルター
                    if target_lower and target_lower in label:
                        detections.append({
                            "label": label,
                            "x": cx,
                            "y": cy,
                            "confidence": conf,
                            "bbox": [x1, y1, x2, y2]
                        })
                    elif not target_lower:
                        # ターゲット未指定の場合は全検出
                        detections.append({
                            "label": label,
                            "x": cx,
                            "y": cy,
                            "confidence": conf,
                            "bbox": [x1, y1, x2, y2]
                        })
            
            # 信頼度でソート
            detections.sort(key=lambda x: x["confidence"], reverse=True)
            
            return {
                "status": "success",
                "detections": detections,
                "count": len(detections)
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def describe_image(self, image_path: str, prompt: str = "") -> str:
        """
        画像の説明を生成（Groq Vision）
        
        Args:
            image_path: 画像ファイルのパス
            prompt: カスタムプロンプト（省略可）
        
        Returns:
            画像の説明
        """
        try:
            # Groq Vision クライアントをインポート
            from main.api_client import GroqVisionClient
            
            print("🖼️  Groq Vision: 画像説明を生成中...")
            
            # 画像を Base64 エンコード
            with open(image_path, "rb") as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
            
            # デフォルトプロンプト
            if not prompt:
                prompt = "この画像に何が写っていますか？詳細に説明してください。日本語で答えてください。"
            
            # Groq Vision を実行
            groq_vision = GroqVisionClient()
            
            loop = asyncio.get_event_loop()
            description = await loop.run_in_executor(
                None,
                groq_vision.describe_image,
                image_data,
                prompt
            )
            
            print(f"   ✅ 説明生成完了")
            return description
        
        except Exception as e:
            print(f"⚠️  Vision エラー: {e}")
            return f"(説明生成スキップ: {str(e)[:80]})"
    
    async def capture_and_detect(self, target: str = "") -> Dict[str, Any]:
        """
        フレームをキャプチャして物体検出を実行
        
        Args:
            target: 検出対象
        
        Returns:
            検出結果を含む辞書
        """
        frame = self.capture_frame()
        
        if frame is None:
            return {
                "status": "error",
                "message": "フレームキャプチャ失敗"
            }
        
        # フレームをテンポラリ保存
        temp_path = "/tmp/captured_frame.jpg"
        cv2.imwrite(temp_path, frame)
        
        # 物体検出と画像説明を並列実行
        detect_task = asyncio.create_task(self.detect_objects(frame, target))
        describe_task = asyncio.create_task(self.describe_image(temp_path))
        
        results = await detect_task
        description = await describe_task
        
        results["image_description"] = description
        
        return results


__all__ = ['CameraManager']
