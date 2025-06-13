import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys


class SimpleNoseMouseController:
    def __init__(self):
        """
        Controller del mouse tramite movimento del naso semplificato senza calibrazione.
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
        
        # Migliori indici per l'occhio sinistro (più accurati per blink detection)
        # Using the standard 6 landmarks for EAR calculation
        self.LEFT_EYE_LANDMARKS_EAR = [362, 385, 380, 374, 381, 382] # P1,P2,P3,P4,P5,P6 for EAR
        
        # These are internal references, not for EAR calculation directly
        self.LEFT_EYE_TOP = 386 
        self.LEFT_EYE_BOTTOM = 374
        self.LEFT_EYE_LEFT = 263  
        self.LEFT_EYE_RIGHT = 362
        
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
        
        # Sistema di rilevamento ammiccamento per click - MIGLIORATO
        self.eye_closed_threshold_multiplier = 0.65  # NEW: Multiplier for dynamic threshold (e.g., 65% of open EAR)
        self.last_click_time = 0
        self.click_cooldown = 0.4  # Tempo minimo tra i click (secondi), reduced for faster response
        self.ear_buffer = []  # Buffer per stabilizzare il rilevamento
        self.ear_buffer_size = 10  # Increased for better stability and smoother EAR
        
        # Nuovo sistema per rilevamento più robusto
        self.blink_consecutive_frames = 0
        self.blink_detection_threshold = 3  # Number of consecutive frames below threshold to confirm blink
        self.eye_open_ear_reference = None  # EAR di riferimento quando l'occhio è aperto
        self.calibration_ear_samples = []
        self.max_calibration_ear_samples = 60 # Number of samples to get a good open-eye EAR

    def calculate_eye_aspect_ratio(self, landmarks):
        """
        Calcola l'Eye Aspect Ratio (EAR) usando 6 punti dell'occhio.
        Formula standard: EAR = (||p2-p6|| + ||p3-p5||) / (2*||p1-p4||)
        
        p1-p6 sono gli indici dei landmark dell'occhio nell'ordine specificato da MediaPipe.
        Per l'occhio sinistro (visto dal lato della telecamera):
        p1: 362 (estrema destra)
        p2: 385 (sopra, interna)
        p3: 380 (sopra, centrale)
        p4: 374 (estrema sinistra)
        p5: 381 (sotto, centrale)
        p6: 382 (sotto, interna)
        """
        try:
            # Get the 6 eye landmarks based on standard EAR definition
            p1 = landmarks[362] # outermost corner
            p2 = landmarks[385] # upper-inner corner
            p3 = landmarks[380] # upper-middle corner
            p4 = landmarks[374] # innermost corner
            p5 = landmarks[381] # lower-middle corner
            p6 = landmarks[382] # lower-inner corner
            
            # Calculate the euclidean distances between the two sets of vertical eye landmarks
            vertical_dist1 = np.linalg.norm(p2 - p6)
            vertical_dist2 = np.linalg.norm(p3 - p5)
            
            # Calculate the euclidean distance between the horizontal eye landmarks
            horizontal_dist = np.linalg.norm(p1 - p4)
            
            # Avoid division by zero
            if horizontal_dist == 0:
                return 0.0
                
            # Calculate EAR
            ear = (vertical_dist1 + vertical_dist2) / (2.0 * horizontal_dist)
            return ear
            
        except Exception as e:
            print(f"Errore calcolo EAR: {e}")
            return 0.0

    def detect_left_eye_blink(self, landmarks):
        """
        Rileva se l'occhio sinistro è chiuso e genera un click - VERSIONE MIGLIORATA.
        """
        try:
            ear = self.calculate_eye_aspect_ratio(landmarks)
            
            # Populate EAR buffer
            self.ear_buffer.append(ear)
            if len(self.ear_buffer) > self.ear_buffer_size:
                self.ear_buffer.pop(0)
            
            # Calculate average EAR from buffer
            avg_ear = np.mean(self.ear_buffer)

            # Calibrate open-eye EAR reference
            if not self.center_calculated and len(self.calibration_ear_samples) < self.max_calibration_ear_samples:
                self.calibration_ear_samples.append(avg_ear)
                if len(self.calibration_ear_samples) == self.max_calibration_ear_samples:
                    self.eye_open_ear_reference = np.mean(self.calibration_ear_samples)
                    print(f"EAR di riferimento occhio aperto calcolato: {self.eye_open_ear_reference:.3f}")
                return False

            # If reference EAR is not yet set (after center calculation and initial frames), wait.
            if self.eye_open_ear_reference is None:
                return False
            
            # Dynamic threshold for blink detection
            dynamic_threshold = self.eye_open_ear_reference * self.eye_closed_threshold_multiplier
            
            # Debug print
            if len(self.ear_buffer) >= self.ear_buffer_size:
                print(f"EAR (Avg): {avg_ear:.3f}, Soglia Dinamica: {dynamic_threshold:.3f}, EAR Aperto: {self.eye_open_ear_reference:.3f}")
            
            current_time = time.time()
            
            if avg_ear < dynamic_threshold:
                self.blink_consecutive_frames += 1
            else:
                self.blink_consecutive_frames = 0
            
            # Execute click only if blink confirmed and cooldown passed
            if (self.blink_consecutive_frames >= self.blink_detection_threshold and 
                current_time - self.last_click_time > self.click_cooldown):
                
                try:
                    pyautogui.click()
                    self.last_click_time = current_time
                    self.blink_consecutive_frames = 0  # Reset counter
                    print(f"\n✓ CLICK ESEGUITO! EAR (Avg): {avg_ear:.4f}, Soglia: {dynamic_threshold:.4f}")
                    return True
                except Exception as e:
                    print(f"Errore nel click: {e}")
            
            return False
            
        except Exception as e:
            print(f"Errore rilevamento blink: {e}")
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

    def draw_interface(self, frame, nose_pos, landmarks=None, last_click_detected=False):
        """
        Disegna l'interfaccia visuale sul frame.
        """
        h, w = frame.shape[:2]

        if not self.center_calculated:
            # Modalità inizializzazione centro
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)  # Arancione
            
            # Testo di inizializzazione centro
            progress_center = len(self.center_samples)
            cv2.putText(frame, f"Inizializzazione centro... {progress_center}/{self.max_center_samples}", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            cv2.putText(frame, "Mantieni la testa ferma al centro per qualche secondo", 
                       (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Testo di calibrazione EAR
            if len(self.center_samples) >= self.max_center_samples: # After center is calculated
                progress_ear = len(self.calibration_ear_samples)
                cv2.putText(frame, f"Calibrazione occhio... {progress_ear}/{self.max_calibration_ear_samples}", 
                           (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.putText(frame, "Mantieni gli occhi aperti normalmente per calibrare il click", 
                           (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

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
                    # Draw the 6 EAR landmarks for the left eye
                    for idx in self.LEFT_EYE_LANDMARKS_EAR:
                        if idx < len(landmarks):
                            point = landmarks[idx].astype(int)
                            cv2.circle(frame, tuple(point), 2, (255, 0, 0), -1) # Blue dots for EAR points
                    
                    # Highlight the main points for visual debugging
                    left_eye_left = landmarks[self.LEFT_EYE_LEFT].astype(int)
                    left_eye_right = landmarks[self.LEFT_EYE_RIGHT].astype(int)
                    left_eye_top = landmarks[self.LEFT_EYE_TOP].astype(int)
                    left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM].astype(int)
                    
                    cv2.circle(frame, tuple(left_eye_left), 3, (0, 255, 0), -1)
                    cv2.circle(frame, tuple(left_eye_right), 3, (0, 255, 0), -1)
                    cv2.circle(frame, tuple(left_eye_top), 3, (255, 0, 255), -1)
                    cv2.circle(frame, tuple(left_eye_bottom), 3, (255, 0, 255), -1)
                    
                    # Indicatore click visuale
                    if last_click_detected:
                        cv2.circle(frame, tuple(left_eye_top), 25, (0, 255, 255), 3) # Yellow circle on click
                        
                except Exception as e:
                    print(f"Errore disegno occhio: {e}")

            # Informazioni di stato
            status_color = (0, 255, 0)
            cv2.putText(frame, "MOUSE ATTIVO + CLICK OCCHIO (MIGLIORATO)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            # Debug info migliorato
            cv2.putText(frame, f"Naso: {int(nose_pos[0])},{int(nose_pos[1])}", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Cursore: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}", 
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if self.center_position is not None:
                distance = np.linalg.norm(nose_pos - self.center_position)
                cv2.putText(frame, f"Distanza: {distance:.1f}px", (20, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mostra EAR migliorato
            if len(self.ear_buffer) > 0:
                avg_ear = np.mean(self.ear_buffer)
                dynamic_threshold = self.eye_open_ear_reference * self.eye_closed_threshold_multiplier if self.eye_open_ear_reference else 0.0
                ear_color = (0, 255, 0) if avg_ear > dynamic_threshold else (0, 0, 255)
                cv2.putText(frame, f"EAR (Avg): {avg_ear:.3f} | Soglia: {dynamic_threshold:.3f}", (20, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, ear_color, 1)
                cv2.putText(frame, f"Blink Counter: {self.blink_consecutive_frames}", (20, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Istruzioni
            cv2.putText(frame, "Muovi la testa per il cursore - Chiudi occhio SX per click", (20, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "ESC per uscire", (20, h-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    print("="*60)
    print("CONTROLLORE MOUSE CON NASO + CLICK CON OCCHIO (VERSIONE MIGLIORATA)")
    print("="*60)
    print("Avvio automatico senza calibrazione manuale.")
    print("Mantieni la testa ferma al centro all'inizio per alcuni secondi.")
    print("Successivamente, tieni gli occhi aperti normalmente per calibrare il click.")
    print("CLICK: Chiudi l'occhio SINISTRO per fare click sinistro")
    print("MIGLIORAMENTI:")
    print("- EAR calculation più accurato con 6 punti standard")
    print("- Soglia dinamica basata sull'EAR normale, calcolata dopo il centramento")
    print("- Contatore consecutivo per evitare falsi positivi")
    print("- Buffer EAR più grande per stabilità")
    print("="*60)

    controller = SimpleNoseMouseController()
    
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
            if hasattr(test_cap, 'release'):
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
    cap.set(cv2.CAP_PROP_FPS, 30)  # Reduced for Raspberry Pi
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("Premi ESC per uscire")
    
    try:
        last_click_detected = False
        
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

                # Auto-imposta il centro
                if not controller.center_calculated:
                    controller.auto_set_center(nose_pos)
                
                # Only after center is calculated, start processing mouse movement and clicks
                if controller.center_calculated:
                    controller.update_cursor_position(nose_pos)
                    # Rileva ammiccamento per click
                    last_click_detected = controller.detect_left_eye_blink(landmarks_np)

                controller.draw_interface(frame, controller.last_nose_pos, landmarks_np, last_click_detected)
            else:
                controller.draw_interface(frame, controller.last_nose_pos) # Still draw interface without landmarks

            cv2.imshow('Head Mouse + Eye Click (MIGLIORATO)', frame)
            
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