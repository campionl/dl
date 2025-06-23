# test13.py
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

# --- Utility function to disable system mouse acceleration on Linux ---
def disable_system_mouse_acceleration():
    """
    Attempts to disable system-wide mouse acceleration on Linux (Xorg).
    This helps prevent conflicts with custom mouse movement.
    """
    if platform.system() == "Linux":
        try:
            # Find the ID of the primary mouse device
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
                # Disable acceleration profiles for the found mouse device
                subprocess.run(["xinput", "--set-prop", mouse_id, "libinput Accel Profile Enabled", "0, 1"], check=True)
                subprocess.run(["xinput", "--set-prop", mouse_id, "libinput Accel Speed", "0"], check=True)
                
                device_props = subprocess.check_output(["xinput", "--list-props", mouse_id]).decode("utf-8")
                
                if "Device Accel Profile" in device_props:
                    try:
                        subprocess.run(["xinput", "--set-prop", mouse_id, "Device Accel Profile", "0"], check=True)
                        print(f"Disabled 'Device Accel Profile' for mouse ID {mouse_id}.")
                    except subprocess.CalledProcessError as e:
                        print(f"Could not set 'Device Accel Profile': {e}")

                if "Device Accel Velocity Scaling" in device_props:
                    try:
                        subprocess.run(["xinput", "--set-prop", mouse_id, "Device Accel Velocity Scaling", "1.0"], check=True)
                        print(f"Set 'Device Accel Velocity Scaling' to 1.0 for mouse ID {mouse_id}.")
                    except subprocess.CalledProcessError as e:
                        print(f"Could not set 'Device Accel Velocity Scaling': {e}")

                print(f"System mouse acceleration likely disabled for mouse ID {mouse_id}.")
            else:
                print("Could not find a mouse device ID to disable acceleration.")
        except subprocess.CalledProcessError as e:
            print(f"Error disabling system mouse acceleration: {e}. 'xinput' might not be installed or permissions are missing.")
            print("Please ensure 'xinput' is installed (e.g., sudo apt install xinput or sudo pacman -S xorg-xinput).")
        except FileNotFoundError:
            print("Warning: 'xinput' command not found. Cannot disable system mouse acceleration.")
            print("Please ensure 'xinput' is installed (e.g., sudo apt install xinput or sudo pacman -S xorg-xinput).")
    else:
        print("System is not Linux, skipping system mouse acceleration disabling.")


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
        self.progress = 0 # Added for web interface

    def add_sample(self, tracking_point):
        """Aggiunge un sample per la calibrazione"""
        if not self.center_calculated:
            self.center_samples.append(tracking_point.copy())
            self.progress = int((len(self.center_samples) / self.max_center_samples) * 100)
            
            if len(self.center_samples) >= self.max_center_samples:
                self.center_position = np.median(self.center_samples, axis=0)
                self.center_calculated = True
                self.progress = 100
                print(f"Centro calibrato: {self.center_position}")
                return True
        return False
    
    def reset_calibration(self):
        """Resetta la calibrazione"""
        self.center_calculated = False
        self.center_samples = []
        self.center_position = None
        self.progress = 0
        print("Calibrazione resettata")
    
    def set_new_center(self, new_center):
        """Imposta un nuovo centro direttamente"""
        self.center_position = new_center.copy()
        self.center_calculated = True
        self.center_samples = [new_center] * self.max_samples # Fill samples to reflect calibrated state
        self.progress = 100
        print(f"Nuovo centro impostato: {self.center_position}")


class NoseJoystick_event(BaseEvent):
    """Classe per rilevare gli eventi del joystick del naso"""
    def __init__(self, deadzone_radius=15.0, max_acceleration_distance=200.0):
        self.deadzone_radius = deadzone_radius
        self.max_acceleration_distance = max_acceleration_distance
        self.outside_deadzone_start_time = None
        self.edge_time_start = None  # Timer per il bordo dello schermo
        self.edge_timeout = 5.0  # 5 secondi sul bordo
    
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
    
    def is_cursor_on_edge(self, cursor_position, screen_w, screen_h, edge_threshold=20):
        """Verifica se il cursore è sul bordo dello schermo"""
        x, y = cursor_position
        # On macOS, the actual reported cursor position might sometimes go slightly negative or beyond screen_w/h
        # when it hits the edge, but for practical purposes, we treat it as being at the edge.
        return (x <= edge_threshold or x >= screen_w - edge_threshold or 
                y <= edge_threshold or y >= screen_h - edge_threshold)
    
    def should_recalibrate(self, cursor_position, screen_w, screen_h):
        """Controlla se è necessario ricalibrare per essere sul bordo troppo a lungo"""
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
        """Resetta il timer per il tempo fuori dalla deadzone"""
        self.outside_deadzone_start_time = None
        self.edge_time_start = None
    
    def check_event(self, tracking_point, center_position):
        """Implementazione del metodo base per verificare l'evento"""
        return self.is_outside_deadzone(tracking_point, center_position)


