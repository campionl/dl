import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys


class DynamicNoseMouseController:
    def __init__(self):
        """
        Controller del mouse tramite movimento del naso con calibrazione dinamica dell'occhio per il click.
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
        
        # Sistema di controllo semplificato
        self.center_position = None  # Sarà impostato automaticamente
        self.last_nose_pos = np.array([320.0, 240.0]) # Posizione predefinita per la prima visualizzazione
        self.movement_sensitivity = 3.0  # Sensibilità predefinita
        self.deadzone_radius = 15.0      # Zona morta predefinita
        
        # Parametri per il centro automatico
        self.center_samples = []
        self.max_center_samples = 30  # Numero di campioni per calcolare il centro
        self.center_calculated = False
        
        # Current cursor position
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        
        # Sistema di rilevamento ammiccamento per click - DINAMICO
        self.calibrated_open_eye_ear = None  # EAR quando l'occhio è aperto normalmente
        self.ear_calibration_samples = []
        self.max_ear_calibration_samples = 60 # Numero di campioni per calibrare l'occhio aperto
        self.ear_calibrated = False
        self.blink_detection_threshold = 0.05 # Soglia per considerare l'occhio "toccato" (può essere molto piccola)
        self.last_click_time = 0
        self.click_cooldown = 0.5  # Tempo minimo tra i click (secondi)
        self.eye_aspect_ratios_buffer = []  # Buffer per stabilizzare il rilevamento
        self.ear_buffer_size = 3  # Numero di campioni per media mobile

    def calculate_eye_aspect_ratio(self, eye_top, eye_bottom):
        """
        Calcola la distanza verticale tra le palpebre.
        Non è un vero e proprio EAR normalizzato, ma la distanza in pixel.
        """
        vertical_distance = abs(eye_top[1] - eye_bottom[1])
        return vertical_distance # Restituiamo la distanza verticale in pixel

    def calibrate_open_eye(self, ear_value):
        """
        Calibra l'EAR dell'occhio aperto basandosi sui primi frame.
        """
        if not self.ear_calibrated:
            self.ear_calibration_samples.append(ear_value)
            
            if len(self.ear_calibration_samples) >= self.max_ear_calibration_samples:
                self.calibrated_open_eye_ear = np.mean(self.ear_calibration_samples)
                self.ear_calibrated = True
                print(f"EAR occhio aperto calibrato: {self.calibrated_open_eye_ear:.4f}")
                # Impostiamo una soglia di click relativa al valore calibrato, ma non la usiamo direttamente
                # con la logica di "toccare"
                return True
        return False

    def detect_left_eye_click(self, landmarks):
        """
        Rileva se l'occhio sinistro è "toccato" (distanza verticale quasi zero) e genera un click.
        """
        if not self.ear_calibrated:
            return False # Non possiamo rilevare click senza calibrazione

        left_eye_top = landmarks[self.LEFT_EYE_TOP]
        left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM]
        
        # Calcola la distanza verticale in pixel (il nostro "EAR" semplificato)
        current_vertical_distance = self.calculate_eye_aspect_ratio(left_eye_top, left_eye_bottom)
        
        # Aggiungi al buffer per stabilizzare
        self.eye_aspect_ratios_buffer.append(current_vertical_distance)
        if len(self.eye_aspect_ratios_buffer) > self.ear_buffer_size:
            self.eye_aspect_ratios_buffer.pop(0)
        
        # Calcola la media per ridurre il rumore
        avg_vertical_distance = np.mean(self.eye_aspect_ratios_buffer)
        
        # Verifica se i punti si "toccano" (distanza quasi zero) e se è passato abbastanza tempo dall'ultimo click
        current_time = time.time()
        # Per rilevare il "tocco", usiamo una soglia molto piccola, indipendente dall'EAR calibrato
        if (avg_vertical_distance < self.blink_detection_threshold and 
            current_time - self.last_click_time > self.click_cooldown):
            
            try:
                pyautogui.click()
                self.last_click_time = current_time
                print(f"\nClick eseguito! Distanza verticale: {avg_vertical_distance:.4f}")
                return True
            except Exception as e:
                print(f"Errore nel click: {e}")
        
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

        # Stato di inizializzazione generale
        if not self.center_calculated:
            # Modalità inizializzazione centro
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)  # Arancione
            progress = len(self.center_samples)
            cv2.putText(frame, f"CALIBRAZIONE CENTRO: {progress}/{self.max_center_samples}", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            cv2.putText(frame, "Mantieni la testa ferma al centro per qualche secondo", 
                       (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        elif not self.ear_calibrated:
            # Modalità calibrazione occhio
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)  # Arancione
            progress = len(self.ear_calibration_samples)
            cv2.putText(frame, f"CALIBRAZIONE OCCHIO: {progress}/{self.max_ear_calibration_samples}", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            cv2.putText(frame, "Tieni l'occhio sinistro aperto normalmente per qualche secondo", 
                       (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Disegna indicatori occhi se disponibili durante la calibrazione
            if landmarks is not None:
                left_eye_top = landmarks[self.LEFT_EYE_TOP].astype(int)
                left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM].astype(int)
                cv2.circle(frame, tuple(left_eye_top), 3, (255, 0, 0), -1)
                cv2.circle(frame, tuple(left_eye_bottom), 3, (255, 0, 0), -1)
                cv2.line(frame, tuple(left_eye_top), tuple(left_eye_bottom), (255, 0, 0), 1)
                
                if len(self.ear_calibration_samples) > 0:
                    current_dist = self.calculate_eye_aspect_ratio(left_eye_top, left_eye_bottom)
                    cv2.putText(frame, f"Dist. Attuale: {current_dist:.2f}px", (20, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

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
                left_eye_top = landmarks[self.LEFT_EYE_TOP].astype(int)
                left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM].astype(int)
                
                # Disegna punti dell'occhio
                cv2.circle(frame, tuple(left_eye_top), 3, (255, 0, 0), -1)
                cv2.circle(frame, tuple(left_eye_bottom), 3, (255, 0, 0), -1)
                cv2.line(frame, tuple(left_eye_top), tuple(left_eye_bottom), (255, 0, 0), 1)
                
                # Indicatore click
                if last_click_detected:
                    cv2.circle(frame, tuple(left_eye_top), 15, (0, 255, 0), 3)

            # Informazioni di stato
            status_color = (0, 255, 0)
            cv2.putText(frame, "MOUSE ATTIVO + CLICK OCCHIO", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Debug info
            cv2.putText(frame, f"Naso: {int(nose_pos[0])},{int(nose_pos[1])}", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Cursore: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}", 
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if self.center_position is not None:
                distance = np.linalg.norm(nose_pos - self.center_position)
                cv2.putText(frame, f"Distanza: {distance:.1f}px", (20, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mostra distanza verticale occhio e soglia di click
            if len(self.eye_aspect_ratios_buffer) > 0:
                avg_vertical_distance = np.mean(self.eye_aspect_ratios_buffer)
                ear_color = (0, 255, 0) if avg_vertical_distance > self.blink_detection_threshold else (0, 0, 255)
                cv2.putText(frame, f"Dist. Occhio: {avg_vertical_distance:.2f}px", (20, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, ear_color, 1)
                cv2.putText(frame, f"Soglia Click: {self.blink_detection_threshold:.2f}px", (20, 150),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Istruzioni
            cv2.putText(frame, "Muovi la testa per il cursore - Chiudi occhio SX (punti si toccano) per click", (20, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "ESC per uscire", (20, h-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    print("="*60)
    print("CONTROLLORE MOUSE CON NASO + CLICK CON OCCHIO (CALIBRAZIONE DINAMICA)")
    print("="*60)
    print("Fase 1: Calibrazione del centro. Mantieni la testa ferma al centro per alcuni secondi.")
    print("Fase 2: Calibrazione dell'occhio. Tieni l'occhio sinistro aperto normalmente per alcuni secondi.")
    print("CLICK: Chiudi l'occhio SINISTRO fino a far 'toccare' i punti superiore e inferiore.")
    print("="*60)

    controller = DynamicNoseMouseController() # Ora usiamo il nuovo controller
    
    # Prova diverse fonti video
    cap = None
    video_sources = [0, 1, 2, '/dev/video0', '/dev/video1', '/dev/video2']
    
    print("Ricerca webcam disponibili...")
    for source in video_sources:
        print(f"Tentativo con fonte video: {source}")
        test_cap = cv2.VideoCapture(source)
        if test_cap.isOpened():
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
    cap.set(cv2.CAP_PROP_FPS, 30)  # Ridotto per Raspberry Pi
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

                # Gestione della calibrazione in sequenza
                if not controller.center_calculated:
                    controller.auto_set_center(nose_pos)
                elif not controller.ear_calibrated:
                    # Calibra l'occhio solo se il centro è già stato calcolato
                    left_eye_top = landmarks_np[controller.LEFT_EYE_TOP]
                    left_eye_bottom = landmarks_np[controller.LEFT_EYE_BOTTOM]
                    current_ear_value = controller.calculate_eye_aspect_ratio(left_eye_top, left_eye_bottom)
                    controller.calibrate_open_eye(current_ear_value)
                else:
                    # Modalità operativa dopo entrambe le calibrazioni
                    controller.update_cursor_position(nose_pos)
                    # Rileva click basato sul "tocco"
                    last_click_detected = controller.detect_left_eye_click(landmarks_np)

                controller.draw_interface(frame, controller.last_nose_pos, landmarks_np, last_click_detected)
            else:
                # Se non rileva un volto, disegna l'interfaccia con le ultime posizioni note.
                # Questo è importante durante la fase di calibrazione iniziale.
                controller.draw_interface(frame, controller.last_nose_pos)
                
            cv2.imshow('Head Mouse + Eye Click', frame)
            
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