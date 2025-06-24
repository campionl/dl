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

# --- Funzione per disabilitare l'accelerazione del mouse di sistema su Linux ---
def disable_system_mouse_acceleration():
    """
    Tenta di disabilitare l'accelerazione del mouse a livello di sistema su Linux (Xorg).
    Questo è importante per evitare che il movimento del nostro mouse virtuale
    entri in conflitto con l'accelerazione del sistema, rendendo il controllo imprevedibile.
    """
    if platform.system() == "Linux": # Controlla se il sistema operativo è Linux
        try:
            # Trova l'ID del dispositivo mouse principale
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
                # Prova a disabilitare i profili di accelerazione.
                # Questo rende il movimento del mouse "piatto", senza accelerazione automatica.
                # '0, 1' per libinput significa profilo "flat" e poi "adaptive", qui impostiamo flat
                try:
                    subprocess.run(["xinput", "--set-prop", mouse_id, "libinput Accel Profile Enabled", "0, 1"], check=True)
                    subprocess.run(["xinput", "--set-prop", mouse_id, "libinput Accel Speed", "0"], check=True) # Velocità a zero per un movimento diretto
                    print(f"Probabilmente l'accelerazione del mouse è stata disabilitata per il mouse ID {mouse_id} (libinput).")
                except subprocess.CalledProcessError:
                    # Se il comando libinput fallisce, prova con proprietà più generiche
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


