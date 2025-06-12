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
        
        # Sistema di rilevamento ammiccamento per click
        self.eye_closed_threshold = 0.02  # Soglia per rilevare occhio chiuso
        self.last_click_time = 0
        self.click_cooldown = 0.5  # Tempo minimo tra i click (secondi)
        self.eye_aspect_ratios = []  # Buffer per stabilizzare il rilevamento
        self.ear_buffer_size = 3  # Numero di campioni per media mobile

    def calculate_eye_aspect_ratio(self, eye_top, eye_bottom):
        """
        Calcola l'Eye Aspect Ratio per determinare se l'occhio è chiuso.
        """
        # Calcola la distanza verticale tra le palpebre
        vertical_distance = abs(eye_top[1] - eye_bottom[1])
        # Normalizza rispetto alla larghezza media dell'occhio
        # Usiamo una larghezza di riferimento fissa per semplicità
        reference_width = 20.0
        ear = vertical_distance / reference_width
        return ear

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
                print(f"\nClick eseguito! EAR: {avg_ear:.4f}")
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
            status_color = (0, 255, 0) if last_click_detected else (0, 255, 0)
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
            
            # Mostra EAR se disponibile
            if len(self.eye_aspect_ratios) > 0:
                avg_ear = np.mean(self.eye_aspect_ratios)
                ear_color = (0, 255, 0) if avg_ear > self.eye_closed_threshold else (0, 0, 255)
                cv2.putText(frame, f"Occhio EAR: {avg_ear:.4f}", (20, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, ear_color, 1)

            # Istruzioni
            cv2.putText(frame, "Muovi la testa per il cursore - Chiudi occhio SX per click", (20, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "ESC per uscire", (20, h-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    print("="*60)
    print("CONTROLLORE MOUSE CON NASO + CLICK CON OCCHIO")
    print("="*60)
    print("Avvio automatico senza calibrazione manuale.")
    print("Mantieni la testa ferma al centro all'inizio per alcuni secondi.")
    print("CLICK: Chiudi l'occhio SINISTRO per fare click sinistro")
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

                # Auto-imposta il centro o controlla il mouse
                if not controller.center_calculated:
                    controller.auto_set_center(nose_pos)
                else:
                    controller.update_cursor_position(nose_pos)
                    # Rileva ammiccamento per click
                    last_click_detected = controller.detect_left_eye_blink(landmarks_np)

                controller.draw_interface(frame, controller.last_nose_pos, landmarks_np, last_click_detected)
            else:
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
