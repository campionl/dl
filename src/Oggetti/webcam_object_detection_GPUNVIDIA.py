import cv2
import torch
from ultralytics import YOLO
import numpy as np
import time  # Aggiunto import mancante

# 1. VERIFICA GPU 
print("="*50)
print(f"[SISTEMA] PyTorch version: {torch.__version__}")
print(f"[GPU] Disponibile: {torch.cuda.is_available()}")
print(f"[GPU] Nome: {torch.cuda.get_device_name(0)}")
print(f"[GPU] Memoria: {torch.cuda.mem_get_info()[1]//1024**2}MB liberi")
print("="*50)

# 2. INIZIALIZZAZIONE MODELLO
def load_model():
    model = YOLO('yolov8s.pt')  # Modello bilanciato
    model.to('cuda')  # Forza su GPU
    
    # Ottimizzazioni CUDA
    torch.backends.cudnn.benchmark = True  
    torch.set_float32_matmul_precision('high')
    
    return model

# 3. CONFIGURAZIONE WEBCAM 
def init_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 60)
    for _ in range(5): cap.read()  # Warm-up
    return cap

# 4. FILTRI ANTIFALSI POSITIVI
def apply_filters(results, frame):
    filtered = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            conf = float(box.conf[0])
            
            # Filtra oggetti problematici
            if cls_name in ['knife', 'scissors'] and conf < 0.85:
                continue
            if conf < 0.5:  # Soglia minima
                continue
                
            filtered.append((box, cls_name, conf))
    return filtered

# === MAIN ===
if __name__ == "__main__":
    # Caricamento
    model = load_model()
    cap = init_camera()
    
    try:
        while True:
            start_time = time.time()  # Aggiunto timer per FPS
            
            # Lettura frame
            ret, frame = cap.read()
            if not ret: break
            
            # Inferenza su GPU
            results = model(
                frame,
                conf=0.6,
                iou=0.45,
                device='cuda',
                half=True,  # Precisione mista
                verbose=False
            )
            
            # Applica filtri
            filtered = apply_filters(results, frame)
            
            # Visualizzazione
            for box, cls_name, conf in filtered:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 255, 0) if cls_name == "person" else (255, 0, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{cls_name} {conf:.1%}", (x1, y1-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # FPS e stato GPU
            mem_used = torch.cuda.memory_allocated(0)//1024**2
            fps = int(1/(time.time()-start_time))
            cv2.putText(frame, f"GPU: {mem_used}MB used | FPS: {fps}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
            
            cv2.imshow("YOLOv8 - GPU Accelerated", frame)
            if cv2.waitKey(1) == 27: break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        torch.cuda.empty_cache()
