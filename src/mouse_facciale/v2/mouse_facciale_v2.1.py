import cv2
import mediapipe as mp
import numpy as np
import pyautogui

class FaceMouse:
    def __init__(self):
        self.mp_face = mp.solutions.face_mesh
        self.face = self.mp_face.FaceMesh(max_num_faces=1, min_detection_confidence=0.5)
        
        # Configurazione mouse
        self.screen_w, self.screen_h = pyautogui.size()
        pyautogui.FAILSAFE = False
        
        # Punti di riferimento
        self.NOSE_TIP = 1
        self.EYE_TOP = 159
        self.EYE_BOTTOM = 145
        
        # Stato del sistema
        self.center = None
        self.cursor_pos = np.array([self.screen_w//2, self.screen_h//2])
        self.eye_closed = False

    def process_frame(self, frame):
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face.process(rgb)
        
        if results.multi_face_landmarks:
            landmarks = np.array([[lm.x * frame.shape[1], lm.y * frame.shape[0]] 
                                for lm in results.multi_face_landmarks[0].landmark])
            
            # 1. Calibrazione automatica (primi frame)
            if self.center is None:
                self.center = landmarks[self.NOSE_TIP].copy()
                return frame
            
            # 2. Movimento del mouse
            nose = landmarks[self.NOSE_TIP]
            movement = (nose - self.center) * 3  # Sensibilità
            self.cursor_pos = np.clip(self.cursor_pos + movement, [0,0], [self.screen_w-1, self.screen_h-1])
            pyautogui.moveTo(*self.cursor_pos)
            
            # 3. Rilevamento click (ammiccamento)
            eye_top = landmarks[self.EYE_TOP]
            eye_bottom = landmarks[self.EYE_BOTTOM]
            eye_height = abs(eye_top[1] - eye_bottom[1])
            
            if eye_height < 5:  # Soglia empirica
                if not self.eye_closed:  # Evita click multipli
                    pyautogui.click()
                    self.eye_closed = True
            else:
                self.eye_closed = False
            
            # Visualizzazione
            cv2.circle(frame, tuple(nose.astype(int)), 10, (0,255,0), -1)
            cv2.circle(frame, tuple(self.center.astype(int)), 5, (0,0,255), -1)
        
        return frame

def main():
    print("Face Mouse - Premi ESC per uscire")
    mouse = FaceMouse()
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        frame = mouse.process_frame(frame)
        cv2.imshow('Face Mouse', frame)
        
        if cv2.waitKey(1) == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()