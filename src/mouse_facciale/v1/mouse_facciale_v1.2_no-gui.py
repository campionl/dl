import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys


class HeadMouseController:
    def __init__(self):
        """
        Controller del mouse tramite movimento del naso senza visualizzazione.
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.001

        self.screen_w, self.screen_h = pyautogui.size()
        self.NOSE_TIP = 1  # Indice del punto del naso in MediaPipe

        # Sistema di controllo
        self.center_position = None
        self.last_nose_pos = np.array([320.0, 240.0])
        self.movement_sensitivity = 2.0
        self.deadzone_radius = 12.0
        
        # Calibrazione automatica
        self.center_samples = []
        self.max_center_samples = 30
        self.center_calculated = False
        
        # Posizione corrente del cursore
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])

    def auto_set_center(self, nose_pos):
        """
        Calcola automaticamente la posizione centrale basandosi sui primi frame.
        """
        if not self.center_calculated:
            self.center_samples.append(nose_pos.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                self.center_position = np.mean(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"Calibrazione completata. Centro: {self.center_position}")
                return True
        return False

    def update_cursor_position(self, nose_pos):
        """
        Aggiorna la posizione del cursore basandosi sul movimento del naso.
        """
        if self.center_position is None:
            return
        
        offset = nose_pos - self.center_position
        distance = np.linalg.norm(offset)

        # Zona morta
        if distance < self.deadzone_radius:
            return

        # Calcola movimento
        movement_factor = (distance - self.deadzone_radius) / distance
        movement_vector = offset * movement_factor * self.movement_sensitivity
        
        self.current_cursor_pos += movement_vector
        
        # Limita alle dimensioni dello schermo
        self.current_cursor_pos[0] = np.clip(self.current_cursor_pos[0], 0, self.screen_w - 1)
        self.current_cursor_pos[1] = np.clip(self.current_cursor_pos[1], 0, self.screen_h - 1)
        
        # Muovi il mouse
        try:
            pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        except Exception as e:
            print(f"Errore movimento mouse: {e}")

    def print_status(self, nose_pos):
        """
        Stampa lo stato nella console invece di mostrarlo a video.
        """
        if not self.center_calculated:
            progress = len(self.center_samples)
            print(f"\rCalibrazione in corso... {progress}/{self.max_center_samples}", end='')
        else:
            if self.center_position is not None:
                distance = np.linalg.norm(nose_pos - self.center_position)
                status = "IN MOVIMENTO" if distance > self.deadzone_radius else "FERMO"
                print(f"\rStato: {status} | Naso: {int(nose_pos[0])},{int(nose_pos[1])} | Cursore: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}", end='')


def main():
    print("="*60)
    print("HEAD MOUSE CONTROLLER - VERSIONE SENZA INTERFACCIA")
    print("="*60)
    print("Calibrazione automatica in corso...")
    print("Mantieni la testa ferma al centro per alcuni secondi.")
    print("Premi CTRL+C per uscire")
    print("="*60)

    controller = HeadMouseController()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Errore: Impossibile aprire la webcam.")
        sys.exit(1)

    # Configurazione camera ottimizzata
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Risoluzione ridotta
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 15)  # Frame rate ridotto
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Errore: Impossibile leggere il frame dalla webcam.")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = controller.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                nose_pos = landmarks_np[controller.NOSE_TIP]
                controller.last_nose_pos = nose_pos.copy()

                # Calibrazione o controllo
                if not controller.center_calculated:
                    controller.auto_set_center(nose_pos)
                else:
                    controller.update_cursor_position(nose_pos)

                controller.print_status(nose_pos)

            # Uscita con ESC (non visibile ma funzionante)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except KeyboardInterrupt:
        print("\nInterrotto dall'utente")
    except Exception as e:
        print(f"\nErrore: {e}")
    finally:
        cap.release()
        print("\nDispositivi rilasciati. Programma terminato.")


if __name__ == "__main__":
    main()