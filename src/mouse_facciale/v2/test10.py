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
        self.open_duration_required = duration  # Rimane 0.5 secondi come richiesto
        self.open_start_time = None
        self.mouth_open = False
        self.event_detected = False
        self.mouth_history = deque(maxlen=3)
    
    def calculate_mouth_openness(self, landmarks):
        """Calcola l'apertura della bocca"""
        try:
            upper_lip = landmarks[self.UPPER_LIP]
            lower_lip = landmarks[self.LOWER_LIP]
            openness = abs(upper_lip[1] - lower_lip[1]) / 25.0
            return openness
        except:
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


class SwitchMode_action(BaseAction):
    """Classe per cambiare modalità tra puntatore e scroll"""
    def __init__(self):
        self.last_switch_time = 0
        self.switch_cooldown = 1.0  # 1 secondo di cooldown
    
    def switch_mode(self, current_mode):
        """Cambia la modalità"""
        current_time = time.time()
        if current_time - self.last_switch_time < self.switch_cooldown:
            return current_mode
        
        new_mode = 'scroll' if current_mode == 'pointer' else 'pointer'
        print(f"Modalità cambiata: {new_mode}")
        self.last_switch_time = current_time
        return new_mode
    
    def execute(self, current_mode):
        """Implementazione del metodo base per eseguire l'azione"""
        return self.switch_mode(current_mode)


class MouseCursor_action(BaseAction):
    """Classe per tradurre il movimento del naso in movimento del cursore"""
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.current_mouse_pos = np.array([screen_w // 2, screen_h // 2], dtype=float)
        self.position_history = deque(maxlen=5) # Usato per lo smoothing del movimento
        self.mouse_lock = threading.Lock() # Lock per thread safety
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

    def freeze_position(self):
        """Blocca la posizione corrente del cursore"""
        with self.mouse_lock:
            # Sincronizza la posizione interna con quella reale del sistema
            system_pos = pyautogui.position()
            self.current_mouse_pos = np.array([system_pos.x, system_pos.y], dtype=float)

    def set_position(self, new_position):
        """Imposta direttamente una nuova posizione"""
        with self.mouse_lock:
            self.current_mouse_pos = new_position.copy()
            try:
                pyautogui.moveTo(int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1]))
            except Exception as e:
                print(f"Errore nell'impostare la posizione: {e}")

    def enforce_position(self):
        """Mantiene forzatamente la posizione corrente"""
        with self.mouse_lock:
            try:
                pyautogui.moveTo(int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1]))
            except Exception as e:
                print(f"Errore enforcement posizione: {e}")

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


class Scroll_action(BaseAction):
    """Classe per eseguire lo scrolling"""
    def __init__(self, scroll_cooldown=0.03):
        self.scroll_cooldown = scroll_cooldown
        self.last_scroll_time = 0
        self.scroll_lock = threading.Lock()
        self.scroll_sensitivity = 2.0
        self.scroll_history = deque(maxlen=3)
    
    def perform_scroll(self, direction, effective_distance):
        """Esegue lo scrolling"""
        current_time = time.time()
        if current_time - self.last_scroll_time < self.scroll_cooldown:
            return False
        
        try:
            with self.scroll_lock:
                # Calcola l'ammontare dello scroll con smoothing
                scroll_amount = -direction[1] * effective_distance * 0.1 * self.scroll_sensitivity
                self.scroll_history.append(scroll_amount)
                smoothed_scroll = np.mean(self.scroll_history) if self.scroll_history else scroll_amount
                
                # Scrolling verticale con controllo più preciso
                scroll_value = int(smoothed_scroll)
                if abs(scroll_value) > 0:  # Solo se c'è movimento significativo
                    pyautogui.scroll(scroll_value)
                    self.last_scroll_time = current_time
                    return True
        except Exception as e:
            print(f"Errore scrolling: {e}")
        return False
    
    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità dello scrolling"""
        self.scroll_sensitivity = np.clip(self.scroll_sensitivity + amount, 1.0, 10.0)
        print(f"Sensibilità scrolling aggiornata: {self.scroll_sensitivity:.1f}")
    
    def execute(self, direction, effective_distance):
        """Implementazione del metodo base per eseguire l'azione"""
        return self.perform_scroll(direction, effective_distance)


