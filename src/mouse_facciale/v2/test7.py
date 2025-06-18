import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys
from collections import deque
import threading


class NoseInputModule:
    """Modulo per la gestione dell'input del naso e movimento del mouse"""
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.current_mouse_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        self.position_history = deque(maxlen=5)
        self.mouse_lock = threading.Lock()
        
        # Parametri configurabili
        self.center_position = None
        self.base_sensitivity = 4.0
        self.deadzone_radius = 15.0
        self.max_acceleration_distance = 200.0
        
        # Calibrazione
        self.center_samples = []
        self.max_center_samples = 30
        self.center_calculated = False
        
        pyautogui.moveTo(self.current_mouse_pos[0], self.current_mouse_pos[1])

    def auto_calibrate_center(self, tracking_point):
        """Calibrazione centro."""
        if not self.center_calculated:
            self.center_samples.append(tracking_point.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                self.center_position = np.median(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"Centro calibrato: {self.center_position}")
                return True
        return False

    def update_mouse_position(self, tracking_point):
        """Aggiorna posizione mouse con accelerazione progressiva."""
        if self.center_position is None:
            return
        
        # Calcola offset e distanza dal centro
        offset = tracking_point - self.center_position
        distance = np.linalg.norm(offset)
        
        # Applica deadzone
        if distance < self.deadzone_radius:
            return
        
        # Calcola fattore accelerazione progressivo
        effective_distance = distance - self.deadzone_radius
        normalized_distance = min(effective_distance / (self.max_acceleration_distance - self.deadzone_radius), 1.0)
        
        # Accelerazione non lineare
        acceleration_factor = 1.0 + (3.0 * normalized_distance ** 2)
        
        # Calcola movimento
        direction = offset / distance
        movement = direction * self.base_sensitivity * acceleration_factor * effective_distance * 0.1
        
        # Smoothing
        self.position_history.append(movement)
        if len(self.position_history) > 1:
            smoothed_movement = np.mean(self.position_history, axis=0)
        else:
            smoothed_movement = movement
        
        # Aggiorna posizione
        with self.mouse_lock:
            self.current_mouse_pos += smoothed_movement
            
            # Limiti schermo
            self.current_mouse_pos[0] = np.clip(self.current_mouse_pos[0], 0, self.screen_w - 1)
            self.current_mouse_pos[1] = np.clip(self.current_mouse_pos[1], 0, self.screen_h - 1)
            
            # Muovi il mouse
            try:
                pyautogui.moveTo(int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1]))
            except Exception as e:
                print(f"Errore movimento: {e}")
    
    def reset_calibration(self):
        """Resetta la calibrazione"""
        self.center_calculated = False
        self.center_samples = []
        self.center_position = None
        print("Calibrazione resettata")
    
    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità"""
        self.base_sensitivity = np.clip(self.base_sensitivity + amount, 0.5, 5.0)
        print(f"Sensibilità aggiornata: {self.base_sensitivity:.1f}")


class EyeInputModule:
    """Modulo per la gestione dell'input degli occhi e rilevamento click"""
    def __init__(self, left_indices=(159, 145), right_indices=(386, 374)):
        # Landmark indices
        self.LEFT_EYE_TOP = left_indices[0]
        self.LEFT_EYE_BOTTOM = left_indices[1]
        self.RIGHT_EYE_TOP = right_indices[0]
        self.RIGHT_EYE_BOTTOM = right_indices[1]
        
        # Parametri blink
        self.blink_threshold = 0.10
        self.blink_duration_required = 0.10
        self.click_cooldown = 0.5
        
        # Stato occhi
        self.left_blink_start_time = None
        self.left_eye_closed = False
        self.left_ear_history = deque(maxlen=3)
        self.last_left_click_time = 0
        
        self.right_blink_start_time = None
        self.right_eye_closed = False
        self.right_ear_history = deque(maxlen=3)
        self.last_right_click_time = 0
        
        self.mouse_lock = threading.Lock()

    def calculate_eye_aspect_ratio(self, landmarks, eye='left'):
        """Calcola EAR per l'occhio specificato."""
        try:
            if eye == 'left':
                top = landmarks[self.LEFT_EYE_TOP]
                bottom = landmarks[self.LEFT_EYE_BOTTOM]
            else:  # right
                top = landmarks[self.RIGHT_EYE_TOP]
                bottom = landmarks[self.RIGHT_EYE_BOTTOM]
                
            ear = abs(top[1] - bottom[1]) / 25.0
            return ear
        except:
            return 0.2  # Valore default sicuro

    def detect_blinks(self, landmarks, current_mouse_pos):
        """Rileva blink di entrambi gli occhi separatamente."""
        # Calcola EAR per entrambi gli occhi
        left_ear = self.calculate_eye_aspect_ratio(landmarks, eye='left')
        right_ear = self.calculate_eye_aspect_ratio(landmarks, eye='right')
        
        # Aggiungi alla storia
        self.left_ear_history.append(left_ear)
        self.right_ear_history.append(right_ear)
        
        # Stabilizza con media mobile
        stable_left_ear = np.mean(list(self.left_ear_history)) if self.left_ear_history else left_ear
        stable_right_ear = np.mean(list(self.right_ear_history)) if self.right_ear_history else right_ear
        
        current_time = time.time()
        
        # Rileva blink occhio sinistro (click sinistro)
        if self.detect_left_blink(stable_left_ear, current_time):
            self.perform_click(current_mouse_pos, button='left')
        
        # Rileva blink occhio destro (click destro)
        if self.detect_right_blink(stable_right_ear, current_time):
            self.perform_click(current_mouse_pos, button='right')

    def detect_left_blink(self, stable_ear, current_time):
        """Rileva blink dell'occhio sinistro per click sinistro."""
        # Inizio blink sinistro
        if stable_ear < self.blink_threshold and not self.left_eye_closed:
            self.left_eye_closed = True
            self.left_blink_start_time = current_time
            return False
        
        # Fine blink sinistro
        elif stable_ear >= self.blink_threshold and self.left_eye_closed:
            self.left_eye_closed = False
            
            if (self.left_blink_start_time is not None and 
                current_time - self.left_blink_start_time >= self.blink_duration_required and
                current_time - self.last_left_click_time > self.click_cooldown):
                return True
        
        return False

    def detect_right_blink(self, stable_ear, current_time):
        """Rileva blink dell'occhio destro per click destro."""
        # Inizio blink destro
        if stable_ear < self.blink_threshold and not self.right_eye_closed:
            self.right_eye_closed = True
            self.right_blink_start_time = current_time
            return False
        
        # Fine blink destro
        elif stable_ear >= self.blink_threshold and self.right_eye_closed:
            self.right_eye_closed = False
            
            if (self.right_blink_start_time is not None and 
                current_time - self.right_blink_start_time >= self.blink_duration_required and
                current_time - self.last_right_click_time > self.click_cooldown):
                return True
        
        return False

    def perform_click(self, current_mouse_pos, button='left'):
        """Esegue click sinistro o destro con gestione errori."""
        try:
            with self.mouse_lock:
                x, y = int(current_mouse_pos[0]), int(current_mouse_pos[1])
            
            if button == 'left':
                pyautogui.click(x=x, y=y, button='left')
                print(f"Click SINISTRO: ({x}, {y})")
                self.last_left_click_time = time.time()
            else:  # right
                pyautogui.click(x=x, y=y, button='right')
                print(f"Click DESTRO: ({x}, {y})")
                self.last_right_click_time = time.time()
            
            return True
        except Exception as e:
            print(f"Errore click {button}: {e}")
            return False


