import cv2
import mediapipe as mp
import numpy as np
import time
import sys
from collections import deque
import threading
import subprocess
import platform

# Importare pybluez - Assicurati di averlo installato: pip install pybluez
# Potrebbe richiedere: sudo apt-get install python3-dev libbluetooth-dev (su Debian/Ubuntu)
# O equivalenti per la tua distribuzione Linux.
import bluetooth


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
                subprocess.run(["xinput", "--set-prop", mouse_id, "libinput Accel Profile Enabled", "0, 1"], check=True) # 0 for flat, 1 for adaptive
                subprocess.run(["xinput", "--set-prop", mouse_id, "libinput Accel Speed", "0"], check=True) # Set speed to 0 for flat
                
                # Fallback for older drivers or different setups
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


class BluetoothTransmitter:
    def __init__(self, target_address=None, port=1, is_server=True):
        self.target_address = target_address
        self.port = port
        self.is_server = is_server
        self.sock = None
        self.client_sock = None
        self.connected = False
        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee" # Un UUID standard per SPP
        self.connection_thread = None
        self.lock = threading.Lock() # Lock per la scrittura sulla socket

        if is_server and not target_address:
            print(f"Bluetooth Transmitter: Avvio come server su porta {self.port} con UUID {self.uuid}")
            self.connection_thread = threading.Thread(target=self._start_server)
        elif target_address and not is_server:
            print(f"Bluetooth Transmitter: Avvio come client, tentativo di connessione a {self.target_address}:{self.port}")
            self.connection_thread = threading.Thread(target=self._start_client)
        else:
            raise ValueError("Must specify either target_address (for client) or is_server=True (for server).")
        
        self.connection_thread.daemon = True # Il thread si chiuderà con il programma principale
        self.connection_thread.start()

    def _start_server(self):
        try:
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.sock.bind(("", self.port))
            self.sock.listen(1) # Ascolta una singola connessione

            bluetooth.advertise_service(
                self.sock, "HeadMouseService",
                service_id = self.uuid,
                service_classes = [ self.uuid, bluetooth.SERIAL_PORT_CLASS ],
                profiles = [ bluetooth.SERIAL_PORT_PROFILE ],
                # Do not set protocols to avoid issues with some clients
            )

            print("In attesa di connessioni Bluetooth sul servizio HeadMouseService...")
            self.client_sock, client_info = self.sock.accept()
            print(f"Accettata connessione da {client_info}")
            self.connected = True
        except bluetooth.BluetoothError as e:
            print(f"Errore Bluetooth come server: {e}")
            self.connected = False
        except Exception as e:
            print(f"Errore generico in _start_server: {e}")
            self.connected = False

    def _start_client(self):
        try:
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.sock.connect((self.target_address, self.port))
            print(f"Connesso al dispositivo Bluetooth: {self.target_address}")
            self.client_sock = self.sock # Client uses the main socket for sending
            self.connected = True
        except bluetooth.BluetoothError as e:
            print(f"Errore Bluetooth come client: {e}")
            self.connected = False
            print("Tentativo di riconnessione in 5 secondi...")
            time.sleep(5)
            self._start_client() # Tentativo di riconnessione
        except Exception as e:
            print(f"Errore generico in _start_client: {e}")
            self.connected = False

    def send_data(self, data):
        """Invia dati binari attraverso la connessione Bluetooth."""
        if self.connected and self.client_sock:
            try:
                with self.lock:
                    self.client_sock.sendall(data)
                return True
            except bluetooth.BluetoothError as e:
                print(f"Errore invio dati Bluetooth: {e}")
                self.connected = False # Segnaliamo la disconnessione
                self.client_sock.close()
                self.client_sock = None
                print("Connessione Bluetooth persa. Riavvio tentativo di connessione...")
                if self.is_server:
                    self.connection_thread = threading.Thread(target=self._start_server)
                else:
                    self.connection_thread = threading.Thread(target=self._start_client)
                self.connection_thread.daemon = True
                self.connection_thread.start()
                return False
            except Exception as e:
                print(f"Errore generico invio dati: {e}")
                return False
        return False

    def close(self):
        """Chiude le connessioni Bluetooth."""
        if self.client_sock:
            try:
                self.client_sock.close()
            except Exception as e:
                print(f"Errore chiusura client_sock: {e}")
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                print(f"Errore chiusura sock: {e}")
        self.connected = False
        print("Connessioni Bluetooth chiuse.")


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
        self.open_duration_required = duration
        self.open_start_time = None
        self.mouth_open = False
        self.event_detected = False
        self.mouth_history = deque(maxlen=3)
        self.neutral_mouth_y = None # Used for potential vertical scrolling
    
    def calculate_mouth_openness(self, landmarks):
        """Calcola l'apertura della bocca"""
        try:
            upper_lip = landmarks[self.UPPER_LIP]
            lower_lip = landmarks[self.LOWER_LIP]
            openness = abs(upper_lip[1] - lower_lip[1]) / 25.0 # Normalized by an approximate face size
            return openness
        except:
            return 0.0
            
    def get_vertical_offset(self, landmarks):
        """Calcola l'offset verticale del centro della bocca rispetto a una posizione neutra"""
        try:
            upper_lip_y = landmarks[self.UPPER_LIP][1]
            lower_lip_y = landmarks[self.LOWER_LIP][1]
            current_mouth_center_y = (upper_lip_y + lower_lip_y) / 2
            
            # Calibrate neutral position only once when mouth is considered closed/neutral
            if self.neutral_mouth_y is None and not self.mouth_open:
                self.neutral_mouth_y = current_mouth_center_y 
                return 0.0
            
            return current_mouth_center_y - self.neutral_mouth_y
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
                self.neutral_mouth_y = None # Reset neutral position on close
        
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
    """Classe per calcolare il movimento direzionale e inviarlo via Bluetooth."""
    def __init__(self, screen_w, screen_h, bt_transmitter):
        self.screen_w = screen_w
        self.screen_h = screen_h
        # current_mouse_pos will be a virtual position for display only
        self.current_mouse_pos = np.array([screen_w // 2, screen_h // 2], dtype=float) 
        self.position_history = deque(maxlen=5) # Usato per lo smoothing del movimento
        self.base_sensitivity = 4.0
        self.bt_transmitter = bt_transmitter # Riferimento al trasmettitore Bluetooth

    def send_directional_movement(self, direction, acceleration_factor, effective_distance):
        """
        Invia la direzione e il fattore di velocità al dispositivo Bluetooth.
        Il formato del pacchetto è:
        [Byte 0: Tipo di pacchetto (0x01 per movimento)]
        [Byte 1: Segno X (0 per negativo, 1 per positivo)]
        [Byte 2: Valore assoluto X (0-255)]
        [Byte 3: Segno Y (0 per negativo, 1 per positivo)]
        [Byte 4: Valore assoluto Y (0-255)]
        [Byte 5: Fattore Velocità (0-255)]
        """
        if direction is None:
            return

        # Calcola movimento relativo
        # Questi valori sono ora utilizzati per SCALARE l'input direzionale
        # Non sono più pixel di movimento, ma l'intensità del movimento
        raw_movement_x = direction[0] * self.base_sensitivity * acceleration_factor * effective_distance * 0.1
        raw_movement_y = direction[1] * self.base_sensitivity * acceleration_factor * effective_distance * 0.1

        # Smoothing
        self.position_history.append(np.array([raw_movement_x, raw_movement_y]))
        smoothed_movement = np.mean(self.position_history, axis=0) if self.position_history else np.array([0.0, 0.0])

        # Normalizza la direzione per l'invio
        # Limita i valori a un range accettabile (e.g., -127 a 127)
        max_val = 100.0 # Valore massimo per il componente direzionale
        move_x = int(np.clip(smoothed_movement[0], -max_val, max_val))
        move_y = int(np.clip(smoothed_movement[1], -max_val, max_val))

        # Codifica per l'invio Bluetooth
        packet_type = 0x01 # Movimento cursore
        
        sign_x = 1 if move_x >= 0 else 0
        abs_x = abs(move_x)

        sign_y = 1 if move_y >= 0 else 0
        abs_y = abs(move_y)

        # Il fattore velocità potrebbe essere un valore separato o derivato da acceleration_factor
        # Per ora, usiamo una scala semplice per acceleration_factor da 1 a 4 (0-255)
        # Assicurati che acceleration_factor sia sempre positivo
        # speed_factor = int(np.clip((acceleration_factor - 1.0) / 3.0 * 255, 0, 255))
        # Utilizziamo effective_distance come base per la velocità, scalato
        speed_factor = int(np.clip(effective_distance * self.base_sensitivity * 0.5, 0, 255)) # Scale effective_distance

        # Esempio di pacchetto (6 byte)
        data_to_send = bytearray([
            packet_type,
            sign_x,
            abs_x & 0xFF, # Assicurati che sia un byte
            sign_y,
            abs_y & 0xFF, # Assicurati che sia un byte
            speed_factor & 0xFF # Assicurati che sia un byte
        ])
        
        self.bt_transmitter.send_data(data_to_send)

    def freeze_position(self):
        # Questo è ora puramente visivo per la finestra della webcam
        pass

    def set_position(self, new_position):
        # Questo è ora puramente visivo per la finestra della webcam
        self.current_mouse_pos = new_position.copy()

    def enforce_position(self):
        # Questo è ora puramente visivo per la finestra della webcam
        pass

    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità base per il movimento direzionale."""
        self.base_sensitivity = np.clip(self.base_sensitivity + amount, 0.5, 20.0) # Maggiore range
        print(f"Sensibilità puntatore aggiornata: {self.base_sensitivity:.1f}")

    def get_current_position(self):
        """Restituisce la posizione virtuale attuale per la visualizzazione."""
        return self.current_mouse_pos.copy()

    def execute(self, direction, acceleration_factor, effective_distance):
        """Implementazione del metodo base per eseguire l'azione."""
        self.send_directional_movement(direction, acceleration_factor, effective_distance)


class Scroll_action(BaseAction):
    """Classe per eseguire lo scrolling inviando comandi via Bluetooth."""
    def __init__(self, bt_transmitter, scroll_cooldown=0.03):
        self.scroll_cooldown = scroll_cooldown
        self.last_scroll_time = 0
        self.scroll_sensitivity = 2.0
        self.scroll_history = deque(maxlen=3)
        self.bt_transmitter = bt_transmitter # Riferimento al trasmettitore Bluetooth
    
    def perform_scroll(self, direction, effective_distance):
        """
        Esegue lo scrolling inviando la direzione e l'intensità dello scroll via Bluetooth.
        Formato del pacchetto:
        [Byte 0: Tipo di pacchetto (0x02 per scroll)]
        [Byte 1: Segno Scroll Y (0 per up, 1 per down)]
        [Byte 2: Valore assoluto Scroll Y (0-255)]
        [Byte 3-5: Riservato/Padding]
        """
        current_time = time.time()
        if current_time - self.last_scroll_time < self.scroll_cooldown:
            return False
        
        if direction is None:
            return False

        # direction[1] per scroll verticale (Y-axis)
        raw_scroll_amount = -direction[1] * effective_distance * 0.1 * self.scroll_sensitivity
        self.scroll_history.append(raw_scroll_amount)
        smoothed_scroll = np.mean(self.scroll_history) if self.scroll_history else raw_scroll_amount
        
        scroll_value = int(smoothed_scroll)
        
        if abs(scroll_value) > 0:
            packet_type = 0x02 # Scroll
            
            sign_y = 1 if scroll_value > 0 else 0 # 1 for down (positive y), 0 for up (negative y)
            abs_y = abs(scroll_value)
            
            # Limita il valore dello scroll a un byte
            abs_y = min(abs_y, 255)

            data_to_send = bytearray([
                packet_type,
                sign_y,
                abs_y & 0xFF,
                0x00, # Padding
                0x00, # Padding
                0x00  # Padding
            ])
            
            self.bt_transmitter.send_data(data_to_send)
            self.last_scroll_time = current_time
            return True
        return False
    
    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità dello scrolling."""
        self.scroll_sensitivity = np.clip(self.scroll_sensitivity + amount, 1.0, 30.0) # Maggiore range
        print(f"Sensibilità scrolling aggiornata: {self.scroll_sensitivity:.1f}")
    
    def execute(self, direction, effective_distance):
        """Implementazione del metodo base per eseguire l'azione."""
        return self.perform_scroll(direction, effective_distance)


class LeftEye_event(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio sinistro"""
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
                  self.open_start_time is not None and # Changed from self.open_start_time to self.blink_start_time
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
    """Classe per eseguire click sinistro inviando comandi via Bluetooth."""
    def __init__(self, bt_transmitter, click_cooldown=0.5):
        self.click_cooldown = click_cooldown
        self.last_click_time = 0
        self.bt_transmitter = bt_transmitter # Riferimento al trasmettitore Bluetooth
    
    def perform_click(self):
        """
        Esegue click sinistro inviando un comando via Bluetooth.
        Formato del pacchetto:
        [Byte 0: Tipo di pacchetto (0x03 per click sinistro)]
        [Byte 1-5: Riservato/Padding]
        """
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            packet_type = 0x03 # Click sinistro
            data_to_send = bytearray([packet_type, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.bt_transmitter.send_data(data_to_send)
            print(f"Click SINISTRO (via Bluetooth)")
            self.last_click_time = current_time
            return True
        except Exception as e:
            print(f"Errore click sinistro (Bluetooth): {e}")
            return False
    
    def execute(self, mouse_position): # mouse_position non è più usato direttamente
        """Implementazione del metodo base per eseguire l'azione."""
        return self.perform_click()


class RightEye_event(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio destro"""
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
    """Classe per eseguire click destro inviando comandi via Bluetooth."""
    def __init__(self, bt_transmitter, click_cooldown=0.5):
        self.click_cooldown = click_cooldown
        self.last_click_time = 0
        self.bt_transmitter = bt_transmitter # Riferimento al trasmettitore Bluetooth
    
    def perform_click(self):
        """
        Esegue click destro inviando un comando via Bluetooth.
        Formato del pacchetto:
        [Byte 0: Tipo di pacchetto (0x04 per click destro)]
        [Byte 1-5: Riservato/Padding]
        """
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            packet_type = 0x04 # Click destro
            data_to_send = bytearray([packet_type, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.bt_transmitter.send_data(data_to_send)
            print(f"Click DESTRO (via Bluetooth)")
            self.last_click_time = current_time
            return True
        except Exception as e:
            print(f"Errore click destro (Bluetooth): {e}")
            return False
    
    def execute(self, mouse_position): # mouse_position non è più usato direttamente
        """Implementazione del metodo base per eseguire l'azione."""
        return self.perform_click()

class HeadMouseController:
    def __init__(self, show_window=True, user_config=None, bt_transmitter=None):
        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )

        # Get screen dimensions using pyautogui (only for screen size, then remove it)
        # These dimensions are now primarily for virtual cursor display and calibration logic
        import pyautogui 
        self.screen_w, self.screen_h = pyautogui.size() 
        del pyautogui # Remove pyautogui from memory after getting screen size

        # Landmark indices
        self.NOSE_TIP = 4
        self.UPPER_LIP = 13
        self.LOWER_LIP = 14
        
        self.bt_transmitter = bt_transmitter # Assegnazione del trasmettitore Bluetooth

        # Inizializzazione delle classi degli eventi e delle azioni
        self.calibration = Calibration_action()
        self.nose_joystick = NoseJoystick_event()
        # Passiamo il trasmettitore Bluetooth alle azioni che lo useranno
        self.mouse_cursor = MouseCursor_action(self.screen_w, self.screen_h, self.bt_transmitter)
        self.scroll_action = Scroll_action(self.bt_transmitter)
        self.open_mouth_event = OpenMouth_event(self.UPPER_LIP, self.LOWER_LIP)
        self.switch_mode_action = SwitchMode_action()
        self.left_eye_event = LeftEye_event()
        self.right_eye_event = RightEye_event()
        self.left_click_action = LeftClick_action(self.bt_transmitter)
        self.right_click_action = RightClick_action(self.bt_transmitter)
        
        # User configuration
        self.user_config = user_config if user_config else {}
        self.scroll_direction_source = self.user_config.get('scroll_direction', 'nose up/down')

        # Dizionario per le associazioni evento-azione
        self.event_action_mappings = []
        self.setup_event_action_mappings() # Setup mappings based on user config
        
        # Stato applicazione
        self.show_window = show_window
        self.paused = False
        self.current_mode = 'pointer'  # 'pointer' o 'scroll'
        self.last_mouse_pos_before_scroll = None # Ora una posizione VIRTUAL

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

        # Always add nose joystick mapping for cursor movement
        self.add_event_action_mapping(
            event=self.nose_joystick,
            action=self.mouse_cursor,
            event_args_mapper=lambda tp, lm, mp: (tp, self.calibration.center_position),
            action_args_mapper=lambda tp, lm, mp: self.nose_joystick.get_movement_vector(tp, self.calibration.center_position)
        )

        # Left Click mapping
        if self.user_config.get('left_click') == 'right eye':
            self.add_event_action_mapping(self.right_eye_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: ()) # No mouse pos for action
        elif self.user_config.get('left_click') == 'left eye':
            self.add_event_action_mapping(self.left_eye_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: ())
        elif self.user_config.get('left_click') == 'mouth open':
            self.add_event_action_mapping(self.open_mouth_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: ())

        # Right Click mapping
        if self.user_config.get('right_click') == 'right eye':
            self.add_event_action_mapping(self.right_eye_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: ())
        elif self.user_config.get('right_click') == 'left eye':
            self.add_event_action_mapping(self.left_eye_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: ())
        elif self.user_config.get('right_click') == 'mouth open':
            self.add_event_action_mapping(self.open_mouth_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: ())
        
        # Mode Switch mapping
        if self.user_config.get('mode_switch') == 'right eye':
            self.add_event_action_mapping(self.right_eye_event, self.switch_mode_action,
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (self.current_mode,))
        elif self.user_config.get('mode_switch') == 'left eye':
            self.add_event_action_mapping(self.left_eye_event, self.switch_mode_action,
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (self.current_mode,))
        elif self.user_config.get('mode_switch') == 'mouth open':
            self.add_event_action_mapping(self.open_mouth_event, self.switch_mode_action,
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (self.current_mode,))


    def toggle_pause(self):
        """Attiva/disattiva la pausa."""
        self.paused = not self.paused
        print(f"Applicazione {'in pausa' if self.paused else 'ripresa'}")

    def reset_mouse_position(self):
        """Resets the virtual cursor position for display."""
        center_x, center_y = self.screen_w // 2, self.screen_h // 2
        self.mouse_cursor.set_position(np.array([center_x, center_y], dtype=float))

    def process_nose_movement(self, tracking_point):
        """Processa il movimento del naso (principalmente per il puntatore)."""
        if self.paused or self.current_mode != 'pointer':  # Solo in modalità pointer
            return
            
        # Fase di calibrazione
        if not self.calibration.center_calculated:
            self.calibration.add_sample(tracking_point)
            return
        
        # Controlla se serve auto-ricalibrare
        # Qui usiamo la posizione virtuale per la ricalibrazione automatica
        current_virtual_mouse_pos = self.mouse_cursor.get_current_position()
        if self.nose_joystick.should_recalibrate(current_virtual_mouse_pos, self.screen_w, self.screen_h):
            print("Auto-ricalibrazione attivata - cursore virtuale sul bordo per 5 secondi")
            self.calibration.set_new_center(tracking_point)
            self.nose_joystick.reset_outside_timer()
            self.reset_mouse_position() # Resetta la posizione virtuale
            return
        
        # Ottieni vettore di movimento
        direction, acceleration_factor, effective_distance = self.nose_joystick.get_movement_vector(
            tracking_point, self.calibration.center_position
        )
        
        # Invia il movimento direzionale via Bluetooth
        self.mouse_cursor.execute(direction, acceleration_factor, effective_distance)
        
        # Aggiorna la posizione virtuale per la visualizzazione (non reale del sistema)
        if direction is not None:
            # Stima il movimento virtuale sul display per dare feedback visivo
            # Questa parte non influenza il mouse reale sul dispositivo embedded
            # Ma simula come il cursore potrebbe muoversi sul display remoto
            movement_x = direction[0] * self.mouse_cursor.base_sensitivity * acceleration_factor * effective_distance * 0.1
            movement_y = direction[1] * self.mouse_cursor.base_sensitivity * acceleration_factor * effective_distance * 0.1
            self.mouse_cursor.current_mouse_pos[0] += movement_x
            self.mouse_cursor.current_mouse_pos[1] += movement_y
            
            # Limita la posizione virtuale entro i bordi dello schermo per la visualizzazione
            self.mouse_cursor.current_mouse_pos[0] = np.clip(self.mouse_cursor.current_mouse_pos[0], 0, self.screen_w)
            self.mouse_cursor.current_mouse_pos[1] = np.clip(self.mouse_cursor.current_mouse_pos[1], 0, self.screen_h)


    def process_events(self, tracking_point, landmarks):
        """Processa tutti gli eventi registrati."""
        if self.paused or not self.calibration.center_calculated:
            return
        current_virtual_mouse_pos = self.mouse_cursor.get_current_position()

        # Iterate through all configured event-action mappings
        for mapping in self.event_action_mappings:
            event_instance = mapping['event']
            action_instance = mapping['action']
            
            # Special handling for nose joystick, as it's continuous movement
            if isinstance(event_instance, NoseJoystick_event):
                continue # Handled in process_nose_movement

            event_args = mapping['event_args_mapper'](tracking_point, landmarks, current_virtual_mouse_pos)
            
            # Check for event activation
            if event_instance.check_event(*event_args):
                if isinstance(action_instance, SwitchMode_action):
                    old_mode = self.current_mode
                    new_mode = action_instance.execute(self.current_mode)
                    if new_mode != old_mode:
                        self.current_mode = new_mode
                        if self.current_mode == 'scroll':
                            print("Passaggio a modalità SCROLL")
                            self.last_mouse_pos_before_scroll = current_virtual_mouse_pos.copy()
                            # Invia comando al BT per indicare cambio modalità se necessario per l'embedded
                            self.bt_transmitter.send_data(bytearray([0x05, 0x01, 0x00, 0x00, 0x00, 0x00])) # 0x05 = Mode Switch, 0x01 = Scroll
                        elif self.current_mode == 'pointer':
                            print("Passaggio a modalità POINTER")
                            if self.last_mouse_pos_before_scroll is not None:
                                self.mouse_cursor.set_position(self.last_mouse_pos_before_scroll)
                            # Reset mouth neutral position for consistent scrolling
                            if isinstance(self.open_mouth_event, OpenMouth_event):
                                self.open_mouth_event.neutral_mouth_y = None
                            self.bt_transmitter.send_data(bytearray([0x05, 0x00, 0x00, 0x00, 0x00, 0x00])) # 0x05 = Mode Switch, 0x00 = Pointer
                elif self.current_mode == 'pointer':
                    # Only execute click actions in pointer mode
                    if isinstance(action_instance, (LeftClick_action, RightClick_action)):
                        # action_args_mapper for clicks now returns empty tuple, as mouse position is not needed
                        action_instance.execute()
        
        # Handle scrolling based on the selected source
        if self.current_mode == 'scroll':
            scroll_direction_vector = None
            effective_distance_for_scroll = 0

            if self.scroll_direction_source == 'nose up/down':
                direction, _, effective_distance_for_scroll = self.nose_joystick.get_movement_vector(
                    tracking_point, self.calibration.center_position
                )
                if direction is not None:
                    scroll_direction_vector = np.array([0, direction[1]]) # Use Y component for vertical scroll
            elif self.scroll_direction_source == 'mouth up/down':
                vertical_offset = self.open_mouth_event.get_vertical_offset(landmarks)
                
                scroll_threshold = 5.0 # pixels
                if abs(vertical_offset) > scroll_threshold:
                    direction_y = 1 if vertical_offset > 0 else -1
                    scroll_direction_vector = np.array([0, direction_y])
                    effective_distance_for_scroll = abs(vertical_offset)
                else:
                    if not self.open_mouth_event.is_mouth_open():
                        self.open_mouth_event.neutral_mouth_y = None

            elif self.scroll_direction_source == 'eyes up/down (average)':
                # Placeholder for eye-based scrolling
                print("Scrolling con occhi non ancora implementato completamente.")
                pass 
            
            if scroll_direction_vector is not None and effective_distance_for_scroll > 0:
                self.scroll_action.execute(scroll_direction_vector, effective_distance_for_scroll)


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

            # Draw virtual cursor position
            if self.mouse_cursor.current_mouse_pos is not None:
                cv2.circle(frame, tuple(self.mouse_cursor.current_mouse_pos.astype(int)), 10, (0, 255, 255), -1)

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
            "Auto-ricalibrazioni dopo 5s sul bordo",
            f"Stato BT: {'Connesso' if self.bt_transmitter.connected else 'Disconnesso'}"
        ]
        
        y_start = h - len(controls) * 20 - 10
        for i, control in enumerate(controls):
            if i == 0:
                color, weight = (255, 255, 0), 2
            elif i == len(controls) - 1: # Bluetooth status
                color, weight = (0, 255, 0) if self.bt_transmitter.connected else (0, 0, 255), 1
            else:
                color, weight = (255, 255, 255), 1
                
            cv2.putText(frame, control, (20, y_start + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, weight)


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

    # Bluetooth Configuration
    bt_mode = get_user_choice("Configurazione Bluetooth: Server (attendi connessione) o Client (connettiti a un dispositivo)?", ["Server", "Client"])
    bt_address = None
    if bt_mode == "Client":
        bt_address = input("Inserisci l'indirizzo MAC Bluetooth del dispositivo (es. 00:11:22:33:44:55): ").strip()
        if not bt_address:
            print("Indirizzo MAC non fornito. Verrà tentato un client senza indirizzo specifico (potrebbe non funzionare).")
    
    # Initialize Bluetooth Transmitter
    bt_transmitter = BluetoothTransmitter(
        target_address=bt_address if bt_mode == "Client" else None,
        is_server=(bt_mode == "Server")
    )
    
    # Give some time for Bluetooth connection to establish
    print("Attendi la connessione Bluetooth...")
    time.sleep(5) 
    if not bt_transmitter.connected:
        print("Avviso: Connessione Bluetooth non stabilita. Assicurati che il dispositivo sia accoppiato e visibile.")

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

    # Determine available scroll directions
    scroll_direction_options_all = ["nose up/down", "mouth up/down", "eyes up/down (average)"]
    scroll_direction_options_filtered = [opt for opt in scroll_direction_options_all if 
                                         (opt == "mouth up/down" and user_config['mode_switch'] != "mouth open") or
                                         (opt == "nose up/down" and user_config['mode_switch'] != "nose up/down") or
                                         (opt == "eyes up/down (average)" and user_config['mode_switch'] != "eyes up/down (average)")]
    
    if user_config['mode_switch'] == 'mouth open' and 'mouth up/down' in scroll_direction_options_filtered:
        scroll_direction_options_filtered.remove('mouth up/down')
    # Add similar logic for other mode_switch gestures if they can also be scroll sources

    if not scroll_direction_options_filtered:
        scroll_direction_options_filtered = ["nose up/down"] # Fallback

    print("\n--- ATTENZIONE: La modalità di scroll 'bocca su/giù' o 'occhi su/giù' richiede una calibrazione manuale/visiva per una corretta interpreatazione del movimento verticale. ---")
    user_config['scroll_direction'] = get_user_choice("Scegli la direzione di SCROLL (se la gesto scelta per il cambio modalità è 'bocca aperta' o 'occhi', le opzioni relative potrebbero essere limitate):", scroll_direction_options_filtered)

    controller = HeadMouseController(show_window=show_window, user_config=user_config, bt_transmitter=bt_transmitter)
    
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
                key = cv2.waitKey(1) & 0xFF
                cv2.imshow('Head Mouse Controller', frame)
                
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
                    if isinstance(controller.open_mouth_event, OpenMouth_event):
                        controller.open_mouth_event.neutral_mouth_y = None
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
        bt_transmitter.close() # Ensure Bluetooth connection is closed
        print("Controller chiuso")


if __name__ == "__main__":
    main()