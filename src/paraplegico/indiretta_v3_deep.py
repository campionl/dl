import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math

class HeadMouseController:
    def __init__(self):
        # Inizializza MediaPipe solo per il rilevamento facciale
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Webcam
        self.cap = cv2.VideoCapture(0)
        
        # Parametri controllo mouse (come da tua richiesta)
        self.dead_zone_radius = 0.15  # 15% del frame
        self.max_speed = 60           # Velocità massima
        self.accel_exponent = 1.7     # Accelerazione non-lineare
        
        # Centri di riferimento FISSI (non si aggiornano)
        self.center_x = None
        self.center_y = None
        self.calibrated = False
        
        # Finestra preview fissa
        self.preview_size = 300
        cv2.namedWindow('Face Preview', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Face Preview', self.preview_size, self.preview_size)
        screen_w, screen_h = pyautogui.size()
        cv2.moveWindow('Face Preview', 10, screen_h - self.preview_size - 40)
        cv2.setWindowProperty('Face Preview', cv2.WND_PROP_TOPMOST, 1)
        
        pyautogui.FAILSAFE = False

    def calibrate(self, nose_x, nose_y):
        """Calibra il centro una sola volta"""
        self.center_x = nose_x
        self.center_y = nose_y
        self.calibrated = True
        print(f"Centro calcolato: ({self.center_x:.3f}, {self.center_y:.3f})")

    def calculate_movement(self, nose_x, nose_y):
        """Calcola movimento SENZA tracciamento continuo"""
        if not self.calibrated:
            return 0, 0
        
        # Differenza dal centro fisso
        rel_x = (nose_x - self.center_x)
        rel_y = (nose_y - self.center_y)
        distance = math.sqrt(rel_x**2 + rel_y**2)
        
        # Zona morta
        if distance < self.dead_zone_radius:
            return 0, 0
        
        # Accelerazione non-lineare
        normalized_dist = (distance - self.dead_zone_radius) / (0.5 - self.dead_zone_radius)
        speed = self.max_speed * (normalized_dist ** self.accel_exponent)
        
        # Direzione
        angle = math.atan2(rel_y, rel_x)
        move_x = speed * math.cos(angle)
        move_y = speed * math.sin(angle)
        
        return move_x, move_y

    def create_preview(self, frame, nose_x, nose_y):
        """Crea preview con crop fisso e overlay"""
        h, w = frame.shape[:2]
        
        # Coordinate naso in pixel
        nose_px = int(nose_x * w)
        nose_py = int(nose_y * h)
        
        # Crop fisso 250x250 attorno al naso
        crop_size = 250
        x1 = max(0, nose_px - crop_size//2)
        y1 = max(0, nose_py - crop_size//2)
        x2 = min(w, nose_px + crop_size//2)
        y2 = min(h, nose_py + crop_size//2)
        
        if x2 > x1 and y2 > y1:
            face_roi = frame[y1:y2, x1:x2]
            preview = cv2.resize(face_roi, (self.preview_size, self.preview_size))
            
            # Disegna zona morta (solo se calibrato)
            if self.calibrated:
                center_preview_x = int((self.center_x * w - x1) / (x2 - x1) * self.preview_size)
                center_preview_y = int((self.center_y * h - y1) / (y2 - y1) * self.preview_size)
                dead_zone_px = int(self.dead_zone_radius * self.preview_size)
                
                cv2.circle(preview, (center_preview_x, center_preview_y), dead_zone_px, (0, 255, 255), 2)
                cv2.line(preview, (center_preview_x, center_preview_y), 
                        (self.preview_size//2, self.preview_size//2), (0, 255, 0), 2)
            
            return preview
        return np.zeros((self.preview_size, self.preview_size, 3), dtype=np.uint8)

    def run(self):
        """Loop principale"""
        print("Mantieni la testa al centro e premi 'c' per calibrare")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                nose_x, nose_y = results.multi_face_landmarks[0].landmark[1].x, results.multi_face_landmarks[0].landmark[1].y
                
                # Calibrazione manuale con tasto 'c'
                key = cv2.waitKey(1)
                if key == ord('c') and not self.calibrated:
                    self.calibrate(nose_x, nose_y)
                
                # Movimento mouse (solo se calibrato)
                if self.calibrated:
                    move_x, move_y = self.calculate_movement(nose_x, nose_y)
                    if move_x != 0 or move_y != 0:
                        pyautogui.moveRel(move_x, move_y)
                
                # Preview
                preview = self.create_preview(frame, nose_x, nose_y)
                cv2.imshow('Face Preview', preview)
            
            # Istruzioni
            cv2.putText(frame, "Premi 'c' per calibrare | ESC per uscire", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow('Webcam', frame)
            
            if cv2.waitKey(1) == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    controller = HeadMouseController()
    controller.run()