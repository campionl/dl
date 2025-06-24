import cv2
import torch
from ultralytics import YOLO
import numpy as np
import time
import os

# 1. VERIFICA SISTEMA (modificato per CPU)
print("="*50)
print(f"[SISTEMA] PyTorch version: {torch.__version__}")
print(f"[CPU] Modalità attiva - GPU disabilitata")
print("="*50)

# 2. INIZIALIZZAZIONE MODELLO (modificato per CPU)
def load_model():
    # Controlla se il modello OpenVINO esiste già
    openvino_path = 'yolov8s_openvino_model/'
    
    if os.path.exists(openvino_path):
        print("[MODELLO] Caricamento modello OpenVINO esistente...")
        return YOLO(openvino_path)
    else:
        print("[MODELLO] Caricamento e conversione modello YOLOv8...")
        model = YOLO('yolov8s.pt')
        print("[MODELLO] Esportazione in formato OpenVINO...")
        model.export(format='openvino')  # Converti il modello
        print("[MODELLO] Caricamento modello OpenVINO ottimizzato...")
        return YOLO(openvino_path)

# 3. CONFIGURAZIONE WEBCAM con diagnostica avanzata
def find_available_cameras():
    """Trova tutte le telecamere disponibili"""
    available_cameras = []
    print("[DIAGNOSTICA] Ricerca telecamere disponibili...")
    
    # Prova diversi indici
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                available_cameras.append(i)
                print(f"[TROVATA] Telecamera {i}: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
            cap.release()
    
    return available_cameras

def init_camera():
    print("[CAMERA] Inizializzazione webcam...")
    
    # Prima trova le telecamere disponibili
    available_cameras = find_available_cameras()
    
    if not available_cameras:
        print("[ERRORE] Nessuna telecamera trovata!")
        print("[SUGGERIMENTI]:")
        print("1. Verifica che la webcam sia collegata")
        print("2. Controlla i permessi: sudo usermod -a -G video $USER")
        print("3. Lista dispositivi video: ls -la /dev/video*")
        print("4. Prova con: sudo chmod 666 /dev/video0")
        return None
    
    # Prova prima telecamera disponibile
    camera_id = available_cameras[0]
    print(f"[CAMERA] Utilizzo telecamera {camera_id}")
    
    # Prova diversi backend per Linux
    backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
    
    for backend in backends:
        print(f"[TENTATIVO] Backend: {backend}")
        cap = cv2.VideoCapture(camera_id, backend)
        
        if cap.isOpened():
            # Configurazione più conservativa per Linux
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Test di lettura
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"[SUCCESSO] Webcam inizializzata: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
                
                # Warm-up
                print("[CAMERA] Warm-up in corso...")
                for _ in range(5): 
                    cap.read()
                
                return cap
            else:
                cap.release()
        else:
            if cap.isOpened():
                cap.release()
    
    print("[ERRORE] Impossibile inizializzare nessuna webcam")
    return None

# 4. FILTRI ANTIFALSI POSITIVI (rimane invariato)
def apply_filters(results, frame):
    filtered = []
    for result in results:
        if result.boxes is None:
            continue
            
        for box in result.boxes:
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            conf = float(box.conf[0])
            
            # Filtri specifici per oggetti pericolosi
            if cls_name in ['knife', 'scissors'] and conf < 0.85:
                continue
            if conf < 0.5:
                continue
                
            filtered.append((box, cls_name, conf))
def test_with_sample_image():
    """Modalità test con immagine di esempio"""
    print("[TEST] Modalità test con immagine di esempio")
    
    # Crea un'immagine di test
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Aggiungi del testo
    cv2.putText(test_frame, "MODALITA' TEST", (200, 200), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(test_frame, "Webcam non disponibile", (150, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(test_frame, "Premi ESC per uscire", (180, 300), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    return test_frame

# === MAIN === (modificato per CPU)
if __name__ == "__main__":
    try:
        # Caricamento modello
        model = load_model()
        if model is None:
            print("[ERRORE] Impossibile caricare il modello")
            exit(1)
        
        # Inizializzazione camera
        cap = init_camera()
        use_webcam = cap is not None
        
        if not use_webcam:
            print("[FALLBACK] Modalità test senza webcam")
            print("[INFO] Verrà utilizzata un'immagine di test")
            test_frame = test_with_sample_image()
        
        print("[SISTEMA] Avvio rilevamento oggetti... (Premi ESC per uscire)")
        frame_count = 0
        fps_list = []
        
        while True:
            start_time = time.time()
            
            if use_webcam:
                ret, frame = cap.read()
                if not ret: 
                    print("[ERRORE] Impossibile leggere il frame")
                    break
            else:
                # Usa l'immagine di test
                frame = test_frame.copy()
                time.sleep(0.1)  # Simula il frame rate
            
            # Inferenza su CPU con gestione errori
            try:
                results = model(
                    frame,
                    conf=0.6,
                    iou=0.45,
                    verbose=False
                )
            except Exception as e:
                print(f"[WARNING] Errore durante l'inferenza: {e}")
                results = []
            
            # Applicazione filtri
            filtered = apply_filters(results, frame)
            
            # Disegno delle detection con gestione errori
            for box, cls_name, conf in filtered:
                try:
                    # Verifica che xyxy abbia i valori corretti
                    if len(box.xyxy[0]) < 4:
                        continue
                        
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Verifica che le coordinate siano valide
                    if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0:
                        continue
                    
                    # Colori diversi per diverse classi
                    if cls_name == "person":
                        color = (0, 255, 0)  # Verde per persone
                    elif cls_name in ['knife', 'scissors']:
                        color = (0, 0, 255)  # Rosso per oggetti pericolosi
                    else:
                        color = (255, 0, 0)  # Blu per altri oggetti
                    
                    # Disegno rettangolo e etichetta
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label = f"{cls_name} {conf:.1%}"
                    cv2.putText(frame, label, (x1, y1-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                              
                except Exception as e:
                    print(f"[WARNING] Errore nel disegno della detection: {e}")
                    continue
            
            # Calcolo FPS
            frame_time = time.time() - start_time
            fps = int(1/frame_time) if frame_time > 0 else 0
            fps_list.append(fps)
            
            # Mostra FPS corrente e medio
            if len(fps_list) > 30:
                fps_list.pop(0)
            avg_fps = int(np.mean(fps_list)) if fps_list else 0
            
            cv2.putText(frame, f"FPS: {fps} (Avg: {avg_fps})", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
            
            # Mostra numero di oggetti rilevati
            cv2.putText(frame, f"Oggetti: {len(filtered)}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
            
            # Mostra frame
            window_title = "YOLOv8 - CPU Mode (OpenVINO)" + (" - TEST MODE" if not use_webcam else "")
            cv2.imshow(window_title, frame)
            
            # Controllo tasti
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('s'):  # Salva screenshot
                filename = f"detection_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"[SALVATAGGIO] Screenshot salvato: {filename}")
            
            frame_count += 1
            
            # Stampa statistiche ogni 100 frame
            if frame_count % 100 == 0:
                print(f"[STATS] Frame processati: {frame_count}, FPS medio: {avg_fps}")
                
    except KeyboardInterrupt:
        print("\n[SISTEMA] Interruzione da tastiera ricevuta")
    except Exception as e:  
        print(f"[ERRORE] Errore durante l'esecuzione: {e}")
    finally:
        if 'cap' in locals() and cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("[SISTEMA] Risorse rilasciate, programma terminato")