class OpenMouth_event(BaseEvent):
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
        self.neutral_mouth_y = None # Used for potential vertical scrolling
        self.last_vertical_offset = 0.0 # Store last offset for smoothing scroll

    def calculate_mouth_openness(self, landmarks):
        """Calcola l'apertura della bocca"""
        try:
            upper_lip = landmarks[self.UPPER_LIP]
            lower_lip = landmarks[self.LOWER_LIP]
            # Simple absolute difference is often good enough if threshold is tuned to it.
            openness = abs(upper_lip[1] - lower_lip[1])
            return openness
        except IndexError: # Handle cases where landmarks might be missing
            return 0.0
            
    def get_vertical_offset(self, landmarks):
        """Calcola l'offset verticale del centro della bocca rispetto a una posizione neutra"""
        try:
            upper_lip_y = landmarks[self.UPPER_LIP][1]
            lower_lip_y = landmarks[self.LOWER_LIP][1]
            current_mouth_center_y = (upper_lip_y + lower_lip_y) / 2
            
            # Calibrate neutral position only once when mouth is considered closed/neutral
            if self.neutral_mouth_y is None and not self.mouth_open: # Only set neutral when mouth is NOT open
                self.neutral_mouth_y = current_mouth_center_y
                return 0.0
                
            # If neutral_mouth_y is still None (e.g., app started with mouth open),
            # or if mouth is currently open, don't use it for offset calculation.
            if self.neutral_mouth_y is None:
                return 0.0
                
            offset = current_mouth_center_y - self.neutral_mouth_y
            self.last_vertical_offset = offset # Store for external access if needed
            return offset
        except IndexError:
            return 0.0

    def detect_open_mouth(self, landmarks):
        """Rileva apertura bocca solo se mantenuta per il tempo richiesto"""
        openness = self.calculate_mouth_openness(landmarks)
        self.mouth_history.append(openness)
        
        # Stabilizza con media mobile
        stable_openness = np.mean(list(self.mouth_history)) if self.mouth_history else openness
        current_time = time.time()
        
        # Se la bocca è aperta (sopra la soglia)
        if stable_openness > self.open_threshold:
            if not self.mouth_open and not self.event_detected:
                # Inizia l'apertura
                self.mouth_open = True
                self.open_start_time = current_time
            elif (self.mouth_open and 
                  not self.event_detected and 
                  self.open_start_time is not None and 
                  current_time - self.open_start_time >= self.open_duration_required):
                # Bocca aperta abbastanza a lungo - registra l'evento
                self.event_detected = True
                return True
        else:
            # Bocca chiusa - resetta lo stato
            if self.mouth_open:
                self.mouth_open = False
                self.open_start_time = None
                self.event_detected = False  # Reset per permettere nuovo rilevamento
        
        return False
    
    def is_mouth_open(self):
        """Restituisce se la bocca è attualmente aperta"""
        return self.mouth_open
    
    def check_event(self, landmarks):
        """Implementazione del metodo base per verificare l'evento"""
        return self.detect_open_mouth(landmarks)


class ToggleModeAction(BaseAction): # Renamed for clarity and to wrap the controller's logic
    """Classe per cambiare modalità tra puntatore e scroll, con riferimento al controller."""
    def __init__(self, controller):
        self.controller = controller
        self.last_switch_time = 0
        self.switch_cooldown = 1.0  # 1 secondo di cooldown
    
    def execute(self):
        """Esegue il cambio di modalità."""
        current_time = time.time()
        if current_time - self.last_switch_time < self.switch_cooldown:
            return
        
        self.controller.set_mode('scroll' if self.controller.current_mode == 'pointer' else 'pointer')
        self.last_switch_time = current_time


