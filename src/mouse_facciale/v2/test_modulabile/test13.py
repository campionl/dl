import cv2
import mediapipe as mp
import numpy as np
import pynput.mouse as mouse
import time
import sys
from collections import deque
import threading
import subprocess
import platform
import pyautogui # For screen size and initial mouse position

# --- Funzione per disabilitare l'accelerazione del mouse di sistema su Linux ---
def disable_system_mouse_acceleration():
    """
    Tenta di disabilitare l'accelerazione del mouse a livello di sistema su Linux (Xorg).
    Questo è importante per evitare che il movimento del nostro mouse virtuale
    entri in conflitto con l'accelerazione del sistema, rendendo il controllo imprevedibile.
    """
    if platform.system() == "Linux":
        try:
            output = subprocess.check_output(["xinput", "--list", "--short"]).decode("utf-8")
            mouse_id = None
            for line in output.splitlines():
                if "pointer" in line and "mouse" in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.startswith("id="):
                            mouse_id = part.split("=")[1]
                            break
                if mouse_id:
                    break

            if mouse_id:
                try:
                    subprocess.run(["xinput", "--set-prop", mouse_id, "libinput Accel Profile Enabled", "0, 1"], check=True)
                    subprocess.run(["xinput", "--set-prop", mouse_id, "libinput Accel Speed", "0"], check=True)
                    print(f"Probabilmente l'accelerazione del mouse è stata disabilitata per il mouse ID {mouse_id} (libinput).")
                except subprocess.CalledProcessError:
                    print(f"Impostazioni libinput non riuscite per ID {mouse_id}. Tentativo con proprietà generiche...")
                    device_props = subprocess.check_output(["xinput", "--list-props", mouse_id]).decode("utf-8")
                    
                    if "Device Accel Profile" in device_props:
                        try:
                            subprocess.run(["xinput", "--set-prop", mouse_id, "Device Accel Profile", "0"], check=True)
                            print(f"Disabilitato 'Device Accel Profile' per mouse ID {mouse_id}.")
                        except subprocess.CalledProcessError as e:
                            print(f"Non è stato possibile impostare 'Device Accel Profile': {e}")

                    if "Device Accel Velocity Scaling" in device_props:
                        try:
                            subprocess.run(["xinput", "--set-prop", mouse_id, "Device Accel Velocity Scaling", "1.0"], check=True)
                            print(f"Impostato 'Device Accel Velocity Scaling' a 1.0 per mouse ID {mouse_id}.")
                        except subprocess.CalledProcessError as e:
                            print(f"Non è stato possibile impostare 'Device Accel Velocity Scaling': {e}")
            else:
                print("Non è stato possibile trovare un ID del dispositivo mouse per disabilitare l'accelerazione.")
        except subprocess.CalledProcessError as e:
            print(f"Errore durante la disabilitazione dell'accelerazione del mouse di sistema: {e}. 'xinput' potrebbe non essere installato o mancano i permessi.")
            print("Assicurati che 'xinput' sia installato (es. sudo apt install xinput o sudo pacman -S xorg-xinput).")
        except FileNotFoundError:
            print("Avviso: Comando 'xinput' non trovato. Impossibile disabilitare l'accelerazione del mouse di sistema.")
            print("Assicurati che 'xinput' sia installato (es. sudo apt install xinput o sudo pacman -S xorg-xinput).")
    else:
        print("Il sistema non è Linux, saltando la disabilitazione dell'accelerazione del mouse di sistema.")


class BaseEvent:
    """Classe base per tutti gli eventi (es. bocca aperta, occhio chiuso)"""
    def check_event(self, *args, **kwargs):
        """Metodo astratto per verificare se l'evento è attivo (da implementare nelle sottoclassi)"""
        raise NotImplementedError


class BaseAction:
    """Classe base per tutte le azioni (es. muovi cursore, click)"""
    def execute(self, *args, **kwargs):
        """Metodo astratto per eseguire l'azione (da implementare nelle sottoclassi)"""
        raise NotImplementedError


