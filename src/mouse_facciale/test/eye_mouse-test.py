import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math
from collections import deque
from scipy.spatial import distance as dist

class HeadMouseController:
    def __init__(self):
        # Inizializzazione MediaPipe con parametri ottimizzati
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Configurazione PyAutoGUI
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.01
        
        # Dimensioni schermo
        self.screen_width, self.screen_height = pyautogui.size()
        self.center_screen = (self.screen_width // 2, self.screen_height // 2)
        
        # Punti di riferimento per MediaPipe (combinazione dei migliori dalle tre versioni)
        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]
        self.MOUTH_POINTS = [13, 14, 78, 308]
        
        # Parametri calibrazione (presi da claude.py e deep.py)
        self.calibration_frames = 30
        self.calibration_samples = []
        self.is_calibrated = False
        self.neutral_head_position = None
        
        # Parametri movimento (combinazione delle tre versioni)
        self.sensitivity = 1.5  # Regolabile dall'utente
        self.max_movement = 0.4  # Limite per movimenti eccessivi
        self.smooth_window = 5   # Dimensione finestra smoothing
        self.pos_history = deque(maxlen=self.smooth_window)
        
        # Parametri click (presi da chat.py e claude.py)
        self.stationary_threshold = 15  # pixel
        self.click_delay = 1.0  # secondi
        self.stationary_start_time = None
        self.last_mouse_pos = self.center_screen
        
        # Parametri bocca (combinazione delle tre versioni)
        self.mouth_open_threshold = 0.03  # Soglia per bocca aperta
        self.mouth_open_delay = 1.0  # secondi
        self.mouth_open_start_time = None
        
        # EAR threshold (da deep.py)
        self.EYE_AR_THRESH = 0.25
        self.MOUTH_AR_THRESH = 0.3
        
        # Posiziona mouse al centro all'avvio
        pyautogui.moveTo(*self.center_screen)
        
        print("=== HEAD MOUSE CONTROL ===")
        print("Posizionati di fronte alla webcam e premi INVIO per iniziare la calibrazione...")
        input()
    
    def eye_aspect_ratio(self, eye_landmarks):
        """Calcola l'Eye Aspect Ratio (da deep.py)"""
        A = dist.euclidean(eye_landmarks[1], eye_landmarks[5])
        B = dist.euclidean(eye_landmarks[2], eye_landmarks[4])
        C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])
        ear = (A + B) / (2.0 * C)
        return ear
    
    def mouth_aspect_ratio(self, mouth_landmarks):
        """Calcola il Mouth Aspect Ratio (da deep.py)"""
        A = dist.euclidean(mouth_landmarks[0], mouth_landmarks[2])
        B = dist.euclidean(mouth_landmarks[1], mouth_landmarks[3])
        mar = (A + B) / 2.0
        return mar
    
    def get_head_pose(self, landmarks, img_width, img_height):
        """Ottieni la posizione della testa (combinazione di chat.py e claude.py)"""
        # Usa il naso come punto di riferimento principale
        nose_tip = landmarks[1]
        return (nose_tip.x, nose_tip.y)
    
    def calibrate_head_position(self, head_x, head_y):
        """Calibra la posizione neutra della testa (da claude.py e deep.py)"""
        self.calibration_samples.append((head_x, head_y))
        
        if len(self.calibration_samples) >= self.calibration_frames:
            self.neutral_head_position = (
                np.mean([x for x, y in self.calibration_samples]),
                np.mean([y for x, y in self.calibration_samples])
            )
            self.is_calibrated = True
            self.calibration_samples.clear()
            print("Calibrazione completata!")
            return True
        return False
    
    def smooth_position(self, x, y):
        """Applica filtro di smoothing (combinazione delle tre versioni)"""
        self.pos_history.append((x, y))
        if not self.pos_history:
            return x, y
        
        avg_x = np.mean([p[0] for p in self.pos_history])
        avg_y = np.mean([p[1] for p in self.pos_history])
        return avg_x, avg_y
    
    def calculate_mouse_position(self, head_x, head_y):
        """Calcola la posizione del mouse (combinazione delle tre versioni)"""
        if not self.is_calibrated:
            return None
        
        # Calcola spostamento dalla posizione neutra
        delta_x = (head_x - self.neutral_head_position[0]) * self.sensitivity
        delta_y = (head_y - self.neutral_head_position[1]) * self.sensitivity
        
        # Limita movimenti eccessivi (da claude.py)
        delta_x = np.clip(delta_x, -self.max_movement, self.max_movement)
        delta_y = np.clip(delta_y, -self.max_movement, self.max_movement)
        
        # Converti in coordinate schermo
        mouse_x = self.center_screen[0] + (delta_x * self.screen_width)
        mouse_y = self.center_screen[1] + (delta_y * self.screen_height)
        
        # Applica smoothing
        mouse_x, mouse_y = self.smooth_position(mouse_x, mouse_y)
        
        # Limita alle dimensioni dello schermo
        mouse_x = np.clip(mouse_x, 0, self.screen_width - 1)
        mouse_y = np.clip(mouse_y, 0, self.screen_height - 1)
        
        return int(mouse_x), int(mouse_y)
    
    def handle_click_detection(self, current_pos, left_ear, right_ear):
        """Gestione dei click (combinazione delle tre versioni)"""
        if current_pos is None:
            return
        
        # Calcola distanza dall'ultima posizione
        distance = math.sqrt(
            (current_pos[0] - self.last_mouse_pos[0])**2 + 
            (current_pos[1] - self.last_mouse_pos[1])**2
        )
        
        # Se il mouse è fermo
        if distance < self.stationary_threshold:
            if self.stationary_start_time is None:
                self.stationary_start_time = time.time()
            elif time.time() - self.stationary_start_time >= self.click_delay:
                # Determina tipo di click
                if left_ear < self.EYE_AR_THRESH and right_ear >= self.EYE_AR_THRESH:
                    print("Doppio click sinistro!")
                    pyautogui.doubleClick()
                elif right_ear < self.EYE_AR_THRESH and left_ear >= self.EYE_AR_THRESH:
                    print("Click destro!")
                    pyautogui.rightClick()
                elif left_ear >= self.EYE_AR_THRESH and right_ear >= self.EYE_AR_THRESH:
                    print("Click sinistro!")
                    pyautogui.click()
                
                self.stationary_start_time = None
        else:
            self.stationary_start_time = None
        
        self.last_mouse_pos = current_pos
    
    def reset_to_center(self):
        """Reset del puntatore al centro e ricalibrazione (da chat.py e claude.py)"""
        print("Reset al centro - Ricalibrando...")
        pyautogui.moveTo(*self.center_screen)
        self.is_calibrated = False
        self.calibration_samples.clear()
        self.pos_history.clear()
        self.stationary_start_time = None
        self.last_mouse_pos = self.center_screen
    
    def run(self):
        """Funzione principale del controller"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Errore: Impossibile aprire la webcam")
            return
        
        print("Webcam attivata. Premi 'q' per uscire.")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Flip orizzontale per effetto specchio
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb_frame)
                
                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        landmarks = face_landmarks.landmark
                        img_height, img_width = frame.shape[:2]
                        
                        # Estrai punti di interesse
                        left_eye = [landmarks[i] for i in self.LEFT_EYE_POINTS]
                        right_eye = [landmarks[i] for i in self.RIGHT_EYE_POINTS]
                        mouth = [landmarks[i] for i in self.MOUTH_POINTS]
                        
                        # Calcola EAR e MAR
                        left_ear = self.eye_aspect_ratio(left_eye)
                        right_ear = self.eye_aspect_ratio(right_eye)
                        mar = self.mouth_aspect_ratio(mouth)
                        
                        # Ottieni posizione della testa
                        head_x, head_y = self.get_head_pose(landmarks, img_width, img_height)
                        
                        # Fase di calibrazione
                        if not self.is_calibrated:
                            calibration_progress = len(self.calibration_samples)
                            print(f"\rCalibrando... {calibration_progress}/{self.calibration_frames}", end="")
                            
                            if self.calibrate_head_position(head_x, head_y):
                                print()  # Nuova riga dopo calibrazione
                            continue
                        
                        # Calcola posizione mouse
                        mouse_pos = self.calculate_mouse_position(head_x, head_y)
                        
                        if mouse_pos is not None:
                            pyautogui.moveTo(mouse_pos[0], mouse_pos[1])
                            
                            # Gestisci click
                            self.handle_click_detection(mouse_pos, left_ear, right_ear)
                            
                            # Rileva bocca aperta per reset
                            if mar > self.MOUTH_AR_THRESH:
                                if self.mouth_open_start_time is None:
                                    self.mouth_open_start_time = time.time()
                                elif time.time() - self.mouth_open_start_time >= self.mouth_open_delay:
                                    self.reset_to_center()
                                    self.mouth_open_start_time = None
                            else:
                                self.mouth_open_start_time = None
                        
                        # Visualizza informazioni su frame (da claude.py)
                        status_text = "CALIBRATO" if self.is_calibrated else "CALIBRANDO"
                        cv2.putText(frame, f"Status: {status_text}", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        if self.is_calibrated and mouse_pos is not None:
                            cv2.putText(frame, f"Mouse: ({mouse_pos[0]}, {mouse_pos[1]})", 
                                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Mostra frame
                cv2.imshow('Head Mouse Controller', frame)
                
                # Esci con 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("\nInterrotto dall'utente")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("Controller mouse disattivato")

if __name__ == "__main__":
    controller = HeadMouseController()
    controller.run()