class Calibration_action:
    """Classe per gestire la calibrazione del centro del viso (punto neutro del naso)"""
    def __init__(self, max_samples=30):
        self.center_samples = [] # Lista di posizioni del naso per calcolare la media
        self.max_center_samples = max_samples # Quanti campioni prendere per la calibrazione
        self.center_calculated = False # Vero se il centro è stato calcolato
        self.center_position = None # La posizione media del naso che diventa il nostro "centro"
    
    def add_sample(self, tracking_point):
        """Aggiunge un campione di posizione del naso per la calibrazione"""
        if not self.center_calculated:
            self.center_samples.append(tracking_point.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                # Calcola la posizione centrale prendendo la mediana dei campioni
                self.center_position = np.median(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"Centro calibrato: {self.center_position}")
                return True # Calibrazione completata
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
        self.center_samples = [new_center] * self.max_center_samples # Riempi i campioni per coerenza
        print(f"Nuovo centro impostato manualmente/auto: {self.center_position}")


class NoseJoystick_event(BaseEvent):
    """Classe per rilevare il movimento del naso come un joystick"""
    def __init__(self, deadzone_radius=15.0, max_acceleration_distance=100.0): # RIDOTTO max_acceleration_distance
        self.deadzone_radius = deadzone_radius # Area centrale dove il cursore non si muove
        # Distanza massima dal centro per cui l'accelerazione è applicata al massimo
        self.max_acceleration_distance = max_acceleration_distance
        self.outside_deadzone_start_time = None
        self.edge_time_start = None  # Timer per quanto tempo il cursore è stato sul bordo dello schermo
        self.edge_timeout = 5.0  # Se il cursore è sul bordo per 5 secondi, ricalibra
    
    def is_outside_deadzone(self, tracking_point, center_position):
        """Controlla se il punto del naso è fuori dalla zona morta"""
        if center_position is None:
            return False
        
        offset = tracking_point - center_position
        distance = np.linalg.norm(offset) # Calcola la distanza dal centro
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
        
        # Se il naso è dentro la deadzone, nessun movimento e resetta il timer
        if distance < self.deadzone_radius:
            self.outside_deadzone_start_time = None
            return None, 0, 0
        
        # Traccia il tempo in cui il naso è fuori dalla deadzone
        current_time = time.time()
        if self.outside_deadzone_start_time is None:
            self.outside_deadzone_start_time = current_time
        
        # Calcola la distanza effettiva per l'accelerazione (escludendo la deadzone)
        effective_distance = distance - self.deadzone_radius
        # Normalizza la distanza effettiva tra 0 e 1, relativa alla distanza massima di accelerazione
        normalized_distance = min(effective_distance / (self.max_acceleration_distance - self.deadzone_radius), 1.0)
        
        # Accelerazione non lineare: più il naso è lontano, più il cursore accelera
        # Aumentato il moltiplicatore e l'esponente per una risposta più aggressiva
        acceleration_factor = 1.0 + (7.0 * normalized_distance ** 3) 
        
        # Calcola la direzione del movimento
        direction = offset / distance
        
        return direction, acceleration_factor, effective_distance
    
    def is_cursor_on_edge(self, cursor_position, screen_w, screen_h, edge_threshold=30): # AUMENTATO edge_threshold
        """Verifica se il cursore è sul bordo dello schermo per l'auto-ricalibrazione"""
        x, y = cursor_position
        # Controlla se il cursore è entro 'edge_threshold' pixel dal bordo
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
                self.edge_time_start = current_time # Inizia il timer del bordo
            elif current_time - self.edge_time_start >= self.edge_timeout:
                return True # Il cursore è sul bordo da troppo tempo
        else:
            self.edge_time_start = None # Resetta il timer se il cursore si allontana dal bordo
        
        return False
    
    def reset_outside_timer(self):
        """Resetta il timer per il tempo trascorso fuori dalla deadzone e il timer del bordo"""
        self.outside_deadzone_start_time = None
        self.edge_time_start = None
    
    def check_event(self, tracking_point, center_position):
        """Controlla se il naso è fuori dalla deadzone (base per il movimento del cursore)"""
        return self.is_outside_deadzone(tracking_point, center_position)


class OpenMouth_event(BaseEvent):
    """Classe per rilevare l'apertura della bocca"""
    def __init__(self, upper_lip_index=13, lower_lip_index=14, threshold=0.15, duration=0.5):
        self.UPPER_LIP = upper_lip_index
        self.LOWER_LIP = lower_lip_index
        self.open_threshold = threshold # Soglia di apertura per considerare la bocca "aperta"
        self.open_duration_required = duration # Per quanto tempo deve rimanere aperta per attivare l'evento
        self.open_start_time = None
        self.mouth_open = False # Stato attuale della bocca (aperta/chiusa)
        self.event_detected = False # Vero se l'evento è stato rilevato (e non si resetta finché non si chiude la bocca)
        self.mouth_history = deque(maxlen=3) # Per smussare le letture dell'apertura
        self.neutral_mouth_y = None # Usato per il potenziale scrolling verticale con la bocca
    
    def calculate_mouth_openness(self, landmarks):
        """Calcola l'apertura della bocca basandosi sulla distanza verticale delle labbra"""
        try:
            upper_lip = landmarks[self.UPPER_LIP]
            lower_lip = landmarks[self.LOWER_LIP]
            # Normalizza l'apertura rispetto a una dimensione approssimativa del viso (25.0)
            openness = abs(upper_lip[1] - lower_lip[1]) / 25.0 
            return openness
        except IndexError: # Gestisce il caso in cui i landmark non siano disponibili
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
            
            # Calibra la posizione neutra solo una volta, quando la bocca è considerata chiusa/neutra
            if self.neutral_mouth_y is None and not self.mouth_open:
                self.neutral_mouth_y = current_mouth_center_y 
                return 0.0 # Nessun offset finché non si è stabilita la posizione neutra
            
            return current_mouth_center_y - self.neutral_mouth_y
        except IndexError:
            return 0.0

    def detect_open_mouth(self, landmarks):
        """Rileva l'apertura della bocca solo se mantenuta per il tempo richiesto"""
        openness = self.calculate_mouth_openness(landmarks)
        self.mouth_history.append(openness)
        
        # Smussa l'apertura con una media mobile
        stable_openness = np.mean(list(self.mouth_history)) if self.mouth_history else openness
        current_time = time.time()
        
        # Se la bocca è aperta (sopra la soglia)
        if stable_openness > self.open_threshold:
            if not self.mouth_open and not self.event_detected:
                # Inizia l'apertura, avvia il timer
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
                self.event_detected = False  # Resetta per permettere un nuovo rilevamento
                self.neutral_mouth_y = None # Resetta la posizione neutra della bocca alla chiusura
        
        return False
    
    def is_mouth_open(self):
        """Restituisce se la bocca è attualmente aperta (anche se l'evento non è ancora scattato)"""
        return self.mouth_open
    
    def check_event(self, landmarks):
        """Verifica l'evento di bocca aperta"""
        return self.detect_open_mouth(landmarks)


class SwitchMode_action(BaseAction):
    """Classe per cambiare modalità tra puntatore e scroll"""
    def __init__(self):
        self.last_switch_time = 0
        self.switch_cooldown = 1.0  # Tempo di attesa tra un cambio di modalità e l'altro
    
    def switch_mode(self, current_mode):
        """Cambia la modalità del mouse da 'pointer' a 'scroll' e viceversa"""
        current_time = time.time()
        if current_time - self.last_switch_time < self.switch_cooldown:
            return current_mode # Non cambiare se è troppo presto
        
        new_mode = 'scroll' if current_mode == 'pointer' else 'pointer'
        print(f"Modalità cambiata: {new_mode}")
        self.last_switch_time = current_time
        return new_mode
    
    def execute(self, current_mode):
        """Esegue l'azione di cambio modalità"""
        return self.switch_mode(current_mode)


class MouseCursor_action(BaseAction):
    """Classe per tradurre il movimento del naso in movimento del cursore del mouse"""
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w # Larghezza dello schermo
        self.screen_h = screen_h # Altezza dello schermo
        self.current_mouse_pos = np.array([screen_w // 2, screen_h // 2], dtype=float)
        self.position_history = deque(maxlen=5) # Usato per smussare il movimento del cursore
        self.mouse_lock = threading.Lock() # Blocca il mouse per evitare problemi con i thread
        self.base_sensitivity = 6.0 # SENSIBILITÀ BASE AUMENTATA (da 4.0 a 6.0)
        
        self.mouse_controller = mouse.Controller() # Inizializza il controller del mouse di pynput
        self.mouse_controller.position = (self.current_mouse_pos[0], self.current_mouse_pos[1])

    def update_position(self, direction, acceleration_factor, effective_distance):
        """Aggiorna la posizione del cursore basandosi sulla direzione e l'accelerazione del naso"""
        if direction is None:
            return

        # Calcola il movimento relativo del cursore
        # Moltiplicatore finale AUMENTATO da 0.1 a 0.2 per una maggiore reattività
        movement_x = direction[0] * self.base_sensitivity * acceleration_factor * effective_distance * 0.2
        movement_y = direction[1] * self.base_sensitivity * acceleration_factor * effective_distance * 0.2

        # --- NUOVA LOGICA: FORZA DI REPULSIONE DAL BORDO ---
        # Ottieni la posizione attuale del cursore di sistema
        current_sys_x, current_sys_y = self.mouse_controller.position
        
        border_force_strength = 25.0 # Forza con cui "spingere" il cursore via dal bordo (in pixel)
        border_threshold = 40 # Quanti pixel dal bordo considerare "bordo" (più grande del precedente)

        # Applica una forza aggiuntiva per allontanare il cursore dal bordo
        # Questa forza è maggiore quanto più il cursore è vicino al bordo
        if current_sys_x <= border_threshold:
            movement_x += border_force_strength * (1 - (current_sys_x / border_threshold))
        elif current_sys_x >= self.screen_w - border_threshold:
            movement_x -= border_force_strength * (1 - ((self.screen_w - current_sys_x) / border_threshold))

        if current_sys_y <= border_threshold:
            movement_y += border_force_strength * (1 - (current_sys_y / border_threshold))
        elif current_sys_y >= self.screen_h - border_threshold:
            movement_y -= border_force_strength * (1 - ((self.screen_h - current_sys_y) / border_threshold))
        # --- FINE NUOVA LOGICA ---

        # Aggiungi il movimento alla cronologia per lo smoothing
        self.position_history.append(np.array([movement_x, movement_y]))

        # Applica lo smoothing (media dei movimenti recenti)
        if len(self.position_history) > 1:
            smoothed_movement = np.mean(self.position_history, axis=0)
        else:
            smoothed_movement = np.array([movement_x, movement_y])

        # Applica il movimento relativo al cursore di sistema usando pynput
        with self.mouse_lock:
            try:
                # pynput.mouse.Controller.move si aspetta valori interi per i pixel di movimento
                self.mouse_controller.move(int(smoothed_movement[0]), int(smoothed_movement[1]))
            except Exception as e:
                print(f"Errore durante il movimento del cursore: {e}")

    def freeze_position(self):
        """Blocca la posizione corrente del cursore (non usato direttamente per il movimento continuo)"""
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
        """Mantiene forzatamente la posizione corrente (non usato direttamente, ma utile per debug)"""
        with self.mouse_lock:
            try:
                self.mouse_controller.position = (int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1]))
            except Exception as e:
                print(f"Errore durante il mantenimento della posizione: {e}")

    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità del puntatore"""
        self.base_sensitivity = np.clip(self.base_sensitivity + amount, 0.5, 12.0) # AUMENTATO max sensitivity a 12.0
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


class Scroll_action(BaseAction):
    """Classe per eseguire lo scrolling della pagina"""
    def __init__(self, scroll_cooldown=0.03):
        self.scroll_cooldown = scroll_cooldown # Tempo minimo tra due scroll
        self.last_scroll_time = 0
        self.scroll_lock = threading.Lock()
        self.scroll_sensitivity = 3.0 # SENSIBILITÀ SCROLL AUMENTATA (da 2.0 a 3.0)
        self.scroll_history = deque(maxlen=3) # Per smussare lo scroll
        self.mouse_controller = mouse.Controller()
    
    def perform_scroll(self, direction, effective_distance):
        """Esegue lo scrolling"""
        current_time = time.time()
        if current_time - self.last_scroll_time < self.scroll_cooldown:
            return False # Non scrollare se è troppo presto
        
        try:
            with self.scroll_lock:
                # Calcola la quantità di scroll. direction[1] è il movimento verticale (asse Y)
                # La direzione dello scroll è invertita (-direction[1]) per una navigazione intuitiva
                scroll_amount = -direction[1] * effective_distance * 0.1 * self.scroll_sensitivity
                self.scroll_history.append(scroll_amount)
                smoothed_scroll = np.mean(self.scroll_history) if self.scroll_history else scroll_amount
                
                scroll_value = int(smoothed_scroll)
                if abs(scroll_value) > 0:  # Scrolla solo se c'è un movimento significativo
                    self.mouse_controller.scroll(0, scroll_value) # 0 per scroll orizzontale, scroll_value per verticale
                    self.last_scroll_time = current_time
                    return True
        except Exception as e:
            print(f"Errore durante lo scrolling: {e}")
        return False
    
    def adjust_sensitivity(self, amount):
        """Modifica la sensibilità dello scrolling"""
        self.scroll_sensitivity = np.clip(self.scroll_sensitivity + amount, 1.0, 20.0) # AUMENTATO max sensitivity a 20.0
        print(f"Sensibilità scrolling aggiornata: {self.scroll_sensitivity:.1f}")
    
    def execute(self, direction, effective_distance):
        """Esegue l'azione di scrolling"""
        return self.perform_scroll(direction, effective_distance)


class LeftEye_event(BaseEvent):
    """Classe per rilevare la chiusura dell'occhio sinistro (blink)"""
    def __init__(self, top_index=159, bottom_index=145, blink_duration=0.3):
        self.LEFT_EYE_TOP = top_index
        self.LEFT_EYE_BOTTOM = bottom_index
        self.blink_threshold = 0.10 # Soglia per considerare l'occhio chiuso (valore EAR)
        self.blink_duration_required = blink_duration # Tempo per cui l'occhio deve rimanere chiuso
        self.blink_start_time = None
        self.eye_closed = False # Stato attuale dell'occhio
        self.blink_detected = False # Vero se il blink è stato rilevato
        self.ear_history = deque(maxlen=3) # Per smussare le letture EAR
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calcola il 'Eye Aspect Ratio' (EAR) per l'occhio sinistro"""
        try:
            top = landmarks[self.LEFT_EYE_TOP]
            bottom = landmarks[self.LEFT_EYE_BOTTOM]
            # L'EAR misura l'apertura dell'occhio. Più basso è il valore, più l'occhio è chiuso.
            ear = abs(top[1] - bottom[1]) / 25.0 # Normalizzato
            return ear
        except IndexError:
            return 0.2  # Valore di default sicuro se i landmark non sono disponibili
    
    def detect_blink(self, landmarks):
        """Rileva il blink dell'occhio sinistro solo se chiuso per il tempo richiesto"""
        ear = self.calculate_eye_aspect_ratio(landmarks)
        self.ear_history.append(ear)
        
        # Smussa l'EAR con una media mobile
        stable_ear = np.mean(list(self.ear_history)) if self.ear_history else ear
        current_time = time.time()
        
        # Se l'occhio è chiuso (sotto la soglia)
        if stable_ear < self.blink_threshold:
            if not self.eye_closed and not self.blink_detected:
                self.eye_closed = True # Segna l'occhio come chiuso
                self.blink_start_time = current_time # Avvia il timer del blink
            elif (self.eye_closed and 
                  not self.blink_detected and 
                  self.blink_start_time is not None and 
                  current_time - self.blink_start_time >= self.blink_duration_required):
                self.blink_detected = True # Il blink è stato mantenuto abbastanza a lungo
                return True
        else:
            # Occhio aperto - resetta lo stato
            if self.eye_closed:
                self.eye_closed = False
                self.blink_start_time = None
                self.blink_detected = False  # Resetta per permettere un nuovo rilevamento
        
        return False
    
    def is_eye_closed(self):
        """Restituisce se l'occhio è attualmente chiuso (anche se il blink non è ancora scattato)"""
        return self.eye_closed
    
    def check_event(self, landmarks):
        """Verifica l'evento di blink dell'occhio sinistro"""
        return self.detect_blink(landmarks)


class LeftClick_action(BaseAction):
    """Classe per eseguire un click sinistro del mouse"""
    def __init__(self, click_cooldown=0.5):
        self.click_cooldown = click_cooldown # Tempo minimo tra due click
        self.last_click_time = 0
        self.mouse_lock = threading.Lock()
        self.mouse_controller = mouse.Controller()
    
    def perform_click(self, mouse_position):
        """Esegue il click sinistro alla posizione attuale del cursore di sistema"""
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False # Non cliccare se è troppo presto
        
        try:
            with self.mouse_lock:
                self.mouse_controller.click(mouse.Button.left) # Esegue il click
            print(f"Click SINISTRO")
            self.last_click_time = current_time
            return True
        except Exception as e:
            print(f"Errore click sinistro: {e}")
            return False
    
    def execute(self, mouse_position):
        """Esegue l'azione di click sinistro"""
        return self.perform_click(mouse_position)


class RightEye_event(BaseEvent):
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


class RightClick_action(BaseAction):
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
    def __init__(self, show_window=True, user_config=None):
        # Setup per MediaPipe Face Mesh (per il riconoscimento dei punti del viso)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, # Rileva al massimo una faccia
            refine_landmarks=True, # Migliora la precisione dei landmark
            min_detection_confidence=0.8, # Confidenza minima per la rilevazione della faccia
            min_tracking_confidence=0.8 # Confidenza minima per il tracciamento della faccia
        )

        # Ottieni le dimensioni dello schermo (usando pyautogui solo per questo scopo e poi lo rimuove)
        import pyautogui 
        self.screen_w, self.screen_h = pyautogui.size() 
        del pyautogui # Rimuovi pyautogui dalla memoria dopo aver ottenuto le dimensioni dello schermo

        # Indici dei landmark (punti specifici sul viso)
        self.NOSE_TIP = 4 # Punta del naso
        self.UPPER_LIP = 13 # Labbro superiore
        self.LOWER_LIP = 14 # Labbro inferiore
        
        # Inizializzazione delle classi per eventi e azioni
        self.calibration = Calibration_action() # Per calibrare il centro del naso
        # max_acceleration_distance è ridotto per una risposta più rapida dell'accelerazione
        self.nose_joystick = NoseJoystick_event(max_acceleration_distance=100.0) 
        self.mouse_cursor = MouseCursor_action(self.screen_w, self.screen_h) # Per muovere il cursore
        self.scroll_action = Scroll_action() # Per lo scrolling
        self.open_mouth_event = OpenMouth_event(self.UPPER_LIP, self.LOWER_LIP) # Per l'evento bocca aperta
        self.switch_mode_action = SwitchMode_action() # Per cambiare modalità
        self.left_eye_event = LeftEye_event() # Per l'evento occhio sinistro chiuso
        self.right_eye_event = RightEye_event() # Per l'evento occhio destro chiuso
        self.left_click_action = LeftClick_action() # Per il click sinistro
        self.right_click_action = RightClick_action() # Per il click destro
        
        # Configurazione utente (per associare gesti a azioni)
        self.user_config = user_config if user_config else {}
        self.scroll_direction_source = self.user_config.get('scroll_direction', 'nose up/down')

        # Lista delle associazioni Evento -> Azione
        self.event_action_mappings = []
        self.setup_event_action_mappings() # Configura le associazioni in base alla scelta dell'utente
        
        # Stato dell'applicazione
        self.show_window = show_window # Mostra la finestra della webcam?
        self.paused = False # L'applicazione è in pausa?
        self.current_mode = 'pointer'  # Modalità attuale: 'pointer' (muovi cursore) o 'scroll'
        self.last_mouse_pos_before_scroll = None # Salva la posizione del mouse prima di passare alla modalità scroll

    def add_event_action_mapping(self, event, action, event_args_mapper, action_args_mapper):
        """Aggiunge una mappatura evento-azione alla lista"""
        self.event_action_mappings.append({
            'event': event,
            'action': action,
            'event_args_mapper': event_args_mapper, # Funzione per mappare gli argomenti all'evento
            'action_args_mapper': action_args_mapper # Funzione per mappare gli argomenti all'azione
        })

    def setup_event_action_mappings(self):
        """Configura le mappature evento-azione in base alla configurazione utente"""
        self.event_action_mappings = [] # Resetta le mappature esistenti

        # Mappatura fissa: movimento del naso per il cursore
        self.add_event_action_mapping(
            event=self.nose_joystick,
            action=self.mouse_cursor,
            event_args_mapper=lambda tp, lm, mp: (tp, self.calibration.center_position),
            action_args_mapper=lambda tp, lm, mp: self.nose_joystick.get_movement_vector(tp, self.calibration.center_position)
        )

        # Mappature per il Click SINISTRO (basate sulla scelta dell'utente)
        if self.user_config.get('left_click') == 'right eye':
            self.add_event_action_mapping(self.right_eye_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        elif self.user_config.get('left_click') == 'left eye':
            self.add_event_action_mapping(self.left_eye_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        elif self.user_config.get('left_click') == 'mouth open':
            self.add_event_action_mapping(self.open_mouth_event, self.left_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))

        # Mappature per il Click DESTRO (basate sulla scelta dell'utente)
        if self.user_config.get('right_click') == 'right eye':
            self.add_event_action_mapping(self.right_eye_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        elif self.user_config.get('right_click') == 'left eye':
            self.add_event_action_mapping(self.left_eye_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        elif self.user_config.get('right_click') == 'mouth open':
            self.add_event_action_mapping(self.open_mouth_event, self.right_click_action, 
                                          lambda tp, lm, mp: (lm,), lambda tp, lm, mp: (mp,))
        
        # Mappature per il CAMBIO MODALITA' (basate sulla scelta dell'utente)
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
        """Attiva/disattiva la pausa dell'applicazione"""
        self.paused = not self.paused
        print(f"Applicazione {'in pausa' if self.paused else 'ripresa'}")

    def reset_mouse_position(self):
        """Riporta il cursore al centro dello schermo"""
        center_x, center_y = self.screen_w // 2, self.screen_h // 2
        self.mouse_cursor.set_position(np.array([center_x, center_y], dtype=float))

    def process_nose_movement(self, tracking_point):
        """Elabora il movimento del naso per il controllo del puntatore"""
        if self.paused or self.current_mode != 'pointer':  # Muovi il cursore solo in modalità 'pointer' e non in pausa
            return
            
        # Fase di calibrazione: se il centro non è ancora calcolato, aggiunge campioni
        if not self.calibration.center_calculated:
            self.calibration.add_sample(tracking_point)
            return
        
        # Controlla se è necessaria l'auto-ricalibrazione (se il cursore è sul bordo troppo a lungo)
        current_mouse_pos = self.mouse_cursor.get_current_position()
        if self.nose_joystick.should_recalibrate(current_mouse_pos, self.screen_w, self.screen_h):
            print("Auto-ricalibrazione attivata - cursore sul bordo per 5 secondi")
            self.calibration.set_new_center(tracking_point) # Imposta il nuovo centro basato sulla posizione attuale del naso
            self.nose_joystick.reset_outside_timer() # Resetta i timer di movimento
            self.reset_mouse_position() # Riporta il cursore al centro
            return
        
        # Ottieni il vettore di movimento (direzione, fattore di accelerazione, distanza effettiva)
        direction, acceleration_factor, effective_distance = self.nose_joystick.get_movement_vector(
            tracking_point, self.calibration.center_position
        )
        
        # Muovi il cursore
        self.mouse_cursor.update_position(direction, acceleration_factor, effective_distance)

    def process_events(self, tracking_point, landmarks):
        """Processa tutti gli eventi configurati (click, cambio modalità, scroll)"""
        if self.paused or not self.calibration.center_calculated:
            return # Non processare eventi se in pausa o non calibrato
            
        current_mouse_pos = self.mouse_cursor.get_current_position()

        # Itera su tutte le mappature evento-azione configurate
        for mapping in self.event_action_mappings:
            event_instance = mapping['event']
            action_instance = mapping['action']
            
            # Il movimento del naso è gestito separatamente in process_nose_movement
            if isinstance(event_instance, NoseJoystick_event):
                continue

            # Mappa gli argomenti necessari per controllare l'evento
            event_args = mapping['event_args_mapper'](tracking_point, landmarks, current_mouse_pos)
            
            # Se l'evento è attivo
            if event_instance.check_event(*event_args):
                if isinstance(action_instance, SwitchMode_action):
                    # Se l'evento è per il cambio modalità
                    old_mode = self.current_mode
                    new_mode = action_instance.execute(self.current_mode)
                    if new_mode != old_mode: # Se la modalità è effettivamente cambiata
                        self.current_mode = new_mode
                        if self.current_mode == 'scroll':
                            print("Passaggio a modalità SCROLL")
                            # Salva la posizione del mouse prima di passare alla modalità scroll
                            self.last_mouse_pos_before_scroll = current_mouse_pos.copy()
                            # Forza il cursore a rimanere nella sua ultima posizione durante lo scroll
                            self.mouse_cursor.freeze_position() 
                        elif self.current_mode == 'pointer':
                            print("Passaggio a modalità POINTER")
                            # Riporta il cursore alla posizione salvata prima dello scroll
                            if self.last_mouse_pos_before_scroll is not None:
                                self.mouse_cursor.set_position(self.last_mouse_pos_before_scroll)
                            # Resetta la posizione neutra della bocca per uno scrolling coerente se si usa la bocca
                            if isinstance(self.open_mouth_event, OpenMouth_event):
                                self.open_mouth_event.neutral_mouth_y = None
                elif self.current_mode == 'pointer':
                    # Esegui le azioni di click solo in modalità puntatore
                    if isinstance(action_instance, (LeftClick_action, RightClick_action)):
                        action_args = mapping['action_args_mapper'](tracking_point, landmarks, current_mouse_pos)
                        action_instance.execute(*action_args)
        
        # Gestisci lo scrolling in base alla modalità corrente e alla sorgente scelta
        if self.current_mode == 'scroll':
            scroll_direction_vector = None
            effective_distance_for_scroll = 0

            if self.scroll_direction_source == 'nose up/down':
                # Usa il movimento verticale del naso per lo scroll
                direction, _, effective_distance_for_scroll = self.nose_joystick.get_movement_vector(
                    tracking_point, self.calibration.center_position
                )
                if direction is not None:
                    # Prendi solo la componente Y (verticale) della direzione
                    scroll_direction_vector = np.array([0, direction[1]]) 
            elif self.scroll_direction_source == 'mouth up/down':
                # Usa l'offset verticale della bocca per lo scroll
                vertical_offset = self.open_mouth_event.get_vertical_offset(landmarks)
                
                scroll_threshold = 5.0 # Soglia minima di movimento della bocca per attivare lo scroll
                if abs(vertical_offset) > scroll_threshold:
                    # Determina la direzione (-1 per su, 1 per giù)
                    direction_y = 1 if vertical_offset > 0 else -1
                    scroll_direction_vector = np.array([0, direction_y])
                    effective_distance_for_scroll = abs(vertical_offset) # L'ampiezza dell'offset determina la velocità
                else:
                    # Resetta la posizione neutra della bocca se non c'è movimento significativo
                    # e la bocca non è attivamente aperta
                    if not self.open_mouth_event.is_mouth_open():
                        self.open_mouth_event.neutral_mouth_y = None

            elif self.scroll_direction_source == 'eyes up/down (average)':
                # Logica per lo scrolling basato sul movimento degli occhi (da implementare se scelto)
                print("Scrolling con occhi non ancora implementato completamente.")
                pass 
            
            if scroll_direction_vector is not None and effective_distance_for_scroll > 0:
                self.scroll_action.execute(scroll_direction_vector, effective_distance_for_scroll)


    def draw_interface(self, frame, tracking_point, landmarks=None):
        """Disegna l'interfaccia utente sulla finestra della webcam"""
        if not self.show_window:
            return

        h, w = frame.shape[:2] # Altezza e larghezza del frame

        if not self.calibration.center_calculated:
            # Mostra lo stato di calibrazione
            cv2.circle(frame, tuple(tracking_point.astype(int)), 15, (0, 165, 255), 3) # Disegna la punta del naso
            progress = len(self.calibration.center_samples)
            percentage = int((progress / self.calibration.max_center_samples) * 100)
            
            cv2.putText(frame, f"CALIBRAZIONE: {percentage}%", 
                       (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
        else:
            # Mostra lo stato attivo del controller
            color = (128, 128, 128) if self.paused else (0, 255, 0) # Colore in base allo stato (pausa/attivo)
            
            # Disegna la posizione del naso
            cv2.circle(frame, tuple(tracking_point.astype(int)), 8, color, -1)
            
            # Disegna il centro calibrato e la deadzone
            if self.calibration.center_position is not None:
                center_pt = tuple(self.calibration.center_position.astype(int))
                cv2.circle(frame, center_pt, int(self.nose_joystick.deadzone_radius), (255, 255, 0), 2)
                
                # Disegna una freccia che indica la direzione del movimento se il naso è fuori dalla deadzone
                if (self.nose_joystick.is_outside_deadzone(tracking_point, self.calibration.center_position) 
                    and not self.paused):
                    cv2.arrowedLine(frame, center_pt, tuple(tracking_point.astype(int)), (0, 255, 255), 3)
                    
                    # Mostra la zona di accelerazione massima
                    cv2.circle(frame, center_pt, int(self.nose_joystick.max_acceleration_distance), (0, 100, 255), 1)

            # Indicatori visivi per occhi e bocca
            if landmarks is not None and not self.paused:
                # Occhio Sinistro: disegna una linea tra i punti superiori e inferiori
                left_eye_top = landmarks[self.left_eye_event.LEFT_EYE_TOP].astype(int)
                left_eye_bottom = landmarks[self.left_eye_event.LEFT_EYE_BOTTOM].astype(int)
                left_eye_color = (0, 0, 255) if self.left_eye_event.is_eye_closed() else (0, 255, 0) # Rosso se chiuso, verde se aperto
                cv2.line(frame, tuple(left_eye_top), tuple(left_eye_bottom), left_eye_color, 3)
                cv2.putText(frame, "L", (left_eye_top[0] - 15, left_eye_top[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, left_eye_color, 2)
                
                # Occhio Destro
                right_eye_top = landmarks[self.right_eye_event.RIGHT_EYE_TOP].astype(int)
                right_eye_bottom = landmarks[self.right_eye_event.RIGHT_EYE_BOTTOM].astype(int)
                right_eye_color = (255, 0, 0) if self.right_eye_event.is_eye_closed() else (0, 255, 0) # Blu se chiuso, verde se aperto
                cv2.line(frame, tuple(right_eye_top), tuple(right_eye_bottom), right_eye_color, 3)
                cv2.putText(frame, "R", (right_eye_top[0] + 10, right_eye_top[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, right_eye_color, 2)
                
                # Bocca
                mouth_color = (0, 165, 255) if self.open_mouth_event.is_mouth_open() else (0, 255, 0) # Arancione se aperta, verde se chiusa
                upper_lip_pt = landmarks[self.open_mouth_event.UPPER_LIP].astype(int)
                lower_lip_pt = landmarks[self.open_mouth_event.LOWER_LIP].astype(int)
                cv2.line(frame, tuple(upper_lip_pt), tuple(lower_lip_pt), mouth_color, 3)
                cv2.putText(frame, "M", (upper_lip_pt[0] - 10, upper_lip_pt[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, mouth_color, 2)


            # Testo di stato (PAUSATO/ATTIVO)
            status_text = "PAUSATO" if self.paused else "ATTIVO"
            status_color = (0, 0, 255) if self.paused else (0, 255, 0)
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Modalità corrente (Puntatore/Scroll)
            mode_text = f"MODALITA: {self.current_mode.upper()}"
            mode_color = (255, 255, 0) if self.current_mode == 'pointer' else (0, 255, 255)
            cv2.putText(frame, mode_text, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)

            # Informazioni sulla sensibilità in base alla modalità
            if self.current_mode == 'pointer':
                cv2.putText(frame, f"Sensibilita Puntatore: {self.mouse_cursor.base_sensitivity:.1f}", 
                           (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            elif self.current_mode == 'scroll':
                cv2.putText(frame, f"Sensibilita Scroll: {self.scroll_action.scroll_sensitivity:.1f}", 
                           (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, f"Scroll Source: {self.scroll_direction_source.capitalize()}", 
                           (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


        # Lista dei controlli visualizzati sullo schermo
        controls = [
            "=== CONTROLLI ===",
            "SPAZIO = Pausa/Riprendi",
            "+/- = Modifica sensibilità (puntatore/scroll)",
            "R = Reset calibrazione",
            "ESC = Esci",
            "Auto-ricalibrazioni dopo 5s sul bordo"
        ]
        
        # Posiziona i controlli in basso a sinistra
        y_start = h - len(controls) * 20 - 10
        for i, control in enumerate(controls):
            if i == 0: # Intestazione
                color, weight = (255, 255, 0), 2
            elif i == len(controls) - 1: # Avviso auto-ricalibrazione
                color, weight = (255, 165, 0), 1
            else: # Altri controlli
                color, weight = (255, 255, 255), 1
                
            cv2.putText(frame, control, (20, y_start + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, weight)


def get_user_choice(prompt, options):
    """Funzione di aiuto per ottenere la scelta dell'utente per le associazioni dei tasti/gesti"""
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
    
    # Tenta di disabilitare l'accelerazione del mouse di sistema su Linux all'avvio
    disable_system_mouse_acceleration()

    # Chiedi all'utente se vuole mostrare la finestra della webcam
    while True:
        choice = input("Mostrare finestra webcam? (s/n): ").lower().strip()
        if choice in ['s', 'n']:
            show_window = choice == 's'
            break
        print("Inserisci 's' per sì o 'n' per no")

    # Opzioni per i gesti (click e cambio modalità)
    gesture_options = ["right eye", "left eye", "mouth open"]
    
    user_config = {}

    # Chiedi all'utente le associazioni per click sinistro, destro e cambio modalità
    user_config['left_click'] = get_user_choice("Scegli la gesto per il Click SINISTRO:", gesture_options)
    user_config['right_click'] = get_user_choice("Scegli la gesto per il Click DESTRO:", gesture_options)
    user_config['mode_switch'] = get_user_choice("Scegli la gesto per il CAMBIO MODALITA' (Puntatore/Scroll):", gesture_options)

    # Definisci le opzioni di direzione dello scroll
    scroll_direction_options_all = ["nose up/down", "mouth up/down", "eyes up/down (average)"]
    scroll_direction_options_filtered = []

    # Filtra le opzioni di scroll per evitare conflitti con la gesto di cambio modalità
    # Ad esempio, se "mouth open" è per il cambio modalità, non offrire "mouth up/down" per lo scroll
    for opt in scroll_direction_options_all:
        # Aggiungi l'opzione solo se non c'è un conflitto logico diretto
        if (opt == "mouth up/down" and user_config['mode_switch'] != "mouth open") or \
           (opt == "nose up/down" and user_config['mode_switch'] != "nose up/down") or \
           (opt == "eyes up/down (average)" and user_config['mode_switch'] != "eyes up/down (average)"):
            scroll_direction_options_filtered.append(opt)
    
    # Assicurati che ci sia sempre almeno un'opzione di scroll, fallback al naso se necessario
    if not scroll_direction_options_filtered:
        scroll_direction_options_filtered = ["nose up/down"] 

    print("\n--- ATTENZIONE: La modalità di scroll 'bocca su/giù' o 'occhi su/giù' richiede una calibrazione manuale/visiva per una corretta interpretazione del movimento verticale. ---")
    user_config['scroll_direction'] = get_user_choice("Scegli la direzione di SCROLL (se la gesto scelta per il cambio modalità è 'bocca aperta' o 'occhi', le opzioni relative potrebbero essere limitate):", scroll_direction_options_filtered)

    # Inizializza il controller del mouse facciale con le impostazioni dell'utente
    controller = HeadMouseController(show_window=show_window, user_config=user_config)
    
    # Setup della webcam
    cap = cv2.VideoCapture(0) # Apri la prima webcam disponibile
    if not cap.isOpened():
        print("Errore: Webcam non trovata! Assicurati che sia collegata e non usata da un altro programma.")
        return

    # Imposta risoluzione e frame rate della webcam per migliori prestazioni
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Stampa un riepilogo dei controlli e delle impostazioni scelte
    print("\n🎮 CONTROLLI:")
    print("SPAZIO = Pausa/Riprendi | +/- = Sensibilità (puntatore/scroll)")
    print("R = Reset calibrazione | ESC = Esci")
    print(f"Click SINISTRO: {user_config['left_click'].replace('_', ' ').capitalize()}")
    print(f"Click DESTRO: {user_config['right_click'].replace('_', ' ').capitalize()}")
    print(f"Cambio Modalità (Puntatore/Scroll): {user_config['mode_switch'].replace('_', ' ').capitalize()}")
    print(f"Direzione Scroll: {user_config['scroll_direction'].replace('_', ' ').capitalize()}")
    print("⚡ Auto-ricalibrazione dopo 5 secondi sul bordo")
    
    try:
        while True:
            ret, frame = cap.read() # Leggi un frame dalla webcam
            if not ret:
                print("Impossibile leggere il frame dalla webcam. Riprova o controlla la webcam.")
                continue

            frame = cv2.flip(frame, 1) # Specchia il frame orizzontalmente (come uno specchio)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Converti il frame in formato RGB per MediaPipe
            results = controller.face_mesh.process(rgb_frame) # Processa il frame per trovare i landmark facciali

            if results.multi_face_landmarks: # Se sono stati trovati dei landmark facciali
                face_landmarks = results.multi_face_landmarks[0] # Prendi il primo viso rilevato
                h, w = frame.shape[:2] # Ottieni altezza e larghezza del frame
                # Converte le coordinate dei landmark (da 0-1) in coordinate pixel
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                tracking_point = landmarks_np[controller.NOSE_TIP] # Il punto che seguiamo è la punta del naso
                
                if not controller.paused: # Se l'applicazione non è in pausa
                    controller.process_nose_movement(tracking_point) # Gestisci il movimento del cursore
                    controller.process_events(tracking_point, landmarks_np) # Processa click, cambio modalità, scroll
                    
                if controller.show_window: # Se l'utente ha scelto di mostrare la finestra
                    controller.draw_interface(frame, tracking_point, landmarks_np) # Disegna l'interfaccia sul frame
            else: # Se nessun viso è stato rilevato
                if controller.show_window:
                    cv2.putText(frame, "VISO NON RILEVATO", (20, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2) # Mostra un messaggio

            if controller.show_window:
                key = cv2.waitKey(1) & 0xFF # Cattura la pressione di un tasto (se la finestra è aperta)
                cv2.imshow('Head Mouse Controller', frame) # Mostra il frame nella finestra
                
                if key == 27:  # ESC per uscire
                    break
                elif key == ord(' '):  # SPAZIO per Pausa/Riprendi
                    controller.toggle_pause()
                elif key == ord('+'):  # + per aumentare la sensibilità
                    if controller.current_mode == 'pointer':
                        controller.mouse_cursor.adjust_sensitivity(0.2)
                    else:
                        controller.scroll_action.adjust_sensitivity(0.5)
                elif key == ord('-'):  # - per diminuire la sensibilità
                    if controller.current_mode == 'pointer':
                        controller.mouse_cursor.adjust_sensitivity(-0.2)
                    else:
                        controller.scroll_action.adjust_sensitivity(-0.5)
                elif key == ord('r'):  # R per resettare la calibrazione
                    controller.calibration.reset_calibration()
                    controller.nose_joystick.reset_outside_timer()
                    controller.reset_mouse_position()
                    # Resetta la posizione neutra della bocca quando si ricalibra
                    if isinstance(controller.open_mouth_event, OpenMouth_event): 
                        controller.open_mouth_event.neutral_mouth_y = None
            else:
                key = cv2.waitKey(1) & 0xFF # Cattura i tasti anche senza finestra per i controlli base
                if key == 27:  # ESC
                    break
                time.sleep(0.01) # Breve pausa per non sovraccaricare la CPU se la finestra non è mostrata

    except KeyboardInterrupt:
        print("\nInterruzione da tastiera (Ctrl+C). Chiusura dell'applicazione.")
    finally:
        cap.release() # Rilascia la webcam
        cv2.destroyAllWindows() # Chiudi tutte le finestre di OpenCV
        print("Controller mouse facciale chiuso con successo.")


if __name__ == "__main__":
    main()