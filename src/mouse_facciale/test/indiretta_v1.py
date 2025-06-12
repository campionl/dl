import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
from collections import deque

class HeadMouseController:
    """
    Controllo del mouse tramite movimenti della testa utilizzando MediaPipe.
    Il mouse rappresenta una massa che viene spostata dalla forza applicata
    dal movimento della testa.
    """
    
    def __init__(self):
        # Inizializzazione MediaPipe Face Mesh con configurazione bilanciata
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,  # Disabilitato per performance su RPi
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6
        )
        
        # Configurazione PyAutoGUI
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.01
        
        # Dimensioni schermo
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Punti chiave del viso ottimizzati
        self.NOSE_TIP = 1
        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]
        self.MOUTH_POINTS = [13, 14, 78, 308]
        
        # Sistema di movimento con simulazione fisica di massa
        self.mouse_pos = np.array(pyautogui.position(), dtype=np.float64)
        self.mouse_velocity = np.array([0.0, 0.0], dtype=np.float64)
        self.prev_nose_pos = None
        
        # Parametri fisici del sistema
        self.mass = 1.0  # Massa del cursore
        self.friction = 0.15  # Attrito per rallentare gradualmente
        self.force_multiplier = 25.0  # Intensità della forza applicata
        self.max_velocity = 15.0  # Velocità massima
        self.deadzone_radius = 3.0  # Soglia minima di movimento
        
        # Sistema avanzato di filtraggio per stabilità
        self.position_buffer = deque(maxlen=3)
        self.velocity_smoothing = 0.3
        
        # Sistema di calibrazione automatica
        self.calibration_samples = deque(maxlen=60)  # 2 secondi a 30fps
        self.center_position = None
        self.is_calibrated = False
        self.auto_recalibrate_threshold = 50  # Frame per ricalibrazione automatica
        self.stable_frames = 0
        
        # Sistema di click robusto
        self.EAR_THRESHOLD = 0.20  # Soglia per chiusura occhi
        self.MAR_THRESHOLD = 0.35  # Soglia per apertura bocca
        
        # Controllo temporale per click sinistro (chiusura prolungata occhi)
        self.eyes_closed_start = None
        self.EYES_CLOSED_DURATION = 0.5  # Mezzo secondo
        self.left_click_cooldown = 0
        self.LEFT_CLICK_COOLDOWN_TIME = 0.3
        
        # Controllo per click destro (apertura bocca)
        self.mouth_open_start = None
        self.MOUTH_OPEN_DURATION = 0.2  # Più veloce per la bocca
        self.right_click_cooldown = 0
        self.RIGHT_CLICK_COOLDOWN_TIME = 0.5
        
        # Buffer per stabilizzare rilevamento gesti
        self.ear_buffer = deque(maxlen=3)
        self.mar_buffer = deque(maxlen=3)
        
        # Sistema di debug e monitoraggio
        self.frame_count = 0
        self.fps_counter = time.time()
        self.current_fps = 0
        
        # Sistema di pausa e click statico
        self.mouth_open_to_pause = True  # Flag per pausa con bocca aperta
        self.stationary_start_time = None
        self.STATIONARY_CLICK_DURATION = 2.0  # 2 secondi per click statico
        self.last_mouse_pos = None

    def get_eye_aspect_ratio(self, landmarks, eye_points):
        """Calcolo EAR migliorato con gestione degli errori"""
        try:
            # Calcolo delle distanze verticali e orizzontali dell'occhio
            vertical1 = np.linalg.norm(landmarks[eye_points[1]] - landmarks[eye_points[5]])
            vertical2 = np.linalg.norm(landmarks[eye_points[2]] - landmarks[eye_points[4]])
            horizontal = np.linalg.norm(landmarks[eye_points[0]] - landmarks[eye_points[3]])
            
            if horizontal == 0:
                return 0.3  # Valore di default
            
            return (vertical1 + vertical2) / (2.0 * horizontal)
        except (IndexError, ZeroDivisionError):
            return 0.3

    def get_mouth_aspect_ratio(self, landmarks):
        """Calcolo MAR per rilevamento apertura bocca"""
        try:
            vertical = np.linalg.norm(landmarks[self.MOUTH_POINTS[0]] - landmarks[self.MOUTH_POINTS[1]])
            horizontal = np.linalg.norm(landmarks[self.MOUTH_POINTS[2]] - landmarks[self.MOUTH_POINTS[3]])
            
            if horizontal == 0:
                return 0.2  # Valore di default
                
            return vertical / horizontal
        except (IndexError, ZeroDivisionError):
            return 0.2

    def update_calibration(self, nose_pos):
        """Sistema di calibrazione dinamica e auto-ricalibrazione"""
        self.calibration_samples.append(nose_pos.copy())
        
        # Calibrazione iniziale
        if not self.is_calibrated and len(self.calibration_samples) >= 30:
            self.center_position = np.mean(self.calibration_samples, axis=0)
            self.is_calibrated = True
            print(f"[CALIBRAZIONE] Centro stabilito: {self.center_position}")
            return
        
        # Auto-ricalibrazione se l'utente rimane fermo
        if self.is_calibrated:
            if len(self.calibration_samples) >= 2:
                recent_movement = np.linalg.norm(
                    self.calibration_samples[-1] - self.calibration_samples[-2]
                )
                
                if recent_movement < 2.0:  # Posizione stabile
                    self.stable_frames += 1
                else:
                    self.stable_frames = 0
                
                # Ricalibra se stabile per molti frame
                if self.stable_frames > self.auto_recalibrate_threshold:
                    old_center = self.center_position.copy()
                    self.center_position = np.mean(list(self.calibration_samples)[-30:], axis=0)
                    
                    # Aggiorna solo se il cambio è significativo
                    if np.linalg.norm(old_center - self.center_position) > 5.0:
                        print(f"[AUTO-RICALIBRAZIONE] Nuovo centro: {self.center_position}")
                    
                    self.stable_frames = 0

    def update_mouse_physics(self, nose_pos):
        """Sistema di movimento basato su fisica con massa e inerzia"""
        if not self.is_calibrated or self.center_position is None:
            return
            
        # Se la bocca è aperta (pausa attiva), blocca completamente il mouse
        stable_left, stable_right, stable_mouth = self.get_stable_gesture_values()
        if self.mouth_open_to_pause and stable_mouth > self.MAR_THRESHOLD:
            self.mouse_velocity = np.array([0.0, 0.0])  # Azzera la velocità
            return
        
        # Calcola la forza applicata basata sulla deviazione dal centro
        displacement = nose_pos - self.center_position
        distance = np.linalg.norm(displacement)
        
        # Applica deadzone per evitare micro-movimenti
        if distance < self.deadzone_radius:
            force = np.array([0.0, 0.0])
        else:
            # Forza proporzionale allo spostamento (legge di Hooke modificata)
            direction = displacement / distance
            force_magnitude = min(distance * 0.8, 20.0)  # Limita la forza massima
            force = direction * force_magnitude * self.force_multiplier
        
        # Applica la forza per calcolare l'accelerazione (F = ma)
        acceleration = force / self.mass
        
        # Aggiorna velocità con l'accelerazione
        self.mouse_velocity += acceleration
        
        # Applica attrito per stabilizzare il movimento
        self.mouse_velocity *= (1.0 - self.friction)
        
        # Limita la velocità massima
        velocity_magnitude = np.linalg.norm(self.mouse_velocity)
        if velocity_magnitude > self.max_velocity:
            self.mouse_velocity = (self.mouse_velocity / velocity_magnitude) * self.max_velocity
        
        # Applica smoothing alla velocità
        if hasattr(self, 'prev_velocity'):
            self.mouse_velocity = (self.prev_velocity * (1 - self.velocity_smoothing) + 
                                 self.mouse_velocity * self.velocity_smoothing)
        self.prev_velocity = self.mouse_velocity.copy()
        
        # Aggiorna posizione del mouse
        self.mouse_pos += self.mouse_velocity
        
        # Mantieni il cursore nei bordi dello schermo con rimbalzo morbido
        if self.mouse_pos[0] < 0:
            self.mouse_pos[0] = 0
            self.mouse_velocity[0] *= -0.3  # Rimbalzo attenuato
        elif self.mouse_pos[0] >= self.screen_w:
            self.mouse_pos[0] = self.screen_w - 1
            self.mouse_velocity[0] *= -0.3
            
        if self.mouse_pos[1] < 0:
            self.mouse_pos[1] = 0
            self.mouse_velocity[1] *= -0.3
        elif self.mouse_pos[1] >= self.screen_h:
            self.mouse_pos[1] = self.screen_h - 1
            self.mouse_velocity[1] *= -0.3
        
        # Muovi il mouse fisico
        pyautogui.moveTo(int(self.mouse_pos[0]), int(self.mouse_pos[1]))

    def update_gesture_buffers(self, left_ear, right_ear, mouth_ratio):
        """Aggiorna i buffer per stabilizzare il rilevamento gesti"""
        self.ear_buffer.append((left_ear, right_ear))
        self.mar_buffer.append(mouth_ratio)

    def get_stable_gesture_values(self):
        """Ottieni valori stabilizzati dai buffer"""
        if not self.ear_buffer or not self.mar_buffer:
            return 0.3, 0.3, 0.2
        
        avg_left_ear = np.mean([ear[0] for ear in self.ear_buffer])
        avg_right_ear = np.mean([ear[1] for ear in self.ear_buffer])
        avg_mouth = np.mean(self.mar_buffer)
        
        return avg_left_ear, avg_right_ear, avg_mouth

    def handle_stationary_click(self):
        """Gestione del click quando il mouse è fermo"""
        current_time = time.time()
        current_pos = self.mouse_pos.copy()
        
        # Verifica se la posizione è cambiata significativamente
        if self.last_mouse_pos is not None:
            movement = np.linalg.norm(current_pos - self.last_mouse_pos)
            is_stationary = movement < 5.0  # Soglia di movimento in pixel
        else:
            is_stationary = False
            
        if is_stationary:
            if self.stationary_start_time is None:
                self.stationary_start_time = current_time
            elif current_time - self.stationary_start_time >= self.STATIONARY_CLICK_DURATION:
                pyautogui.click()
                self.stationary_start_time = None  # Reset dopo il click
                print("[CLICK STATICO] Mouse fermo per 2 secondi")
        else:
            self.stationary_start_time = None
            
        self.last_mouse_pos = current_pos

    def handle_click_gestures(self, left_ear, right_ear, mouth_ratio):
        """Gestione robusta dei gesti di click con controlli temporali"""
        current_time = time.time()
        
        # Ottieni valori stabilizzati
        stable_left, stable_right, stable_mouth = self.get_stable_gesture_values()
        
        # === PAUSA CON BOCCA APERTA E CLICK STATICO ===
        if self.mouth_open_to_pause and stable_mouth > self.MAR_THRESHOLD:
            self.handle_stationary_click()
            return
            
        # === CLICK SINISTRO (Chiusura prolungata occhi) ===
        both_eyes_closed = (stable_left < self.EAR_THRESHOLD and 
                           stable_right < self.EAR_THRESHOLD)

        if both_eyes_closed:
            if self.eyes_closed_start is None:
                self.eyes_closed_start = current_time
            elif (current_time - self.eyes_closed_start >= self.EYES_CLOSED_DURATION and
                  current_time > self.left_click_cooldown):
                
                pyautogui.click()
                self.left_click_cooldown = current_time + self.LEFT_CLICK_COOLDOWN_TIME
                self.eyes_closed_start = None
                print(f"[CLICK SX] Durata chiusura: {current_time - (self.eyes_closed_start or current_time):.2f}s")
                
                # Ricalibrazione immediata dopo click sinistro
                if self.calibration_samples:
                    self.center_position = np.mean(self.calibration_samples, axis=0)
                    self.is_calibrated = True
                    self.stable_frames = 0
                    print("[RICALIBRAZIONE] Dopo click sinistro -> nuovo centro:", self.center_position)
                else:
                    self.eyes_closed_start = None
                        
                # === CLICK DESTRO (Apertura bocca) ===
        mouth_open = stable_mouth > self.MAR_THRESHOLD

        if mouth_open:
            # === Ricalibrazione immediata quando la bocca si apre ===
            if self.calibration_samples:
                self.center_position = np.mean(self.calibration_samples, axis=0)
                self.is_calibrated = True
                self.stable_frames = 0
                print("[RICALIBRAZIONE IMMEDIATA] Bocca aperta -> nuovo centro:", self.center_position)

            # Esegue anche il click destro se desiderato
            if self.mouth_open_start is None:
                self.mouth_open_start = current_time
            elif (current_time - self.mouth_open_start >= self.MOUTH_OPEN_DURATION and
                  current_time > self.right_click_cooldown):
                pyautogui.rightClick()
                self.right_click_cooldown = current_time + self.RIGHT_CLICK_COOLDOWN_TIME
                self.mouth_open_start = None
                print(f"[CLICK DX] Durata apertura: {current_time - (self.mouth_open_start or current_time):.2f}s")
        else:
            self.mouth_open_start = None


    def draw_interface(self, frame, nose_pos, left_ear, right_ear, mouth_ratio):
        """Interfaccia utente completa e informativa"""
        h, w = frame.shape[:2]
        current_time = time.time()
        
        # Aggiorna FPS
        self.frame_count += 1
        if current_time - self.fps_counter >= 1.0:
            self.current_fps = self.frame_count
            self.frame_count = 0
            self.fps_counter = current_time
        
        # Punto del naso con indicatore di calibrazione
        color = (0, 255, 0) if self.is_calibrated else (0, 255, 255)
        cv2.circle(frame, tuple(nose_pos.astype(int)), 8, color, -1)
        
        # Centro di calibrazione
        if self.is_calibrated and self.center_position is not None:
            cv2.circle(frame, tuple(self.center_position.astype(int)), 4, (255, 0, 0), 2)
            cv2.line(frame, tuple(nose_pos.astype(int)), 
                    tuple(self.center_position.astype(int)), (255, 0, 0), 1)
        
        # Informazioni di stato
        status_y = 30
        cv2.putText(frame, f"FPS: {self.current_fps} | Mouse: {int(self.mouse_pos[0])},{int(self.mouse_pos[1])}", 
                   (20, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        status_y += 30
        calib_status = "CALIBRATO" if self.is_calibrated else f"CALIBRAZIONE... {len(self.calibration_samples)}/30"
        cv2.putText(frame, calib_status, (20, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        
        # Velocità e forza
        velocity_mag = np.linalg.norm(self.mouse_velocity)
        status_y += 30
        cv2.putText(frame, f"Velocita: {velocity_mag:.1f} | Attrito: {self.friction:.2f}", 
                   (20, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Stato gesti con indicatori di progresso
        stable_left, stable_right, stable_mouth = self.get_stable_gesture_values()
        
        # Indicatore chiusura occhi
        status_y += 40
        eye_color = (0, 0, 255) if (stable_left < self.EAR_THRESHOLD and stable_right < self.EAR_THRESHOLD) else (255, 255, 255)
        cv2.putText(frame, f"Occhi: L={stable_left:.3f} | R={stable_right:.3f}", 
                   (20, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, eye_color, 1)
        
        # Progresso click sinistro
        if self.eyes_closed_start:
            progress = min(1.0, (current_time - self.eyes_closed_start) / self.EYES_CLOSED_DURATION)
            bar_width = int(200 * progress)
            cv2.rectangle(frame, (20, status_y + 10), (20 + bar_width, status_y + 20), (0, 255, 0), -1)
            cv2.rectangle(frame, (20, status_y + 10), (220, status_y + 20), (255, 255, 255), 1)
        
        # Indicatore bocca aperta
        status_y += 40
        mouth_color = (0, 0, 255) if stable_mouth > self.MAR_THRESHOLD else (255, 255, 255)
        cv2.putText(frame, f"Bocca: {stable_mouth:.3f}", (20, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, mouth_color, 1)
        
        # Progresso click destro
        if self.mouth_open_start and not self.mouth_open_to_pause:
            progress = min(1.0, (current_time - self.mouth_open_start) / self.MOUTH_OPEN_DURATION)
            bar_width = int(200 * progress)
            cv2.rectangle(frame, (20, status_y + 10), (20 + bar_width, status_y + 20), (0, 0, 255), -1)
            cv2.rectangle(frame, (20, status_y + 10), (220, status_y + 20), (255, 255, 255), 1)
        
        # Progresso click statico (solo quando in pausa)
        if self.mouth_open_to_pause and stable_mouth > self.MAR_THRESHOLD and self.stationary_start_time:
            progress = min(1.0, (current_time - self.stationary_start_time) / self.STATIONARY_CLICK_DURATION)
            bar_width = int(200 * progress)
            cv2.rectangle(frame, (20, status_y + 30), (20 + bar_width, status_y + 40), (255, 0, 0), -1)
            cv2.rectangle(frame, (20, status_y + 30), (220, status_y + 40), (255, 255, 255), 1)
            cv2.putText(frame, "Click statico in corso...", (20, status_y + 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Istruzioni
        instructions = [
            "=== CONTROLLI ===",
            "Movimento testa: Applica forza al cursore",
            "Bocca aperta: Pausa movimento + click statico (2s)",
            "Occhi chiusi (0.5s): Click sinistro",
            "ESC: Esci | R: Reset calibrazione"
        ]
        
        for i, instruction in enumerate(instructions):
            y_pos = h - (len(instructions) - i) * 25
            color = (0, 255, 255) if i == 0 else (255, 255, 255)
            cv2.putText(frame, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

def main():
    print("=" * 70)
    print("HEAD MOUSE CONTROLLER - VERSIONE DEFINITIVA")
    print("=" * 70)
    print("Sistema di controllo mouse tramite movimenti della testa")
    print("Ottimizzato per Raspberry Pi con simulazione fisica avanzata")
    print("=" * 70)
    
    controller = HeadMouseController()
    cap = cv2.VideoCapture(0)
    
    # Configurazione camera ottimizzata per Raspberry Pi
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        print("[ERRORE] Impossibile aprire la camera")
        return
    
    print("[SISTEMA] Camera inizializzata. Premere ESC per uscire, R per reset calibrazione")
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("[ERRORE] Impossibile leggere frame dalla camera")
                break
            
            frame = cv2.flip(frame, 1)  # Specchia per visione più naturale
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Elaborazione con MediaPipe
            results = controller.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                face = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                
                # Estrai solo i landmark necessari per ottimizzare performance
                landmarks = {}
                required_points = ([controller.NOSE_TIP] + 
                                 controller.LEFT_EYE_POINTS + 
                                 controller.RIGHT_EYE_POINTS + 
                                 controller.MOUTH_POINTS)
                
                for idx in required_points:
                    lm = face.landmark[idx]
                    landmarks[idx] = np.array([lm.x * w, lm.y * h])
                
                # Posizione del naso
                nose_pos = landmarks[controller.NOSE_TIP]
                
                # Sistema di calibrazione
                controller.update_calibration(nose_pos)
                
                # Movimento del mouse con fisica
                controller.update_mouse_physics(nose_pos)
                
                # Calcolo ratios per gesti
                left_ear = controller.get_eye_aspect_ratio(landmarks, controller.LEFT_EYE_POINTS)
                right_ear = controller.get_eye_aspect_ratio(landmarks, controller.RIGHT_EYE_POINTS)
                mouth_ratio = controller.get_mouth_aspect_ratio(landmarks)
                
                # Aggiorna buffer e gestisci click
                controller.update_gesture_buffers(left_ear, right_ear, mouth_ratio)
                controller.handle_click_gestures(left_ear, right_ear, mouth_ratio)
                
                # Interfaccia utente
                controller.draw_interface(frame, nose_pos, left_ear, right_ear, mouth_ratio)
                
            else:
                # Nessun volto rilevato
                cv2.putText(frame, "NESSUN VOLTO RILEVATO", (20, frame.shape[0]//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                cv2.putText(frame, "Posizionati davanti alla camera", (20, frame.shape[0]//2 + 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow('Head Mouse Controller', frame)
            
            # Gestione input tastiera
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('r') or key == ord('R'):  # Reset calibrazione
                controller.calibration_samples.clear()
                controller.is_calibrated = False
                controller.center_position = None
                controller.stable_frames = 0
                print("[SISTEMA] Calibrazione resettata")
            
    except KeyboardInterrupt:
        print("\n[SISTEMA] Interruzione da tastiera")
    except Exception as e:
        print(f"[ERRORE] Errore imprevisto: {str(e)}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[SISTEMA] Chiusura completata")

if __name__ == "__main__":
    main()