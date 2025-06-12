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
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Parametri controllo mouse
        self.dead_zone = 0.030  # Zona morta ridotta (3% dello schermo)
        self.max_acceleration = 6.5  # Accelerazione massima
        self.base_sensitivity = 0.8  # Sensibilità base aumentata
        
        # Posizione centro di riferimento (calibrazione automatica)
        self.center_nose_x = None
        self.center_nose_y = None
        self.calibration_frames = 30
        self.calibration_count = 0
        self.calibration_sum_x = 0
        self.calibration_sum_y = 0
        
        # Bounds del crop fisso (calcolato solo durante calibrazione)
        self.crop_bounds = None  # (min_x, min_y, max_x, max_y)
        
        # Dimensioni schermo
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Smooth movement
        self.mouse_x = self.screen_width // 2
        self.mouse_y = self.screen_height // 2
        self.smooth_factor = 0.3
        
        # Tracciamento velocità per accelerazione
        self.prev_nose_x = None
        self.prev_nose_y = None
        self.head_velocity = 0.0
        self.velocity_history = []
        self.velocity_history_size = 5
        
        # Stato movimento
        self.is_in_dead_zone = True
        self.was_in_dead_zone = True
        
        # Disabilita fail-safe di pyautogui
        pyautogui.FAILSAFE = False
        
        print("Inizializzazione completata...")
        print("Mantieni la testa al centro per i primi 30 frame per la calibrazione")

    def get_nose_position(self, landmarks, image_shape):
        """Estrae la posizione del naso dai landmarks"""
        # Punto del naso (tip of nose)
        nose_tip = landmarks[1]  # Landmark 1 è la punta del naso
        
        h, w = image_shape[:2]
        nose_x = nose_tip.x
        nose_y = nose_tip.y
        
        return nose_x, nose_y

    def calculate_face_bounds(self, landmarks, image_shape):
        """Calcola i bounds della faccia per il crop - chiamato solo durante calibrazione"""
        h, w = image_shape[:2]
        
        # Trova i punti estremi della faccia
        x_coords = [landmark.x * w for landmark in landmarks]
        y_coords = [landmark.y * h for landmark in landmarks]
        
        face_center_x = sum(x_coords) / len(x_coords)
        face_center_y = sum(y_coords) / len(y_coords)
        
        # Dimensioni fisse per il crop (200x200 pixel)
        crop_size = 200
        half_size = crop_size // 2
        
        # Calcola i bounds mantenendo il crop centrato sulla faccia
        min_x = int(face_center_x - half_size)
        max_x = int(face_center_x + half_size)
        min_y = int(face_center_y - half_size)
        max_y = int(face_center_y + half_size)
        
        # Assicurati che il crop rimanga dentro i limiti dell'immagine
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
            
        # Assicurati che le coordinate siano valide
        min_x = max(0, min_x)
        max_x = min(w, max_x)
        min_y = max(0, min_y)
        max_y = min(h, max_y)
        
        return min_x, min_y, max_x, max_y

    def calculate_head_velocity(self, nose_x, nose_y):
        """Calcola la velocità di movimento della testa"""
        if self.prev_nose_x is None or self.prev_nose_y is None:
            self.prev_nose_x = nose_x
            self.prev_nose_y = nose_y
            return 0.0
        
        # Calcola la differenza di posizione
        dx = abs(nose_x - self.prev_nose_x)
        dy = abs(nose_y - self.prev_nose_y)
        
        # Velocità come distanza euclidea
        velocity = math.sqrt(dx*dx + dy*dy)
        
        # Aggiungi alla storia delle velocità
        self.velocity_history.append(velocity)
        if len(self.velocity_history) > self.velocity_history_size:
            self.velocity_history.pop(0)
        
        # Calcola velocità media per smoothing
        avg_velocity = sum(self.velocity_history) / len(self.velocity_history)
        
        # Aggiorna posizione precedente
        self.prev_nose_x = nose_x
        self.prev_nose_y = nose_y
        
        return avg_velocity
        
    def apply_dead_zone_and_acceleration(self, dx, dy, head_velocity):
        """Applica zona morta e accelerazione basata sulla velocità della testa"""
        # Calcola la distanza dal centro
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Zona morta
        self.is_in_dead_zone = distance < self.dead_zone
        
        if self.is_in_dead_zone:
            return 0, 0  # Ferma completamente il movimento
        
        # Calcola accelerazione basata sulla velocità della testa
        # Velocità normalizzata (0.0 - 1.0)
        max_head_velocity = 0.05  # Velocità massima della testa considerata
        normalized_velocity = min(head_velocity / max_head_velocity, 1.0)
        
        # Accelerazione basata su posizione + velocità
        position_factor = min(distance / 0.08, 1.0)  # Fattore posizione (8% dello schermo)
        velocity_factor = normalized_velocity  # Fattore velocità
        
        # Combina i due fattori (60% posizione, 40% velocità)
        combined_factor = (position_factor * 0.6) + (velocity_factor * 0.4)
        
        # Calcola accelerazione finale
        min_acceleration = 0.3  # Accelerazione minima
        max_acceleration = self.max_acceleration
        acceleration = min_acceleration + (combined_factor * (max_acceleration - min_acceleration))
        
        # Applica l'accelerazione mantenendo la direzione
        if distance > 0:
            movement_x = (dx / distance) * acceleration * self.base_sensitivity * 10
            movement_y = (dy / distance) * acceleration * self.base_sensitivity * 10
        else:
            movement_x = movement_y = 0
            
        return movement_x, movement_y

    def update_mouse_position(self, nose_x, nose_y):
        """Aggiorna la posizione del mouse basandosi sulla posizione del naso"""
        if self.center_nose_x is None or self.center_nose_y is None:
            return
        
        # Calcola la velocità della testa
        head_velocity = self.calculate_head_velocity(nose_x, nose_y)
        
        # Calcola la differenza dalla posizione centrale
        dx = nose_x - self.center_nose_x
        dy = nose_y - self.center_nose_y
        
        # Applica zona morta e accelerazione
        movement_x, movement_y = self.apply_dead_zone_and_acceleration(dx, dy, head_velocity)
        
        # Se siamo nella zona morta, ferma il mouse
        if self.is_in_dead_zone:
            return  # Non aggiornare la posizione del mouse
        
        # Aggiorna posizione mouse (movimento tipo controller)
        self.mouse_x += movement_x
        self.mouse_y += movement_y
        
        # Limita ai bounds dello schermo
        self.mouse_x = max(0, min(self.screen_width - 1, self.mouse_x))
        self.mouse_y = max(0, min(self.screen_height - 1, self.mouse_y))
        
        # Smooth movement
        current_mouse_x, current_mouse_y = pyautogui.position()
        smooth_x = current_mouse_x + (self.mouse_x - current_mouse_x) * self.smooth_factor
        smooth_y = current_mouse_y + (self.mouse_y - current_mouse_y) * self.smooth_factor
        
        # Muovi il mouse
        pyautogui.moveTo(smooth_x, smooth_y)

    def draw_interface(self, image, nose_x, nose_y):
        h, w = image.shape[:2]
        if self.center_nose_x and self.center_nose_y:
            center_pixel_x = int(self.center_nose_x * w)
            center_pixel_y = int(self.center_nose_y * h)
            cv2.circle(image, (center_pixel_x, center_pixel_y), 8, (0, 255, 0), 2)
            cv2.circle(image, (center_pixel_x, center_pixel_y), 3, (0, 255, 0), -1)

            # **Cerchio zona morta**
            dead_zone_radius = int(self.dead_zone * min(w, h))
            cv2.circle(image, (center_pixel_x, center_pixel_y), dead_zone_radius, (255, 0, 0), 2)

        nose_pixel_x = int(nose_x * w)
        nose_pixel_y = int(nose_y * h)
        nose_color = (0, 255, 255) if self.is_in_dead_zone else (0, 0, 255)
        cv2.circle(image, (nose_pixel_x, nose_pixel_y), 6, nose_color, 2)
        
        # Disegna la zona morta
        if self.center_nose_x and self.center_nose_y:
            dead_zone_radius = int(self.dead_zone * min(w, h))
            cv2.circle(image, (center_pixel_x, center_pixel_y), dead_zone_radius, (255, 255, 0), 2)
        
        # Informazioni di stato
        cv2.putText(image, f"Mouse: ({int(self.mouse_x)}, {int(self.mouse_y)})", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mostra velocità della testa
        if hasattr(self, 'head_velocity'):
            cv2.putText(image, f"Velocita: {self.head_velocity:.4f}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Stato zona morta
        status_text = "ZONA MORTA" if self.is_in_dead_zone else "ATTIVO"
        status_color = (0, 255, 255) if self.is_in_dead_zone else (0, 255, 0)
        cv2.putText(image, status_text, 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
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
            
            # Flip orizzontale per effetto specchio
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Elaborazione MediaPipe
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                # Ottieni posizione del naso
                nose_x, nose_y = self.get_nose_position(face_landmarks.landmark, frame.shape)
                
                # Calibrazione automatica
                if self.calibration_count < self.calibration_frames:
                    self.calibration_sum_x += nose_x
                    self.calibration_sum_y += nose_y
                    self.calibration_count += 1
                    
                    if self.calibration_count == self.calibration_frames:
                        self.center_nose_x = self.calibration_sum_x / self.calibration_frames
                        self.center_nose_y = self.calibration_sum_y / self.calibration_frames
                        
                        # CALCOLA I BOUNDS DEL CROP SOLO UNA VOLTA DURANTE LA CALIBRAZIONE
                        self.crop_bounds = self.calculate_face_bounds(face_landmarks.landmark, frame.shape)
                        
                        # Posiziona il mouse al centro dello schermo dopo la calibrazione
                        self.mouse_x = self.screen_width // 2
                        self.mouse_y = self.screen_height // 2
                        pyautogui.moveTo(self.mouse_x, self.mouse_y)
                        print(f"Calibrazione completata! Centro: ({self.center_nose_x:.3f}, {self.center_nose_y:.3f})")
                        print(f"Crop bounds fisso impostato: {self.crop_bounds}")
                        print("Mouse posizionato al centro dello schermo")
                
                # Aggiorna posizione mouse se calibrato
                elif self.center_nose_x is not None:
                    self.update_mouse_position(nose_x, nose_y)
                
                # Usa i bounds del crop fisso se disponibili
                if self.crop_bounds is not None:
                    min_x, min_y, max_x, max_y = self.crop_bounds
                    
                    # Crea crop della faccia con bounds fissi
                    face_crop = frame[min_y:max_y, min_x:max_x]
                    
                    # Il crop dovrebbe essere già 200x200, ma verifica per sicurezza
                    if face_crop.size > 0 and face_crop.shape[0] > 0 and face_crop.shape[1] > 0:
                        # Se il crop non è esattamente 200x200, ridimensiona
                        if face_crop.shape[0] != 200 or face_crop.shape[1] != 200:
                            face_crop_display = cv2.resize(face_crop, (200, 200))
                        else:
                            face_crop_display = face_crop.copy()
                        
                        # Disegna interfaccia sul crop
                        # Calcola posizione relativa del naso nel crop FISSO
                        relative_nose_x = (nose_x * frame.shape[1] - min_x) / max(1, (max_x - min_x))
                        relative_nose_y = (nose_y * frame.shape[0] - min_y) / max(1, (max_y - min_y))
                        
                        face_crop_display = self.draw_interface(face_crop_display, relative_nose_x, relative_nose_y)
                        
                        # Posiziona il crop in basso a sinistra del frame principale
                        h, w = frame.shape[:2]
                        y_offset = h - 220  # 20 pixel dal bordo
                        x_offset = 20       # 20 pixel dal bordo
                        
                        if y_offset >= 0 and x_offset + 200 <= w:
                            frame[y_offset:y_offset+200, x_offset:x_offset+200] = face_crop_display
            
            # Aggiungi informazioni generali sul frame principale
            frame_info = f"Risoluzione: {frame.shape[1]}x{frame.shape[0]} | FPS: Real-time"
            cv2.putText(frame, frame_info, (frame.shape[1]//2 - 200, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Mostra il frame
            cv2.imshow('Controllo Mouse con Testa', frame)
            
            # Gestione input tastiera
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('r') or key == ord('R'):  # Ricalibrare
                print("Ricalibrazione in corso...")
                self.center_nose_x = None
                self.center_nose_y = None
                self.crop_bounds = None  # RESET DEI BOUNDS DEL CROP
                self.calibration_count = 0
                self.calibration_sum_x = 0
                self.calibration_sum_y = 0
                # Reset velocità
                self.prev_nose_x = None
                self.prev_nose_y = None
                self.velocity_history = []
                # Posiziona il mouse al centro dello schermo
                self.mouse_x = self.screen_width // 2
                self.mouse_y = self.screen_height // 2
                pyautogui.moveTo(self.mouse_x, self.mouse_y)
                print("Mouse riposizionato al centro dello schermo")
        
        # Cleanup
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