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
        # These are the 6 points that define the eye shape for EAR calculation
        self.LEFT_EYE_LANDMARKS = [
            362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398
        ]
        # Specific points for EAR calculation (P1 to P6)
        # P1: 362 (outer corner), P2: 382 (top), P3: 381, P4: 263 (inner corner)
        # P5: 374 (bottom), P6: 380
        
        self.LEFT_EYE_POINTS_EAR = [
            362,  # P1 - Outer corner of left eye
            382,  # P2 - Upper part
            381,  # P3 - Upper part
            263,  # P4 - Inner corner of left eye
            374,  # P5 - Lower part
            380   # P6 - Lower part
        ]

        # Specific points for EAR calculation (corresponding to P1-P6 for clarity)
        self.P1_LEFT_EYE = 362  # Horizontal Left
        self.P4_LEFT_EYE = 263  # Horizontal Right
        self.P2_LEFT_EYE = 382  # Vertical Top 1
        self.P6_LEFT_EYE = 380  # Vertical Bottom 1
        self.P3_LEFT_EYE = 381  # Vertical Top 2
        self.P5_LEFT_EYE = 374  # Vertical Bottom 2
        
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
        self.last_click_time = 0
        self.click_cooldown = 0.6  # Aumentato per maggiore stabilità
        self.eye_aspect_ratios = []  # Buffer per stabilizzare il rilevamento
        self.ear_buffer_size = 10  # Aumentato ulteriormente per maggiore stabilità
        
        # Nuovo sistema per rilevamento più robusto
        self.blink_counter = 0
        self.blink_threshold = 3  # Numero di frame consecutivi sotto soglia per confermare blink (aumentato)
        self.eye_open_ear = None  # EAR di riferimento quando l'occhio è aperto
        self.ear_open_samples = [] # Samples to establish initial open eye EAR
        self.max_ear_open_samples = 50 # Number of samples to get a stable open EAR
        self.ear_calibration_done = False


    def calculate_eye_aspect_ratio(self, landmarks):
        """
        Calcola l'Eye Aspect Ratio corretto usando 6 punti dell'occhio.
        Formula standard: EAR = (|p2-p6| + |p3-p5|) / (2*|p1-p4|)
        """
        try:
            # Get the 6 eye landmarks based on the defined indices
            p1 = landmarks[self.P1_LEFT_EYE]
            p2 = landmarks[self.P2_LEFT_EYE]
            p3 = landmarks[self.P3_LEFT_EYE]
            p4 = landmarks[self.P4_LEFT_EYE]
            p5 = landmarks[self.P5_LEFT_EYE]
            p6 = landmarks[self.P6_LEFT_EYE]
            
            # Compute the euclidean distances between the two sets of
            # vertical eye landmarks (p2-p6, p3-p5)
            vertical_dist1 = np.linalg.norm(p2 - p6)
            vertical_dist2 = np.linalg.norm(p3 - p5)
            
            # Compute the euclidean distance between the horizontal
            # eye landmark (p1-p4)
            horizontal_dist = np.linalg.norm(p1 - p4)
            
            # Avoid division by zero
            if horizontal_dist == 0:
                return 0.0
                
            # Compute the eye aspect ratio
            ear = (vertical_dist1 + vertical_dist2) / (2.0 * horizontal_dist)
            return ear
            
        except Exception as e:
            # print(f"Errore calcolo EAR: {e}") # Suppress frequent error prints
            return 0.0

    def detect_left_eye_blink(self, landmarks):
        """
        Rileva se l'occhio sinistro è chiuso e genera un click - VERSIONE MIGLIORATA.
        """
        try:
            ear = self.calculate_eye_aspect_ratio(landmarks)
            
            # Initial calibration for eye_open_ear
            if not self.ear_calibration_done:
                self.ear_open_samples.append(ear)
                if len(self.ear_open_samples) >= self.max_ear_open_samples:
                    self.eye_open_ear = np.mean(self.ear_open_samples)
                    # We might want to remove outliers before averaging
                    # For simplicity, we just take the mean here.
                    self.ear_calibration_done = True
                    print(f"EAR di riferimento (occhi aperti) calcolato: {self.eye_open_ear:.3f}")
                return False # Don't detect clicks during initial calibration

            # Add to buffer for stabilization
            self.eye_aspect_ratios.append(ear)
            if len(self.eye_aspect_ratios) > self.ear_buffer_size:
                self.eye_aspect_ratios.pop(0)
            
            # Calculate the mean for noise reduction
            avg_ear = np.mean(self.eye_aspect_ratios)
            
            # Adjust reference EAR dynamically, but not too aggressively
            # Only update if current avg_ear is significantly higher than existing eye_open_ear
            if avg_ear > self.eye_open_ear * 1.05: # Allow for slight increase
                self.eye_open_ear = (self.eye_open_ear * 0.9) + (avg_ear * 0.1) # Smooth update
            
            # Calculate dynamic threshold based on reference EAR
            # This threshold is critical for avoiding false clicks
            dynamic_threshold = self.eye_open_ear * 0.65  # Decreased to be more strict (65% of normal EAR)
            
            # Debug print
            # if len(self.eye_aspect_ratios) >= self.ear_buffer_size:
            #     print(f"EAR: {avg_ear:.3f}, Soglia: {dynamic_threshold:.3f}, Aperto: {self.eye_open_ear:.3f}, Blink Count: {self.blink_counter}")
            
            current_time = time.time()
            
            if avg_ear < dynamic_threshold:
                self.blink_counter += 1
            else:
                self.blink_counter = 0
            
            # Execute click only if blink confirmed and cooldown passed
            if (self.blink_counter >= self.blink_threshold and 
                current_time - self.last_click_time > self.click_cooldown):
                
                try:
                    pyautogui.click()
                    self.last_click_time = current_time
                    self.blink_counter = 0  # Reset counter
                    print(f"\n✓ CLICK ESEGUITO! EAR: {avg_ear:.4f}, Soglia: {dynamic_threshold:.4f}")
                    return True
                except Exception as e:
                    print(f"Errore nel click: {e}")
            
            return False
            
        except Exception as e:
            # print(f"Errore rilevamento blink: {e}") # Suppress frequent error prints
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
            # print(f"Errore movimento mouse: {e}") # Suppress frequent error prints
            pass # Keep it silent to avoid flooding terminal

    def draw_interface(self, frame, nose_pos, landmarks=None, last_click_detected=False):
        """
        Disegna l'interfaccia visuale sul frame.
        """
        h, w = frame.shape[:2]

        if not self.center_calculated:
            # Modalità inizializzazione del centro
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)  # Arancione
            
            # Testo di inizializzazione
            progress = len(self.center_samples)
            cv2.putText(frame, f"Inizializzazione centro... {progress}/{self.max_center_samples}", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            cv2.putText(frame, "Mantieni la testa ferma al centro per qualche secondo", 
                       (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Also indicate EAR calibration if not done
            if not self.ear_calibration_done:
                ear_progress = len(self.ear_open_samples)
                cv2.putText(frame, f"Calibrazione Occhio (EAR)... {ear_progress}/{self.max_ear_open_samples}", 
                           (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

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
                    # Draw eye contour (all 16 points)
                    for idx in self.LEFT_EYE_LANDMARKS:
                        if idx < len(landmarks):
                            point = landmarks[idx].astype(int)
                            cv2.circle(frame, tuple(point), 1, (255, 0, 0), -1) # Blue for general points
                    
                    # Main points for EAR (P1-P6) - These are the 'due pallini'
                    p1 = landmarks[self.P1_LEFT_EYE].astype(int)
                    p2 = landmarks[self.P2_LEFT_EYE].astype(int)
                    p3 = landmarks[self.P3_LEFT_EYE].astype(int)
                    p4 = landmarks[self.P4_LEFT_EYE].astype(int)
                    p5 = landmarks[self.P5_LEFT_EYE].astype(int)
                    p6 = landmarks[self.P6_LEFT_EYE].astype(int)

                    cv2.circle(frame, tuple(p1), 3, (0, 255, 0), -1) # Green
                    cv2.circle(frame, tuple(p4), 3, (0, 255, 0), -1) # Green
                    cv2.circle(frame, tuple(p2), 3, (255, 0, 255), -1) # Magenta
                    cv2.circle(frame, tuple(p6), 3, (255, 0, 255), -1) # Magenta
                    cv2.circle(frame, tuple(p3), 3, (255, 255, 0), -1) # Cyan
                    cv2.circle(frame, tuple(p5), 3, (255, 255, 0), -1) # Cyan
                    
                    # Indicatore click: circle around the eye points
                    if last_click_detected:
                        # Draw a larger circle around the eye area
                        # Calculate center of the eye for the visual cue
                        eye_center_x = int((p1[0] + p4[0]) / 2)
                        eye_center_y = int((p2[1] + p5[1]) / 2) # Average of vertical points
                        cv2.circle(frame, (eye_center_x, eye_center_y), 25, (0, 255, 0), 3) # Green circle on click
                        
                except Exception as e:
                    # print(f"Errore disegno occhio: {e}") # Suppress frequent error prints
                    pass

            # Informazioni di stato
            status_color = (0, 255, 0) # Always green if active
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
            if len(self.eye_aspect_ratios) > 0 and self.ear_calibration_done:
                avg_ear = np.mean(self.eye_aspect_ratios)
                dynamic_threshold = self.eye_open_ear * 0.65 # Same threshold as in detection
                ear_color = (0, 255, 0) if avg_ear > dynamic_threshold else (0, 0, 255) # Green when open, Red when closed
                cv2.putText(frame, f"EAR: {avg_ear:.3f} | Soglia: {dynamic_threshold:.3f}", (20, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, ear_color, 1)
                cv2.putText(frame, f"Blink Counter: {self.blink_counter}", (20, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, f"EAR Aperto Rif: {self.eye_open_ear:.3f}", (20, 170),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1) # Cyan for reference EAR

            # Istruzioni
            cv2.putText(frame, "Muovi la testa per il cursore - Chiudi occhio SX per click", (20, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "ESC per uscire", (20, h-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    print("="*60)
    print("CONTROLLORE MOUSE CON NASO + CLICK CON OCCHIO (VERSIONE MIGLIORATA E STABILIZZATA)")
    print("="*60)
    print("Avvio automatico senza calibrazione manuale.")
    print("Mantieni la testa ferma e l'occhio SINISTRO ben aperto all'inizio per alcuni secondi.")
    print("CLICK: Chiudi l'occhio SINISTRO per fare click sinistro")
    print("MIGLIORAMENTI:")
    print("- EAR calculation più accurato con 6 punti (standard)")
    print("- Soglia dinamica per il click basata sull'EAR normale, più restrittiva (65%)")
    print("- Contatore consecutivo per evitare falsi positivi (richiede più frame di chiusura)")
    print("- Buffer più grande per stabilità del rilevamento")
    print("- Calibrazione iniziale dell'EAR quando l'occhio è aperto")
    print("- Cooldown del click leggermente aumentato")
    print("="*60)

    controller = SimpleNoseMouseController()
    
    # Prova diverse fonti video
    cap = None
    video_sources = [0, 1, 2, '/dev/video0', '/dev/video1', '/dev/video2'] # Common sources for Linux
    
    print("Ricerca webcam disponibili...")
    for source in video_sources:
        print(f"Tentativo con fonte video: {source}")
        try:
            test_cap = cv2.VideoCapture(source)
            if test_cap.isOpened():
                # Test if it can actually read a frame
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
        except Exception as e:
            print(f"Errore durante l'apertura di {source}: {e}")
            if 'test_cap' in locals() and hasattr(test_cap, 'release'):
                test_cap.release() # Ensure release if error occurs before read

    if cap is None or not cap.isOpened():
        print("="*60)
        print("ERRORE: Nessuna webcam trovata o accessibile!")
        print("="*60)
        print("Possibili soluzioni:")
        print("1. Controlla che la webcam sia collegata e non sia in uso da un'altra applicazione.")
        print("2. Verifica i permessi della webcam. Su Linux, potresti dover aggiungere il tuo utente al gruppo 'video':")
        print("   sudo usermod -a -G video $USER")
        print("   Poi riavvia il sistema.")
        print("3. Prova a dare permessi temporanei ai dispositivi video:")
        print("   sudo chmod 666 /dev/video*")
        print("4. Lista i dispositivi video per identificare la sorgente corretta:")
        print("   ls -la /dev/video*")
        print("   oppure")
        print("   v4l2-ctl --list-devices")
        print("="*60)
        sys.exit(1)

    # Impostazioni camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 20)  # Ridotto a 20 FPS per minori requisiti di CPU
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduce buffer size to minimize lag

    print("Premi ESC per uscire")
    
    try:
        last_click_detected = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Impossibile leggere il frame. La webcam potrebbe essere disconnessa o occupata.")
                time.sleep(0.1) # Wait a bit before trying again
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame with Face Mesh
            results = controller.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                nose_pos = landmarks_np[controller.NOSE_TIP]
                controller.last_nose_pos = nose_pos.copy()

                # Auto-set the center or control the mouse
                if not controller.center_calculated:
                    controller.auto_set_center(nose_pos)
                else:
                    controller.update_cursor_position(nose_pos)
                    # Detect blink for click
                    last_click_detected = controller.detect_left_eye_blink(landmarks_np)

                controller.draw_interface(frame, controller.last_nose_pos, landmarks_np, last_click_detected)
            else:
                # If no face detected, still draw the interface and last known nose position
                controller.draw_interface(frame, controller.last_nose_pos)
                cv2.putText(frame, "Nessun volto rilevato", (20, h - 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                # Reset blink counter if face is lost, to prevent accidental clicks upon re-detection
                controller.blink_counter = 0 
                # Reset EAR calibration if face is lost for too long?
                # For now, let's keep it calibrated once set.

            cv2.imshow('Head Mouse + Eye Click (MIGLIORATO)', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                break
            # Optional: Add keys for sensitivity/deadzone adjustment if needed for real-time tuning

    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")
    except Exception as e:
        print(f"Errore critico durante l'esecuzione: {e}")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("Pulizia completata. Uscita.")

if __name__ == "__main__":
    main()