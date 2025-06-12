import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math

class HeadMouseController:
    def __init__(self):
        # Inizializza MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Configurazione webcam
        self.cap = cv2.VideoCapture(0)
        # Imposto una risoluzione comune per la webcam, se supportata
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Parametri controllo mouse
        self.dead_zone = 0.030  # Zona morta (3% dell'intervallo di movimento normalizzato)
        self.max_acceleration = 6.5  # Accelerazione massima
        self.base_sensitivity = 0.8  # Sensibilità base
        
        # Posizione centro di riferimento del naso (calibrazione automatica)
        self.center_nose_x = None
        self.center_nose_y = None
        self.calibration_frames = 30 # Numero di frame per la calibrazione
        self.calibration_count = 0
        self.calibration_sum_x = 0.0
        self.calibration_sum_y = 0.0
        
        # Bounds del crop fisso (calcolato solo durante calibrazione)
        self.crop_bounds = None  # (min_x, min_y, max_x, max_y)
        self.fixed_crop_size = 200 # Dimensione fissa del crop (es. 200x200 pixel)
        
        # Dimensioni schermo
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Variabili per smooth movement del cursore
        self.current_mouse_target_x = self.screen_width // 2
        self.current_mouse_target_y = self.screen_height // 2
        self.smooth_factor = 0.25 # Fattore di smoothing (0.0 - 1.0, più basso = più liscio)
        
        # Tracciamento velocità per accelerazione dinamica
        self.prev_nose_x = None
        self.prev_nose_y = None
        self.head_velocity = 0.0
        self.velocity_history = []
        self.velocity_history_size = 5 # Media su N frame per la velocità
        
        # Stato movimento per il comportamento "controller"
        self.current_dx = 0.0
        self.current_dy = 0.0
        
        # Disabilita fail-safe di pyautogui per evitare interruzioni accidentali
        pyautogui.FAILSAFE = False
        
        print("Inizializzazione completata...")
        print(f"Mantieni la testa al centro per i primi {self.calibration_frames} frame per la calibrazione.")

    def get_nose_position(self, landmarks, image_shape):
        """
        Estrae la posizione normalizzata del naso (punto 1) dai landmarks del viso.
        Le coordinate sono normalizzate tra 0 e 1.
        """
        if not landmarks:
            return None, None
        # Landmark 1 è la punta del naso nella mesh di MediaPipe
        nose_tip = landmarks[1]
        
        return nose_tip.x, nose_tip.y

    def calculate_face_bounds(self, landmarks, image_shape):
        """
        Calcola i bounds per un crop fisso della faccia, centrato
        sulla posizione media dei landmark della faccia.
        Questo viene chiamato solo durante la calibrazione.
        """
        h, w = image_shape[:2]
        
        if not landmarks:
            return None
        
        # Calcola il centro medio dei landmark della faccia
        x_coords = [landmark.x * w for landmark in landmarks]
        y_coords = [landmark.y * h for landmark in landmarks]
        
        face_center_x = sum(x_coords) / len(x_coords)
        face_center_y = sum(y_coords) / len(y_coords)
        
        half_size = self.fixed_crop_size // 2
        
        # Calcola i bounds del crop basandosi sul centro del viso e la dimensione fissa
        min_x = int(face_center_x - half_size)
        max_x = int(face_center_x + half_size)
        min_y = int(face_center_y - half_size)
        max_y = int(face_center_y + half_size)
        
        # Assicurati che i bounds non escano dall'immagine originale
        min_x = max(0, min_x)
        max_x = min(w, max_x)
        min_y = max(0, min_y)
        max_y = min(h, max_y)
        
        # Aggiusta i bounds se sono stati tagliati per mantenere la dimensione fissa
        if (max_x - min_x) < self.fixed_crop_size:
            if min_x == 0:
                max_x = min(w, self.fixed_crop_size)
            else: # max_x == w
                min_x = max(0, w - self.fixed_crop_size)
        
        if (max_y - min_y) < self.fixed_crop_size:
            if min_y == 0:
                max_y = min(h, self.fixed_crop_size)
            else: # max_y == h
                min_y = max(0, h - self.fixed_crop_size)

        return min_x, min_y, max_x, max_y

    def calculate_head_velocity(self, nose_x, nose_y):
        """
        Calcola la velocità di movimento del naso (e quindi della testa)
        come media della distanza tra frame.
        """
        if self.prev_nose_x is None or self.prev_nose_y is None:
            self.prev_nose_x = nose_x
            self.prev_nose_y = nose_y
            return 0.0
        
        # Calcola la differenza di posizione normalizzata
        dx_norm = abs(nose_x - self.prev_nose_x)
        dy_norm = abs(nose_y - self.prev_nose_y)
        
        # Velocità come distanza euclidea normalizzata
        velocity = math.sqrt(dx_norm**2 + dy_norm**2)
        
        self.velocity_history.append(velocity)
        if len(self.velocity_history) > self.velocity_history_size:
            self.velocity_history.pop(0)
        
        avg_velocity = sum(self.velocity_history) / len(self.velocity_history)
        
        self.prev_nose_x = nose_x
        self.prev_nose_y = nose_y
        
        return avg_velocity

    def apply_dead_zone_and_acceleration(self, dx_norm, dy_norm, head_velocity):
        """
        Applica la zona morta e calcola il movimento con accelerazione
        basata sulla distanza dal centro e sulla velocità della testa.
        """
        # Calcola la distanza euclidea normalizzata dal centro calibrato
        distance = math.sqrt(dx_norm**2 + dy_norm**2)
        
        # Determina se il naso è all'interno della zona morta
        self.is_in_dead_zone = distance < self.dead_zone
        
        if self.is_in_dead_zone:
            # Se in zona morta, il movimento si ferma
            return 0.0, 0.0
        
        # Calcola un fattore di accelerazione combinato
        # che dipende sia dalla distanza dal centro che dalla velocità della testa.
        
        # Fattore di posizione: aumenta all'aumentare della distanza dalla dead zone
        # Mappa la distanza da dead_zone a 1.0 su un intervallo di 0.1 (arbitrario)
        position_factor = min(max(0, (distance - self.dead_zone) / 0.1), 1.0)
        
        # Fattore di velocità: più veloce è la testa, più il mouse accelera
        max_head_velocity_threshold = 0.04 # Soglia di velocità per la massima accelerazione
        velocity_factor = min(head_velocity / max_head_velocity_threshold, 1.0)
        
        # Combina i due fattori (es. 70% posizione, 30% velocità)
        # Puoi regolare i pesi (0.7 e 0.3) per dare più importanza a uno o all'altro
        combined_factor = (position_factor * 0.7) + (velocity_factor * 0.3)
        
        # Calcola l'accelerazione finale
        # Minima accelerazione quando appena fuori dalla dead zone, massima quando lontano e/o veloce
        min_movement_speed = 0.01 # Velocità minima del mouse quando appena fuori dalla dead zone
        
        # Scalo il combined_factor nell'intervallo [min_movement_speed, self.max_acceleration]
        movement_speed = min_movement_speed + (combined_factor * (self.max_acceleration - min_movement_speed))
        
        # Calcola il movimento del mouse mantenendo la direzione
        # Uso la distanza come normalizzazione per mantenere la direzione corretta
        if distance > 0:
            movement_x = (dx_norm / distance) * movement_speed * self.base_sensitivity * 100 # Moltiplico per 100 per un movimento più ampio
            movement_y = (dy_norm / distance) * movement_speed * self.base_sensitivity * 100
        else:
            movement_x = movement_y = 0.0 # Caso limite per evitare divisione per zero
            
        return movement_x, movement_y

    def update_mouse_position(self, nose_x, nose_y):
        """
        Aggiorna la posizione del mouse basandosi sulla posizione del naso
        e implementa il comportamento "controller".
        """
        if self.center_nose_x is None or self.center_nose_y is None:
            return # Non posso muovere il mouse senza calibrazione
        
        # Calcola la velocità della testa
        self.head_velocity = self.calculate_head_velocity(nose_x, nose_y)
        
        # Calcola la differenza normalizzata dalla posizione centrale
        # La normalizzazione è rispetto alla dimensione del frame (0.0-1.0)
        dx_norm = nose_x - self.center_nose_x
        dy_norm = nose_y - self.center_nose_y
        
        # Applica zona morta e accelerazione per ottenere i delta di movimento
        movement_x_delta, movement_y_delta = self.apply_dead_zone_and_acceleration(dx_norm, dy_norm, self.head_velocity)
        
        # Comportamento "controller":
        # Se siamo usciti dalla zona morta, o se eravamo già fuori
        # e c'è del movimento rilevato, aggiorniamo il delta del mouse.
        # Se entriamo nella zona morta, il delta del mouse si azzera.
        if not self.is_in_dead_zone:
            # Aggiorna la direzione del movimento continuo
            self.current_dx = movement_x_delta
            self.current_dy = movement_y_delta
        else:
            # Se in zona morta, il mouse smette di muoversi
            self.current_dx = 0.0
            self.current_dy = 0.0
            
        # Aggiorna la posizione target del mouse
        self.current_mouse_target_x += self.current_dx
        self.current_mouse_target_y += self.current_dy
        
        # Limita la posizione target ai bordi dello schermo
        self.current_mouse_target_x = max(0, min(self.screen_width - 1, self.current_mouse_target_x))
        self.current_mouse_target_y = max(0, min(self.screen_height - 1, self.current_mouse_target_y))
        
        # Applica smoothing al movimento del mouse
        current_mouse_x, current_mouse_y = pyautogui.position()
        smooth_x = current_mouse_x + (self.current_mouse_target_x - current_mouse_x) * self.smooth_factor
        smooth_y = current_mouse_y + (self.current_mouse_target_y - current_mouse_y) * self.smooth_factor
        
        # Muovi il mouse
        pyautogui.moveTo(smooth_x, smooth_y)

    def draw_interface(self, image, nose_x_norm, nose_y_norm):
        """
        Disegna l'interfaccia visiva sul frame croppato del viso,
        inclusi il centro, la zona morta e la posizione del naso.
        Le coordinate nose_x_norm e nose_y_norm sono relative al crop.
        """
        h, w = image.shape[:2]
        
        # Calcola le coordinate pixel del centro e del naso nel crop
        # Assumendo che (0.5, 0.5) sia il centro del crop per la zona morta
        center_pixel_x = int(0.5 * w)
        center_pixel_y = int(0.5 * h)
        
        nose_pixel_x = int(nose_x_norm * w)
        nose_pixel_y = int(nose_y_norm * h)
        
        # Disegna il centro di riferimento nel crop (verde)
        cv2.circle(image, (center_pixel_x, center_pixel_y), 5, (0, 255, 0), -1)
        cv2.circle(image, (center_pixel_x, center_pixel_y), 8, (0, 255, 0), 2)
        
        # Disegna la zona morta (giallo)
        # La dead zone è una percentuale della dimensione più piccola del crop
        dead_zone_radius = int(self.dead_zone * min(w, h))
        cv2.circle(image, (center_pixel_x, center_pixel_y), dead_zone_radius, (0, 255, 255), 2) # Giallo

        # Disegna la posizione attuale del naso
        nose_color = (0, 0, 255) if not self.is_in_dead_zone else (255, 255, 0) # Rosso se attivo, Blu se in zona morta (cambiato da giallo a blu per distinzione)
        cv2.circle(image, (nose_pixel_x, nose_pixel_y), 7, nose_color, -1)
        cv2.circle(image, (nose_pixel_x, nose_pixel_y), 10, nose_color, 2)
        
        # Informazioni di stato
        cv2.putText(image, f"Mouse: ({int(self.current_mouse_target_x)}, {int(self.current_mouse_target_y)})", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        cv2.putText(image, f"Velocita: {self.head_velocity:.4f}", 
                        (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        status_text = "ZONA MORTA" if self.is_in_dead_zone else "ATTIVO"
        status_color = (0, 255, 255) if self.is_in_dead_zone else (0, 255, 0) # Giallo per zona morta, Verde per attivo
        cv2.putText(image, status_text, 
                        (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1, cv2.LINE_AA)
        
        if self.calibration_count < self.calibration_frames:
            calib_text = f"Calibrazione: {self.calibration_count}/{self.calibration_frames}"
            prompt_text = "Mantieni la testa al centro!"
            cv2.putText(image, calib_text, 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(image, prompt_text, 
                            (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        else:
            cv2.putText(image, "Calibrato - Controllo attivo", 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            
        return image

    def run(self):
        """Loop principale dell'applicazione per il controllo del mouse."""
        print("Avvio controllo mouse con testa...")
        print("Premi ESC per uscire, R per ricalibrare.")
        
        # Per la finestra in primo piano, creiamo una finestra non resizeable e impostiamo TOPMOST
        cv2.namedWindow('Controllo Mouse con Testa', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Controllo Mouse con Testa', cv2.WND_PROP_TOPMOST, 1)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Errore nella lettura del frame dalla webcam. Riprova.")
                break
            
            # Flip orizzontale per un effetto specchio più intuitivo
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = self.face_mesh.process(rgb_frame)
            
            # Crea una copia del frame per disegnare il crop sopra
            display_frame = frame.copy()
            
            nose_x, nose_y = None, None # Inizializza per evitare errori se non ci sono landmarks
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                # Ottieni posizione del naso normalizzata (0-1) rispetto al frame originale
                nose_x, nose_y = self.get_nose_position(face_landmarks.landmark, frame.shape)
                
                # Calibrazione automatica del centro del naso e dei bounds del crop
                if self.calibration_count < self.calibration_frames:
                    if nose_x is not None and nose_y is not None:
                        self.calibration_sum_x += nose_x
                        self.calibration_sum_y += nose_y
                        self.calibration_count += 1
                        
                        if self.calibration_count == self.calibration_frames:
                            self.center_nose_x = self.calibration_sum_x / self.calibration_frames
                            self.center_nose_y = self.calibration_sum_y / self.calibration_frames
                            
                            # Calcola i bounds del crop fisso UNA SOLA VOLTA
                            self.crop_bounds = self.calculate_face_bounds(face_landmarks.landmark, frame.shape)
                            
                            # Posiziona il mouse al centro dello schermo dopo la calibrazione
                            pyautogui.moveTo(self.screen_width // 2, self.screen_height // 2)
                            self.current_mouse_target_x = self.screen_width // 2
                            self.current_mouse_target_y = self.screen_height // 2
                            
                            print(f"Calibrazione completata! Centro naso normalizzato: ({self.center_nose_x:.3f}, {self.center_nose_y:.3f})")
                            print(f"Crop bounds fisso impostato: {self.crop_bounds}")
                            print("Mouse posizionato al centro dello schermo.")
                
                # Aggiorna posizione mouse solo se calibrato
                elif self.center_nose_x is not None and nose_x is not None and nose_y is not None:
                    self.update_mouse_position(nose_x, nose_y)
                
                # Gestione e visualizzazione del crop fisso del viso
                if self.crop_bounds is not None:
                    min_x, min_y, max_x, max_y = self.crop_bounds
                    
                    # Estrai il crop dal frame originale
                    face_crop = frame[min_y:max_y, min_x:max_x]
                    
                    # Assicurati che il crop abbia la dimensione fissa desiderata (200x200)
                    if face_crop.shape[0] > 0 and face_crop.shape[1] > 0:
                        face_crop_display = cv2.resize(face_crop, (self.fixed_crop_size, self.fixed_crop_size))
                        
                        # Calcola la posizione del naso normalizzata RELATIVAMENTE al crop fisso
                        if nose_x is not None and nose_y is not None:
                            # Trasformo le coordinate del naso dal frame originale al crop
                            nose_x_in_crop = (nose_x * frame.shape[1] - min_x) / (max_x - min_x)
                            nose_y_in_crop = (nose_y * frame.shape[0] - min_y) / (max_y - min_y)
                            
                            # Disegna l'interfaccia sul crop (passando coordinate normalizzate rispetto al crop)
                            face_crop_display = self.draw_interface(face_crop_display, nose_x_in_crop, nose_y_in_crop)
                        else:
                            # Se non viene rilevato il naso, disegna solo l'interfaccia senza il punto del naso
                            face_crop_display = self.draw_interface(face_crop_display, 0.5, 0.5) # Posizione fittizia
                            
                        # Sovrapponi il crop del viso ingrandito sul display_frame
                        # Posizione in basso a sinistra del display_frame
                        h_disp, w_disp = display_frame.shape[:2]
                        
                        # Margine dal bordo (es. 20 pixel)
                        margin = 20
                        
                        # Calcola la posizione di inizio per il posizionamento in basso a sinistra
                        y_offset_start = h_disp - self.fixed_crop_size - margin
                        x_offset_start = margin
                        
                        # Assicurati che il crop non vada fuori dai bordi del display_frame
                        if y_offset_start >= 0 and x_offset_start >= 0 and \
                           y_offset_start + self.fixed_crop_size <= h_disp and \
                           x_offset_start + self.fixed_crop_size <= w_disp:
                            display_frame[y_offset_start : y_offset_start + self.fixed_crop_size, 
                                          x_offset_start : x_offset_start + self.fixed_crop_size] = face_crop_display
                        else:
                            print("Attenzione: La dimensione del frame è troppo piccola per mostrare il crop del viso correttamente.")
                            # Se non c'è spazio sufficiente, mostra solo il frame completo
                            cv2.imshow('Controllo Mouse con Testa', display_frame)
                    else:
                        # Se il crop è vuoto (es. faccia troppo vicina al bordo), mostra il frame originale
                        cv2.imshow('Controllo Mouse con Testa', display_frame)
                else:
                    # Se non è ancora calibrato, mostra il frame originale con un messaggio
                    if self.calibration_count < self.calibration_frames:
                         cv2.putText(display_frame, f"Calibrazione in corso: {self.calibration_count}/{self.calibration_frames}", 
                                        (frame.shape[1]//2 - 250, frame.shape[0]//2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                         cv2.putText(display_frame, "Mantieni la testa al centro!", 
                                        (frame.shape[1]//2 - 200, frame.shape[0]//2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
                    cv2.imshow('Controllo Mouse con Testa', display_frame)
            else:
                # Nessun volto rilevato, mostra il frame originale con messaggio
                cv2.putText(display_frame, "Nessun volto rilevato. Assicurati che la webcam sia visibile.", 
                                (frame.shape[1]//2 - 300, frame.shape[0]//2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.imshow('Controllo Mouse con Testa', display_frame)

            # Informazioni generali sul frame principale
            frame_info = f"Risoluzione: {frame.shape[1]}x{frame.shape[0]} | FPS: Real-time"
            cv2.putText(display_frame, frame_info, (frame.shape[1]//2 - 150, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(display_frame, "ESC: Esci | R: Ricalibra", 
                            (frame.shape[1] - 250, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Mostra il frame principale
            cv2.imshow('Controllo Mouse con Testa', display_frame)
            
            # Gestione input tastiera
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC per uscire
                break
            elif key == ord('r') or key == ord('R'):  # 'R' per ricalibrare
                print("Ricalibrazione in corso...")
                self.center_nose_x = None
                self.center_nose_y = None
                self.crop_bounds = None  # Resetta i bounds del crop per ricalcolarli
                self.calibration_count = 0
                self.calibration_sum_x = 0.0
                self.calibration_sum_y = 0.0
                # Reset velocità e smoothing
                self.prev_nose_x = None
                self.prev_nose_y = None
                self.velocity_history = []
                self.current_dx = 0.0
                self.current_dy = 0.0
                # Posiziona il mouse al centro dello schermo
                pyautogui.moveTo(self.screen_width // 2, self.screen_height // 2)
                self.current_mouse_target_x = self.screen_width // 2
                self.current_mouse_target_y = self.screen_height // 2
                print("Mouse riposizionato al centro dello schermo. Avvia nuova calibrazione.")
        
        # Pulizia al termine
        self.cap.release()
        cv2.destroyAllWindows()
        print("Applicazione chiusa.")

if __name__ == "__main__":
    try:
        controller = HeadMouseController()
        controller.run()
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente.")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")