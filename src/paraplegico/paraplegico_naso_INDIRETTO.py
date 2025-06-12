import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time

class VirtualHeadMouse:
    def __init__(self):
        # Configurazione Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,  # Abilitato per migliore precisione sul naso
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Schermo e posizione del cursore
        self.screen_w, self.screen_h = pyautogui.size()
        self.cursor_pos = np.array([self.screen_w/2, self.screen_h/2], dtype=np.float32)
        
        # Punti chiave del viso (focus sul naso)
        self.NOSE_TIP = 4        # Punta del naso (più stabile)
        self.NOSE_BASE = 1        # Base del naso
        self.FOREHEAD = 10        # Fronte
        
        # Calibrazione
        self.reference_position = None
        self.calibration_samples = []
        self.calibration_duration = 3.0
        self.calibration_start = None
        self.calibrated = False
        
        # Controllo movimento
        self.mouse_sensitivity = 5
        self.movement_threshold = 5
        
        # Gestione FPS
        self.last_frame_time = 0
        self.target_fps = 30
        
        # UI
        self.show_ui = True

    def calibrate(self, nose_pos):
        self.calibration_samples.append(nose_pos)
        
        if time.time() - self.calibration_start >= self.calibration_duration:
            self.reference_position = np.mean(self.calibration_samples, axis=0)
            self.calibrated = True
            print("Calibrazione completata!")
            return True
        return False

    def process_frame(self, frame):
        current_time = time.time()
        if current_time - self.last_frame_time < 1 / self.target_fps:
            return None
        self.last_frame_time = current_time
        
        small_frame = cv2.resize(frame, (640, 480))
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        results = self.face_mesh.process(rgb_frame)
        output_frame = frame.copy() if self.show_ui else None
        
        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            h, w = small_frame.shape[:2]
            
            # Estraiamo SOLO i punti del naso (più precisi)
            nose_tip = [
                face.landmark[self.NOSE_TIP].x * w * 2, 
                face.landmark[self.NOSE_TIP].y * h * 2
            ]
            
            nose_base = [
                face.landmark[self.NOSE_BASE].x * w * 2,
                face.landmark[self.NOSE_BASE].y * h * 2
            ]
            
            # Usiamo solo la punta del naso come riferimento
            nose_pos = np.array(nose_tip, dtype=np.float32)
            
            # Calibrazione
            if not self.calibrated:
                if self.calibration_start is None:
                    print("Calibrazione in corso... Mantieni la testa ferma")
                    self.calibration_start = current_time
                    self.calibration_samples = []
                
                remaining_time = max(0, self.calibration_duration - (current_time - self.calibration_start))
                if output_frame is not None:
                    cv2.putText(
                        output_frame, 
                        f"Calibrazione: {remaining_time:.1f}s", 
                        (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                    )
                    # Mostra il punto di riferimento sulla punta del naso
                    cv2.circle(output_frame, tuple(nose_pos.astype(int)), 8, (0, 0, 255), -1)
                
                self.calibrate(nose_pos)
                return output_frame
            
            # Movimento del mouse basato SOLO sul naso
            head_movement = nose_pos - self.reference_position
            
            if np.linalg.norm(head_movement) > self.movement_threshold:
                self.cursor_pos += head_movement * (self.mouse_sensitivity / 100)
                self.cursor_pos[0] = np.clip(self.cursor_pos[0], 0, self.screen_w - 1)
                self.cursor_pos[1] = np.clip(self.cursor_pos[1], 0, self.screen_h - 1)
                pyautogui.moveTo(int(self.cursor_pos[0]), int(self.cursor_pos[1]))
            
            # UI - mostra SOLO il punto sul naso
            if self.show_ui and output_frame is not None:
                cv2.circle(output_frame, tuple(nose_pos.astype(int)), 8, (0, 255, 0), -1)
                cv2.putText(
                    output_frame, 
                    f"Cursor: {int(self.cursor_pos[0])}, {int(self.cursor_pos[1])}", 
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
                )
                cv2.putText(
                    output_frame, 
                    f"Sensibilita: {self.mouse_sensitivity} (+, -)", 
                    (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
                )
        
        return output_frame

def main():
    print("=== CONTROLLO DEL MOUSE CON IL NASO ===")
    print("Configurazione iniziale...")
    
    mouse = VirtualHeadMouse()
    cap = cv2.VideoCapture(0)
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            output_frame = mouse.process_frame(frame)
            
            if output_frame is not None:
                cv2.imshow('Naso - Controllo Mouse', output_frame)
            
            key = cv2.waitKey(1)
            if key & 0xFF == 27:
                break
            elif key == ord('+') and mouse.mouse_sensitivity < 20:
                mouse.mouse_sensitivity += 1
            elif key == ord('-') and mouse.mouse_sensitivity > 1:
                mouse.mouse_sensitivity -= 1
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Programma terminato.")

if __name__ == "__main__":
    main()