class HeadMouseController:
    def __init__(self, show_window=True):
        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )

        # PyAutoGUI setup
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.001
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Landmark indices
        self.NOSE_TIP = 4
        
        # Moduli separati
        self.nose_module = NoseInputModule(self.screen_w, self.screen_h)
        self.eye_module = EyeInputModule()
        
        # Stato applicazione
        self.show_window = show_window
        self.paused = False
        
        print("=== HEAD MOUSE CONTROLLER ===")
        print("Click sinistro: occhio sinistro | Click destro: occhio destro")
        print("Punto di riferimento: punta del naso")

    def toggle_pause(self):
        """Metodo per mettere in pausa/riprendere il controllo."""
        self.paused = not self.paused
        status = "PAUSATO" if self.paused else "ATTIVO"
        print(f"Stato cambiato: {status}")

    def draw_interface(self, frame, tracking_point, landmarks=None):
        """Disegna interfaccia utente."""
        if not self.show_window:
            return

        h, w = frame.shape[:2]

        if not self.nose_module.center_calculated:
            # Fase calibrazione
            cv2.circle(frame, tuple(tracking_point.astype(int)), 15, (0, 165, 255), 3)
            progress = len(self.nose_module.center_samples)
            percentage = int((progress / self.nose_module.max_center_samples) * 100)
            
            cv2.putText(frame, f"CALIBRAZIONE: {percentage}%", 
                       (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
        else:
            # Stato attivo
            color = (128, 128, 128) if self.paused else (0, 255, 0)
            
            # Punto tracking
            cv2.circle(frame, tuple(tracking_point.astype(int)), 8, color, -1)
            
            # Centro e deadzone
            if self.nose_module.center_position is not None:
                center_pt = tuple(self.nose_module.center_position.astype(int))
                cv2.circle(frame, center_pt, int(self.nose_module.deadzone_radius), (255, 255, 0), 2)
                
                # Freccia movimento
                distance = np.linalg.norm(tracking_point - self.nose_module.center_position)
                if distance > self.nose_module.deadzone_radius and not self.paused:
                    cv2.arrowedLine(frame, center_pt, tuple(tracking_point.astype(int)), (0, 255, 255), 3)
                    
                    # Mostra zona accelerazione
                    cv2.circle(frame, center_pt, int(self.nose_module.max_acceleration_distance), (0, 100, 255), 1)

            # Indicatori occhi
            if landmarks is not None and not self.paused:
                # Occhio sinistro (click sinistro)
                left_eye_top = landmarks[self.eye_module.LEFT_EYE_TOP].astype(int)
                left_eye_bottom = landmarks[self.eye_module.LEFT_EYE_BOTTOM].astype(int)
                left_eye_color = (0, 0, 255) if self.eye_module.left_eye_closed else (0, 255, 0)
                cv2.line(frame, tuple(left_eye_top), tuple(left_eye_bottom), left_eye_color, 3)
                
                # Etichetta occhio sinistro
                cv2.putText(frame, "L", (left_eye_top[0] - 15, left_eye_top[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, left_eye_color, 2)
                
                # Occhio destro (click destro)
                right_eye_top = landmarks[self.eye_module.RIGHT_EYE_TOP].astype(int)
                right_eye_bottom = landmarks[self.eye_module.RIGHT_EYE_BOTTOM].astype(int)
                right_eye_color = (255, 0, 0) if self.eye_module.right_eye_closed else (0, 255, 0)
                cv2.line(frame, tuple(right_eye_top), tuple(right_eye_bottom), right_eye_color, 3)
                
                # Etichetta occhio destro
                cv2.putText(frame, "R", (right_eye_top[0] + 10, right_eye_top[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, right_eye_color, 2)

            # Status
            status_text = "PAUSATO" if self.paused else "ATTIVO"
            status_color = (0, 0, 255) if self.paused else (0, 255, 0)
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Info sensibilità
            cv2.putText(frame, f"Sensibilita: {self.nose_module.base_sensitivity:.1f}", 
                       (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Controlli aggiornati
        controls = [
            "=== CONTROLLI ===",
            "Occhio SX = Click Sinistro",
            "Occhio DX = Click Destro", 
            "SPAZIO = Pausa/Riprendi",
            "+/- = Modifica sensibilità",
            "R = Reset calibrazione",
            "ESC = Esci"
        ]
        
        y_start = h - len(controls) * 22 - 10
        for i, control in enumerate(controls):
            if i == 0:
                color, weight = (255, 255, 0), 2
            elif i <= 2:
                color, weight = (0, 255, 255), 1
            else:
                color, weight = (255, 255, 255), 1
                
            cv2.putText(frame, control, (20, y_start + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, weight)


def main():
    print("=== HEAD MOUSE CONTROLLER ===")
    print("Click sinistro: occhio sinistro | Click destro: occhio destro")
    print("Punto di riferimento: punta del naso")
    
    # Scelta modalità display
    while True:
        choice = input("Mostrare finestra webcam? (s/n): ").lower().strip()
        if choice in ['s', 'n']:
            show_window = choice == 's'
            break
        print("Inserisci 's' per sì o 'n' per no")

    controller = HeadMouseController(show_window=show_window)
    
    # Setup webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Errore: Webcam non trovata!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("\n🎮 CONTROLLI:")
    print("Occhio SINISTRO = Click Sinistro | Occhio DESTRO = Click Destro")
    print("SPAZIO = Pausa/Riprendi | +/- = Sensibilità")
    print("R = Reset calibrazione | ESC = Esci")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Impossibile leggere il frame.")
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = controller.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                tracking_point = landmarks_np[controller.NOSE_TIP]
                
                if not controller.nose_module.center_calculated:
                    controller.nose_module.auto_calibrate_center(tracking_point)
                elif not controller.paused:
                    controller.nose_module.update_mouse_position(tracking_point)
                    controller.eye_module.detect_blinks(
                        landmarks_np,
                        controller.nose_module.current_mouse_pos
                    )

                if controller.show_window:
                    controller.draw_interface(frame, tracking_point, landmarks_np)
            else:
                if controller.show_window:
                    cv2.putText(frame, "VISO NON RILEVATO", (20, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            
            if controller.show_window:
                cv2.imshow('Head Mouse Controller', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord(' '):  # SPAZIO
                    controller.toggle_pause()
                elif key == ord('+'):  # +
                    controller.nose_module.adjust_sensitivity(0.2)
                elif key == ord('-'):  # -
                    controller.nose_module.adjust_sensitivity(-0.2)
                elif key == ord('r'):  # R
                    controller.nose_module.reset_calibration()
            else:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nInterruzione da tastiera")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Controller chiuso")


if __name__ == "__main__":
    main()