import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time

class GazeMouseController:
    def __init__(self):
        # Inizializzazione MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Configurazione mouse
        self.screen_w, self.screen_h = pyautogui.size()
        self.screen_center = np.array([self.screen_w//2, self.screen_h//2])
        self.prev_pos = self.screen_center.copy()
        
        # Punti chiave del viso
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]
        self.LEFT_EYE = [33, 133]  # Angolo esterno e interno
        self.RIGHT_EYE = [362, 263] # Angolo esterno e interno
        self.NOSE_TIP = 1
        
        # Parametri di controllo
        self.smoothing = 0.85
        self.gaze_sensitivity = 1.5  # Fattore di sensibilità
        self.blink_threshold = 0.25
        self.eye_history = []
        self.HISTORY_LENGTH = 3
        
        # Calibrazione automatica
        self.calibration_complete = False
        self.neutral_gaze = None
        self.calibration_frames = 0
        self.CALIBRATION_TIME = 30  # frames

    def get_iris_center(self, landmarks, iris_points):
        """Calcola il centro dell'iride"""
        iris = [landmarks[p] for p in iris_points]
        return np.mean(iris, axis=0)

    def calibrate_neutral_gaze(self, landmarks):
        """Calibra la posizione neutra dello sguardo"""
        if self.calibration_complete:
            return
            
        left_iris = self.get_iris_center(landmarks, self.LEFT_IRIS)
        right_iris = self.get_iris_center(landmarks, self.RIGHT_IRIS)
        
        if self.calibration_frames == 0:
            self.neutral_gaze = {
                'left': left_iris,
                'right': right_iris
            }
        else:
            # Media mobile per una calibrazione più stabile
            self.neutral_gaze['left'] = 0.9*self.neutral_gaze['left'] + 0.1*left_iris
            self.neutral_gaze['right'] = 0.9*self.neutral_gaze['right'] + 0.1*right_iris
        
        self.calibration_frames += 1
        if self.calibration_frames >= self.CALIBRATION_TIME:
            self.calibration_complete = True
            print("Calibrazione completata!")

    def get_gaze_direction(self, landmarks):
        """Calcola la direzione dello sguardo rispetto alla posizione neutra"""
        if not self.calibration_complete:
            return self.screen_center
            
        # Centri iridi attuali
        left_iris = self.get_iris_center(landmarks, self.LEFT_IRIS)
        right_iris = self.get_iris_center(landmarks, self.RIGHT_IRIS)
        
        # Differenza dalla posizione neutra
        left_diff = left_iris - self.neutral_gaze['left']
        right_diff = right_iris - self.neutral_gaze['right']
        
        # Media delle due iridi
        gaze_diff = (left_diff + right_diff) / 2
        
        # Mappa sullo schermo
        screen_pos = self.screen_center + gaze_diff * np.array([self.screen_w*self.gaze_sensitivity, 
                                                              self.screen_h*self.gaze_sensitivity])
        
        return np.clip(screen_pos, [0, 0], [self.screen_w-1, self.screen_h-1])

    def smooth_movement(self, target_pos):
        """Applica smoothing al movimento"""
        smooth_pos = self.prev_pos * self.smoothing + target_pos * (1 - self.smoothing)
        self.prev_pos = smooth_pos
        return smooth_pos

    def detect_blink(self, landmarks):
        """Rileva ammicco per il click"""
        left_eye_ear = (np.linalg.norm(landmarks[159] - landmarks[145]) + 
                       np.linalg.norm(landmarks[33] - landmarks[133])) / (2 * np.linalg.norm(landmarks[33] - landmarks[133]))
        right_eye_ear = (np.linalg.norm(landmarks[386] - landmarks[374]) + 
                        np.linalg.norm(landmarks[362] - landmarks[263])) / (2 * np.linalg.norm(landmarks[362] - landmarks[263]))
        
        self.eye_history.append((left_eye_ear, right_eye_ear))
        if len(self.eye_history) > self.HISTORY_LENGTH:
            self.eye_history.pop(0)
        
        # Rileva chiusura occhi prolungata
        blink_detected = all(ear[0] < self.blink_threshold and ear[1] < self.blink_threshold 
                          for ear in self.eye_history)
        
        if blink_detected:
            pyautogui.click()
            self.eye_history = []  # Reset per evitare click multipli
            return True
        return False

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb_frame)
                
                if results.multi_face_landmarks:
                    face = results.multi_face_landmarks[0]
                    h, w = frame.shape[:2]
                    landmarks = np.array([[lm.x * w, lm.y * h] for lm in face.landmark])
                    
                    # Calibrazione automatica iniziale
                    if not self.calibration_complete:
                        self.calibrate_neutral_gaze(landmarks)
                        cv2.putText(frame, "Calibrazione in corso...", (50, 50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.putText(frame, "Mantenere lo sguardo dritto", (50, 100), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1)
                    else:
                        # Tracciamento sguardo
                        gaze_target = self.get_gaze_direction(landmarks)
                        smooth_pos = self.smooth_movement(gaze_target)
                        pyautogui.moveTo(smooth_pos[0], smooth_pos[1])
                        
                        # Rilevamento click
                        self.detect_blink(landmarks)
                        
                        # Visualizzazione
                        cv2.circle(frame, tuple(gaze_target.astype(int)), 10, (0, 255, 0), -1)
                        cv2.circle(frame, tuple(landmarks[self.NOSE_TIP].astype(int)), 5, (0, 0, 255), -1)
                
                cv2.imshow('Gaze Mouse Controller', frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    print("="*60)
    print("GAZE CONTROLLER 2.0")
    print("="*60)
    print("Sistema avanzato di puntamento oculare")
    print("Istruzioni:")
    print("- Guarda dritto durante la calibrazione iniziale (2 secondi)")
    print("- Muovi gli occhi per controllare il cursore")
    print("- Ammicca per cliccare")
    print("- Premi ESC per uscire")
    print("="*60)
    
    controller = GazeMouseController()
    controller.run()