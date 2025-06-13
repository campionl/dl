import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math

class HeadMouseController:
    def __init__(self):
        # Inizializza MediaPipe Face Mesh per il rilevamento dei landmarks facciali
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,  # Rileva solo una faccia
            refine_landmarks=True,  # Affina i landmarks per maggiore precisione
            min_detection_confidence=0.5,  # Soglia minima di confidenza per il rilevamento
            min_tracking_confidence=0.5  # Soglia minima per il tracking
        )
        
        # Configurazione della webcam
        self.cap = cv2.VideoCapture(0)  # Apre la webcam predefinita
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Imposta larghezza frame
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Imposta altezza frame
        
        # Parametri per il controllo del mouse
        self.dead_zone = 0.3  # Area inattiva (30% dell'immagine) dove il mouse non si muove
        self.max_acceleration = 4.5  # Massima accelerazione del movimento del mouse
        self.base_sensitivity = 0.5  # Sensibilità base del movimento
        
        # Variabili per la calibrazione automatica
        self.center_nose_x = None  # Coordinata X centrale del naso dopo calibrazione
        self.center_nose_y = None  # Coordinata Y centrale del naso dopo calibrazione
        self.calibration_frames = 30  # Numero di frame per la calibrazione
        self.calibration_count = 0  # Contatore frame di calibrazione
        self.calibration_sum_x = 0  # Somma delle X per calibrazione
        self.calibration_sum_y = 0  # Somma delle Y per calibrazione
        
        # Area di ritaglio (crop) fisso del volto
        self.crop_bounds = None  # Coordinate (min_x, min_y, max_x, max_y)
        
        # Dimensioni dello schermo
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Variabili per lo smooth del movimento del mouse
        self.mouse_x = self.screen_width // 2  # Posizione X iniziale al centro
        self.mouse_y = self.screen_height // 2  # Posizione Y iniziale al centro
        self.smooth_factor = 0.3  # Fattore di smoothing per movimenti fluidi
        
        # Variabili per il tracciamento della velocità della testa
        self.prev_nose_x = None  # Posizione X precedente del naso
        self.prev_nose_y = None  # Posizione Y precedente del naso
        self.head_velocity = 0.0  # Velocità corrente della testa
        self.velocity_history = []  # Storico delle velocità per smoothing
        self.velocity_history_size = 5  # Dimensione dello storico velocità
        
        # Stato del movimento
        self.is_in_dead_zone = True  # Se attualmente nella zona morta
        self.was_in_dead_zone = True  # Se precedentemente nella zona morta
        
        # Disabilita il failsafe di pyautogui (evita arresti improvvisi)
        pyautogui.FAILSAFE = False
        
        print("Inizializzazione completata...")
        print("Mantieni la testa al centro per i primi 30 frame per la calibrazione")

    def get_nose_position(self, landmarks, image_shape):
        """Estrae le coordinate della punta del naso dai landmarks"""
        # Landmark 1 corrisponde alla punta del naso
        nose_tip = landmarks[1]  
        
        # Dimensioni dell'immagine
        h, w = image_shape[:2]
        
        # Coordinate normalizzate (0-1) del naso
        nose_x = nose_tip.x
        nose_y = nose_tip.y
        
        return nose_x, nose_y

    def calculate_face_bounds(self, landmarks, image_shape):
        """Calcola i confini del volto per il ritaglio (usato solo in calibrazione)"""
        h, w = image_shape[:2]
        
        # Estrae tutte le coordinate X e Y dei landmarks
        x_coords = [landmark.x * w for landmark in landmarks]
        y_coords = [landmark.y * h for landmark in landmarks]
        
        # Calcola il centro del volto
        face_center_x = sum(x_coords) / len(x_coords)
        face_center_y = sum(y_coords) / len(y_coords)
        
        # Dimensioni fisse per l'area di ritaglio
        crop_size = 200
        half_size = crop_size // 2
        
        # Calcola i confini mantenendo il ritaglio centrato
        min_x = int(face_center_x - half_size)
        max_x = int(face_center_x + half_size)
        min_y = int(face_center_y - half_size)
        max_y = int(face_center_y + half_size)
        
        # Aggiusta i confini se escono dall'immagine
        if min_x < 0:
            max_x -= min_x
            min_x = 0
        if max_x > w:
            min_x -= (max_x - w)
            max_x = w
        if min_y < 0:
            max_y -= min_y
            min_y = 0
        if max_y > h:
            min_y -= (max_y - h)
            max_y = h
            
        # Assicura che le coordinate siano valide
        min_x = max(0, min_x)
        max_x = min(w, max_x)
        min_y = max(0, min_y)
        max_y = min(h, max_y)
        
        return min_x, min_y, max_x, max_y

    def calculate_head_velocity(self, nose_x, nose_y):
        """Calcola la velocità di movimento della testa"""
        if self.prev_nose_x is None or self.prev_nose_y is None:
            # Prima misurazione, inizializza le posizioni precedenti
            self.prev_nose_x = nose_x
            self.prev_nose_y = nose_y
            return 0.0
        
        # Calcola lo spostamento dalla posizione precedente
        dx = abs(nose_x - self.prev_nose_x)
        dy = abs(nose_y - self.prev_nose_y)
        
        # Velocità come distanza euclidea
        velocity = math.sqrt(dx*dx + dy*dy)
        
        # Aggiunge la velocità allo storico
        self.velocity_history.append(velocity)
        if len(self.velocity_history) > self.velocity_history_size:
            self.velocity_history.pop(0)  # Mantiene solo le ultime velocità
        
        # Calcola la velocità media per smoothing
        avg_velocity = sum(self.velocity_history) / len(self.velocity_history)
        
        # Aggiorna le posizioni precedenti
        self.prev_nose_x = nose_x
        self.prev_nose_y = nose_y
        
        return avg_velocity
        
    def apply_dead_zone_and_acceleration(self, dx, dy, head_velocity):
        """Applica la zona morta e calcola l'accelerazione del mouse"""
        # Calcola la distanza dal centro
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Verifica se siamo nella zona morta
        self.is_in_dead_zone = distance < self.dead_zone
        
        if self.is_in_dead_zone:
            return 0, 0  # Nessun movimento nella zona morta
        
        # Calcola l'accelerazione basata sulla velocità della testa
        max_head_velocity = 0.2  # Velocità massima considerata
        normalized_velocity = min(head_velocity / max_head_velocity, 1.0)
        
        # Fattori per il calcolo dell'accelerazione
        position_factor = min(distance / 0.08, 1.0)  # Influenza della posizione
        velocity_factor = normalized_velocity  # Influenza della velocità
        
        # Combina i fattori (60% posizione, 40% velocità)
        combined_factor = (position_factor * 0.6) + (velocity_factor * 0.4)
        
        # Calcola l'accelerazione finale
        min_acceleration = 0.3  # Accelerazione minima
        max_acceleration = self.max_acceleration
        acceleration = min_acceleration + (combined_factor * (max_acceleration - min_acceleration))
        
        # Calcola il movimento mantenendo la direzione
        if distance > 0:
            movement_x = (dx / distance) * acceleration * self.base_sensitivity * 10
            movement_y = (dy / distance) * acceleration * self.base_sensitivity * 10
        else:
            movement_x = movement_y = 0
            
        return movement_x, movement_y

    def update_mouse_position(self, nose_x, nose_y):
        """Aggiorna la posizione del mouse basata sul movimento della testa"""
        if self.center_nose_x is None or self.center_nose_y is None:
            return  # Non aggiornare se non calibrato
        
        # Calcola la velocità della testa
        head_velocity = self.calculate_head_velocity(nose_x, nose_y)
        
        # Calcola lo spostamento dal centro
        dx = nose_x - self.center_nose_x
        dy = nose_y - self.center_nose_y
        
        # Applica zona morta e accelerazione
        movement_x, movement_y = self.apply_dead_zone_and_acceleration(dx, dy, head_velocity)
        
        if self.is_in_dead_zone:
            return  # Ferma il mouse se nella zona morta
        
        # Aggiorna la posizione del mouse
        self.mouse_x += movement_x
        self.mouse_y += movement_y
        
        # Mantiene il mouse dentro i bordi dello schermo
        self.mouse_x = max(0, min(self.screen_width - 1, self.mouse_x))
        self.mouse_y = max(0, min(self.screen_height - 1, self.mouse_y))
        
        # Applica lo smoothing al movimento
        current_mouse_x, current_mouse_y = pyautogui.position()
        smooth_x = current_mouse_x + (self.mouse_x - current_mouse_x) * self.smooth_factor
        smooth_y = current_mouse_y + (self.mouse_y - current_mouse_y) * self.smooth_factor
        
        # Muove effettivamente il mouse
        pyautogui.moveTo(smooth_x, smooth_y)

        def draw_interface(self, image, nose_x, nose_y):
            """Disegna l'interfaccia con dead zone colorata e indicatori"""
            h, w = image.shape[:2]

            # Disegna il centro di calibrazione
            if self.center_nose_x is not None and self.center_nose_y is not None:
                center_pixel_x = int(self.center_nose_x * w)
                center_pixel_y = int(self.center_nose_y * h)
                cv2.circle(image, (center_pixel_x, center_pixel_y), 8, (0, 255, 0), 2)
                cv2.circle(image, (center_pixel_x, center_pixel_y), 3, (0, 255, 0), -1)

            # Disegna la posizione attuale del naso
            nose_pixel_x = int(nose_x * w)
            nose_pixel_y = int(nose_y * h)
            nose_color = (0, 255, 255) if self.is_in_dead_zone else (0, 0, 255)
            cv2.circle(image, (nose_pixel_x, nose_pixel_y), 6, nose_color, 2)

            # Disegna la dead zone come area semi-trasparente
            if self.center_nose_x is not None and self.center_nose_y is not None:
                dead_zone_radius = int(self.dead_zone * min(w, h))
                # 1) crea overlay
                overlay = image.copy()
                # 2) disegna cerchio pieno sull'overlay
                cv2.circle(overlay, (center_pixel_x, center_pixel_y), dead_zone_radius, (0, 255, 255), -1)
                # 3) fonde overlay e immagine originale (alpha = 0.2)
                alpha = 0.2
                cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
                # 4) bordo nitido
                cv2.circle(image, (center_pixel_x, center_pixel_y), dead_zone_radius, (0, 255, 255), 2)

            # Informazioni di stato
            cv2.putText(image, f"Mouse: ({int(self.mouse_x)}, {int(self.mouse_y)})",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(image, f"Velocita: {getattr(self, 'head_velocity', 0.0):.4f}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            status_text = "ZONA MORTA" if self.is_in_dead_zone else "ATTIVO"
            status_color = (0, 255, 255) if self.is_in_dead_zone else (0, 255, 0)
            cv2.putText(image, status_text,
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

            # Testo calibrazione
            if self.calibration_count < self.calibration_frames:
                cv2.putText(image, f"Calibrazione: {self.calibration_count}/{self.calibration_frames}",
                            (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(image, "Mantieni la testa al centro!",
                            (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                cv2.putText(image, "Calibrato - Controllo attivo",
                            (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Istruzioni
            cv2.putText(image, "ESC: Esci | R: Ricalibra",
                        (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            return image


    def run(self):
        """Loop principale dell'applicazione"""
        print("Avvio controllo mouse con testa...")
        print("Premi ESC per uscire, R per ricalibrare")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Errore nella lettura della webcam")
                break
            
            # Specchia l'immagine per un effetto più naturale
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Elabora il frame con MediaPipe
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                # Ottiene la posizione del naso
                nose_x, nose_y = self.get_nose_position(face_landmarks.landmark, frame.shape)
                
                # Fase di calibrazione
                if self.calibration_count < self.calibration_frames:
                    self.calibration_sum_x += nose_x
                    self.calibration_sum_y += nose_y
                    self.calibration_count += 1
                    
                    if self.calibration_count == self.calibration_frames:
                        # Calcola la posizione centrale media
                        self.center_nose_x = self.calibration_sum_x / self.calibration_frames
                        self.center_nose_y = self.calibration_sum_y / self.calibration_frames
                        
                        # Calcola l'area di ritaglio del volto
                        self.crop_bounds = self.calculate_face_bounds(face_landmarks.landmark, frame.shape)
                        
                        # Posiziona il mouse al centro dello schermo
                        self.mouse_x = self.screen_width // 2
                        self.mouse_y = self.screen_height // 2
                        pyautogui.moveTo(self.mouse_x, self.mouse_y)
                        print("Calibrazione completata!")
                
                # Se calibrato, aggiorna la posizione del mouse
                elif self.center_nose_x is not None:
                    self.update_mouse_position(nose_x, nose_y)
                
                # Mostra il ritaglio del volto se disponibile
                if self.crop_bounds is not None:
                    min_x, min_y, max_x, max_y = self.crop_bounds
                    face_crop = frame[min_y:max_y, min_x:max_x]
                    
                    if face_crop.size > 0:
                        # Ridimensiona se necessario
                        if face_crop.shape[0] != 200 or face_crop.shape[1] != 200:
                            face_crop_display = cv2.resize(face_crop, (200, 200))
                        else:
                            face_crop_display = face_crop.copy()
                        
                        # Calcola la posizione relativa del naso nel ritaglio
                        relative_nose_x = (nose_x * frame.shape[1] - min_x) / max(1, (max_x - min_x))
                        relative_nose_y = (nose_y * frame.shape[0] - min_y) / max(1, (max_y - min_y))
                        
                        # Disegna l'interfaccia sul ritaglio
                        face_crop_display = self.draw_interface(face_crop_display, relative_nose_x, relative_nose_y)
                        
                        # Posiziona il ritaglio in basso a sinistra
                        h, w = frame.shape[:2]
                        y_offset = h - 220
                        x_offset = 20
                        
                        if y_offset >= 0 and x_offset + 200 <= w:
                            frame[y_offset:y_offset+200, x_offset:x_offset+200] = face_crop_display
            
            # Aggiunge informazioni sul frame
            frame_info = f"Risoluzione: {frame.shape[1]}x{frame.shape[0]} | FPS: Real-time"
            cv2.putText(frame, frame_info, (frame.shape[1]//2 - 200, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Mostra il frame
            cv2.imshow('Controllo Mouse con Testa', frame)
            
            # Gestione input tastiera
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC per uscire
                break
            elif key == ord('r') or key == ord('R'):  # R per ricalibrare
                print("Ricalibrazione in corso...")
                self.reset_calibration()
        
        # Rilascia le risorse
        self.cap.release()
        cv2.destroyAllWindows()
        print("Applicazione chiusa.")

if __name__ == "__main__":
    try:
        controller = HeadMouseController()
        controller.run()
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente")
    except Exception as e:
        print(f"Errore: {e}")