class MouseCursor_action(BaseAction):
    """Classe per tradurre il movimento del naso in movimento del cursore"""
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.current_mouse_pos = np.array([screen_w // 2, screen_h // 2], dtype=float)
        self.position_history = deque(maxlen=5) # Usato per lo smoothing del movimento
        self.mouse_lock = threading.Lock() # Lock per thread safety
        self.base_sensitivity = 4.0
        
        self.mouse_controller = mouse.Controller() # Initialize pynput controller
        self.mouse_controller.position = (self.current_mouse_pos[0], self.current_mouse_pos[1])
        
        self.platform = platform.system()
        self.stuck_check_interval = 0.5 # How often to check if stuck
        self.last_stuck_check_time = time.time()
        self.last_reported_pos = self.mouse_controller.position


    def update_position(self, direction, acceleration_factor, effective_distance):
        """Aggiorna la posizione del cursore"""
        if direction is None:
            return

        current_time = time.time()

        # macOS specific "unstick" logic if cursor is at the very edge and not moving
        if self.platform == "Darwin" and current_time - self.last_stuck_check_time > self.stuck_check_interval:
            actual_pos = self.mouse_controller.position
            # Check if reported position hasn't changed and it's at an edge
            if actual_pos == self.last_reported_pos and self.is_at_edge(actual_pos):
                print("Cursor might be stuck at edge on macOS, attempting to unstick...")
                # Nudge it slightly inward from the edge it's stuck on
                nudge_x, nudge_y = 0, 0
                if actual_pos[0] <= 1: nudge_x = 5
                if actual_pos[0] >= self.screen_w - 2: nudge_x = -5
                if actual_pos[1] <= 1: nudge_y = 5
                if actual_pos[1] >= self.screen_h - 2: nudge_y = -5
                
                if nudge_x != 0 or nudge_y != 0:
                    with self.mouse_lock:
                        try:
                            self.mouse_controller.move(nudge_x, nudge_y)
                            print(f"Nudged cursor by ({nudge_x}, {nudge_y})")
                        except Exception as e:
                            print(f"Error nudging cursor: {e}")
            self.last_reported_pos = actual_pos
            self.last_stuck_check_time = current_time

        # Calculate relative movement
        movement_x = direction[0] * self.base_sensitivity * acceleration_factor * effective_distance * 0.1
        movement_y = direction[1] * self.base_sensitivity * acceleration_factor * effective_distance * 0.1

        # Smoothing
        self.position_history.append(np.array([movement_x, movement_y]))

        if len(self.position_history) > 1:
            smoothed_movement = np.mean(self.position_history, axis=0)
        else:
            smoothed_movement = np.array([movement_x, movement_y])

        # Apply relative movement with pynput
        with self.mouse_lock:
            try:
                self.mouse_controller.move(int(smoothed_movement[0]), int(smoothed_movement[1]))
            except Exception as e:
                print(f"Errore movimento: {e}")

    def is_at_edge(self, position, threshold=2):
        """Checks if a given position is within a few pixels of the screen edge."""
        x, y = position
        return (x <= threshold or x >= self.screen_w - 1 - threshold or
                y <= threshold or y >= self.screen_h - 1 - threshold)


    def freeze_position(self):
        """Blocca la posizione corrente del cursore"""
        with self.mouse_lock:
            # Sincronizza la posizione interna con quella reale del sistema
            system_pos = self.mouse_controller.position
            self.current_mouse_pos = np.array([system_pos[0], system_pos[1]], dtype=float)

    def set_position(self, new_position):
        """Imposta direttamente una nuova posizione"""
        with self.mouse_lock:
            self.current_mouse_pos = new_position.copy()
            try:
                self.mouse_controller.position = (int(new_position[0]), int(new_position[1]))
            except Exception as e:
                print(f"Errore set posizione: {e}")

    def enforce_position(self):
        """Mantiene forzatamente la posizione corrente"""
        with self.mouse_lock:
            try:
                self.mouse_controller.position = (int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1]))
            except Exception as e:
                print(f"Errore enforcement posizione: {e}")

    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità"""
        self.base_sensitivity = np.clip(self.base_sensitivity + amount, 0.5, 15.0) # Increased max sensitivity
        print(f"Sensibilità puntatore aggiornata: {self.base_sensitivity:.1f}")

    def get_sensitivity(self):
        return self.base_sensitivity

    def get_current_position(self):
        """Restituisce la posizione attuale del cursore"""
        with self.mouse_lock:
            # Ottiene la posizione in tempo reale dal controller di pynput
            system_pos = self.mouse_controller.position
            self.current_mouse_pos = np.array([system_pos[0], system_pos[1]], dtype=float)
            return self.current_mouse_pos.copy()

    def execute(self, direction, acceleration_factor, effective_distance):
        """Implementazione del metodo base per eseguire l'azione"""
        self.update_position(direction, acceleration_factor, effective_distance)


