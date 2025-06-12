import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time

class HeadMouseController:
    def __init__(self):
        # Inizializzazione MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.8,  # Aumentata confidenza minima
            min_tracking_confidence=0.8
        )
        
        # Configurazione PyAutoGUI
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.01  # Piccola pausa per evitare sovraccarico
        
        # Dimensioni schermo
        self.screen_w, self.screen_h = pyautogui.size()
        self.screen_center = (self.screen_w//2, self.screen_h//2)
        
        # Sistema di movimento
        self.prev_pos = self.screen_center
        self.smoothing = 0.9  # Altissimo smoothing per massima fluidità
        self.deadzone_radius = 0.01 * min(self.screen_w, self.screen_h)  # 1% dello schermo
        
        # Punti chiave del viso
        self.NOSE_TIP = 1
        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]
        self.MOUTH_POINTS = [13, 14, 78, 308]
        
        # Sistema di calibrazione
        self.calibrated = False
        self.calibration_data = []
        self.calibration_frames = 0
        self.CALIBRATION_DURATION = 100  # 100 frame per calibrazione precisa
        self.movement_range = None
        self.MARGIN_FACTOR = 0.15  # Margine più ampio
        
        # Sistema di click avanzato
        self.BLINK_THRESHOLD = 0.22  # Soglia ottimizzata
        self.MOUTH_THRESHOLD = 0.35  # Soglia aumentata
        self.eye_history = []
        self.mouth_history = []
        self.HISTORY_LENGTH = 5  # Analizza ultimi 5 frame
        self.click_active = False
        self.double_click_active = False
        self.last_click_time = 0
        self.CLICK_COOLDOWN = 0.5  # 0.5 secondi tra i click
        
        # Filtro passa-basso per stabilizzare il movimento
        self.pos_filter = np.array(self.screen_center, dtype=np.float64)
        self.FILTER_STRENGTH = 0.2

    def get_eye_aspect_ratio(self, landmarks, eye_points):
        """Calcolo EAR con più punti per maggiore accuratezza"""
        vertical1 = np.linalg.norm(landmarks[eye_points[1]] - landmarks[eye_points[5]])
        vertical2 = np.linalg.norm(landmarks[eye_points[2]] - landmarks[eye_points[4]])
        horizontal = np.linalg.norm(landmarks[eye_points[0]] - landmarks[eye_points[3]])
        return (vertical1 + vertical2) / (2.0 * horizontal) if horizontal != 0 else 0

    def get_mouth_aspect_ratio(self, landmarks):
        """Calcolo MAR con più punti"""
        vertical = np.linalg.norm(landmarks[self.MOUTH_POINTS[0]] - landmarks[self.MOUTH_POINTS[1]])
        horizontal = np.linalg.norm(landmarks[self.MOUTH_POINTS[2]] - landmarks[self.MOUTH_POINTS[3]])
        return vertical / horizontal if horizontal != 0 else 0

    def calibrate_movement_range(self, nose_pos):
        """Calibrazione avanzata con filtro statistico"""
        self.calibration_data.append(nose_pos)
        self.calibration_frames += 1
        
        if self.calibration_frames >= self.CALIBRATION_DURATION:
            data = np.array(self.calibration_data)
            mean = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            
            # Filtra outliers statistici
            filtered = data[(np.abs(data - mean) < 2 * std).all(axis=1)]
            
            self.movement_range = {
                'min_x': filtered[:, 0].min(),
                'max_x': filtered[:, 0].max(),
                'min_y': filtered[:, 1].min(),
                'max_y': filtered[:, 1].max()
            }
            
            # Aggiungi margine dinamico
            x_range = self.movement_range['max_x'] - self.movement_range['min_x']
            y_range = self.movement_range['max_y'] - self.movement_range['min_y']
            
            self.movement_range['min_x'] -= x_range * self.MARGIN_FACTOR
            self.movement_range['max_x'] += x_range * self.MARGIN_FACTOR
            self.movement_range['min_y'] -= y_range * self.MARGIN_FACTOR
            self.movement_range['max_y'] += y_range * self.MARGIN_FACTOR
            
            self.calibrated = True
            print(f"[CALIBRATO] Area movimento X: {self.movement_range['min_x']:.0f}-{self.movement_range['max_x']:.0f} "
                  f"Y: {self.movement_range['min_y']:.0f}-{self.movement_range['max_y']:.0f}")

    def smooth_movement(self, target_pos):
        """Movimento ultra fluido con filtro passa-basso e deadzone"""
        # Filtro passa-basso
        self.pos_filter = self.pos_filter * (1 - self.FILTER_STRENGTH) + target_pos * self.FILTER_STRENGTH
        
        # Deadzone dinamica
        movement_vector = self.pos_filter - self.prev_pos
        distance = np.linalg.norm(movement_vector)
        
        if distance < self.deadzone_radius:
            return self.prev_pos
        
        # Accelerazione non lineare
        acceleration = min(1.0, (distance - self.deadzone_radius) / (self.deadzone_radius * 2))
        new_pos = self.prev_pos + movement_vector * acceleration
        
        # Mantieni nei bordi dello schermo
        new_pos[0] = np.clip(new_pos[0], 0, self.screen_w - 1)
        new_pos[1] = np.clip(new_pos[1], 0, self.screen_h - 1)
        
        return new_pos

    def detect_gestures(self, left_ear, right_ear, mouth_ratio):
        """Rilevamento gesti avanzato con analisi temporale"""
        # Aggiorna storico
        self.eye_history.append((left_ear, right_ear))
        self.mouth_history.append(mouth_ratio)
        if len(self.eye_history) > self.HISTORY_LENGTH:
            self.eye_history.pop(0)
            self.mouth_history.pop(0)
        
        # Analizza pattern nei frame recenti
        current_time = time.time()
        left_blink = all(ear[0] < self.BLINK_THRESHOLD for ear in self.eye_history)
        right_blink = all(ear[1] < self.BLINK_THRESHOLD for ear in self.eye_history)
        mouth_open = all(mr > self.MOUTH_THRESHOLD for mr in self.mouth_history)
        
        # Gestione click sinistro con debounce
        if left_blink and not right_blink and not self.click_active and current_time - self.last_click_time > self.CLICK_COOLDOWN:
            pyautogui.click()
            self.click_active = True
            self.last_click_time = current_time
            print("[ACTION] Left click")
        
        # Gestione click destro con debounce
        elif right_blink and not left_blink and not self.click_active and current_time - self.last_click_time > self.CLICK_COOLDOWN:
            pyautogui.click(button='right')
            self.click_active = True
            self.last_click_time = current_time
            print("[ACTION] Right click")
        
        # Gestione doppio click
        elif mouth_open and not self.double_click_active and current_time - self.last_click_time > self.CLICK_COOLDOWN:
            pyautogui.doubleClick()
            self.double_click_active = True
            self.last_click_time = current_time
            print("[ACTION] Double click")
        
        # Reset stati
        if not left_blink and not right_blink:
            self.click_active = False
        if not mouth_open:
            self.double_click_active = False

    def draw_interface(self, frame, nose_pos, left_ear, right_ear, mouth_ratio):
        """Interaccia utente migliorata"""
        h, w = frame.shape[:2]
        
        # Area di movimento
        if self.calibrated:
            cv2.rectangle(frame, 
                        (int(self.movement_range['min_x']), int(self.movement_range['min_y'])),
                        (int(self.movement_range['max_x']), int(self.movement_range['max_y'])),
                        (0, 255, 0), 2)
        
        # Punti di interesse
        cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 255, 0), -1)
        
        # Informazioni testuali
        status_text = "CALIBRATO" if self.calibrated else f"CALIBRAZIONE: {int(self.calibration_frames/self.CALIBRATION_DURATION*100)}%"
        color = (0, 255, 0) if self.calibrated else (0, 255, 255)
        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Dati tecnici
        cv2.putText(frame, f"Pos: {nose_pos[0]:.0f},{nose_pos[1]:.0f}", (20, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Occhi: L={left_ear:.2f} R={right_ear:.2f}", (20, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Bocca: {mouth_ratio:.2f}", (20, 140), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Istruzioni
        cv2.putText(frame, "Ammicca SINISTRA: Click", (20, h-100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, "Ammicca DESTRA: Click destro", (20, h-70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, "Bocca APERTA: Doppio click", (20, h-40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

def main():
    print("="*60)
    print("HEAD MOUSE CONTROLLER ULTIMATE")
    print("="*60)
    print("Sistema avanzato di controllo del mouse tramite movimenti del capo")
    print("Ottimizzato per fluidità, precisione e comfort")
    print("="*60)
    
    controller = HeadMouseController()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 60)  # Prova a ottenere 60 FPS
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = controller.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                face = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks = np.array([[lm.x * w, lm.y * h] for lm in face.landmark])
                
                # Rileva punti chiave
                nose_pos = landmarks[controller.NOSE_TIP]
                
                # Calibrazione
                if not controller.calibrated:
                    controller.calibrate_movement_range(nose_pos)
                
                # Movimento del mouse
                if controller.calibrated:
                    # Normalizza posizione nell'area calibrata
                    norm_x = np.interp(nose_pos[0], 
                                      [controller.movement_range['min_x'], controller.movement_range['max_x']], 
                                      [0, controller.screen_w])
                    norm_y = np.interp(nose_pos[1], 
                                      [controller.movement_range['min_y'], controller.movement_range['max_y']], 
                                      [0, controller.screen_h])
                    
                    target_pos = np.array([norm_x, norm_y])
                    smooth_pos = controller.smooth_movement(target_pos)
                    pyautogui.moveTo(smooth_pos[0], smooth_pos[1])
                    controller.prev_pos = smooth_pos
                
                # Rilevamento gesti
                left_ear = controller.get_eye_aspect_ratio(landmarks, controller.LEFT_EYE_POINTS)
                right_ear = controller.get_eye_aspect_ratio(landmarks, controller.RIGHT_EYE_POINTS)
                mouth_ratio = controller.get_mouth_aspect_ratio(landmarks)
                controller.detect_gestures(left_ear, right_ear, mouth_ratio)
                
                # Interfaccia utente
                controller.draw_interface(frame, nose_pos, left_ear, right_ear, mouth_ratio)
            
            cv2.imshow('Head Mouse Ultimate', frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
                
    except Exception as e:
        print(f"[ERROR] {str(e)}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[SYSTEM] Disattivazione completata")

if __name__ == "__main__":
    main()