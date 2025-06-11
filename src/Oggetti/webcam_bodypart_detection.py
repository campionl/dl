import cv2
import mediapipe as mp
import numpy as np
import time

class FullBodyHandDetector:
    def __init__(self):
        # MediaPipe Holistic per corpo completo + mani
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles
        
        # ID delle punte delle dita
        self.finger_tips = [4, 8, 12, 16, 20]
        self.finger_pips = [3, 6, 10, 14, 18]
    
    def count_fingers(self, landmarks):
        """Conta dita alzate per una mano"""
        if not landmarks:
            return 0
        
        fingers = 0
        # Pollice
        if landmarks[4].x > landmarks[3].x:
            fingers += 1
        # Altre dita
        for i in range(1, 5):
            if landmarks[self.finger_tips[i]].y < landmarks[self.finger_pips[i]].y:
                fingers += 1
        return fingers
    
    def draw_landmarks(self, frame, results):
        """Disegna tutti i landmarks del corpo"""
        h, w = frame.shape[:2]
        
        # Disegna pose (corpo)
        if results.pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame, results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_draw_styles.get_default_pose_landmarks_style())
        
        # Disegna faccia
        if results.face_landmarks:
            self.mp_draw.draw_landmarks(
                frame, results.face_landmarks, self.mp_holistic.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_draw_styles.get_default_face_mesh_contours_style())
        
        # Disegna mano sinistra
        if results.left_hand_landmarks:
            self.mp_draw.draw_landmarks(
                frame, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.mp_draw_styles.get_default_hand_landmarks_style(),
                connection_drawing_spec=self.mp_draw_styles.get_default_hand_connections_style())
            
            # Conta dita mano sinistra
            left_fingers = self.count_fingers(results.left_hand_landmarks.landmark)
            cv2.putText(frame, f"Sinistra: {left_fingers}", (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Disegna mano destra
        if results.right_hand_landmarks:
            self.mp_draw.draw_landmarks(
                frame, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=self.mp_draw_styles.get_default_hand_landmarks_style(),
                connection_drawing_spec=self.mp_draw_styles.get_default_hand_connections_style())
            
            # Conta dita mano destra
            right_fingers = self.count_fingers(results.right_hand_landmarks.landmark)
            cv2.putText(frame, f"Destra: {right_fingers}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Totale dita
        total_fingers = 0
        if results.left_hand_landmarks:
            total_fingers += self.count_fingers(results.left_hand_landmarks.landmark)
        if results.right_hand_landmarks:
            total_fingers += self.count_fingers(results.right_hand_landmarks.landmark)
        
        cv2.putText(frame, f"Totale: {total_fingers}", (10, 130), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

def main():
    print("="*50)
    print("[SISTEMA] Rilevamento corpo completo + dita")
    print("[INFO] Premi ESC per uscire")
    print("="*50)
    
    # Inizializza
    detector = FullBodyHandDetector()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    prev_time = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip per effetto specchio
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Processo di rilevamento
            results = detector.holistic.process(frame_rgb)
            
            # Disegna tutto
            detector.draw_landmarks(frame, results)
            
            # FPS
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time
            cv2.putText(frame, f"FPS: {int(fps)}", (frame.shape[1]-150, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Mostra
            cv2.imshow("Corpo + Mani", frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                break
                
    except KeyboardInterrupt:
        print("\n[INFO] Interruzione")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()