class ScrollAction(BaseAction): # Renamed for consistency
    """Classe per eseguire lo scrolling"""
    def __init__(self, scroll_cooldown=0.03):
        self.scroll_cooldown = scroll_cooldown
        self.last_scroll_time = 0
        self.scroll_lock = threading.Lock()
        self.scroll_sensitivity = 2.0
        self.scroll_history = deque(maxlen=3)
        self.mouse_controller = mouse.Controller() # Initialize pynput controller
        self.scroll_threshold_pixels = 3.0 # Minimum movement from neutral to trigger scroll for mouth/eyes

    def perform_scroll(self, direction, effective_distance):
        """Esegue lo scrolling"""
        current_time = time.time()
        if current_time - self.last_scroll_time < self.scroll_cooldown:
            return False
        
        # Apply threshold for mouth/eye based scrolling to prevent micro-movements
        if effective_distance < self.scroll_threshold_pixels:
            return False

        try:
            with self.scroll_lock:
                # direction[1] for vertical scroll (Y-axis)
                # Scroll amount scales with sensitivity and effective distance
                scroll_amount = -direction[1] * effective_distance * 0.1 * self.scroll_sensitivity
                self.scroll_history.append(scroll_amount)
                smoothed_scroll = np.mean(self.scroll_history) if self.scroll_history else scroll_amount
                
                scroll_value = int(smoothed_scroll)
                if abs(scroll_value) > 0:  # Only if there's significant movement
                    self.mouse_controller.scroll(0, scroll_value) # x, y for scroll
                    self.last_scroll_time = current_time
                    return True
        except Exception as e:
            print(f"Errore scrolling: {e}")
        return False
    
    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità dello scrolling"""
        self.scroll_sensitivity = np.clip(self.scroll_sensitivity + amount, 0.5, 20.0) # Increased max sensitivity
        print(f"Sensibilità scrolling aggiornata: {self.scroll_sensitivity:.1f}")

    def get_sensitivity(self):
        return self.scroll_sensitivity
    
    def execute(self, direction, effective_distance):
        """Implementazione del metodo base per eseguire l'azione"""
        return self.perform_scroll(direction, effective_distance)


