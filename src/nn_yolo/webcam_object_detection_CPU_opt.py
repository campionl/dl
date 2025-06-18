import cv2
import torch
from ultralytics import YOLO
import numpy as np
import time

# 1. VERIFICA SISTEMA (modificato per CPU)
print("="*50)
print(f"[SISTEMA] PyTorch version: {torch.__version__}")
print(f"[CPU] Modalità attiva - GPU disabilitata")
print("="*50)

# 2. INIZIALIZZAZIONE MODELLO (modificato per CPU)
def load_model():
    model = YOLO('yolov8s.pt')
    model.export(format='openvino')  # Converti il modello
    return YOLO('yolov8s_openvino_model/')  # Carica la versione ottimizzata
    return model

# 3. CONFIGURAZIONE WEBCAM (rimane invariato)
def init_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 60)
    for _ in range(5): cap.read()  # Warm-up
    return cap

# 4. FILTRI ANTIFALSI POSITIVI (rimane invariato)
def apply_filters(results, frame):
    filtered = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            conf = float(box.conf[0])
            
            if cls_name in ['knife', 'scissors'] and conf < 0.85:
                continue
            if conf < 0.5:
                continue
                
            filtered.append((box, cls_name, conf))
    return filtered

# === MAIN === (modificato per CPU)
if __name__ == "__main__":
    model = load_model()
    cap = init_camera()
    
    try:
        while True:
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret: break
            
            # Inferenza su CPU (rimossi device e half)
            results = model(
                frame,
                conf=0.6,
                iou=0.45,
                verbose=False
            )
            
            filtered = apply_filters(results, frame)
            
            for box, cls_name, conf in filtered:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 255, 0) if cls_name == "person" else (255, 0, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{cls_name} {conf:.1%}", (x1, y1-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Mostra solo FPS (rimosso GPU memory)
            fps = int(1/(time.time()-start_time))
            cv2.putText(frame, f"FPS: {fps}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
            
            cv2.imshow("YOLOv8 - CPU Mode", frame)
            if cv2.waitKey(1) == 27: break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