class LeftEye_event(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio sinistro"""
    def __init__(self, top_index=159, bottom_index=145, blink_duration=0.3):
        self.LEFT_EYE_TOP = top_index
        self.LEFT_EYE_BOTTOM = bottom_index
        self.blink_threshold = 0.10
        self.blink_duration_required = blink_duration  # 300ms come richiesto
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
        self.blink_duration_required = blink_duration  # 300ms come richiesto
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
        self.UPPER_LIP = 13
        self.LOWER_LIP = 14
        
        # Inizializzazione delle classi
        self.calibration = Calibration_action()
        self.nose_joystick = NoseJoystick_event()
        self.mouse_cursor = MouseCursor_action(self.screen_w, self.screen_h)
        self.scroll_action = Scroll_action()
        self.open_mouth_event = OpenMouth_event(self.UPPER_LIP, self.LOWER_LIP)
        self.switch_mode_action = SwitchMode_action()
        
        # Dizionario per le associazioni evento-azione
        self.event_action_mappings = []
        
        # Stato applicazione
        self.show_window = show_window
        self.paused = False
        self.current_mode = 'pointer'  # 'pointer' o 'scroll'
        self.last_mouse_pos_before_scroll = None

    def add_event_action_mapping(self, event, action, event_args_mapper, action_args_mapper):
        """Aggiunge una mappatura evento-azione"""
        self.event_action_mappings.append({
            'event': event,
            'action': action,
            'event_args_mapper': event_args_mapper,
            'action_args_mapper': action_args_mapper
        })

    def toggle_pause(self):
        """Attiva/disattiva la pausa"""
        self.paused = not self.paused
        print(f"Applicazione {'in pausa' if self.paused else 'ripresa'}")

    def reset_mouse_position(self):
        """Riporta il cursore al centro dello schermo"""
        center_x, center_y = self.screen_w // 2, self.screen_h // 2
        self.mouse_cursor.set_position(np.array([center_x, center_y], dtype=float))

    def process_nose_movement(self, tracking_point):
        """Processa il movimento del naso"""
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
        
        # Gestione cambio modalità
        if self.open_mouth_event.check_event(landmarks):
            old_mode = self.current_mode
            new_mode = self.switch_mode_action.execute(self.current_mode)
            
            if new_mode != old_mode:  # Solo se c'è un effettivo cambio
                self.current_mode = new_mode
                
                if self.current_mode == 'scroll':
                    # Passa a modalità scroll: salva la posizione corrente
                    print("Passaggio a modalità SCROLL - posizione bloccata")
                    self.last_mouse_pos_before_scroll = self.mouse_cursor.get_current_position().copy()
                    self.mouse_cursor.freeze_position()
                    
                elif self.current_mode == 'pointer':
                    # Torna a modalità pointer: ripristina la posizione
                    print("Passaggio a modalità POINTER - posizione ripristinata")
                    if self.last_mouse_pos_before_scroll is not None:
                        self.mouse_cursor.set_position(self.last_mouse_pos_before_scroll)
        
        # Processa eventi specifici per modalità
        if self.current_mode == 'pointer':
            # Eventi di click solo in modalità puntatore
            for mapping in self.event_action_mappings:
                # Prepara gli argomenti per l'evento
                event_args = mapping['event_args_mapper'](tracking_point, landmarks, current_mouse_pos)
                
                # Verifica se l'evento è attivo
                if mapping['event'].check_event(*event_args):
                    # Prepara gli argomenti per l'azione
                    action_args = mapping['action_args_mapper'](tracking_point, landmarks, current_mouse_pos)
                    
                    # Esegui l'azione associata
                    mapping['action'].execute(*action_args)
                    
        elif self.current_mode == 'scroll':
            # Mantieni forzatamente la posizione del cursore
            self.mouse_cursor.enforce_position()
            
            # Gestione scroll
            direction, _, effective_distance = self.nose_joystick.get_movement_vector(
                tracking_point, self.calibration.center_position
            )
            if direction is not None:
                # Usiamo solo la componente verticale per lo scrolling
                scroll_direction = np.array([0, direction[1]])  # Solo componente Y
                self.scroll_action.execute(scroll_direction, effective_distance)

    def draw_interface(self, frame, tracking_point, landmarks=None):
        """Disegna interfaccia utente"""
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

            # Indicatori occhi
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

        # Controlli
        controls = [
            "=== CONTROLLI ===",
            "SPAZIO = Pausa/Riprendi",
            "+/- = Modifica sensibilità",
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
    
    # Configurazione eventi e azioni
    controller.add_event_action_mapping(
        event=controller.nose_joystick,
        action=controller.mouse_cursor,
        event_args_mapper=lambda tp, lm, mp: (tp, controller.calibration.center_position),
        action_args_mapper=lambda tp, lm, mp: controller.nose_joystick.get_movement_vector(tp, controller.calibration.center_position)
    )
    
    # Aggiungi mappature solo per la modalità puntatore (click)
    controller.add_event_action_mapping(
        event=LeftEye_event(),
        action=LeftClick_action(),
        event_args_mapper=lambda tp, lm, mp: (lm,),
        action_args_mapper=lambda tp, lm, mp: (mp,)
    )
    
    controller.add_event_action_mapping(
        event=RightEye_event(),
        action=RightClick_action(),
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
    print("Apertura bocca = Cambia modalità (puntatore/scroll)")
    print("⚡ Auto-ricalibrazione dopo 5 secondi sul bordo")
    
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
                    controller.process_nose_movement(tracking_point)
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
                    if controller.current_mode == 'pointer':
                        controller.mouse_cursor.adjust_sensitivity(0.2)
                    else:
                        controller.scroll_action.adjust_sensitivity(0.5)
                elif key == ord('-'):  # -
                    if controller.current_mode == 'pointer':
                        controller.mouse_cursor.adjust_sensitivity(-0.2)
                    else:
                        controller.scroll_action.adjust_sensitivity(-0.5)
                elif key == ord('r'):  # R
                    controller.calibration.reset_calibration()
                    controller.nose_joystick.reset_outside_timer()
                    controller.reset_mouse_position()
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