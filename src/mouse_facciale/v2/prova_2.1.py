import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys


class SimpleEyeMouseController:
    def __init__(self):
        """
        Controller del mouse con rilevamento ammiccamento semplificato.
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
        
        # Landmark indices
        self.NOSE_TIP = 1
        
        # Punti semplici per l'occhio sinistro (dal punto di vista utente)
        self.LEFT_EYE_TOP = 159      # Punto superiore centrale
        self.LEFT_EYE_BOTTOM = 145   # Punto inferiore centrale
        
        # Sistema di controllo
        self.center_position = None
        self.last_nose_pos = np.array([320.0, 240.0])
        self.movement_sensitivity = 3.0
        self.deadzone_radius = 15.0
        
        # Parametri per il centro automatico
        self.center_samples = []
        self.max_center_samples = 30
        self.center_calculated = False
        
        # Current cursor position
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        
        # Sistema di rilevamento ammiccamento SEMPLIFICATO
        self.eye_distance_threshold = 5.0  # Distanza minima in pixel
        self.last_click_time = 0
        self.click_cooldown = 0.8
        
        # Buffer per baseline (occhio aperto)
        self.baseline_distances = []
        self.baseline_calculated = False
        self.baseline_sample_count = 50
        self.baseline_distance = None
        
        # Buffer per stabilità
        self.distance_history = []
        self.distance_buffer_size = 3
        
        # Contatori
        self.closed_frame_count = 0
        self.required_closed_frames = 2
        
        # Debug
        self.debug_mode = True

    def calculate_eye_distance(self, landmarks):
        """
        Calcola la distanza diretta tra palpebra superiore e inferiore.
        """
        try:
            top_point = landmarks[self.LEFT_EYE_TOP]
            bottom_point = landmarks[self.LEFT_EYE_BOTTOM]
            
            # Calcola distanza euclidea semplice
            distance = np.linalg.norm(top_point - bottom_point)
            return distance
            
        except Exception as e:
            if self.debug_mode:
                print(f"Errore calcolo distanza: {e}")
            return 10.0  # Valore default per occhio aperto

    def update_baseline_distance(self, current_distance):
        """
        Calcola la baseline per occhio aperto.
        """
        if not self.baseline_calculated:
            self.baseline_distances.append(current_distance)
            
            if len(self.baseline_distances) >= self.baseline_sample_count:
                # Usa la media dei valori centrali (scarta outlier)
                sorted_distances = sorted(self.baseline_distances)
                start_idx = len(sorted_distances) // 4
                end_idx = 3 * len(sorted_distances) // 4
                
                self.baseline_distance = np.mean(sorted_distances[start_idx:end_idx])
                self.baseline_calculated = True
                
                # Imposta soglia come percentuale della baseline
                self.eye_distance_threshold = self.baseline_distance * 0.4  # 40% della baseline
                
                if self.debug_mode:
                    print(f"\n🎯 Baseline distanza occhio: {self.baseline_distance:.2f}px")
                    print(f"🎯 Soglia chiusura: {self.eye_distance_threshold:.2f}px")
                
                return True
        return False

    def detect_eye_blink(self, landmarks):
        """
        Rileva ammiccamento con metodo semplificato.
        """
        current_distance = self.calculate_eye_distance(landmarks)
        
        # Aggiorna baseline se necessario
        if not self.baseline_calculated:
            self.update_baseline_distance(current_distance)
            return False
        
        # Aggiungi al buffer
        self.distance_history.append(current_distance)
        if len(self.distance_history) > self.distance_buffer_size:
            self.distance_history.pop(0)
        
        # Calcola media per ridurre rumore
        avg_distance = np.mean(self.distance_history)
        
        # Determina se l'occhio è chiuso
        is_eye_closed = avg_distance < self.eye_distance_threshold
        
        if is_eye_closed:
            self.closed_frame_count += 1
        else:
            self.closed_frame_count = 0
        
        # Esegui click se l'occhio è stato chiuso abbastanza a lungo
        current_time = time.time()
        if (self.closed_frame_count >= self.required_closed_frames and 
            current_time - self.last_click_time > self.click_cooldown):
            
            try:
                pyautogui.click()
                self.last_click_time = current_time
                self.closed_frame_count = 0  # Reset
                
                if self.debug_mode:
                    print(f"\n🖱️  CLICK! Distanza: {avg_distance:.2f}px (soglia: {self.eye_distance_threshold:.2f}px)")
                
                return True
                
            except Exception as e:
                print(f"Errore nel click: {e}")
        
        return False

    def auto_set_center(self, nose_pos):
        """
        Calcola automaticamente la posizione centrale.
        """
        if not self.center_calculated:
            self.center_samples.append(nose_pos.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                self.center_position = np.mean(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"Centro automatico calcolato: {self.center_position}")
                return True
        return False

    def update_cursor_position(self, nose_pos):
        """
        Aggiorna la posizione del cursore.
        """
        if self.center_position is None:
            return
        
        offset = nose_pos - self.center_position
        distance = np.linalg.norm(offset)

        if distance < self.deadzone_radius:
            return

        movement_factor = (distance - self.deadzone_radius) / distance
        movement_vector = offset * movement_factor * self.movement_sensitivity
        
        self.current_cursor_pos += movement_vector
        
        self.current_cursor_pos[0] = np.clip(self.current_cursor_pos[0], 0, self.screen_w - 1)
        self.current_cursor_pos[1] = np.clip(self.current_cursor_pos[1], 0, self.screen_h - 1)
        
        try:
            pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        except Exception as e:
            print(f"Errore movimento mouse: {e}")

    def draw_interface(self, frame, nose_pos, landmarks=None, last_click_detected=False):
        """
        Disegna l'interfaccia con informazioni di debug dettagliate.
        """
        h, w = frame.shape[:2]

        if not self.center_calculated:
            # Fase 1: Calibrazione centro
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)
            
            progress = len(self.center_samples)
            cv2.putText(frame, f"FASE 1: Calibrazione centro... {progress}/{self.max_center_samples}", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            cv2.putText(frame, "Mantieni la testa ferma al centro", 
                       (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
        elif not self.baseline_calculated:
            # Fase 2: Calibrazione occhio
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (255, 165, 0), -1)
            
            baseline_progress = len(self.baseline_distances)
            cv2.putText(frame, f"FASE 2: Calibrazione occhio... {baseline_progress}/{self.baseline_sample_count}", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
            cv2.putText(frame, "Mantieni l'occhio APERTO normalmente", 
                       (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "NON chiudere l'occhio durante questa fase!", 
                       (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Mostra distanza corrente durante calibrazione
            if landmarks is not None:
                current_distance = self.calculate_eye_distance(landmarks)
                cv2.putText(frame, f"Distanza corrente: {current_distance:.2f}px", 
                           (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            # Fase 3: Controllo attivo
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 255, 0), -1)
            
            if self.center_position is not None:
                center_screen = self.center_position.astype(int)
                cv2.circle(frame, tuple(center_screen), int(self.deadzone_radius), (255, 255, 0), 2)
                cv2.circle(frame, tuple(center_screen), 3, (255, 255, 0), -1)
                
                if np.linalg.norm(nose_pos - self.center_position) > self.deadzone_radius:
                    cv2.arrowedLine(frame, tuple(center_screen), tuple(nose_pos.astype(int)), (0, 255, 255), 2)

            # Disegna indicatori occhio
            if landmarks is not None:
                top_point = landmarks[self.LEFT_EYE_TOP].astype(int)
                bottom_point = landmarks[self.LEFT_EYE_BOTTOM].astype(int)
                
                # Linea tra i punti dell'occhio
                line_color = (0, 0, 255) if len(self.distance_history) > 0 and np.mean(self.distance_history) < self.eye_distance_threshold else (0, 255, 0)
                cv2.line(frame, tuple(top_point), tuple(bottom_point), line_color, 2)
                
                # Punti
                cv2.circle(frame, tuple(top_point), 4, (255, 0, 0), -1)
                cv2.circle(frame, tuple(bottom_point), 4, (255, 0, 0), -1)
                
                # Indicatore click
                if last_click_detected:
                    cv2.circle(frame, tuple(top_point), 25, (0, 255, 0), 3)

            # Informazioni di stato
            status_color = (0, 255, 0) if last_click_detected else (0, 255, 0)
            cv2.putText(frame, "FASE 3: CONTROLLO ATTIVO", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Debug info dettagliato
            y_offset = 70
            if len(self.distance_history) > 0:
                current_distance = self.distance_history[-1]
                avg_distance = np.mean(self.distance_history)
                
                # Colore basato sullo stato
                distance_color = (0, 0, 255) if avg_distance < self.eye_distance_threshold else (0, 255, 0)
                
                cv2.putText(frame, f"Distanza occhio: {avg_distance:.2f}px", 
                           (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, distance_color, 2)
                y_offset += 25
                
                cv2.putText(frame, f"Soglia chiusura: {self.eye_distance_threshold:.2f}px", 
                           (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                y_offset += 20
                
                cv2.putText(frame, f"Baseline (aperto): {self.baseline_distance:.2f}px", 
                           (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 20
                
                cv2.putText(frame, f"Frame chiuso: {self.closed_frame_count}", 
                           (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 20
                
                # Indicatore visuale dello stato
                eye_status = "CHIUSO" if avg_distance < self.eye_distance_threshold else "APERTO"
                eye_status_color = (0, 0, 255) if avg_distance < self.eye_distance_threshold else (0, 255, 0)
                cv2.putText(frame, f"Occhio: {eye_status}", 
                           (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_status_color, 2)
                y_offset += 30

            # Cursore info
            cv2.putText(frame, f"Cursore: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}", 
                       (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Istruzioni
            cv2.putText(frame, "Muovi testa = cursore | Chiudi occhio SX = click", (20, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "ESC per uscire", (20, h-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    print("="*70)
    print("CONTROLLORE MOUSE SEMPLIFICATO - DISTANZA DIRETTA PALPEBRE")
    print("="*70)
    print("Sistema semplificato che misura la distanza diretta tra le palpebre")
    print("Dovrebbe essere molto più affidabile per il rilevamento ammiccamento")
    print("="*70)
    print("FASI:")
    print("1. Calibrazione centro (testa ferma)")
    print("2. Calibrazione occhio (occhio APERTO - NON chiudere!)")
    print("3. Controllo attivo")
    print("="*70)

    controller = SimpleEyeMouseController()
    
    # Ricerca webcam
    cap = None
    video_sources = [0, 1, 2, '/dev/video0', '/dev/video1', '/dev/video2']
    
    print("Ricerca webcam disponibili...")
    for source in video_sources:
        print(f"Tentativo con fonte video: {source}")
        test_cap = cv2.VideoCapture(source)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret:
                cap = test_cap
                print(f"✓ Webcam trovata su: {source}")
                break
            else:
                test_cap.release()
        else:
            if hasattr(test_cap, 'release'):
                test_cap.release()
    
    if cap is None or not cap.isOpened():
        print("="*60)
        print("ERRORE: Nessuna webcam trovata!")
        print("="*60)
        sys.exit(1)

    # Impostazioni camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("\n🚀 Avvio programma...")
    print("⚠️  IMPORTANTE: Durante la fase 2, mantieni l'occhio APERTO!")
    
    try:
        last_click_detected = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Impossibile leggere il frame.")
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

                # Sequenza delle fasi
                if not controller.center_calculated:
                    # Fase 1: Calibrazione centro
                    controller.auto_set_center(nose_pos)
                elif not controller.baseline_calculated:
                    # Fase 2: Calibrazione baseline occhio (solo calcolo, no click)
                    current_distance = controller.calculate_eye_distance(landmarks_np)
                    controller.update_baseline_distance(current_distance)
                else:
                    # Fase 3: Controllo attivo
                    controller.update_cursor_position(nose_pos)
                    last_click_detected = controller.detect_eye_blink(landmarks_np)

                controller.draw_interface(frame, controller.last_nose_pos, landmarks_np, last_click_detected)
            else:
                controller.draw_interface(frame, controller.last_nose_pos)
                
            cv2.imshow('Mouse Controller - Distanza Diretta', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    except KeyboardInterrupt:
        print("\nInterrotto dall'utente")
    except Exception as e:
        print(f"Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Pulizia completata.")


if __name__ == "__main__":
    main()