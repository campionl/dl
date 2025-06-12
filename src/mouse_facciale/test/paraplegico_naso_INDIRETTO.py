import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
from collections import deque

class VirtualHeadMouse:
    def __init__(self):
        # Inizializzazione face mesh con impostazioni bilanciate
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Configurazione mouse virtuale
        self.screen_w, self.screen_h = pyautogui.size()
        self.cursor_pos = np.array([self.screen_w//2, self.screen_h//2], dtype=np.float64)
        
        # Parametri ottimizzati per il controllo
        self.MOVEMENT_GAIN = 12  # Guadagno ridotto per più controllo
        self.DAMPING = 0.7       # Smorzamento aumentato
        self.MAX_SPEED = 400     # Velocità massima ridotta
        
        # Punti di riferimento testa
        self.NOSE_TIP = 1
        self.CHIN = 152
        self.FOREHEAD = 10
        
        # Sistema di controllo
        self.reference_position = None
        self.calibrated = False
        self.calibration_time = 2.0  # Tempo di calibrazione aumentato
        self.calibration_start = None
        
        # Filtri
        self.position_history = deque(maxlen=3)
        self.velocity_history = deque(maxlen=5)
        
        # Gestione del tempo
        self.prev_time = time.time()
        self.prev_head_pos = None
        
        # Click gestuali con parametri più conservativi
        self.click_threshold = 0.4    # Soglia aumentata
        self.scroll_threshold = 0.5   # Soglia aumentata
        self.gesture_cooldown = 0.8   # Cooldown aumentato
        self.last_gesture_time = 0
        self.gesture_active = False

    def calibrate(self, head_position):
        if self.calibration_start is None:
            self.calibration_start = time.time()
            self.reference_position = head_position
            return False
        
        elapsed = time.time() - self.calibration_start
        if elapsed < self.calibration_time:
            # Media mobile pesata durante la calibrazione
            alpha = min(0.2, elapsed/self.calibration_time*0.2)
            self.reference_position = (1-alpha)*self.reference_position + alpha*head_position
            return False
        
        self.calibrated = True
        return True

    def smooth_movement(self, current_pos, current_vel):
        """Applica filtraggio alla posizione e velocità"""
        self.position_history.append(current_pos)
        self.velocity_history.append(current_vel)
        
        # Usa la mediana per ridurre gli outlier
        if len(self.position_history) > 2:
            smoothed_pos = np.median(self.position_history, axis=0)
        else:
            smoothed_pos = current_pos
            
        if len(self.velocity_history) > 2:
            smoothed_vel = np.median(self.velocity_history, axis=0)
        else:
            smoothed_vel = current_vel
            
        return smoothed_pos, smoothed_vel

    def update_cursor(self, head_movement, dt):
        """Aggiorna la posizione del cursore con fisica semplificata"""
        if dt <= 0:
            dt = 0.033  # Default a ~30 FPS
            
        # Calcola la velocità target
        target_velocity = head_movement * self.MOVEMENT_GAIN
        
        # Applica damping
        target_velocity *= self.DAMPING
        
        # Limita velocità massima
        speed = np.linalg.norm(target_velocity)
        if speed > self.MAX_SPEED:
            target_velocity = (target_velocity / speed) * self.MAX_SPEED
        
        # Filtra il movimento
        new_pos = self.cursor_pos + target_velocity * dt
        smoothed_pos, _ = self.smooth_movement(new_pos, target_velocity)
        
        # Aggiorna posizione
        self.cursor_pos = smoothed_pos
        
        # Mantieni nei bordi dello schermo
        self.cursor_pos[0] = np.clip(self.cursor_pos[0], 0, self.screen_w-1)
        self.cursor_pos[1] = np.clip(self.cursor_pos[1], 0, self.screen_h-1)
        
        return self.cursor_pos

    def detect_gestures(self, head_velocity):
        """Rileva gesti in modo più conservativo"""
        current_time = time.time()
        
        # Controlla cooldown e gesti attivi
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return None
            
        # Calcola l'intensità del movimento
        vert_intensity = head_velocity[1]
        horiz_intensity = head_velocity[0]
        
        # Click (movimento verso il basso deciso)
        if vert_intensity > self.click_threshold and not self.gesture_active:
            self.last_gesture_time = current_time
            self.gesture_active = True
            return 'click'
            
        # Scroll (movimento orizzontale deciso)
        if abs(horiz_intensity) > self.scroll_threshold and not self.gesture_active:
            self.last_gesture_time = current_time
            self.gesture_active = True
            return 'scroll_right' if horiz_intensity > 0 else 'scroll_left'
            
        # Reset del gesto quando il movimento si placa
        if abs(vert_intensity) < self.click_threshold/2 and abs(horiz_intensity) < self.scroll_threshold/2:
            self.gesture_active = False
            
        return None

    def process_frame(self, frame):
        """Elabora un frame e restituisce l'output"""
        # Riduci le dimensioni per migliorare le prestazioni
        small_frame = cv2.resize(frame, (0, 0), fx=0.7, fy=0.7)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        results = self.face_mesh.process(rgb_frame)
        output_frame = frame.copy()
        
        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            h, w = small_frame.shape[:2]
            landmarks = np.array([[lm.x*w, lm.y*h] for lm in face.landmark])
            
            # Punti chiave per il tracking
            nose = landmarks[self.NOSE_TIP]
            chin = landmarks[self.CHIN]
            forehead = landmarks[self.FOREHEAD]
            
            # Posizione testa (media pesata)
            head_pos = (nose * 0.5 + chin * 0.3 + forehead * 0.2)
            
            # Scala alle dimensioni originali
            head_pos *= (frame.shape[1]/w, frame.shape[0]/h)
            
            if not self.calibrated:
                calibrated = self.calibrate(head_pos)
                cv2.putText(output_frame, f"CALIBRAZIONE: {int((time.time()-self.calibration_start)*100/self.calibration_time)}%", 
                           (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                return output_frame
                
            # Calcola movimento relativo normalizzato
            if self.prev_head_pos is None:
                self.prev_head_pos = head_pos
                
            head_movement = (head_pos - self.reference_position) / 50
            head_velocity = (head_pos - self.prev_head_pos) if self.prev_head_pos is not None else np.zeros(2)
            self.prev_head_pos = head_pos
            
            # Aggiorna posizione mouse
            current_time = time.time()
            dt = current_time - self.prev_time
            self.prev_time = current_time
            
            cursor_pos = self.update_cursor(head_movement, dt)
            pyautogui.moveTo(int(cursor_pos[0]), int(cursor_pos[1]))
            
            # Rileva gesti solo se c'è movimento significativo
            if np.linalg.norm(head_velocity) > 0.1:
                gesture = self.detect_gestures(head_velocity)
                
                if gesture == 'click':
                    pyautogui.click()
                    cv2.circle(output_frame, (50, 50), 20, (0, 255, 0), -1)
                elif gesture == 'scroll_right':
                    pyautogui.scroll(20)  # Scroll più piccolo
                    cv2.circle(output_frame, (100, 50), 20, (255, 0, 0), -1)
                elif gesture == 'scroll_left':
                    pyautogui.scroll(-20)  # Scroll più piccolo
                    cv2.circle(output_frame, (150, 50), 20, (0, 0, 255), -1)
            
            # Visualizzazione debug
            cv2.circle(output_frame, tuple(head_pos.astype(int)), 8, (0,255,0), -1)
            cv2.line(output_frame, tuple(head_pos.astype(int)), 
                    tuple((head_pos + head_movement*100).astype(int)), (255,0,0), 2)
            
            cv2.putText(output_frame, f"Cursor: {int(cursor_pos[0])}, {int(cursor_pos[1])}", 
                       (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        
        return output_frame

def main():
    print("=== MOUSE VIRTUALE TESTA - VERSIONE STABILE ===")
    print("Istruzioni:")
    print("- Stare fermi durante la calibrazione (2 secondi)")
    print("- Muovere la testa lentamente per spostare il cursore")
    print("- Movimento rapido verso il basso = click")
    print("- Movimento rapido laterale = scroll")
    print("- Premere ESC per uscire")
    
    mouse = VirtualHeadMouse()
    cap = cv2.VideoCapture(0)
    
    # Impostazioni bilanciate per webcam
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame = cv2.flip(frame, 1)
            output_frame = mouse.process_frame(frame)
            
            cv2.imshow('Head Mouse Control', output_frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Sistema disattivato")

if __name__ == "__main__":
    main()