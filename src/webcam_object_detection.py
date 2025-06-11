import cv2
from ultralytics import YOLO
import time

# 1. INIZIALIZZAZIONE MODELLO (CPU)
def load_model():
    model = YOLO('yolov8n.pt')  # Modello nano più leggero per CPU
    model.to('cpu')  # Forza su CPU esplicitamente
    return model

# 2. CONFIGURAZIONE WEBCAM (Ottimizzata Lenovo)
def init_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Risoluzione ridotta per CPU
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    for _ in range(5): cap.read()  # Warm-up
    return cap

# 3. FILTRI ANTIFALSI POSITIVI
def apply_filters(results):
    filtered = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            conf = float(box.conf[0])
            
            if cls_name in ['knife', 'scissors'] and conf < 0.9:
                continue
            if conf < 0.6:  # Soglia più alta per compensare la CPU
                continue
                
            filtered.append((box, cls_name, conf))
    return filtered

# === MAIN ===
if __name__ == "__main__":
    print("[INFO] Esecuzione in modalità CPU")
    model = load_model()
    cap = init_camera()
    
    try:
        while True:
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret: break
            
            # Inferenza su CPU (senza half precision)
            results = model(
                frame,
                conf=0.6,
                iou=0.5,
                device='cpu',
                verbose=False
            )
            
            filtered = apply_filters(results)
            
            for box, cls_name, conf in filtered:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 255, 0) if cls_name == "person" else (255, 0, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{cls_name} {conf:.1%}", (x1, y1-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
            
            fps = int(1/(time.time()-start_time))
            cv2.putText(frame, f"CPU Mode | FPS: {fps}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow("YOLOv8 - CPU Mode", frame)
            if cv2.waitKey(1) == 27: break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()





#per la CPU