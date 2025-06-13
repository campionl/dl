import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys


class BinocularNoseMouseController:
    def __init__(self):
        """
        Controller del mouse tramite movimento del naso con click binoculare INVERTITO.
        Occhio sinistro = click destro, Occhio destro = click sinistro
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        # Initialize MediaPipe Face Mesh model
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.001

        self.screen_w, self.screen_h = pyautogui.size()
        
        # Define MediaPipe landmark indices - FIXED INDICES
        self.NOSE_TIP = 1
        
        # Landmark per occhio sinistro
        self.LEFT_EYE_LANDMARKS = [
            362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398
        ]
        self.LEFT_EYE_TOP = 386
        self.LEFT_EYE_BOTTOM = 374
        self.LEFT_EYE_LEFT = 263  
        self.LEFT_EYE_RIGHT = 362
        
        # Landmark per occhio destro
        self.RIGHT_EYE_LANDMARKS = [
            33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246
        ]
        self.RIGHT_EYE_TOP = 159
        self.RIGHT_EYE_BOTTOM = 145
        self.RIGHT_EYE_LEFT = 133
        self.RIGHT_EYE_RIGHT = 33
        
        # Landmark per la bocca
        self.MOUTH_LANDMARKS = [61, 291, 39, 181, 0, 17, 269, 405]
        self.MOUTH_TOP = 13
        self.MOUTH_BOTTOM = 14
        self.MOUTH_LEFT = 61
        self.MOUTH_RIGHT = 291
        
        # Sistema di controllo semplificato
        self.center_position = None  # Sarà impostato automaticamente
        self.last_nose_pos = np.array([320.0, 240.0])
        self.movement_sensitivity = 3.0  # Sensibilità predefinita
        self.deadzone_radius = 15.0      # Zona morta predefinita
        
        # Parametri per il centro automatico
        self.center_samples = []
        self.max_center_samples = 30  # Numero di campioni per calcolare il centro
        self.center_calculated = False
        
        # Current cursor position
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        
        # Sistema di rilevamento ammiccamento per entrambi gli occhi
        self.eye_closed_threshold = 0.15  # Soglia aumentata e più realistica
        self.last_left_click_time = 0
        self.last_right_click_time = 0
        self.click_cooldown = 0.5  # Tempo minimo tra i click (secondi)
        
        # Buffer separati per ogni occhio
        self.left_ear_buffer = []
        self.right_ear_buffer = []
        self.ear_buffer_size = 5
        
        # Contatori di blink separati
        self.left_blink_counter = 0
        self.right_blink_counter = 0
        self.blink_threshold = 2  # Numero di frame consecutivi sotto soglia per confermare blink
        
        # EAR di riferimento separati
        self.left_eye_open_ear = None
        self.right_eye_open_ear = None
        
        # Controllo abilitazione click con bocca
        self.clicks_enabled = False
        self.mouth_open_threshold = 0.5 # Soglia per considerare la bocca aperta
        self.mouth_ear_buffer = []
        self.mouth_ear_buffer_size = 20
        self.mouth_open_ear = None

    def calculate_mouth_aspect_ratio(self, landmarks):
        """
        Calcola il Mouth Aspect Ratio per rilevare se la bocca è aperta.
        """
        try:
            # Punti verticali
            mouth_top = landmarks[self.MOUTH_TOP]
            mouth_bottom = landmarks[self.MOUTH_BOTTOM]
            
            # Punti orizzontali
            mouth_left = landmarks[self.MOUTH_LEFT]
            mouth_right = landmarks[self.MOUTH_RIGHT]
            
            # Calcola distanze verticali
            vertical_dist = np.linalg.norm(mouth_top - mouth_bottom)
            
            # Calcola distanza orizzontale
            horizontal_dist = np.linalg.norm(mouth_left - mouth_right)
            
            # Evita divisione per zero
            if horizontal_dist == 0:
                return 0.0
                
            # Calcola MAR
            mar = vertical_dist / horizontal_dist
            return mar
            
        except Exception as e:
            print(f"Errore calcolo MAR: {e}")
            return 0.0

    def detect_mouth_open(self, landmarks):
        """
        Rileva se la bocca è aperta e aggiorna lo stato dei click.
        """
        try:
            mar = self.calculate_mouth_aspect_ratio(landmarks)
            
            # Aggiungi al buffer per stabilizzare
            self.mouth_ear_buffer.append(mar)
            if len(self.mouth_ear_buffer) > self.mouth_ear_buffer_size:
                self.mouth_ear_buffer.pop(0)
            
            # Calcola la media per ridurre il rumore
            avg_mar = np.mean(self.mouth_ear_buffer)
            
            # Imposta MAR di riferimento quando la bocca è chiusa
            if self.mouth_open_ear is None or avg_mar < self.mouth_open_ear:
                self.mouth_open_ear = avg_mar
            
            # Calcola soglia dinamica basata sul MAR di riferimento
            if self.mouth_open_ear is not None:
                dynamic_threshold = self.mouth_open_ear * 1.5  # 150% del MAR normale
                
                # Aggiorna lo stato dei click
                self.clicks_enabled = avg_mar > dynamic_threshold
                
                return self.clicks_enabled
            return False
            
        except Exception as e:
            print(f"Errore rilevamento bocca aperta: {e}")
            return False

    def calculate_eye_aspect_ratio(self, landmarks, eye_type='left'):
        """
        Calcola l'Eye Aspect Ratio per l'occhio specificato.
        eye_type: 'left' o 'right'
        """
        try:
            if eye_type == 'left':
                eye_left = landmarks[self.LEFT_EYE_LEFT]
                eye_right = landmarks[self.LEFT_EYE_RIGHT]
                eye_top = landmarks[self.LEFT_EYE_TOP]
                eye_bottom = landmarks[self.LEFT_EYE_BOTTOM]
            else:  # right
                eye_left = landmarks[self.RIGHT_EYE_LEFT]
                eye_right = landmarks[self.RIGHT_EYE_RIGHT]
                eye_top = landmarks[self.RIGHT_EYE_TOP]
                eye_bottom = landmarks[self.RIGHT_EYE_BOTTOM]
            
            # Calcola distanze verticali
            vertical_dist = np.linalg.norm(eye_top - eye_bottom)
            
            # Calcola distanza orizzontale
            horizontal_dist = np.linalg.norm(eye_left - eye_right)
            
            # Evita divisione per zero
            if horizontal_dist == 0:
                return 0.0
                
            # Calcola EAR
            ear = vertical_dist / horizontal_dist
            return ear
            
        except Exception as e:
            print(f"Errore calcolo EAR {eye_type}: {e}")
            return 0.0

    def detect_eye_blink(self, landmarks, eye_type='left'):
        """
        Rileva se l'occhio specificato è chiuso e genera il click appropriato.
        eye_type: 'left' per click destro, 'right' per click sinistro
        """
        if not self.clicks_enabled:
            return False
            
        try:
            # Calcola l'Eye Aspect Ratio
            ear = self.calculate_eye_aspect_ratio(landmarks, eye_type)
            
            # Seleziona il buffer appropriato - INVERTITO
            if eye_type == 'left':
                ear_buffer = self.left_ear_buffer
                blink_counter_attr = 'left_blink_counter'
                eye_open_ear_attr = 'left_eye_open_ear'
                last_click_time_attr = 'last_left_click_time'
                click_button = 'right'  # INVERTITO: occhio sinistro -> click destro
            else:
                ear_buffer = self.right_ear_buffer
                blink_counter_attr = 'right_blink_counter'
                eye_open_ear_attr = 'right_eye_open_ear'
                last_click_time_attr = 'last_right_click_time'
                click_button = 'left'   # INVERTITO: occhio destro -> click sinistro
            
            # Aggiungi al buffer per stabilizzare
            ear_buffer.append(ear)
            if len(ear_buffer) > self.ear_buffer_size:
                ear_buffer.pop(0)
            
            # Calcola la media per ridurre il rumore
            avg_ear = np.mean(ear_buffer)
            
            # Imposta EAR di riferimento quando l'occhio è aperto
            eye_open_ear = getattr(self, eye_open_ear_attr)
            if eye_open_ear is None or avg_ear > eye_open_ear:
                setattr(self, eye_open_ear_attr, avg_ear)
                eye_open_ear = avg_ear
            
            # Calcola soglia dinamica basata sull'EAR di riferimento
            dynamic_threshold = eye_open_ear * 0.7  # 70% dell'EAR normale
            
            # Rileva blink con contatore consecutivo
            current_time = time.time()
            blink_counter = getattr(self, blink_counter_attr)
            last_click_time = getattr(self, last_click_time_attr)
            
            if avg_ear < dynamic_threshold:
                blink_counter += 1
            else:
                blink_counter = 0
            
            setattr(self, blink_counter_attr, blink_counter)
            
            # Esegui click solo se blink confermato e cooldown passato
            if (blink_counter >= self.blink_threshold and 
                current_time - last_click_time > self.click_cooldown):
                
                try:
                    pyautogui.click(button=click_button)
                    setattr(self, last_click_time_attr, current_time)
                    setattr(self, blink_counter_attr, 0)  # Reset counter
                    click_type = "DESTRO" if eye_type == 'left' else "SINISTRO"  # INVERTITO
                    print(f"\n✓ CLICK {click_type} ESEGUITO! EAR: {avg_ear:.4f}, Soglia: {dynamic_threshold:.4f}")
                    return True
                except Exception as e:
                    print(f"Errore nel click {eye_type}: {e}")
            
            return False
            
        except Exception as e:
            print(f"Errore rilevamento blink {eye_type}: {e}")
            return False

    def auto_set_center(self, nose_pos):
        """
        Calcola automaticamente la posizione centrale basandosi sui primi frame.
        """
        if not self.center_calculated:
            self.center_samples.append(nose_pos.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                # Calcola la posizione media come centro
                self.center_position = np.mean(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"Centro automatico calcolato: {self.center_position}")
                return True
        return False

    def update_cursor_position(self, nose_pos):
        """
        Aggiorna la posizione del cursore basandosi sul movimento del naso.
        """
        if self.center_position is None:
            return
        
        offset = nose_pos - self.center_position
        distance = np.linalg.norm(offset)

        # Applica zona morta
        if distance < self.deadzone_radius:
            return

        # Calcola movimento
        movement_factor = (distance - self.deadzone_radius) / distance
        movement_vector = offset * movement_factor * self.movement_sensitivity
        
        self.current_cursor_pos += movement_vector
        
        # Limita alle dimensioni dello schermo
        self.current_cursor_pos[0] = np.clip(self.current_cursor_pos[0], 0, self.screen_w - 1)
        self.current_cursor_pos[1] = np.clip(self.current_cursor_pos[1], 0, self.screen_h - 1)
        
        # Muovi il mouse
        try:
            pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        except Exception as e:
            print(f"Errore movimento mouse: {e}")

    def draw_interface(self, frame, nose_pos, landmarks=None, left_click_detected=False, right_click_detected=False):
        """
        Disegna l'interfaccia visuale sul frame.
        """
        h, w = frame.shape[:2]

        if not self.center_calculated:
            # Modalità inizializzazione
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)  # Arancione
            
            # Testo di inizializzazione
            progress = len(self.center_samples)
            cv2.putText(frame, f"Inizializzazione centro... {progress}/{self.max_center_samples}", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            cv2.putText(frame, "Mantieni la testa ferma al centro per qualche secondo", 
                       (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        else:
            # Modalità attiva
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 255, 0), -1)  # Verde
            
            # Disegna centro e zona morta
            if self.center_position is not None:
                center_screen = self.center_position.astype(int)
                cv2.circle(frame, tuple(center_screen), int(self.deadzone_radius), (255, 255, 0), 2)
                cv2.circle(frame, tuple(center_screen), 3, (255, 255, 0), -1)
                
                # Disegna freccia se fuori dalla zona morta
                if np.linalg.norm(nose_pos - self.center_position) > self.deadzone_radius:
                    cv2.arrowedLine(frame, tuple(center_screen), tuple(nose_pos.astype(int)), (0, 255, 255), 2)

            # Disegna indicatori occhi se disponibili
            if landmarks is not None:
                try:
                    # Disegna contorno occhio sinistro (BLU)
                    for idx in self.LEFT_EYE_LANDMARKS:
                        if idx < len(landmarks):
                            point = landmarks[idx].astype(int)
                            cv2.circle(frame, tuple(point), 1, (255, 0, 0), -1)
                    
                    # Disegna contorno occhio destro (ROSSO)
                    for idx in self.RIGHT_EYE_LANDMARKS:
                        if idx < len(landmarks):
                            point = landmarks[idx].astype(int)
                            cv2.circle(frame, tuple(point), 1, (0, 0, 255), -1)
                    
                    # Punti principali per EAR - Occhio SINISTRO
                    left_eye_left = landmarks[self.LEFT_EYE_LEFT].astype(int)
                    left_eye_right = landmarks[self.LEFT_EYE_RIGHT].astype(int)
                    left_eye_top = landmarks[self.LEFT_EYE_TOP].astype(int)
                    left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM].astype(int)
                    
                    cv2.circle(frame, tuple(left_eye_left), 3, (255, 255, 0), -1)
                    cv2.circle(frame, tuple(left_eye_right), 3, (255, 255, 0), -1)
                    cv2.circle(frame, tuple(left_eye_top), 3, (255, 0, 255), -1)
                    cv2.circle(frame, tuple(left_eye_bottom), 3, (255, 0, 255), -1)
                    
                    # Punti principali per EAR - Occhio DESTRO
                    right_eye_left = landmarks[self.RIGHT_EYE_LEFT].astype(int)
                    right_eye_right = landmarks[self.RIGHT_EYE_RIGHT].astype(int)
                    right_eye_top = landmarks[self.RIGHT_EYE_TOP].astype(int)
                    right_eye_bottom = landmarks[self.RIGHT_EYE_BOTTOM].astype(int)
                    
                    cv2.circle(frame, tuple(right_eye_left), 3, (255, 255, 0), -1)
                    cv2.circle(frame, tuple(right_eye_right), 3, (255, 255, 0), -1)
                    cv2.circle(frame, tuple(right_eye_top), 3, (255, 0, 255), -1)
                    cv2.circle(frame, tuple(right_eye_bottom), 3, (255, 0, 255), -1)
                    
                    # Disegna contorno bocca (VERDE se aperta, ROSSO se chiusa)
                    mouth_color = (0, 255, 0) if self.clicks_enabled else (0, 0, 255)
                    for idx in self.MOUTH_LANDMARKS:
                        if idx < len(landmarks):
                            point = landmarks[idx].astype(int)
                            cv2.circle(frame, tuple(point), 2, mouth_color, -1)
                    
                    # Punti principali per MAR - Bocca
                    mouth_top = landmarks[self.MOUTH_TOP].astype(int)
                    mouth_bottom = landmarks[self.MOUTH_BOTTOM].astype(int)
                    mouth_left = landmarks[self.MOUTH_LEFT].astype(int)
                    mouth_right = landmarks[self.MOUTH_RIGHT].astype(int)
                    
                    cv2.circle(frame, tuple(mouth_top), 3, (0, 255, 255), -1)
                    cv2.circle(frame, tuple(mouth_bottom), 3, (0, 255, 255), -1)
                    cv2.circle(frame, tuple(mouth_left), 3, (0, 255, 255), -1)
                    cv2.circle(frame, tuple(mouth_right), 3, (0, 255, 255), -1)
                    
                    # Indicatori click - INVERTITO
                    if left_click_detected and self.clicks_enabled:
                        cv2.circle(frame, tuple(left_eye_top), 20, (0, 255, 0), 3)
                        cv2.putText(frame, "RIGHT CLICK!", tuple(left_eye_top - [0, 30]), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    if right_click_detected and self.clicks_enabled:
                        cv2.circle(frame, tuple(right_eye_top), 20, (0, 255, 0), 3)
                        cv2.putText(frame, "LEFT CLICK!", tuple(right_eye_top - [0, 30]), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                except Exception as e:
                    print(f"Errore disegno occhi/bocca: {e}")

            # Informazioni di stato
            status_color = (0, 255, 0) if (left_click_detected or right_click_detected) else (0, 255, 0)
            cv2.putText(frame, "MOUSE BINOCULARE ATTIVO", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            # Stato click (abilitato/disabilitato)
            click_status = "ABILITATI" if self.clicks_enabled else "DISABILITATI"
            click_status_color = (0, 255, 0) if self.clicks_enabled else (0, 0, 255)
            cv2.putText(frame, f"Click: {click_status}", (w - 200, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, click_status_color, 2)
            
            # Debug info
            cv2.putText(frame, f"Naso: {int(nose_pos[0])},{int(nose_pos[1])}", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Cursore: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}", 
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if self.center_position is not None:
                distance = np.linalg.norm(nose_pos - self.center_position)
                cv2.putText(frame, f"Distanza: {distance:.1f}px", (20, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mostra EAR per entrambi gli occhi
            if len(self.left_ear_buffer) > 0:
                left_avg_ear = np.mean(self.left_ear_buffer)
                left_threshold = self.left_eye_open_ear * 0.7 if self.left_eye_open_ear else 0.25
                left_ear_color = (255, 0, 0) if left_avg_ear > left_threshold else (0, 0, 255)
                cv2.putText(frame, f"L-EAR: {left_avg_ear:.3f} | {left_threshold:.3f}", (20, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, left_ear_color, 1)
                cv2.putText(frame, f"L-Blink: {self.left_blink_counter}", (20, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
            if len(self.right_ear_buffer) > 0:
                right_avg_ear = np.mean(self.right_ear_buffer)
                right_threshold = self.right_eye_open_ear * 0.7 if self.right_eye_open_ear else 0.25
                right_ear_color = (255, 0, 0) if right_avg_ear > right_threshold else (0, 0, 255)
                cv2.putText(frame, f"R-EAR: {right_avg_ear:.3f} | {right_threshold:.3f}", (250, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, right_ear_color, 1)
                cv2.putText(frame, f"R-Blink: {self.right_blink_counter}", (250, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mostra MAR per la bocca
            if len(self.mouth_ear_buffer) > 0:
                avg_mar = np.mean(self.mouth_ear_buffer)
                threshold = self.mouth_open_ear * 1.5 if self.mouth_open_ear else 0.3
                mar_color = (0, 255, 0) if self.clicks_enabled else (0, 0, 255)
                cv2.putText(frame, f"MAR: {avg_mar:.3f} | {threshold:.3f}", (w - 200, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, mar_color, 1)

            # Istruzioni aggiornate - INVERTITO
            cv2.putText(frame, "Muovi testa=cursore | Occhio SX=click DX | Occhio DX=click SX", (20, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Apri/chiudi bocca per abilitare/disabilitare i click", (20, h-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    print("="*60)
    print("CONTROLLORE MOUSE BINOCULARE CON NASO")
    print("="*60)
    print("NOVITA': Controllo con entrambi gli occhi e bocca!")
    print("- OCCHIO SINISTRO chiuso = CLICK DESTRO")
    print("- OCCHIO DESTRO chiuso = CLICK SINISTRO") 
    print("- Movimento del naso = movimento cursore")
    print("- Apri la bocca per ABILITARE i click")
    print("- Chiudi la bocca per DISABILITARE i click")
    print("="*60)
    print("Avvio automatico senza calibrazione manuale.")
    print("Mantieni la testa ferma al centro all'inizio per alcuni secondi.")
    print("="*60)

    controller = BinocularNoseMouseController()
    
    # Prova diverse fonti video
    cap = None
    video_sources = [0, 1, 2, '/dev/video0', '/dev/video1', '/dev/video2']
    
    print("Ricerca webcam disponibili...")
    for source in video_sources:
        print(f"Tentativo con fonte video: {source}")
        test_cap = cv2.VideoCapture(source)
        if test_cap.isOpened():
            # Test se riesce effettivamente a leggere un frame
            ret, frame = test_cap.read()
            if ret:
                cap = test_cap
                print(f"✓ Webcam trovata su: {source}")
                break
            else:
                test_cap.release()
        else:
            if hasattr(test_cap, 'release'): # Ensure release method exists before calling
                test_cap.release()
    
    if cap is None or not cap.isOpened():
        print("="*60)
        print("ERRORE: Nessuna webcam trovata!")
        print("="*60)
        print("Possibili soluzioni:")
        print("1. Controlla che la webcam sia collegata")
        print("2. Verifica i permessi: sudo usermod -a -G video $USER")
        print("3. Riavvia il sistema dopo aver aggiunto i permessi")
        print("4. Prova: sudo chmod 666 /dev/video*")
        print("5. Lista dispositivi video: ls -la /dev/video*")
        print("6. Verifica con: v4l2-ctl --list-devices")
        print("="*60)
        sys.exit(1)

    # Impostazioni camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)  # Ridotto per Raspberry Pi
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("Premi ESC per uscire")
    
    try:
        left_click_detected = False
        right_click_detected = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Impossibile leggere il frame.")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = controller.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                nose_pos = landmarks_np[controller.NOSE_TIP]
                controller.last_nose_pos = nose_pos.copy()

                # Auto-imposta il centro o controlla il mouse
                if not controller.center_calculated:
                    controller.auto_set_center(nose_pos)
                else:
                    controller.update_cursor_position(nose_pos)
                    # Rileva stato bocca
                    controller.detect_mouth_open(landmarks_np)
                    # Rileva ammiccamento per entrambi gli occhi
                    left_click_detected = controller.detect_eye_blink(landmarks_np, 'left') if controller.clicks_enabled else False
                    right_click_detected = controller.detect_eye_blink(landmarks_np, 'right') if controller.clicks_enabled else False

                controller.draw_interface(frame, controller.last_nose_pos, landmarks_np, 
                                        left_click_detected, right_click_detected)
            else:
                controller.draw_interface(frame, controller.last_nose_pos)
                
            cv2.imshow('Mouse Binoculare - Naso + Occhi SX/DX + Bocca', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    except KeyboardInterrupt:
        print("\nInterrotto dall'utente")
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Pulizia completata.")


if __name__ == "__main__":
    main()