class CalibrationAction:
    """Classe per gestire la calibrazione del centro del viso (punto neutro del naso)"""
    def __init__(self, max_samples=30):
        self.center_samples = []
        self.max_center_samples = max_samples
        self.center_calculated = False
        self.center_position = None
    
    def add_sample(self, tracking_point):
        """Aggiunge un campione di posizione del naso per la calibrazione"""
        if not self.center_calculated:
            self.center_samples.append(tracking_point.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                self.center_position = np.median(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"Centro calibrato: {self.center_position}")
                return True
        return False
    
    def reset_calibration(self):
        """Resetta la calibrazione, permettendo di rifarla"""
        self.center_calculated = False
        self.center_samples = []
        self.center_position = None
        print("Calibrazione resettata")
    
    def set_new_center(self, new_center):
        """Imposta un nuovo centro direttamente (usato per l'auto-ricalibrazione)"""
        self.center_position = new_center.copy()
        self.center_calculated = True
        self.center_samples = [new_center] * self.max_center_samples
        print(f"Nuovo centro impostato manualmente/auto: {self.center_position}")


class NoseJoystickEvent(BaseEvent):
    """Classe per rilevare il movimento del naso come un joystick"""
    def __init__(self, deadzone_radius=15.0, max_acceleration_distance=100.0):
        self.deadzone_radius = deadzone_radius
        self.max_acceleration_distance = max_acceleration_distance
        self.outside_deadzone_start_time = None
        self.edge_time_start = None
        self.edge_timeout = 5.0
    
    def is_outside_deadzone(self, tracking_point, center_position):
        """Controlla se il punto del naso è fuori dalla zona morta"""
        if center_position is None:
            return False
        
        offset = tracking_point - center_position
        distance = np.linalg.norm(offset)
        return distance >= self.deadzone_radius
    
    def get_movement_vector(self, tracking_point, center_position):
        """
        Calcola la direzione e l'accelerazione del movimento del cursore
        basate sulla posizione del naso rispetto al centro.
        """
        if center_position is None:
            return None, 0, 0
        
        offset = tracking_point - center_position
        distance = np.linalg.norm(offset)
        
        if distance < self.deadzone_radius:
            self.outside_deadzone_start_time = None
            return None, 0, 0
        
        current_time = time.time()
        if self.outside_deadzone_start_time is None:
            self.outside_deadzone_start_time = current_time
        
        effective_distance = distance - self.deadzone_radius
        normalized_distance = min(effective_distance / (self.max_acceleration_distance - self.deadzone_radius), 1.0)
        
        acceleration_factor = 1.0 + (7.0 * normalized_distance ** 3) 
        
        direction = offset / distance
        
        return direction, acceleration_factor, effective_distance
    
    def is_cursor_on_edge(self, cursor_position, screen_w, screen_h, edge_threshold=40):
        """Verifica se il cursore è sul bordo dello schermo per l'auto-ricalibrazione"""
        x, y = cursor_position
        return (x <= edge_threshold or x >= screen_w - edge_threshold or 
                y <= edge_threshold or y >= screen_h - edge_threshold)
    
    def should_recalibrate(self, cursor_position, screen_w, screen_h):
        """
        Controlla se è necessario ricalibrare automaticamente perché il cursore
        è rimasto sul bordo troppo a lungo.
        """
        current_time = time.time()
        
        if self.is_cursor_on_edge(cursor_position, screen_w, screen_h):
            if self.edge_time_start is None:
                self.edge_time_start = current_time
            elif current_time - self.edge_time_start >= self.edge_timeout:
                return True
        else:
            self.edge_time_start = None
        
        return False
    
    def reset_outside_timer(self):
        """Resetta il timer per il tempo trascorso fuori dalla deadzone e il timer del bordo"""
        self.outside_deadzone_start_time = None
        self.edge_time_start = None
    
    def check_event(self, tracking_point, center_position):
        """Controlla se il naso è fuori dalla deadzone (base per il movimento del cursore)"""
        return self.is_outside_deadzone(tracking_point, center_position)


class OpenMouthEvent(BaseEvent):
    """Classe per rilevare l'apertura della bocca"""
    def __init__(self, upper_lip_index=13, lower_lip_index=14, threshold=0.15, duration=0.5):
        self.UPPER_LIP = upper_lip_index
        self.LOWER_LIP = lower_lip_index
        self.open_threshold = threshold
        self.open_duration_required = duration
        self.open_start_time = None
        self.mouth_open = False
        self.event_detected = False
        self.mouth_history = deque(maxlen=3)
        self.neutral_mouth_y = None
    
    def calculate_mouth_openness(self, landmarks):
        """Calcola l'apertura della bocca basandosi sulla distanza verticale delle labbra"""
        try:
            upper_lip = landmarks[self.UPPER_LIP]
            lower_lip = landmarks[self.LOWER_LIP]
            openness = abs(upper_lip[1] - lower_lip[1]) / 25.0
            return openness
        except IndexError:
            return 0.0
            
    def get_vertical_offset(self, landmarks):
        """
        Calcola l'offset verticale del centro della bocca rispetto a una posizione neutra.
        Usato per lo scrolling con la bocca.
        """
        try:
            upper_lip_y = landmarks[self.UPPER_LIP][1]
            lower_lip_y = landmarks[self.LOWER_LIP][1]
            current_mouth_center_y = (upper_lip_y + lower_lip_y) / 2
            
            if self.neutral_mouth_y is None and not self.mouth_open:
                self.neutral_mouth_y = current_mouth_center_y 
                return 0.0
            
            return current_mouth_center_y - self.neutral_mouth_y
        except IndexError:
            return 0.0

    def detect_open_mouth(self, landmarks):
        """Rileva l'apertura della bocca solo se mantenuta per il tempo richiesto"""
        openness = self.calculate_mouth_openness(landmarks)
        self.mouth_history.append(openness)
        
        stable_openness = np.mean(list(self.mouth_history)) if self.mouth_history else openness
        current_time = time.time()
        
        if stable_openness > self.open_threshold:
            if not self.mouth_open and not self.event_detected:
                self.mouth_open = True
                self.open_start_time = current_time
            elif (self.mouth_open and 
                  not self.event_detected and 
                  self.open_start_time is not None and 
                  current_time - self.open_start_time >= self.open_duration_required):
                self.event_detected = True
                return True
        else:
            if self.mouth_open:
                self.mouth_open = False
                self.open_start_time = None
                self.event_detected = False
                self.neutral_mouth_y = None
        
        return False
    
    def is_mouth_open(self):
        """Restituisce se la bocca è attualmente aperta (anche se l'evento non è ancora scattato)"""
        return self.mouth_open
    
    def check_event(self, landmarks):
        """Verifica l'evento di bocca aperta"""
        return self.detect_open_mouth(landmarks)


class ToggleModeAction(BaseAction):
    """Classe per cambiare modalità tra puntatore e scroll"""
    def __init__(self):
        self.last_switch_time = 0
        self.switch_cooldown = 1.0
    
    def switch_mode(self, current_mode):
        """Cambia la modalità del mouse da 'pointer' a 'scroll' e viceversa"""
        current_time = time.time()
        if current_time - self.last_switch_time < self.switch_cooldown:
            return current_mode
        
        new_mode = 'scroll' if current_mode == 'pointer' else 'pointer'
        print(f"Modalità cambiata: {new_mode}")
        self.last_switch_time = current_time
        return new_mode
    
    def execute(self, current_mode):
        """Esegue l'azione di cambio modalità"""
        return self.switch_mode(current_mode)


class MouseCursorAction(BaseAction):
    """Classe per tradurre il movimento del naso in movimento del cursore del mouse"""
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.current_mouse_pos = np.array([screen_w // 2, screen_h // 2], dtype=float)
        self.position_history = deque(maxlen=5)
        self.mouse_lock = threading.Lock()
        self.base_sensitivity = 6.0
        
        self.mouse_controller = mouse.Controller()
        self.mouse_controller.position = (self.current_mouse_pos[0], self.current_mouse_pos[1])

    def update_position(self, direction, acceleration_factor, effective_distance):
        """Aggiorna la posizione del cursore basandosi sulla direzione e l'accelerazione del naso"""
        if direction is None:
            return

        movement_x = direction[0] * self.base_sensitivity * acceleration_factor * effective_distance * 0.2
        movement_y = direction[1] * self.base_sensitivity * acceleration_factor * effective_distance * 0.2

        current_sys_x, current_sys_y = self.mouse_controller.position
        
        border_force_strength = 25.0
        border_threshold = 40

        if current_sys_x <= border_threshold:
            movement_x += border_force_strength * (1 - (current_sys_x / border_threshold))
        elif current_sys_x >= self.screen_w - border_threshold:
            movement_x -= border_force_strength * (1 - ((self.screen_w - current_sys_x) / border_threshold))

        if current_sys_y <= border_threshold:
            movement_y += border_force_strength * (1 - (current_sys_y / border_threshold))
        elif current_sys_y >= self.screen_h - border_threshold:
            movement_y -= border_force_strength * (1 - ((self.screen_h - current_sys_y) / border_threshold))

        self.position_history.append(np.array([movement_x, movement_y]))

        if len(self.position_history) > 1:
            smoothed_movement = np.mean(self.position_history, axis=0)
        else:
            smoothed_movement = np.array([movement_x, movement_y])

        with self.mouse_lock:
            try:
                self.mouse_controller.move(int(smoothed_movement[0]), int(smoothed_movement[1]))
            except Exception as e:
                print(f"Errore durante il movimento del cursore: {e}")

    def freeze_position(self):
        """Blocca la posizione corrente del cursore"""
        with self.mouse_lock:
            system_pos = self.mouse_controller.position
            self.current_mouse_pos = np.array([system_pos[0], system_pos[1]], dtype=float)

    def set_position(self, new_position):
        """Imposta direttamente una nuova posizione del cursore (usato per riportarlo al centro)"""
        with self.mouse_lock:
            self.current_mouse_pos = new_position.copy()
            try:
                self.mouse_controller.position = (int(new_position[0]), int(new_position[1]))
            except Exception as e:
                print(f"Errore durante l'impostazione diretta della posizione: {e}")

    def enforce_position(self):
        """Mantiene forzatamente la posizione corrente"""
        with self.mouse_lock:
            try:
                self.mouse_controller.position = (int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1]))
            except Exception as e:
                print(f"Errore durante il mantenimento della posizione: {e}")

    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità del puntatore"""
        self.base_sensitivity = np.clip(self.base_sensitivity + amount, 0.5, 12.0)
        print(f"Sensibilità puntatore aggiornata: {self.base_sensitivity:.1f}")

    def get_current_position(self):
        """Restituisce la posizione attuale del cursore di sistema"""
        with self.mouse_lock:
            system_pos = self.mouse_controller.position
            self.current_mouse_pos = np.array([system_pos[0], system_pos[1]], dtype=float)
            return self.current_mouse_pos.copy()

    def execute(self, direction, acceleration_factor, effective_distance):
        """Esegue l'azione di movimento del cursore"""
        self.update_position(direction, acceleration_factor, effective_distance)


class ScrollAction(BaseAction):
    """Classe per eseguire lo scrolling della pagina"""
    def __init__(self, scroll_cooldown=0.03):
        self.scroll_cooldown = scroll_cooldown
        self.last_scroll_time = 0
        self.scroll_lock = threading.Lock()
        self.scroll_sensitivity = 3.0
        self.scroll_history = deque(maxlen=3)
        self.mouse_controller = mouse.Controller()
    
    def perform_scroll(self, direction, effective_distance):
        """Esegue lo scrolling"""
        current_time = time.time()
        if current_time - self.last_scroll_time < self.scroll_cooldown:
            return False
        
        try:
            with self.scroll_lock:
                scroll_amount = -direction[1] * effective_distance * 0.1 * self.scroll_sensitivity
                self.scroll_history.append(scroll_amount)
                smoothed_scroll = np.mean(self.scroll_history) if self.scroll_history else scroll_amount
                
                scroll_value = int(smoothed_scroll)
                if abs(scroll_value) > 0:
                    self.mouse_controller.scroll(0, scroll_value)
                    self.last_scroll_time = current_time
                    return True
        except Exception as e:
            print(f"Errore durante lo scrolling: {e}")
        return False
    
    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità dello scrolling"""
        self.scroll_sensitivity = np.clip(self.scroll_sensitivity + amount, 1.0, 20.0)
        print(f"Sensibilità scrolling aggiornata: {self.scroll_sensitivity:.1f}")
    
    def execute(self, direction, effective_distance):
        """Esegue l'azione di scrolling"""
        return self.perform_scroll(direction, effective_distance)


class LeftEyeEvent(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio sinistro (blink)"""
    def __init__(self, top_index=159, bottom_index=145, blink_duration=0.3):
        self.LEFT_EYE_TOP = top_index
        self.LEFT_EYE_BOTTOM = bottom_index
        self.blink_threshold = 0.10
        self.blink_duration_required = blink_duration
        self.blink_start_time = None
        self.eye_closed = False
        self.blink_detected = False
        self.ear_history = deque(maxlen=3)
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calcola il 'Eye Aspect Ratio' (EAR) per l'occhio sinistro"""
        try:
            top = landmarks[self.LEFT_EYE_TOP]
            bottom = landmarks[self.LEFT_EYE_BOTTOM]
            ear = abs(top[1] - bottom[1]) / 25.0
            return ear
        except IndexError:
            return 0.2
    
    def detect_blink(self, landmarks):
        """Rileva il blink dell'occhio sinistro solo se chiuso per il tempo richiesto"""
        ear = self.calculate_eye_aspect_ratio(landmarks)
        self.ear_history.append(ear)
        
        stable_ear = np.mean(list(self.ear_history)) if self.ear_history else ear
        current_time = time.time()
        
        if stable_ear < self.blink_threshold:
            if not self.eye_closed and not self.blink_detected:
                self.eye_closed = True
                self.blink_start_time = current_time
            elif (self.eye_closed and 
                  not self.blink_detected and 
                  self.blink_start_time is not None and 
                  current_time - self.blink_start_time >= self.blink_duration_required):
                self.blink_detected = True
                return True
        else:
            if self.eye_closed:
                self.eye_closed = False
                self.blink_start_time = None
                self.blink_detected = False
        
        return False
    
    def is_eye_closed(self):
        """Restituisce se l'occhio è attualmente chiuso (anche se il blink non è ancora scattato)"""
        return self.eye_closed
    
    def check_event(self, landmarks):
        """Verifica l'evento di blink dell'occhio sinistro"""
        return self.detect_blink(landmarks)


class LeftClickAction(BaseAction):
    """Classe per eseguire un click sinistro del mouse"""
    def __init__(self, click_cooldown=0.5):
        self.click_cooldown = click_cooldown
        self.last_click_time = 0
        self.mouse_lock = threading.Lock()
        self.mouse_controller = mouse.Controller()
    
    def perform_click(self, mouse_position):
        """Esegue il click sinistro alla posizione attuale del cursore di sistema"""
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            with self.mouse_lock:
                self.mouse_controller.click(mouse.Button.left)
            print(f"Click SINISTRO")
            self.last_click_time = current_time
            return True
        except Exception as e:
            print(f"Errore click sinistro: {e}")
            return False
    
    def execute(self, mouse_position):
        """Esegue l'azione di click sinistro"""
        return self.perform_click(mouse_position)


class RightEyeEvent(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio destro (blink)"""
    def __init__(self, top_index=386, bottom_index=374, blink_duration=0.3):
        self.RIGHT_EYE_TOP = top_index
        self.RIGHT_EYE_BOTTOM = bottom_index
        self.blink_threshold = 0.10
        self.blink_duration_required = blink_duration
        self.blink_start_time = None
        self.eye_closed = False
        self.blink_detected = False
        self.ear_history = deque(maxlen=3)
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calcola l'EAR per l'occhio destro"""
        try:
            top = landmarks[self.RIGHT_EYE_TOP]
            bottom = landmarks[self.RIGHT_EYE_BOTTOM]
            ear = abs(top[1] - bottom[1]) / 25.0
            return ear
        except IndexError:
            return 0.2
    
    def detect_blink(self, landmarks):
        """Rileva il blink dell'occhio destro solo se chiuso per il tempo richiesto"""
        ear = self.calculate_eye_aspect_ratio(landmarks)
        self.ear_history.append(ear)
        
        stable_ear = np.mean(list(self.ear_history)) if self.ear_history else ear
        current_time = time.time()
        
        if stable_ear < self.blink_threshold:
            if not self.eye_closed and not self.blink_detected:
                self.eye_closed = True
                self.blink_start_time = current_time
            elif (self.eye_closed and 
                  not self.blink_detected and 
                  self.blink_start_time is not None and 
                  current_time - self.blink_start_time >= self.blink_duration_required):
                self.blink_detected = True
                return True
        else:
            if self.eye_closed:
                self.eye_closed = False
                self.blink_start_time = None
                self.blink_detected = False
        
        return False
    
    def is_eye_closed(self):
        """Restituisce se l'occhio è attualmente chiuso"""
        return self.eye_closed
    
    def check_event(self, landmarks):
        """Verifica l'evento di blink dell'occhio destro"""
        return self.detect_blink(landmarks)


class RightClickAction(BaseAction):
    """Classe per eseguire un click destro del mouse"""
    def __init__(self, click_cooldown=0.5):
        self.click_cooldown = click_cooldown
        self.last_click_time = 0
        self.mouse_lock = threading.Lock()
        self.mouse_controller = mouse.Controller()
    
    def perform_click(self, mouse_position):
        """Esegue il click destro alla posizione attuale del cursore di sistema"""
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            with self.mouse_lock:
                self.mouse_controller.click(mouse.Button.right)
            print(f"Click DESTRO")
            self.last_click_time = current_time
            return True
        except Exception as e:
            print(f"Errore click destro: {e}")
            return False
    
    def execute(self, mouse_position):
        """Esegue l'azione di click destro"""
        return self.perform_click(mouse_position)


class HeadMouseController:
    """Classe principale che gestisce il mouse facciale"""
    def __init__(self, show_window=False, user_config=None):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )

        self.screen_w, self.screen_h = pyautogui.size()

        self.NOSE_TIP = 4
        self.UPPER_LIP = 13
        self.LOWER_LIP = 14
        
        self.calibration = CalibrationAction()
        self.nose_joystick = NoseJoystickEvent(max_acceleration_distance=100.0)
        self.mouse_cursor = MouseCursorAction(self.screen_w, self.screen_h)
        self.scroll_action = ScrollAction()
        self.open_mouth_event = OpenMouthEvent(self.UPPER_LIP, self.LOWER_LIP)
        self.toggle_mode_action = ToggleModeAction()
        self.left_eye_event = LeftEyeEvent()
        self.right_eye_event = RightEyeEvent()
        self.left_click_action = LeftClickAction()
        self.right_click_action = RightClickAction()
        
        self.user_config = user_config if user_config else {}
        self.scroll_direction_source = self.user_config.get('scroll_direction', 'nose up/down')

        self.event_action_mappings = []
        self.setup_event_action_mappings()
        
        self.show_window = show_window
        self.paused = False
        self.current_mode = 'pointer'
        self.last_mouse_pos_before_scroll = None

        self.status_lock = threading.Lock()
        self.current_status = self.get_current_status()

        # Webcam setup (moved here for thread management)
        self.cap = None
        self.video_frame = None
        self.processing_thread = None
        self.running = False

    def add_event_action_mapping(self, event, action, event_args_mapper, action_args_mapper):
        self.event_action_mappings.append({
            'event': event,
            'action': action,
            'event_args_mapper': event_args_mapper,
            'action_args_mapper': action_args_mapper
        })

    def setup_event_action_mappings(self):
        self.event_action_mappings = []

        self.add_event_action_mapping(
            event=self.nose_joystick,
            action=self.mouse_cursor,
            event_args_mapper=lambda tp, lm, mp: (tp, self.calibration.center_position),
            action_args_mapper=lambda tp, lm, mp: self.nose_joystick.get_movement_vector(tp, self.calibration.center_position)
        )

        if self.user_config.get('left_click') == 'right eye':
            self.add_event_action_mapping(self.right_eye_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        elif self.user_config.get('left_click') == 'left eye':
            self.add_event_action_mapping(self.left_eye_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        elif self.user_config.get('left_click') == 'mouth open':
            self.add_event_action_mapping(self.open_mouth_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))

        if self.user_config.get('right_click') == 'right eye':
            self.add_event_action_mapping(self.right_eye_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        elif self.user_config.get('right_click') == 'left eye':
            self.add_event_action_mapping(self.left_eye_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        elif self.user_config.get('right_click') == 'mouth open':
            self.add_event_action_mapping(self.open_mouth_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        
        if self.user_config.get('mode_switch') == 'right eye':
            self.add_event_action_mapping(self.right_eye_event, self.toggle_mode_action,
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (self.current_mode,))
        elif self.user_config.get('mode_switch') == 'left eye':
            self.add_event_action_mapping(self.left_eye_event, self.toggle_mode_action,
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (self.current_mode,))
        elif self.user_config.get('mode_switch') == 'mouth open':
            self.add_event_action_mapping(self.open_mouth_event, self.toggle_mode_action,
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (self.current_mode,))

    def start_webcam(self):
        """Initializes and starts the webcam in a separate thread."""
        if self.running:
            print("Webcam already running.")
            return False

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Errore: Webcam non trovata!")
            self.cap = None
            return False
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # <--- NUOVA IMPOSTAZIONE PER RIDURRE LA LATENZA

        self.running = True
        self.processing_thread = threading.Thread(target=self._process_video_feed)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        print("Webcam thread started.")
        return True

    def stop_webcam(self):
        """Stops the webcam and processing thread."""
        if self.running:
            self.running = False
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
                print("Webcam thread stopped.")
            if self.cap:
                self.cap.release()
                self.cap = None
        print("Webcam stopped.")

    def _process_video_feed(self):
        """Internal method to process video frames."""
        print("Processing video feed...")
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Impossibile leggere il frame dalla webcam.")
                break

            frame = cv2.flip(frame, 1)
            self.video_frame = frame.copy()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                tracking_point = landmarks_np[self.NOSE_TIP]
                
                if not self.paused:
                    self.process_nose_movement(tracking_point)
                    self.process_events(tracking_point, landmarks_np)
                
                self.update_web_status(tracking_point, landmarks_np)
            else:
                self.update_web_status(None, None, face_detected=False)

            time.sleep(0.01)
        print("_process_video_feed loop ended.")
        if self.cap:
            self.cap.release()
        self.cap = None

    # --- Methods for Web Interaction ---
    def toggle_pause(self):
        """Toggles the paused state."""
        self.paused = not self.paused
        print(f"Applicazione {'in pausa' if self.paused else 'ripresa'}")
        self.update_web_status()
        return {'paused': self.paused}

    def reset_mouse_position(self):
        """Resets the mouse cursor to the center of the screen."""
        center_x, center_y = self.screen_w // 2, self.screen_h // 2
        self.mouse_cursor.set_position(np.array([center_x, center_y], dtype=float))
        print("Posizione mouse resettata al centro.")
        self.update_web_status()
        return {'success': True, 'message': 'Mouse position reset.'}

    def reset_calibration(self):
        """Resets the facial calibration."""
        self.calibration.reset_calibration()
        self.nose_joystick.reset_outside_timer()
        self.reset_mouse_position()
        if isinstance(self.open_mouth_event, OpenMouthEvent):
            self.open_mouth_event.neutral_mouth_y = None
        print("Calibrazione resettata.")
        self.update_web_status()
        return {'success': True, 'message': 'Calibration reset.'}

    def adjust_pointer_sensitivity(self, amount):
        """Adjusts the pointer sensitivity."""
        self.mouse_cursor.adjust_sensitivity(amount)
        self.update_web_status()
        return {'sensitivity': self.mouse_cursor.base_sensitivity}

    def adjust_scroll_sensitivity(self, amount):
        """Adjusts the scroll sensitivity."""
        self.scroll_action.adjust_sensitivity(amount)
        self.update_web_status()
        return {'scroll_sensitivity': self.scroll_action.scroll_sensitivity}

    def set_mode(self, mode):
        """Sets the current operating mode (pointer/scroll)."""
        if mode not in ['pointer', 'scroll']:
            return {'success': False, 'message': 'Invalid mode.'}
        
        if self.current_mode != mode:
            print(f"Modalità impostata a: {mode}")
            self.current_mode = mode
            if self.current_mode == 'scroll':
                self.last_mouse_pos_before_scroll = self.mouse_cursor.get_current_position().copy()
                self.mouse_cursor.freeze_position()
            elif self.current_mode == 'pointer':
                if self.last_mouse_pos_before_scroll is not None:
                    self.mouse_cursor.set_position(self.last_mouse_pos_before_scroll)
                if isinstance(self.open_mouth_event, OpenMouthEvent):
                    self.open_mouth_event.neutral_mouth_y = None
            self.update_web_status()
        return {'current_mode': self.current_mode}

    def get_current_status(self):
        """Returns the current status of the controller for the web interface."""
        with self.status_lock:
            status = {
                'paused': self.paused,
                'current_mode': self.current_mode,
                'sensitivity': float(f"{self.mouse_cursor.base_sensitivity:.1f}"),
                'scroll_sensitivity': float(f"{self.scroll_action.scroll_sensitivity:.1f}"),
                'calibration_done': self.calibration.center_calculated,
                'face_detected': True
            }
            self.current_status = status
            return status

    def update_web_status(self, tracking_point=None, landmarks_np=None, face_detected=True):
        """Updates the internal status dictionary for the web interface."""
        with self.status_lock:
            self.current_status['paused'] = self.paused
            self.current_status['current_mode'] = self.current_mode
            self.current_status['sensitivity'] = float(f"{self.mouse_cursor.base_sensitivity:.1f}")
            self.current_status['scroll_sensitivity'] = float(f"{self.scroll_action.scroll_sensitivity:.1f}")
            self.current_status['calibration_done'] = self.calibration.center_calculated
            self.current_status['face_detected'] = face_detected
            
            if tracking_point is not None and landmarks_np is not None:
                h, w = self.video_frame.shape[:2] if self.video_frame is not None else (480, 640)
                
                nose_x, nose_y = tracking_point[0], tracking_point[1]

                self.current_status['nose_pos'] = {'x': int(nose_x), 'y': int(nose_y)}
                self.current_status['center_pos'] = {'x': int(self.calibration.center_position[0]), 'y': int(self.calibration.center_position[1])} if self.calibration.center_position is not None else None
                self.current_status['deadzone_radius'] = self.nose_joystick.deadzone_radius
                self.current_status['max_acceleration_distance'] = self.nose_joystick.max_acceleration_distance
                
                self.current_status['left_eye_closed'] = self.left_eye_event.is_eye_closed()
                self.current_status['right_eye_closed'] = self.right_eye_event.is_eye_closed()
                self.current_status['mouth_open'] = self.open_mouth_event.is_mouth_open()

                self.current_status['landmarks'] = [{'x': int(lm[0]), 'y': int(lm[1])} for lm in landmarks_np]
            else:
                self.current_status['nose_pos'] = None
                self.current_status['center_pos'] = None
                self.current_status['landmarks'] = None

    def process_nose_movement(self, tracking_point):
        if self.paused or self.current_mode != 'pointer':
            return
            
        if not self.calibration.center_calculated:
            self.calibration.add_sample(tracking_point)
            with self.status_lock:
                self.current_status['calibration_progress'] = int((len(self.calibration.center_samples) / self.calibration.max_center_samples) * 100)
            return
        
        current_mouse_pos = self.mouse_cursor.get_current_position()
        if self.nose_joystick.should_recalibrate(current_mouse_pos, self.screen_w, self.screen_h):
            print("Auto-ricalibrazione attivata - cursore sul bordo per 5 secondi")
            self.calibration.set_new_center(tracking_point)
            self.nose_joystick.reset_outside_timer()
            self.reset_mouse_position()
            return
        
        direction, acceleration_factor, effective_distance = self.nose_joystick.get_movement_vector(
            tracking_point, self.calibration.center_position
        )
        self.mouse_cursor.update_position(direction, acceleration_factor, effective_distance)

    def process_events(self, tracking_point, landmarks):
        if self.paused or not self.calibration.center_calculated:
            return
            
        current_mouse_pos = self.mouse_cursor.get_current_position()

        for mapping in self.event_action_mappings:
            event_instance = mapping['event']
            action_instance = mapping['action']
            
            if isinstance(event_instance, NoseJoystickEvent):
                continue

            event_args = mapping['event_args_mapper'](tracking_point, landmarks, current_mouse_pos)
            
            if event_instance.check_event(*event_args):
                if isinstance(action_instance, ToggleModeAction):
                    old_mode = self.current_mode
                    new_mode = action_instance.execute(self.current_mode)
                    if new_mode != old_mode:
                        self.set_mode(new_mode)
                elif self.current_mode == 'pointer':
                    if isinstance(action_instance, (LeftClickAction, RightClickAction)):
                        action_args = mapping['action_args_mapper'](tracking_point, landmarks, current_mouse_pos)
                        action_instance.execute(*action_args)
        
        if self.current_mode == 'scroll':
            scroll_direction_vector = None
            effective_distance_for_scroll = 0

            if self.scroll_direction_source == 'nose up/down':
                direction, _, effective_distance_for_scroll = self.nose_joystick.get_movement_vector(
                    tracking_point, self.calibration.center_position
                )
                if direction is not None:
                    scroll_direction_vector = np.array([0, direction[1]])
            elif self.scroll_direction_source == 'mouth up/down':
                vertical_offset = self.open_mouth_event.get_vertical_offset(landmarks)
                
                scroll_threshold = 5.0
                if abs(vertical_offset) > scroll_threshold:
                    direction_y = 1 if vertical_offset > 0 else -1
                    scroll_direction_vector = np.array([0, direction_y])
                    effective_distance_for_scroll = abs(vertical_offset)
                else:
                    if not self.open_mouth_event.is_mouth_open():
                        self.open_mouth_event.neutral_mouth_y = None

            elif self.scroll_direction_source == 'eyes up/down (average)':
                print("Scrolling con occhi non ancora implementato completamente.")
                pass
            
            if scroll_direction_vector is not None and effective_distance_for_scroll > 0:
                self.scroll_action.execute(scroll_direction_vector, effective_distance_for_scroll)

disable_system_mouse_acceleration()