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
        
        # Define MediaPipe landmark indices
        self.NOSE_TIP = 1
        # Indici per l'occhio sinistro (dal punto di vista dell'utente, quindi occhio destro nella webcam)
        self.LEFT_EYE_TOP = 159
        self.LEFT_EYE_BOTTOM = 145
        
        # Indici per le sopracciglia
        self.LEFT_EYEBROW_TOP = 70   # Punto più alto del sopracciglio sinistro
        self.LEFT_EYEBROW_INNER = 55 # Punto interno del sopracciglio sinistro
        self.RIGHT_EYEBROW_TOP = 300 # Punto più alto del sopracciglio destro
        self.RIGHT_EYEBROW_INNER = 285 # Punto interno del sopracciglio destro
        
        # Sistema di controllo semplificato
        self.center_position = None  # Sarà impostato automaticamente
        self.last_nose_pos = np.array([320.0, 240.0])
        self.movement_sensitivity = 3.0  # Sensibilità predefinita
        self.deadzone_radius = 15.0      # Zona morta predefinita
        
        # Parametri per il centro automatico
        self.center_samples = []
        self.max_center_samples = 30  # Numero di campioni per calcolare il centro
        self.center_calculated = False
        
        # Sistema di ricalibrazione automatica della zona morta
        self.recalibration_enabled = True
        self.stillness_threshold = 5.0  # Soglia di movimento per considerare il naso "fermo"
        self.stillness_duration_required = 10.0  # Secondi di immobilità richiesti
        self.stillness_start_time = None
        self.stillness_positions = []  # Buffer delle posizioni durante l'immobilità
        self.last_recalibration_time = 0
        self.recalibration_cooldown = 30.0  # Tempo minimo tra ricalirazioni (secondi)
        
        # Current cursor position
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        
        # Sistema di rilevamento click - MODALITÀ TOGGLE
        self.click_mode = "eye"  # "eye" o "eyebrow"
        
        # Parametri per click con occhio
        self.eye_closed_threshold = 0.02  # Soglia per rilevare occhio chiuso
        self.eye_aspect_ratios = []  # Buffer per stabilizzare il rilevamento
        self.ear_buffer_size = 3  # Numero di campioni per media mobile
        
        # Parametri per click con sopracciglia
        self.eyebrow_raise_threshold = 0.03  # Soglia per rilevare sopracciglia alzate
        self.eyebrow_ratios = []  # Buffer per stabilizzare il rilevamento sopracciglia
        self.baseline_eyebrow_distance = None  # Distanza di base delle sopracciglia
        self.eyebrow_calibration_samples = []
        self.eyebrow_calibrated = False
        
        # Parametri comuni per i click
        self.last_click_time = 0
        self.click_cooldown = 0.5  # Tempo minimo tra i click (secondi)

    def toggle_click_mode(self):
        """
        Cambia modalità di click tra occhio e sopracciglia.
        """
        if self.click_mode == "eye":
            self.click_mode = "eyebrow"
            # Reset calibrazione sopracciglia quando si cambia modalità
            self.eyebrow_calibrated = False
            self.eyebrow_calibration_samples = []
            self.baseline_eyebrow_distance = None
            print("Modalità click: SOPRACCIGLIA")
        else:
            self.click_mode = "eye"
            print("Modalità click: OCCHIO SINISTRO")

    def toggle_recalibration(self):
        """
        Attiva/disattiva la ricalibrazione automatica.
        """
        self.recalibration_enabled = not self.recalibration_enabled
        status = "ATTIVATA" if self.recalibration_enabled else "DISATTIVATA"
        print(f"Ricalibrazione automatica {status}")

    def calculate_eye_aspect_ratio(self, eye_top, eye_bottom):
        """
        Calcola l'Eye Aspect Ratio per determinare se l'occhio è chiuso.
        """
        # Calcola la distanza verticale tra le palpebre
        vertical_distance = abs(eye_top[1] - eye_bottom[1])
        # Normalizza rispetto alla larghezza di riferimento fissa
        reference_width = 20.0
        ear = vertical_distance / reference_width
        return ear

    def calculate_eyebrow_ratio(self, landmarks):
        """
        Calcola la distanza delle sopracciglia dagli occhi per rilevare l'alzata.
        """
        # Punti del sopracciglio sinistro
        left_eyebrow_top = landmarks[self.LEFT_EYEBROW_TOP]
        left_eye_top = landmarks[self.LEFT_EYE_TOP]
        
        # Punti del sopracciglio destro
        right_eyebrow_top = landmarks[self.RIGHT_EYEBROW_TOP]
        right_eye_top = landmarks[self.LEFT_EYE_TOP]  # Nota: usando stesso punto per semplicità
        
        # Calcola distanze verticali
        left_distance = abs(left_eyebrow_top[1] - left_eye_top[1])
        right_distance = abs(right_eyebrow_top[1] - right_eye_top[1])
        
        # Media delle distanze
        avg_distance = (left_distance + right_distance) / 2.0
        
        return avg_distance

    def calibrate_eyebrow_baseline(self, landmarks):
        """
        Calibra la posizione di base delle sopracciglia.
        """
        if not self.eyebrow_calibrated and self.center_calculated:
            eyebrow_distance = self.calculate_eyebrow_ratio(landmarks)
            self.eyebrow_calibration_samples.append(eyebrow_distance)
            
            if len(self.eyebrow_calibration_samples) >= 20:  # 20 campioni per calibrare
                self.baseline_eyebrow_distance = np.mean(self.eyebrow_calibration_samples)
                self.eyebrow_calibrated = True
                print(f"Baseline sopracciglia calibrata: {self.baseline_eyebrow_distance:.4f}")

    def detect_left_eye_blink(self, landmarks):
        """
        Rileva se l'occhio sinistro è chiuso e genera un click.
        """
        left_eye_top = landmarks[self.LEFT_EYE_TOP]
        left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM]
        
        # Calcola l'Eye Aspect Ratio
        ear = self.calculate_eye_aspect_ratio(left_eye_top, left_eye_bottom)
        
        # Aggiungi al buffer per stabilizzare
        self.eye_aspect_ratios.append(ear)
        if len(self.eye_aspect_ratios) > self.ear_buffer_size:
            self.eye_aspect_ratios.pop(0)
        
        # Calcola la media per ridurre il rumore
        avg_ear = np.mean(self.eye_aspect_ratios)
        
        # Verifica se l'occhio è chiuso e se è passato abbastanza tempo dall'ultimo click
        current_time = time.time()
        if (avg_ear < self.eye_closed_threshold and 
            current_time - self.last_click_time > self.click_cooldown):
            
            try:
                pyautogui.click()
                self.last_click_time = current_time
                print(f"\nClick occhio eseguito! EAR: {avg_ear:.4f}")
                return True
            except Exception as e:
                print(f"Errore nel click: {e}")
        
        return False

    def detect_eyebrow_raise(self, landmarks):
        """
        Rileva se le sopracciglia sono alzate e genera un click.
        """
        if not self.eyebrow_calibrated or self.baseline_eyebrow_distance is None:
            self.calibrate_eyebrow_baseline(landmarks)
            return False
        
        current_eyebrow_distance = self.calculate_eyebrow_ratio(landmarks)
        
        # Aggiungi al buffer per stabilizzare
        self.eyebrow_ratios.append(current_eyebrow_distance)
        if len(self.eyebrow_ratios) > self.ear_buffer_size:
            self.eyebrow_ratios.pop(0)
        
        # Calcola la media per ridurre il rumore
        avg_eyebrow_distance = np.mean(self.eyebrow_ratios)
        
        # Calcola la differenza rispetto al baseline
        eyebrow_raise_amount = avg_eyebrow_distance - self.baseline_eyebrow_distance
        
        # Verifica se le sopracciglia sono alzate abbastanza
        current_time = time.time()
        if (eyebrow_raise_amount > self.eyebrow_raise_threshold and 
            current_time - self.last_click_time > self.click_cooldown):
            
            try:
                pyautogui.click()
                self.last_click_time = current_time
                print(f"\nClick sopracciglia eseguito! Alzata: {eyebrow_raise_amount:.4f}")
                return True
            except Exception as e:
                print(f"Errore nel click: {e}")
        
        return False

    def check_for_recalibration(self, nose_pos):
        """
        Controlla se il naso è rimasto fermo abbastanza a lungo per ricalibra il centro.
        """
        if not self.center_calculated or not self.recalibration_enabled:
            return False
        
        current_time = time.time()
        
        # Controlla se è passato abbastanza tempo dall'ultima ricalibrazione
        if current_time - self.last_recalibration_time < self.recalibration_cooldown:
            return False
        
        # Calcola la distanza dal centro attuale
        if self.center_position is not None:
            distance_from_center = np.linalg.norm(nose_pos - self.center_position)
            
            # Se il naso è dentro la soglia di immobilità
            if distance_from_center <= self.stillness_threshold:
                # Se è la prima volta che rileva immobilità, inizia il timer
                if self.stillness_start_time is None:
                    self.stillness_start_time = current_time
                    self.stillness_positions = [nose_pos.copy()]
                else:
                    # Aggiungi la posizione corrente al buffer
                    self.stillness_positions.append(nose_pos.copy())
                    
                    # Controlla se è passato abbastanza tempo
                    stillness_duration = current_time - self.stillness_start_time
                    if stillness_duration >= self.stillness_duration_required:
                        # Ricalibra usando le posizioni raccolte
                        new_center = np.mean(self.stillness_positions, axis=0)
                        old_center = self.center_position.copy()
                        self.center_position = new_center
                        self.last_recalibration_time = current_time
                        
                        # Reset del sistema di immobilità
                        self.stillness_start_time = None
                        self.stillness_positions = []
                        
                        print(f"RICALIBRAZIONE COMPLETATA!")
                        print(f"Vecchio centro: [{old_center[0]:.1f}, {old_center[1]:.1f}]")
                        print(f"Nuovo centro: [{new_center[0]:.1f}, {new_center[1]:.1f}]")
                        return True
            else:
                # Il naso si è mosso troppo, reset del timer
                self.stillness_start_time = None
                self.stillness_positions = []
        
        return False

    def get_stillness_progress(self):
        """
        Restituisce il progresso della ricalibrazione (0.0 - 1.0) se in corso.
        """
        if self.stillness_start_time is None:
            return 0.0
        
        current_time = time.time()
        elapsed = current_time - self.stillness_start_time
        progress = min(elapsed / self.stillness_duration_required, 1.0)
        return progress

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

            # Disegna indicatori per la modalità corrente
            if landmarks is not None:
                if self.click_mode == "eye":
                    # Modalità occhio
                    left_eye_top = landmarks[self.LEFT_EYE_TOP].astype(int)
                    left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM].astype(int)
                    
                    # Disegna punti dell'occhio
                    cv2.circle(frame, tuple(left_eye_top), 3, (255, 0, 0), -1)
                    cv2.circle(frame, tuple(left_eye_bottom), 3, (255, 0, 0), -1)
                    cv2.line(frame, tuple(left_eye_top), tuple(left_eye_bottom), (255, 0, 0), 1)
                    
                    # Indicatore click
                    if last_click_detected:
                        cv2.circle(frame, tuple(left_eye_top), 15, (0, 255, 0), 3)
                
                elif self.click_mode == "eyebrow":
                    # Modalità sopracciglia
                    left_eyebrow = landmarks[self.LEFT_EYEBROW_TOP].astype(int)
                    right_eyebrow = landmarks[self.RIGHT_EYEBROW_TOP].astype(int)
                    left_eye = landmarks[self.LEFT_EYE_TOP].astype(int)
                    
                    # Disegna punti delle sopracciglia
                    cv2.circle(frame, tuple(left_eyebrow), 4, (255, 0, 255), -1)
                    cv2.circle(frame, tuple(right_eyebrow), 4, (255, 0, 255), -1)
                    
                    # Linee di riferimento
                    cv2.line(frame, tuple(left_eyebrow), tuple(left_eye), (255, 0, 255), 1)
                    
                    # Indicatore click
                    if last_click_detected:
                        cv2.circle(frame, tuple(left_eyebrow), 20, (0, 255, 0), 3)
                        cv2.circle(frame, tuple(right_eyebrow), 20, (0, 255, 0), 3)

            # Indicatore di ricalibrazione in corso
            if self.recalibration_enabled:
                stillness_progress = self.get_stillness_progress()
                if stillness_progress > 0:
                    # Barra di progresso per ricalibrazione
                    bar_width = 200
                    bar_height = 10
                    bar_x = w - bar_width - 20
                    bar_y = 20
                    
                    # Sfondo barra
                    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
                    # Progresso
                    progress_width = int(bar_width * stillness_progress)
                    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), (0, 255, 255), -1)
                    
                    # Testo
                    remaining_time = self.stillness_duration_required * (1 - stillness_progress)
                    cv2.putText(frame, f"Ricalibrazione in: {remaining_time:.1f}s", (bar_x, bar_y - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            # Informazioni di stato
            mode_text = "OCCHIO SX" if self.click_mode == "eye" else "SOPRACCIGLIA"
            status_color = (0, 255, 0) if last_click_detected else (0, 255, 0)
            cv2.putText(frame, f"MOUSE ATTIVO + CLICK: {mode_text}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Debug info
            cv2.putText(frame, f"Naso: {int(nose_pos[0])},{int(nose_pos[1])}", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Cursore: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}", 
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if self.center_position is not None:
                distance = np.linalg.norm(nose_pos - self.center_position)
                cv2.putText(frame, f"Distanza: {distance:.1f}px", (20, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mostra valori per modalità corrente
            if self.click_mode == "eye" and len(self.eye_aspect_ratios) > 0:
                avg_ear = np.mean(self.eye_aspect_ratios)
                ear_color = (0, 255, 0) if avg_ear > self.eye_closed_threshold else (0, 0, 255)
                cv2.putText(frame, f"Occhio EAR: {avg_ear:.4f}", (20, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, ear_color, 1)
            
            elif self.click_mode == "eyebrow":
                if self.eyebrow_calibrated and len(self.eyebrow_ratios) > 0:
                    avg_eyebrow = np.mean(self.eyebrow_ratios)
                    eyebrow_raise = avg_eyebrow - self.baseline_eyebrow_distance if self.baseline_eyebrow_distance else 0
                    eyebrow_color = (0, 255, 0) if eyebrow_raise > self.eyebrow_raise_threshold else (255, 255, 255)
                    cv2.putText(frame, f"Sopracciglia: {eyebrow_raise:.4f}", (20, 130),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, eyebrow_color, 1)
                elif not self.eyebrow_calibrated:
                    progress = len(self.eyebrow_calibration_samples)
                    cv2.putText(frame, f"Calibrazione sopracciglia: {progress}/20", (20, 130),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            # Istruzioni
            click_instruction = "Chiudi occhio SX" if self.click_mode == "eye" else "Alza le sopracciglia"
            cv2.putText(frame, f"Muovi la testa per cursore - {click_instruction} per click", (20, h-120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Stato ricalibrazione
            recal_status = "ON" if self.recalibration_enabled else "OFF"
            cv2.putText(frame, f"Ricalibrazione auto: {recal_status} (Tieni fermo 10s per ricalibra)", (20, h-90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.putText(frame, "C = Cambia modalità click | R = Toggle ricalibrazione", (20, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
            cv2.putText(frame, "ESC = Esci", (20, h-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    print("="*60)
    print("CONTROLLORE MOUSE CON NASO + CLICK CONFIGURABILE")
    print("="*60)
    print("Avvio automatico senza calibrazione manuale.")
    print("Mantieni la testa ferma al centro all'inizio per alcuni secondi.")
    print("CLICK OCCHIO: Chiudi l'occhio SINISTRO per fare click")
    print("CLICK SOPRACCIGLIA: Alza le sopracciglia per fare click")
    print("RICALIBRAZIONE: Tieni la testa ferma per 10s per ricalibra il centro")
    print("Premi 'C' per cambiare modalità click, 'R' per toggle ricalibrazione")
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
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("Premi ESC per uscire, C per cambiare modalità click, R per toggle ricalibrazione")
    
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

                # Auto-imposta il centro o controlla il mouse
                if not controller.center_calculated:
                    controller.auto_set_center(nose_pos)
                else:
                    controller.update_cursor_position(nose_pos)
                    
                    # Controlla per ricalibrazione automatica
                    recalibration_occurred = controller.check_for_recalibration(nose_pos)
                    
                    # Rileva click in base alla modalità corrente
                    if controller.click_mode == "eye":
                        last_click_detected = controller.detect_left_eye_blink(landmarks_np)
                    elif controller.click_mode == "eyebrow":
                        last_click_detected = controller.detect_eyebrow_raise(landmarks_np)

                controller.draw_interface(frame, controller.last_nose_pos, landmarks_np, last_click_detected)
            else:
                controller.draw_interface(frame, controller.last_nose_pos)
                
            cv2.imshow('Head Mouse + Configurable Click', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('c') or key == ord('C'):  # Toggle modalità click
                controller.toggle_click_mode()
            elif key == ord('r') or key == ord('R'):  # Toggle ricalibrazione
                controller.toggle_recalibration()

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