class LeftEye_event(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio sinistro"""
    def __init__(self, top_index=159, bottom_index=145, blink_duration=0.3):
        self.LEFT_EYE_TOP = top_index
        self.LEFT_EYE_BOTTOM = bottom_index
        self.blink_threshold = 0.10 # Reduced threshold for more sensitive blink detection
        self.blink_duration_required = blink_duration
        self.blink_start_time = None
        self.eye_closed = False
        self.blink_detected = False
        self.ear_history = deque(maxlen=3)
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calcola EAR per l'occhio sinistro"""
        try:
            top = landmarks[self.LEFT_EYE_TOP]
            bottom = landmarks[self.LEFT_EYE_BOTTOM]
            ear = abs(top[1] - bottom[1]) # Absolute pixel difference
            # You might want to normalize this by eye width or similar for robustness to distance
            # For now, let's use a fixed pixel threshold tuned to typical webcam distances.
            return ear
        except IndexError:
            return 100.0  # Return a high value to indicate eye is open if landmarks are missing
    
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
        self.mouse_controller = mouse.Controller() # Initialize pynput controller
    
    def perform_click(self, mouse_position): # mouse_position is passed but not used by pynput.click, kept for consistency
        """Esegue click sinistro"""
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
        """Implementazione del metodo base per eseguire l'azione"""
        return self.perform_click(mouse_position)


class RightEye_event(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio destro"""
    def __init__(self, top_index=386, bottom_index=374, blink_duration=0.3):
        self.RIGHT_EYE_TOP = top_index
        self.RIGHT_EYE_BOTTOM = bottom_index
        self.blink_threshold = 0.10 # Reduced threshold for more sensitive blink detection
        self.blink_duration_required = blink_duration
        self.blink_start_time = None
        self.eye_closed = False
        self.blink_detected = False
        self.ear_history = deque(maxlen=3)
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calcola EAR per l'occhio destro"""
        try:
            top = landmarks[self.RIGHT_EYE_TOP]
            bottom = landmarks[self.RIGHT_EYE_BOTTOM]
            ear = abs(top[1] - bottom[1]) # Absolute pixel difference
            return ear
        except IndexError:
            return 100.0  # Return a high value to indicate eye is open if landmarks are missing
    
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
        self.mouse_controller = mouse.Controller() # Initialize pynput controller
    
    def perform_click(self, mouse_position): # mouse_position is passed but not used by pynput.click, kept for consistency
        """Esegue click destro"""
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
        """Implementazione del metodo base per eseguire l'azione"""
        return self.perform_click(mouse_position)

class HeadMouseController:
    def __init__(self, show_window=True, user_config=None):
        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )

        # Get screen dimensions
        import pyautogui 
        self.screen_w, self.screen_h = pyautogui.size() 
        del pyautogui 

        # Landmark indices
        self.NOSE_TIP = 4
        self.UPPER_LIP = 13
        self.LOWER_LIP = 14
        
        # Inizializzazione delle classi degli eventi e delle azioni
        self.calibration = Calibration_action()
        self.nose_joystick = NoseJoystick_event()
        self.mouse_cursor = MouseCursor_action(self.screen_w, self.screen_h)
        self.scroll_action = ScrollAction() # Updated class name
        self.open_mouth_event = OpenMouth_event(self.UPPER_LIP, self.LOWER_LIP)
        self.left_eye_event = LeftEye_event()
        self.right_eye_event = RightEye_event()
        self.left_click_action = LeftClick_action()
        self.right_click_action = RightClick_action()
        
        # User configuration
        self.user_config = user_config if user_config else {}
        # Default scroll direction if not provided
        self.scroll_direction_source = self.user_config.get('scroll_direction', 'nose up/down')
        
        # Dizionario per le associazioni evento-azione
        self.event_action_mappings = []
        self.setup_event_action_mappings() # Setup mappings based on user config
        
        # Stato applicazione
        self.show_window = show_window
        self.paused = False
        self.current_mode = 'pointer'  # 'pointer' o 'scroll'
        self.last_mouse_pos_before_scroll = None
        
        # Initialize internal status for web
        self.current_status = {
            'mode': self.current_mode,
            'paused': self.paused,
            'calibrated': self.calibration.center_calculated,
            'calibration_progress': self.calibration.progress,
            'sensitivity': self.mouse_cursor.get_sensitivity(),
            'scroll_sensitivity': self.scroll_action.get_sensitivity()
        }

    def add_event_action_mapping(self, event, action, event_args_mapper, action_args_mapper):
        """Aggiunge una mappatura evento-azione"""
        self.event_action_mappings.append({
            'event': event,
            'action': action,
            'event_args_mapper': event_args_mapper,
            'action_args_mapper': action_args_mapper
        })

    def setup_event_action_mappings(self):
        """Configura le mappature evento-azione in base alla configurazione utente"""
        self.event_action_mappings = [] # Reset existing mappings

        # Always add nose joystick mapping for cursor movement (primary for pointer mode)
        self.add_event_action_mapping(
            event=self.nose_joystick,
            action=self.mouse_cursor,
            event_args_mapper=lambda tp, lm, mp: (tp, self.calibration.center_position),
            action_args_mapper=lambda tp, lm, mp: self.nose_joystick.get_movement_vector(tp, self.calibration.center_position)
        )

        # Click events
        left_click_gesture = self.user_config.get('left_click')
        right_click_gesture = self.user_config.get('right_click')
        mode_switch_gesture = self.user_config.get('mode_switch')

        # Define a helper to get the event instance based on string name
        def get_event_instance(gesture_name):
            if gesture_name == 'right eye':
                return self.right_eye_event
            elif gesture_name == 'left eye':
                return self.left_eye_event
            elif gesture_name == 'mouth open':
                return self.open_mouth_event
            return None

        # Left Click mapping
        if left_click_gesture:
            event_instance = get_event_instance(left_click_gesture)
            if event_instance:
                self.add_event_action_mapping(event_instance, self.left_click_action, 
                                              lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))

        # Right Click mapping
        if right_click_gesture:
            event_instance = get_event_instance(right_click_gesture)
            if event_instance:
                self.add_event_action_mapping(event_instance, self.right_click_action, 
                                              lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        
        # Mode Switch mapping
        if mode_switch_gesture:
            event_instance = get_event_instance(mode_switch_gesture)
            if event_instance:
                # ToggleModeAction needs the controller instance to change its mode
                self.add_event_action_mapping(event_instance, ToggleModeAction(self),
                                              lambda tp, lm, mp: (lm,), # Event args for detection (e.g., landmarks for mouth/eyes)
                                              lambda tp, lm, mp: ()) # Action args (none needed, ToggleModeAction uses controller ref)

    def set_mode(self, new_mode):
        """Sets the current mode and handles transitions."""
        if self.current_mode == new_mode:
            return

        old_mode = self.current_mode
        self.current_mode = new_mode
        print(f"Modalità cambiata: {old_mode.upper()} -> {new_mode.upper()}")

        if self.current_mode == 'scroll':
            # Store current mouse position when entering scroll mode
            self.last_mouse_pos_before_scroll = self.mouse_cursor.get_current_position().copy()
            print("Passaggio a modalità SCROLL")
        elif self.current_mode == 'pointer':
            print("Passaggio a modalità POINTER")
            # Restore mouse position when returning to pointer mode
            if self.last_mouse_pos_before_scroll is not None:
                self.mouse_cursor.set_position(self.last_mouse_pos_before_scroll)
            # Reset mouth neutral position for consistent scrolling experience
            if isinstance(self.open_mouth_event, OpenMouth_event):
                self.open_mouth_event.neutral_mouth_y = None


    def toggle_pause(self):
        """Attiva/disattiva la pausa"""
        self.paused = not self.paused
        print(f"Applicazione {'in pausa' if self.paused else 'ripresa'}")

    def reset_mouse_position(self):
        """Riporta il cursore al centro dello schermo"""
        center_x, center_y = self.screen_w // 2, self.screen_h // 2
        self.mouse_cursor.set_position(np.array([center_x, center_y], dtype=float))
        return {'success': True} # For web

    def process_nose_movement(self, tracking_point):
        """Processa il movimento del naso (principalmente per il puntatore)"""
        if self.paused or self.current_mode != 'pointer':  # Solo in modalità pointer
            return
            
        # Fase di calibrazione
        if not self.calibration.center_calculated:
            self.calibration.add_sample(tracking_point)
            return
        
        # Controlla se serve auto-ricalibrare
        current_mouse_pos = self.mouse_cursor.get_current_position()
        if self.nose_joystick.should_recalibrate(current_mouse_pos, self.screen_w, self.screen_h):
            print("Auto-ricalibrazione attivata - cursore sul bordo per 5 secondi")
            self.calibration.set_new_center(tracking_point)
            self.nose_joystick.reset_outside_timer()
            self.reset_mouse_position()
            return
        
        # Ottieni vettore di movimento
        direction, acceleration_factor, effective_distance = self.nose_joystick.get_movement_vector(
            tracking_point, self.calibration.center_position
        )
        
        # Muovi il cursore
        self.mouse_cursor.update_position(direction, acceleration_factor, effective_distance)

    def process_events(self, tracking_point, landmarks):
        """Processa tutti gli eventi registrati"""
        if self.paused or not self.calibration.center_calculated:
            return
        current_mouse_pos = self.mouse_cursor.get_current_position()

        # Iterate through all configured event-action mappings
        for mapping in self.event_action_mappings:
            event_instance = mapping['event']
            action_instance = mapping['action']
            
            # Special handling for nose joystick, as it's continuous movement in pointer mode
            if isinstance(event_instance, NoseJoystick_event):
                continue

            event_args = mapping['event_args_mapper'](tracking_point, landmarks, current_mouse_pos)
            
            # Check for event activation
            if event_instance.check_event(*event_args):
                if isinstance(action_instance, ToggleModeAction):
                    action_instance.execute() # ToggleModeAction internally updates controller.current_mode
                elif self.current_mode == 'pointer':
                    # Only execute click actions in pointer mode
                    if isinstance(action_instance, (LeftClick_action, RightClick_action)):
                        action_args = mapping['action_args_mapper'](tracking_point, landmarks, current_mouse_pos)
                        action_instance.execute(*action_args)
        
        # Handle scrolling based on the selected source
        if self.current_mode == 'scroll':
            scroll_direction_vector = None
            effective_distance_for_scroll = 0

            if self.scroll_direction_source == 'nose up/down':
                direction, _, effective_distance_for_scroll = self.nose_joystick.get_movement_vector(
                    tracking_point, self.calibration.center_position
                )
                if direction is not None:
                    # Use Y component for vertical scroll, negative for up, positive for down (standard scroll direction)
                    scroll_direction_vector = np.array([0, direction[1]])
            elif self.scroll_direction_source == 'mouth up/down':
                vertical_offset = self.open_mouth_event.get_vertical_offset(landmarks)
                
                # A positive vertical_offset means the mouth center is below neutral (scrolling down)
                # A negative vertical_offset means the mouth center is above neutral (scrolling up)
                if abs(vertical_offset) > self.scroll_action.scroll_threshold_pixels: # Use scroll action's threshold
                    direction_y = 1 if vertical_offset > 0 else -1
                    scroll_direction_vector = np.array([0, direction_y])
                    effective_distance_for_scroll = abs(vertical_offset) # Use magnitude for speed
                else:
                    # Reset neutral mouth position if mouth is close to neutral AND not actively open
                    # This ensures recalibration of neutral position if user moves head slightly.
                    if not self.open_mouth_event.is_mouth_open():
                        self.open_mouth_event.neutral_mouth_y = None

            elif self.scroll_direction_source == 'eyes up/down (average)':
                # To implement eye-based scrolling, you'd need:
                # 1. A way to establish a 'neutral eye height' (similar to neutral_mouth_y).
                # 2. Calculate the average Y position of key eye landmarks (e.g., center of each eye).
                # 3. Compare current average Y to neutral eye height to get an offset.
                # 4. Use this offset to determine scroll direction and magnitude.
                # This would require a new event class or extending an existing one.
                print("Scrolling with eyes up/down not fully implemented yet in test13.py.")
                pass # Placeholder for future implementation
            
            if scroll_direction_vector is not None and effective_distance_for_scroll > 0:
                self.scroll_action.execute(scroll_direction_vector, effective_distance_for_scroll)


    def draw_interface(self, frame, tracking_point, landmarks=None):
        """Disegna interfaccia utente"""
        if not self.show_window:
            return

        h, w = frame.shape[:2]

        if not self.calibration.center_calculated:
            # Fase calibrazione
            cv2.circle(frame, tuple(tracking_point.astype(int)), 15, (0, 165, 255), 3)
            percentage = self.calibration.progress
            
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

            # Indicatori occhi e bocca
            if landmarks is not None and not self.paused:
                # Left Eye
                left_eye_top = landmarks[self.left_eye_event.LEFT_EYE_TOP].astype(int)
                left_eye_bottom = landmarks[self.left_eye_event.LEFT_EYE_BOTTOM].astype(int)
                left_eye_color = (0, 0, 255) if self.left_eye_event.is_eye_closed() else (0, 255, 0)
                cv2.line(frame, tuple(left_eye_top), tuple(left_eye_bottom), left_eye_color, 3)
                cv2.putText(frame, "L", (left_eye_top[0] - 15, left_eye_top[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, left_eye_color, 2)
                
                # Right Eye
                right_eye_top = landmarks[self.right_eye_event.RIGHT_EYE_TOP].astype(int)
                right_eye_bottom = landmarks[self.right_eye_event.RIGHT_EYE_BOTTOM].astype(int)
                right_eye_color = (255, 0, 0) if self.right_eye_event.is_eye_closed() else (0, 255, 0)
                cv2.line(frame, tuple(right_eye_top), tuple(right_eye_bottom), right_eye_color, 3)
                cv2.putText(frame, "R", (right_eye_top[0] + 10, right_eye_top[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, right_eye_color, 2)
                
                # Mouth
                mouth_color = (0, 165, 255) if self.open_mouth_event.is_mouth_open() else (0, 255, 0)
                upper_lip_pt = landmarks[self.open_mouth_event.UPPER_LIP].astype(int)
                lower_lip_pt = landmarks[self.open_mouth_event.LOWER_LIP].astype(int)
                cv2.line(frame, tuple(upper_lip_pt), tuple(lower_lip_pt), mouth_color, 3)
                cv2.putText(frame, "M", (upper_lip_pt[0] - 10, upper_lip_pt[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, mouth_color, 2)


            # Status
            status_text = "PAUSATO" if self.paused else "ATTIVO"
            status_color = (0, 0, 255) if self.paused else (0, 255, 0)
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Current Mode
            mode_text = f"MODALITA: {self.current_mode.upper()}"
            mode_color = (255, 255, 0) if self.current_mode == 'pointer' else (0, 255, 255)
            cv2.putText(frame, mode_text, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)

            # Info sensibilità (dynamic based on mode)
            if self.current_mode == 'pointer':
                cv2.putText(frame, f"Sensibilita Puntatore: {self.mouse_cursor.base_sensitivity:.1f}", 
                           (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            elif self.current_mode == 'scroll':
                cv2.putText(frame, f"Sensibilita Scroll: {self.scroll_action.scroll_sensitivity:.1f}", 
                           (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, f"Scroll Source: {self.scroll_direction_source.capitalize()}", 
                           (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


        # Controlli
        controls = [
            "=== CONTROLLI ===",
            "SPAZIO = Pausa/Riprendi",
            "+/- = Modifica sensibilità (puntatore/scroll)",
            "R = Reset calibrazione",
            "ESC = Esci",
            "Auto-ricalibrazioni dopo 5s sul bordo"
        ]
        
        y_start = h - len(controls) * 20 - 10
        for i, control in enumerate(controls):
            if i == 0:
                color, weight = (255, 255, 0), 2
            elif i == len(controls) - 1:
                color, weight = (255, 165, 0), 1
            else:
                color, weight = (255, 255, 255), 1
                
            cv2.putText(frame, control, (20, y_start + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, weight)
        return frame # Return the frame after drawing

    def process_frame(self, frame):
        """
        Processes a single video frame for face landmarks, applies control logic,
        and draws the interface if self.show_window is True.
        Returns the processed frame.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        h, w = frame.shape[:2]
        tracking_point = None
        landmarks_np = None

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)
            tracking_point = landmarks_np[self.NOSE_TIP]
            
            if not self.paused:
                self.process_nose_movement(tracking_point)
                self.process_events(tracking_point, landmarks_np)
        
        # Draw interface regardless of whether face is detected or paused,
        # but drawing specifics depend on these states within draw_interface.
        self.draw_interface(frame, tracking_point, landmarks_np)

        self.update_web_status() # Update status for web interface
        return frame


    # --- Web-specific methods for HeadMouseController ---
    def toggle_pause_web(self):
        self.toggle_pause()
        self.update_web_status()
        return self.current_status

    def adjust_sensitivity_web(self, amount):
        if self.current_mode == 'pointer':
            self.mouse_cursor.adjust_sensitivity(amount)
        elif self.current_mode == 'scroll':
            self.scroll_action.adjust_sensitivity(amount * 2.5) # Scroll sensitivity might need larger steps
        self.update_web_status()
        return self.current_status

    def reset_calibration_web(self):
        self.calibration.reset_calibration()
        self.nose_joystick.reset_outside_timer()
        self.reset_mouse_position()
        if isinstance(self.open_mouth_event, OpenMouth_event):
            self.open_mouth_event.neutral_mouth_y = None
        self.update_web_status()
        return {'success': True, 
                'calibrated': self.current_status['calibrated'], 
                'calibration_progress': self.current_status['calibration_progress']}

    def reset_mouse_position_web(self):
        status = self.reset_mouse_position()
        self.update_web_status()
        return status
        
    def update_web_status(self):
        """Updates the internal status dictionary for web display."""
        self.current_status['mode'] = self.current_mode
        self.current_status['paused'] = self.paused
        self.current_status['calibrated'] = self.calibration.center_calculated
        self.current_status['calibration_progress'] = self.calibration.progress
        self.current_status['sensitivity'] = self.mouse_cursor.get_sensitivity()
        self.current_status['scroll_sensitivity'] = self.scroll_action.get_sensitivity()


def get_user_choice(prompt, options):
    """Helper function to get user's choice for keybindings"""
    print(prompt)
    for i, option in enumerate(options):
        print(f"{i+1}. {option}")
    while True:
        try:
            choice = int(input("Inserisci il numero della tua scelta: "))
            if 1 <= choice <= len(options):
                return options[choice-1]
            else:
                print("Scelta non valida. Riprova.")
        except ValueError:
            print("Input non valido. Inserisci un numero.")

def main():
    print("=== HEAD MOUSE CONTROLLER ===")
    
    # Attempt to disable system mouse acceleration on Linux at startup
    disable_system_mouse_acceleration()

    # Scelta modalità display
    while True:
        choice = input("Mostrare finestra webcam? (s/n): ").lower().strip()
        if choice in ['s', 'n']:
            show_window = choice == 's'
            break
        print("Inserisci 's' per sì o 'n' per no")

    # User configuration for actions
    gesture_options = ["right eye", "left eye", "mouth open"]
    
    user_config = {}

    user_config['left_click'] = get_user_choice("Scegli la gesto per il Click SINISTRO:", gesture_options)
    user_config['right_click'] = get_user_choice("Scegli la gesto per il Click DESTRO:", gesture_options)
    user_config['mode_switch'] = get_user_choice("Scegli la gesto per il CAMBIO MODALITA' (Puntatore/Scroll):", gesture_options)

    # Determine available scroll directions (excluding the one chosen for mode switch)
    scroll_direction_options_all = ["nose up/down", "mouth up/down"] # Removed "eyes up/down (average)" as it's not fully implemented
    scroll_direction_options_filtered = []
    
    for opt in scroll_direction_options_all:
        if (opt == "mouth up/down" and user_config['mode_switch'] != "mouth open") or \
           (opt == "nose up/down" and user_config['mode_switch'] != "nose up/down"): # nose up/down usually doesn't conflict with mode switch gestures
           scroll_direction_options_filtered.append(opt)

    # Ensure there's always at least one option, falling back to nose if necessary
    if not scroll_direction_options_filtered:
        scroll_direction_options_filtered = ["nose up/down"] # Fallback

    print("\n--- ATTENZIONE: La modalità di scroll 'bocca su/giù' richiede una calibrazione manuale/visiva per una corretta interpreatazione del movimento verticale. ---")
    user_config['scroll_direction'] = get_user_choice("Scegli la direzione di SCROLL (se la gesto scelta per il cambio modalità è 'bocca aperta', l'opzione relativa potrebbe essere limitata):", scroll_direction_options_filtered)

    controller = HeadMouseController(show_window=show_window, user_config=user_config)
    
    # Setup webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Errore: Webcam non trovata!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("\n🎮 CONTROLLI:")
    print("SPAZIO = Pausa/Riprendi | +/- = Sensibilità (puntatore/scroll)")
    print("R = Reset calibrazione | ESC = Esci")
    print(f"Click SINISTRO: {user_config['left_click']}")
    print(f"Click DESTRO: {user_config['right_click']}")
    print(f"Cambio Modalità (Puntatore/Scroll): {user_config['mode_switch']}")
    print(f"Direzione Scroll: {user_config['scroll_direction']}")
    print("⚡ Auto-ricalibrazione dopo 5 secondi sul bordo")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Impossibile leggere il frame.")
                continue

            # Process the frame using the controller's new method
            processed_frame = controller.process_frame(frame)

            if controller.show_window:
                key = cv2.waitKey(1) & 0xFF
                cv2.imshow('Head Mouse Controller', processed_frame) # Show the processed frame
                
                if key == 27:  # ESC
                    break
                elif key == ord(' '):  # SPAZIO
                    controller.toggle_pause_web() # Use web method for consistency
                elif key == ord('+'):  # +
                    controller.adjust_sensitivity_web(0.2)
                elif key == ord('-'):  # -
                    controller.adjust_sensitivity_web(-0.2)
                elif key == ord('r'):  # R
                    controller.reset_calibration_web()
                elif key == ord('c'): # New hotkey for recentering mouse
                    controller.reset_mouse_position_web()
            else:
                key = cv2.waitKey(1) & 0xFF # Still need waitKey for event processing even without imshow
                if key == 27:  # ESC
                    break
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nInterruzione da tastiera")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Controller closed")


if __name__ == "__main__":
    main()