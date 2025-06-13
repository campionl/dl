import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys
from collections import deque
import threading


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
        self.NOSE_TIP = 4  # Punto naso centrale
        self.LEFT_EYE_TOP = 159
        self.LEFT_EYE_BOTTOM = 145
        self.RIGHT_EYE_TOP = 386
        self.RIGHT_EYE_BOTTOM = 374
        
        # Parametri configurabili
        self.center_position = None
        self.base_sensitivity = 3.0  # Sensibilità base aumentata
        self.deadzone_radius = 15.0  # Area morta iniziale
        self.max_acceleration_distance = 200.0  # Distanza massima per accelerazione aumentata
        
        # Sistema di smoothing
        self.position_history = deque(maxlen=5)
        
        # Posizione mouse iniziale
        self.current_mouse_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_mouse_pos[0], self.current_mouse_pos[1])
        
        # Calibrazione
        self.center_samples = []
        self.max_center_samples = 30
        self.center_calculated = False
        
        # Blink clicking
        self.blink_threshold = 0.10  # Soglia per blink volontari
        self.blink_duration_required = 0.05  # Durata minima
        self.blink_start_time = None
        self.eye_closed = False
        self.ear_history = deque(maxlen=3)
        self.last_click_time = 0
        self.click_cooldown = 0.5
        
        # Threading
        self.mouse_lock = threading.Lock()
        
        self.show_window = show_window
        self.paused = False
        
        print("=== HEAD MOUSE CONTROLLER ===")
        print("Click con occhio sinistro | Movimento accelerato")
        print("Punto di riferimento: punta del naso")

    def calculate_eye_aspect_ratio(self, landmarks, eye='left'):
        """Calcola EAR per un solo occhio (sinistro di default)."""
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

    def detect_blink(self, landmarks):
        """Rileva blink solo dell'occhio sinistro per click."""
        ear = self.calculate_eye_aspect_ratio(landmarks, eye='left')
        self.ear_history.append(ear)
        
        # Stabilizza con media mobile
        stable_ear = np.mean(list(self.ear_history)) if len(self.ear_history) >= 2 else ear
        
        current_time = time.time()
        
        # Inizio blink
        if stable_ear < self.blink_threshold and not self.eye_closed:
            self.eye_closed = True
            self.blink_start_time = current_time
            return False
        
        # Fine blink - controlla se è volontario
        elif stable_ear >= self.blink_threshold and self.eye_closed:
            self.eye_closed = False
            
            if (self.blink_start_time is not None and 
                current_time - self.blink_start_time >= self.blink_duration_required and
                current_time - self.last_click_time > self.click_cooldown):
                
                self.perform_click()
                return True
        
        return False

    def perform_click(self):
        """Esegue click con gestione errori."""
        try:
            with self.mouse_lock:
                x, y = int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1])
            
            pyautogui.click(x=x, y=y)
            print(f"Click: ({x}, {y})")
            
            self.last_click_time = time.time()
            return True
        except Exception as e:
            print(f"Errore click: {e}")
            return False

    def toggle_pause(self):
        """Metodo per mettere in pausa/riprendere il controllo."""
        self.paused = not self.paused
        status = "PAUSATO" if self.paused else "ATTIVO"
        print(f"Stato cambiato: {status}")

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
        if self.center_position is None or self.paused:
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
        
        # Accelerazione non lineare (esponenziale per maggiore controllo)
        acceleration_factor = 1.0 + (3.0 * normalized_distance ** 2)  # 1x-4x
        
        # Calcola movimento con accelerazione progressiva
        direction = offset / distance  # Normalizza
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

    def draw_interface(self, frame, tracking_point, landmarks=None):
        """Disegna interfaccia utente."""
        if not self.show_window:
            return

        h, w = frame.shape[:2]

        if not self.center_calculated:
            # Fase calibrazione
            cv2.circle(frame, tuple(tracking_point.astype(int)), 15, (0, 165, 255), 3)
            progress = len(self.center_samples)
            percentage = int((progress / self.max_center_samples) * 100)
            
            cv2.putText(frame, f"CALIBRAZIONE: {percentage}%", 
                       (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
        else:
            # Stato attivo
            color = (128, 128, 128) if self.paused else (0, 255, 0)
            
            # Punto tracking
            cv2.circle(frame, tuple(tracking_point.astype(int)), 8, color, -1)
            
            # Centro e deadzone
            if self.center_position is not None:
                center_pt = tuple(self.center_position.astype(int))
                cv2.circle(frame, center_pt, int(self.deadzone_radius), (255, 255, 0), 2)
                
                # Freccia movimento
                distance = np.linalg.norm(tracking_point - self.center_position)
                if distance > self.deadzone_radius and not self.paused:
                    cv2.arrowedLine(frame, center_pt, tuple(tracking_point.astype(int)), (0, 255, 255), 3)
                    
                    # Mostra zona accelerazione
                    cv2.circle(frame, center_pt, int(self.max_acceleration_distance), (0, 100, 255), 1)

            # Indicatore occhio sinistro
            if landmarks is not None and not self.paused:
                left_eye_top = landmarks[self.LEFT_EYE_TOP].astype(int)
                left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM].astype(int)

                eye_color = (0, 0, 255) if self.eye_closed else (0, 255, 0)
                cv2.line(frame, tuple(left_eye_top), tuple(left_eye_bottom), eye_color, 2)

            # Status
            status_text = "PAUSATO" if self.paused else "ATTIVO"
            status_color = (0, 0, 255) if self.paused else (0, 255, 0)
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Info sensibilità
            cv2.putText(frame, f"Sensibilita: {self.base_sensitivity:.1f}", 
                       (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Controlli
        controls = [
            "=== CONTROLLI ===",
            "SPAZIO = Pausa/Riprendi",
            "+/- = Modifica sensibilità",
            "R = Reset calibrazione",
            "ESC = Esci"
        ]
        
        y_start = h - len(controls) * 22 - 10
        for i, control in enumerate(controls):
            color = (255, 255, 0) if i == 0 else (255, 255, 255)
            weight = 2 if i == 0 else 1
            cv2.putText(frame, control, (20, y_start + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, weight)


def main():
    print("=== HEAD MOUSE CONTROLLER ===")
    print("Click con occhio sinistro | Punto di riferimento: naso")
    
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
                
                if not controller.center_calculated:
                    controller.auto_calibrate_center(tracking_point)
                else:
                    controller.update_mouse_position(tracking_point)
                    controller.detect_blink(landmarks_np)

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
                    controller.base_sensitivity = min(5.0, controller.base_sensitivity + 0.2)
                    print(f"Sensibilità aumentata a: {controller.base_sensitivity:.1f}")
                elif key == ord('-'):  # -
                    controller.base_sensitivity = max(0.5, controller.base_sensitivity - 0.2)
                    print(f"Sensibilità diminuita a: {controller.base_sensitivity:.1f}")
                elif key == ord('r'):  # R
                    controller.center_calculated = False
                    controller.center_samples = []
                    controller.center_position = None
                    print("Calibrazione resettata")
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