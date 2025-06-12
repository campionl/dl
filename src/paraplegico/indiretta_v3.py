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
        self.dead_zone = 0.005  # Zona morta (2% dello schermo)
        self.max_acceleration = 3.0  # Accelerazione massima
        self.base_sensitivity = 1.0  # Sensibilità base
        
        # Posizione centro di riferimento (calibrazione automatica)
        self.center_nose_x = None
        self.center_nose_y = None
        self.calibration_frames = 30
        self.calibration_count = 0
        self.calibration_sum_x = 0
        self.calibration_sum_y = 0
        
        # Dimensioni schermo
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Smooth movement
        self.mouse_x = self.screen_width // 2
        self.mouse_y = self.screen_height // 2
        self.smooth_factor = 0.3
        
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
        """Calcola i bounds della faccia per il crop"""
        h, w = image_shape[:2]
        
        # Trova i punti estremi della faccia
        x_coords = [landmark.x * w for landmark in landmarks]
        y_coords = [landmark.y * h for landmark in landmarks]
        
        min_x = int(min(x_coords))
        max_x = int(max(x_coords))
        min_y = int(min(y_coords))
        max_y = int(max(y_coords))
        
        # Aggiungi margine
        margin = 50
        min_x = max(0, min_x - margin)
        max_x = min(w, max_x + margin)
        min_y = max(0, min_y - margin)
        max_y = min(h, max_y + margin)
        
        return min_x, min_y, max_x, max_y

    def apply_dead_zone_and_acceleration(self, dx, dy):
        """Applica zona morta e accelerazione al movimento"""
        # Calcola la distanza dal centro
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Zona morta
        if distance < self.dead_zone:
            return 0, 0
        
        # Rimuovi la zona morta dalla distanza
        effective_distance = distance - self.dead_zone
        max_distance = math.sqrt(2) - self.dead_zone  # Distanza massima possibile
        
        # Calcola l'accelerazione (quadratica)
        acceleration = min((effective_distance / max_distance) ** 2 * self.max_acceleration, self.max_acceleration)
        
        # Applica l'accelerazione mantenendo la direzione
        if distance > 0:
            movement_x = (dx / distance) * acceleration * self.base_sensitivity * 15
            movement_y = (dy / distance) * acceleration * self.base_sensitivity * 15
        else:
            movement_x = movement_y = 0
            
        return movement_x, movement_y

    def update_mouse_position(self, nose_x, nose_y):
        """Aggiorna la posizione del mouse basandosi sulla posizione del naso"""
        if self.center_nose_x is None or self.center_nose_y is None:
            return
        
        # Calcola la differenza dalla posizione centrale
        dx = nose_x - self.center_nose_x
        dy = nose_y - self.center_nose_y
        
        # Applica zona morta e accelerazione
        movement_x, movement_y = self.apply_dead_zone_and_acceleration(dx, dy)
        
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
        """Disegna l'interfaccia con indicatori"""
        h, w = image.shape[:2]
        
        # Disegna il centro di calibrazione
        if self.center_nose_x and self.center_nose_y:
            center_pixel_x = int(self.center_nose_x * w)
            center_pixel_y = int(self.center_nose_y * h)
            cv2.circle(image, (center_pixel_x, center_pixel_y), 8, (0, 255, 0), 2)
            cv2.circle(image, (center_pixel_x, center_pixel_y), 3, (0, 255, 0), -1)
        
        # Disegna la posizione attuale del naso
        nose_pixel_x = int(nose_x * w)
        nose_pixel_y = int(nose_y * h)
        cv2.circle(image, (nose_pixel_x, nose_pixel_y), 6, (0, 0, 255), 2)
        
        # Disegna la zona morta
        if self.center_nose_x and self.center_nose_y:
            dead_zone_radius = int(self.dead_zone * min(w, h))
            cv2.circle(image, (center_pixel_x, center_pixel_y), dead_zone_radius, (255, 255, 0), 2)
        
        # Informazioni di stato
        cv2.putText(image, f"Mouse: ({int(self.mouse_x)}, {int(self.mouse_y)})", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if self.calibration_count < self.calibration_frames:
            cv2.putText(image, f"Calibrazione: {self.calibration_count}/{self.calibration_frames}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(image, "Mantieni la testa al centro!", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            cv2.putText(image, "Calibrato - Controllo attivo", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
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
                        print(f"Calibrazione completata! Centro: ({self.center_nose_x:.3f}, {self.center_nose_y:.3f})")
                
                # Aggiorna posizione mouse se calibrato
                elif self.center_nose_x is not None:
                    self.update_mouse_position(nose_x, nose_y)
                
                # Calcola bounds della faccia per il crop
                min_x, min_y, max_x, max_y = self.calculate_face_bounds(face_landmarks.landmark, frame.shape)
                
                # Crea crop della faccia
                face_crop = frame[min_y:max_y, min_x:max_x]
                
                # Ridimensiona il crop per la visualizzazione (200x200 pixel)
                if face_crop.size > 0:
                    face_crop_resized = cv2.resize(face_crop, (200, 200))
                    
                    # Disegna interfaccia sul crop
                    # Calcola posizione relativa del naso nel crop
                    relative_nose_x = (nose_x * frame.shape[1] - min_x) / (max_x - min_x)
                    relative_nose_y = (nose_y * frame.shape[0] - min_y) / (max_y - min_y)
                    
                    face_crop_resized = self.draw_interface(face_crop_resized, relative_nose_x, relative_nose_y)
                    
                    # Posiziona il crop in basso a sinistra del frame principale
                    h, w = frame.shape[:2]
                    y_offset = h - 220  # 20 pixel dal bordo
                    x_offset = 20       # 20 pixel dal bordo
                    
                    if y_offset >= 0 and x_offset + 200 <= w:
                        frame[y_offset:y_offset+200, x_offset:x_offset+200] = face_crop_resized
                
                # Disegna landmarks sulla faccia (opzionale, per debug)
                # self.mp_drawing.draw_landmarks(frame, face_landmarks, self.mp_face_mesh.FACEMESH_CONTOURS)
            
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
                self.calibration_count = 0
                self.calibration_sum_x = 0
                self.calibration_sum_y = 0
        
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