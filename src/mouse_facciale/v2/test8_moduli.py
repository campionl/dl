import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys
from collections import deque
import threading


class BaseEvent:
    """Classe base per tutti gli eventi"""
    def check_event(self, *args, **kwargs):
        """Metodo astratto per verificare se l'evento è attivo"""
        raise NotImplementedError


class BaseAction:
    """Classe base per tutte le azioni"""
    def execute(self, *args, **kwargs):
        """Metodo astratto per eseguire l'azione"""
        raise NotImplementedError


class Calibration_action:
    """Classe per la gestione della calibrazione del centro"""
    def __init__(self, max_samples=30):
        self.center_samples = []
        self.max_center_samples = max_samples
        self.center_calculated = False
        self.center_position = None
    
    def add_sample(self, tracking_point):
        """Aggiunge un sample per la calibrazione"""
        if not self.center_calculated:
            self.center_samples.append(tracking_point.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                self.center_position = np.median(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"Centro calibrato: {self.center_position}")
                return True
        return False
    
    def reset_calibration(self):
        """Resetta la calibrazione"""
        self.center_calculated = False
        self.center_samples = []
        self.center_position = None
        print("Calibrazione resettata")
    
    def set_new_center(self, new_center):
        """Imposta un nuovo centro direttamente"""
        self.center_position = new_center.copy()
        self.center_calculated = True
        self.center_samples = [new_center] * self.max_center_samples
        print(f"Nuovo centro impostato: {self.center_position}")


class NoseJoystick_event(BaseEvent):
    """Classe per rilevare gli eventi del joystick del naso"""
    def __init__(self, deadzone_radius=15.0, max_acceleration_distance=200.0):
        self.deadzone_radius = deadzone_radius
        self.max_acceleration_distance = max_acceleration_distance
        self.outside_deadzone_start_time = None
        self.auto_recalibrate_timeout = 5.0  # 5 secondi
        
    def is_outside_deadzone(self, tracking_point, center_position):
        """Controlla se il punto è fuori dalla zona morta"""
        if center_position is None:
            return False
        
        offset = tracking_point - center_position
        distance = np.linalg.norm(offset)
        return distance >= self.deadzone_radius
    
    def get_movement_vector(self, tracking_point, center_position):
        """Calcola il vettore di movimento basato sulla posizione del naso"""
        if center_position is None:
            return None, 0, 0
        
        offset = tracking_point - center_position
        distance = np.linalg.norm(offset)
        
        # Se dentro la deadzone, nessun movimento
        if distance < self.deadzone_radius:
            self.outside_deadzone_start_time = None
            return None, 0, 0
        
        # Traccia tempo fuori dalla deadzone
        current_time = time.time()
        if self.outside_deadzone_start_time is None:
            self.outside_deadzone_start_time = current_time
        
        # Calcola fattore accelerazione progressivo
        effective_distance = distance - self.deadzone_radius
        normalized_distance = min(effective_distance / (self.max_acceleration_distance - self.deadzone_radius), 1.0)
        
        # Accelerazione non lineare
        acceleration_factor = 1.0 + (3.0 * normalized_distance ** 2)
        
        # Calcola direzione
        direction = offset / distance
        
        return direction, acceleration_factor, effective_distance
    
    def should_recalibrate(self):
        """Controlla se è necessario ricalibrare per essere fuori dalla deadzone troppo a lungo"""
        if self.outside_deadzone_start_time is None:
            return False
        
        return (time.time() - self.outside_deadzone_start_time) > self.auto_recalibrate_timeout
    
    def reset_outside_timer(self):
        """Resetta il timer per il tempo fuori dalla deadzone"""
        self.outside_deadzone_start_time = None
    
    def check_event(self, tracking_point, center_position):
        """Implementazione del metodo base per verificare l'evento"""
        return self.is_outside_deadzone(tracking_point, center_position)


class MouseCursor_action(BaseAction):
    """Classe per tradurre il movimento del naso in movimento del cursore"""
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.current_mouse_pos = np.array([screen_w // 2, screen_h // 2], dtype=float)
        self.position_history = deque(maxlen=5)
        self.mouse_lock = threading.Lock()
        self.base_sensitivity = 4.0
        
        pyautogui.moveTo(self.current_mouse_pos[0], self.current_mouse_pos[1])
    
    def update_position(self, direction, acceleration_factor, effective_distance):
        """Aggiorna la posizione del cursore"""
        if direction is None:
            return
        
        # Calcola movimento
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
    
    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità"""
        self.base_sensitivity = np.clip(self.base_sensitivity + amount, 0.5, 5.0)
        print(f"Sensibilità aggiornata: {self.base_sensitivity:.1f}")
    
    def get_current_position(self):
        """Restituisce la posizione attuale del cursore"""
        with self.mouse_lock:
            return self.current_mouse_pos.copy()
    
    def execute(self, direction, acceleration_factor, effective_distance):
        """Implementazione del metodo base per eseguire l'azione"""
        self.update_position(direction, acceleration_factor, effective_distance)


class LeftEye_event(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio sinistro"""
    def __init__(self, top_index=159, bottom_index=145, blink_duration=0.3):
        self.LEFT_EYE_TOP = top_index
        self.LEFT_EYE_BOTTOM = bottom_index
        self.blink_threshold = 0.10
        self.blink_duration_required = blink_duration  # 300ms di default
        self.blink_start_time = None
        self.eye_closed = False
        self.blink_detected = False  # Flag per tracciare se il blink è stato rilevato
        self.ear_history = deque(maxlen=3)
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calcola EAR per l'occhio sinistro"""
        try:
            top = landmarks[self.LEFT_EYE_TOP]
            bottom = landmarks[self.LEFT_EYE_BOTTOM]
            ear = abs(top[1] - bottom[1]) / 25.0
            return ear
        except:
            return 0.2  # Valore default sicuro
    
    def detect_blink(self, landmarks):
        """Rileva blink dell'occhio sinistro solo se chiuso per il tempo richiesto"""
        ear = self.calculate_eye_aspect_ratio(landmarks)
        self.ear_history.append(ear)
        
        # Stabilizza con media mobile
        stable_ear = np.mean(list(self.ear_history)) if self.ear_history else ear
        current_time = time.time()
        
        # Se l'occhio è chiuso (sotto la soglia)
        if stable_ear < self.blink_threshold:
            if not self.eye_closed and not self.blink_detected:
                # Inizia il blink
                self.eye_closed = True
                self.blink_start_time = current_time
            elif (self.eye_closed and 
                  not self.blink_detected and 
                  self.blink_start_time is not None and 
                  current_time - self.blink_start_time >= self.blink_duration_required):
                # Occhio chiuso abbastanza a lungo - registra il blink
                self.blink_detected = True
                return True
        else:
            # Occhio aperto - resetta lo stato
            if self.eye_closed:
                self.eye_closed = False
                self.blink_start_time = None
                self.blink_detected = False  # Reset per permettere nuovo rilevamento
        
        return False
    
    def is_eye_closed(self):
        """Restituisce se l'occhio è attualmente chiuso"""
        return self.eye_closed
    
    def check_event(self, landmarks):
        """Implementazione del metodo base per verificare l'evento"""
        return self.detect_blink(landmarks)


class LeftClick_action(BaseAction):
    """Classe per eseguire click sinistro"""
    def __init__(self, click_cooldown=0.5):
        self.click_cooldown = click_cooldown
        self.last_click_time = 0
        self.mouse_lock = threading.Lock()
    
    def perform_click(self, mouse_position):
        """Esegue click sinistro"""
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            with self.mouse_lock:
                x, y = int(mouse_position[0]), int(mouse_position[1])
            
            pyautogui.click(x=x, y=y, button='left')
            print(f"Click SINISTRO: ({x}, {y})")
            self.last_click_time = current_time
            return True
        except Exception as e:
            print(f"Errore click sinistro: {e}")
            return False
    
    def execute(self, mouse_position):
        """Implementazione del metodo base per eseguire l'azione"""
        return self.perform_click(mouse_position)


class RightEye_event(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio destro"""
    def __init__(self, top_index=386, bottom_index=374, blink_duration=0.3):
        self.RIGHT_EYE_TOP = top_index
        self.RIGHT_EYE_BOTTOM = bottom_index
        self.blink_threshold = 0.10
        self.blink_duration_required = blink_duration  # 300ms di default
        self.blink_start_time = None
        self.eye_closed = False
        self.blink_detected = False  # Flag per tracciare se il blink è stato rilevato
        self.ear_history = deque(maxlen=3)
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calcola EAR per l'occhio destro"""
        try:
            top = landmarks[self.RIGHT_EYE_TOP]
            bottom = landmarks[self.RIGHT_EYE_BOTTOM]
            ear = abs(top[1] - bottom[1]) / 25.0
            return ear
        except:
            return 0.2  # Valore default sicuro
    
    def detect_blink(self, landmarks):
        """Rileva blink dell'occhio destro solo se chiuso per il tempo richiesto"""
        ear = self.calculate_eye_aspect_ratio(landmarks)
        self.ear_history.append(ear)
        
        # Stabilizza con media mobile
        stable_ear = np.mean(list(self.ear_history)) if self.ear_history else ear
        current_time = time.time()
        
        # Se l'occhio è chiuso (sotto la soglia)
        if stable_ear < self.blink_threshold:
            if not self.eye_closed and not self.blink_detected:
                # Inizia il blink
                self.eye_closed = True
                self.blink_start_time = current_time
            elif (self.eye_closed and 
                  not self.blink_detected and 
                  self.blink_start_time is not None and 
                  current_time - self.blink_start_time >= self.blink_duration_required):
                # Occhio chiuso abbastanza a lungo - registra il blink
                self.blink_detected = True
                return True
        else:
            # Occhio aperto - resetta lo stato
            if self.eye_closed:
                self.eye_closed = False
                self.blink_start_time = None
                self.blink_detected = False  # Reset per permettere nuovo rilevamento
        
        return False
    
    def is_eye_closed(self):
        """Restituisce se l'occhio è attualmente chiuso"""
        return self.eye_closed
    
    def check_event(self, landmarks):
        """Implementazione del metodo base per verificare l'evento"""
        return self.detect_blink(landmarks)


class RightClick_action(BaseAction):
    """Classe per eseguire click destro"""
    def __init__(self, click_cooldown=0.5):
        self.click_cooldown = click_cooldown
        self.last_click_time = 0
        self.mouse_lock = threading.Lock()
    
    def perform_click(self, mouse_position):
        """Esegue click destro"""
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            with self.mouse_lock:
                x, y = int(mouse_position[0]), int(mouse_position[1])
            
            pyautogui.click(x=x, y=y, button='right')
            print(f"Click DESTRO: ({x}, {y})")
            self.last_click_time = current_time
            return True
        except Exception as e:
            print(f"Errore click destro: {e}")
            return False
    
    def execute(self, mouse_position):
        """Implementazione del metodo base per eseguire l'azione"""
        return self.perform_click(mouse_position)


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
        
        # Inizializzazione delle classi
        self.calibration = Calibration_action()
        self.nose_joystick = NoseJoystick_event()
        self.mouse_cursor = MouseCursor_action(self.screen_w, self.screen_h)
        
        # Dizionario per le associazioni evento-azione
        self.event_action_mappings = []
        
        # Stato applicazione
        self.show_window = show_window
        self.paused = False
        
        print("=== HEAD MOUSE CONTROLLER ===")
        print("Click sinistro: occhio sinistro | Click destro: occhio destro")
        print("Punto di riferimento: punta del naso")

    def add_event_action_mapping(self, event, action, event_args_mapper=None, action_args_mapper=None):
        """Aggiunge un'associazione tra un evento e un'azione"""
        self.event_action_mappings.append({
            'event': event,
            'action': action,
            'event_args_mapper': event_args_mapper or (lambda *args, **kwargs: args),
            'action_args_mapper': action_args_mapper or (lambda *args, **kwargs: args)
        })

    def toggle_pause(self):
        """Metodo per mettere in pausa/riprendere il controllo."""
        self.paused = not self.paused
        status = "PAUSATO" if self.paused else "ATTIVO"
        print(f"Stato cambiato: {status}")

    def process_nose_movement(self, tracking_point):
        """Processa il movimento del naso"""
        # Fase di calibrazione
        if not self.calibration.center_calculated:
            self.calibration.add_sample(tracking_point)
            return
        
        # Controlla se serve auto-ricalibrare
        if self.nose_joystick.should_recalibrate():
            print("Auto-ricalibrazione attivata - naso fuori dalla deadzone troppo a lungo")
            self.calibration.set_new_center(tracking_point)
            self.nose_joystick.reset_outside_timer()
            return
        
        # Ottieni vettore di movimento
        direction, acceleration_factor, effective_distance = self.nose_joystick.get_movement_vector(
            tracking_point, self.calibration.center_position
        )
        
        # Aggiorna posizione cursore
        self.mouse_cursor.update_position(direction, acceleration_factor, effective_distance)

    def process_events(self, tracking_point, landmarks):
        """Processa tutti gli eventi registrati"""
        if self.paused or not self.calibration.center_calculated:
            return
            
        current_mouse_pos = self.mouse_cursor.get_current_position()
        
        for mapping in self.event_action_mappings:
            # Prepara gli argomenti per l'evento
            event_args = mapping['event_args_mapper'](tracking_point, landmarks, current_mouse_pos)
            
            # Verifica se l'evento è attivo
            if mapping['event'].check_event(*event_args):
                # Prepara gli argomenti per l'azione
                action_args = mapping['action_args_mapper'](tracking_point, landmarks, current_mouse_pos)
                
                # Esegui l'azione associata
                mapping['action'].execute(*action_args)

    def draw_interface(self, frame, tracking_point, landmarks=None):
        """Disegna interfaccia utente."""
        if not self.show_window:
            return

        h, w = frame.shape[:2]

        if not self.calibration.center_calculated:
            # Fase calibrazione
            cv2.circle(frame, tuple(tracking_point.astype(int)), 15, (0, 165, 255), 3)
            progress = len(self.calibration.center_samples)
            percentage = int((progress / self.calibration.max_center_samples) * 100)
            
            cv2.putText(frame, f"CALIBRAZIONE: {percentage}%", 
                       (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
        else:
            # Stato attivo
            color = (128, 128, 128) if self.paused else (0, 255, 0)
            
            # Punto tracking
            cv2.circle(frame, tuple(tracking_point.astype(int)), 8, color, -1)
            
            # Centro e deadzone
            if self.calibration.center_position is not None:
                center_pt = tuple(self.calibration.center_position.astype(int))
                cv2.circle(frame, center_pt, int(self.nose_joystick.deadzone_radius), (255, 255, 0), 2)
                
                # Freccia movimento se fuori deadzone
                if (self.nose_joystick.is_outside_deadzone(tracking_point, self.calibration.center_position) 
                    and not self.paused):
                    cv2.arrowedLine(frame, center_pt, tuple(tracking_point.astype(int)), (0, 255, 255), 3)
                    
                    # Mostra zona accelerazione
                    cv2.circle(frame, center_pt, int(self.nose_joystick.max_acceleration_distance), (0, 100, 255), 1)

            # Indicatori occhi (se presenti tra gli eventi registrati)
            if landmarks is not None and not self.paused:
                for mapping in self.event_action_mappings:
                    if isinstance(mapping['event'], LeftEye_event):
                        left_eye_top = landmarks[mapping['event'].LEFT_EYE_TOP].astype(int)
                        left_eye_bottom = landmarks[mapping['event'].LEFT_EYE_BOTTOM].astype(int)
                        left_eye_color = (0, 0, 255) if mapping['event'].is_eye_closed() else (0, 255, 0)
                        cv2.line(frame, tuple(left_eye_top), tuple(left_eye_bottom), left_eye_color, 3)
                        cv2.putText(frame, "L", (left_eye_top[0] - 15, left_eye_top[1] - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, left_eye_color, 2)
                    
                    if isinstance(mapping['event'], RightEye_event):
                        right_eye_top = landmarks[mapping['event'].RIGHT_EYE_TOP].astype(int)
                        right_eye_bottom = landmarks[mapping['event'].RIGHT_EYE_BOTTOM].astype(int)
                        right_eye_color = (255, 0, 0) if mapping['event'].is_eye_closed() else (0, 255, 0)
                        cv2.line(frame, tuple(right_eye_top), tuple(right_eye_bottom), right_eye_color, 3)
                        cv2.putText(frame, "R", (right_eye_top[0] + 10, right_eye_top[1] - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, right_eye_color, 2)

            # Status
            status_text = "PAUSATO" if self.paused else "ATTIVO"
            status_color = (0, 0, 255) if self.paused else (0, 255, 0)
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Info sensibilità
            cv2.putText(frame, f"Sensibilita: {self.mouse_cursor.base_sensitivity:.1f}", 
                       (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Controlli aggiornati
        controls = [
            "=== CONTROLLI ===",
            "SPAZIO = Pausa/Riprendi",
            "+/- = Modifica sensibilità",
            "R = Reset calibrazione",
            "ESC = Esci",
            "Auto-ricalibrazioni dopo 5s fuori deadzone"
        ]
        
        y_start = h - len(controls) * 20 - 10
        for i, control in enumerate(controls):
            if i == 0:
                color, weight = (255, 255, 0), 2
            elif i == len(controls) - 1:
                color, weight = (255, 165, 0), 1  # Arancione per l'auto-ricalibrazione
            else:
                color, weight = (255, 255, 255), 1
                
            cv2.putText(frame, control, (20, y_start + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, weight)


def main():
    print("=== HEAD MOUSE CONTROLLER ===")
    
    # Scelta modalità display
    while True:
        choice = input("Mostrare finestra webcam? (s/n): ").lower().strip()
        if choice in ['s', 'n']:
            show_window = choice == 's'
            break
        print("Inserisci 's' per sì o 'n' per no")

    controller = HeadMouseController(show_window=show_window)
    
    # Creazione delle istanze di eventi e azioni
    nose_joystick = NoseJoystick_event()
    mouse_cursor = MouseCursor_action(controller.screen_w, controller.screen_h)
    left_eye = LeftEye_event()
    left_click = LeftClick_action()
    right_eye = RightEye_event()
    right_click = RightClick_action()
    
    # Configurazione delle associazioni evento-azione
    controller.add_event_action_mapping(
        event=nose_joystick,
        action=mouse_cursor,
        event_args_mapper=lambda tp, lm, mp: (tp, controller.calibration.center_position),
        action_args_mapper=lambda tp, lm, mp: nose_joystick.get_movement_vector(tp, controller.calibration.center_position)
    )
    
    controller.add_event_action_mapping(
        event=left_eye,
        action=left_click,
        event_args_mapper=lambda tp, lm, mp: (lm,),
        action_args_mapper=lambda tp, lm, mp: (mp,)
    )
    
    controller.add_event_action_mapping(
        event=right_eye,
        action=right_click,
        event_args_mapper=lambda tp, lm, mp: (lm,),
        action_args_mapper=lambda tp, lm, mp: (mp,)
    )
    
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
    print("⚡ Auto-ricalibrazione dopo 5 secondi fuori dalla deadzone")
    
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
                
                if not controller.paused:
                    # Processa movimento del naso (calibrazione)
                    controller.process_nose_movement(tracking_point)
                    
                    # Processa tutti gli eventi registrati
                    controller.process_events(tracking_point, landmarks_np)

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
                    controller.mouse_cursor.adjust_sensitivity(0.2)
                elif key == ord('-'):  # -
                    controller.mouse_cursor.adjust_sensitivity(-0.2)
                elif key == ord('r'):  # R
                    controller.calibration.reset_calibration()
                    controller.nose_joystick.reset_outside_timer()
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