import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys
from collections import deque
import threading


class OptimizedHeadMouse:
    def __init__(self, show_window=True):
        """
        Controller del mouse ottimizzato con controllo testa e click intelligenti.
        Implementa i principi del progetto di riferimento per stabilità e personalizzazione.
        """
        # MediaPipe setup con parametri ottimizzati per stabilità
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.8,  # Aumentato per maggiore stabilità
            min_tracking_confidence=0.8
        )

        # PyAutoGUI setup
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.001

        self.screen_w, self.screen_h = pyautogui.size()
        
        # Landmark indices (usando punti più stabili come nel progetto di riferimento)
        self.FOREHEAD_CENTER = 9  # Punto fronte centrale (più stabile dell'iride)
        self.NOSE_TIP = 1
        self.LEFT_EYE_TOP = 159
        self.LEFT_EYE_BOTTOM = 145
        self.RIGHT_EYE_TOP = 386
        self.RIGHT_EYE_BOTTOM = 374
        
        # PARAMETRI PERSONALIZZABILI (come nel progetto originale)
        self.center_position = None
        self.movement_sensitivity = 2.5
        self.deadzone_radius = 20.0
        
        # Sensitivity separata per direzioni (come nel progetto originale)
        self.sensitivity_x = 1.0  # Orizzontale
        self.sensitivity_y = 1.0  # Verticale
        
        # Sistema di smoothing avanzato per ridurre jitter
        self.position_history = deque(maxlen=6)  # Aumentato per più smoothing
        self.smoothing_factor = 0.3  # Più aggressivo
        
        # Posizione mouse inizializzata al centro
        self.current_mouse_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_mouse_pos[0], self.current_mouse_pos[1])
        
        # Calibrazione migliorata
        self.center_samples = []
        self.max_center_samples = 30  # Più campioni per calibrazione più accurata
        self.center_calculated = False
        
        # Sistema click multiplo (dwell + gesture)
        self.click_mode = "dwell"
        self.last_click_time = 0
        self.click_cooldown = 0.6  # Ridotto per responsività
        
        # Dwell clicking personalizzabile
        self.dwell_time = 1.2  # Tempo ottimizzato
        self.dwell_start_time = None
        self.dwell_position = None
        self.dwell_threshold = 15  # Soglia movimento
        
        # Blink clicking migliorato per gesture volontarie
        self.blink_mode_enabled = False
        self.blink_threshold = 0.12  # Soglia per blink volontari
        self.blink_duration_required = 0.25  # Durata minima
        self.blink_start_time = None
        self.eye_closed = False
        self.ear_history = deque(maxlen=3)  # Storia per stabilità
        
        # Gesture personalizzabili (eyebrow raise per click destro)
        self.eyebrow_click_enabled = True
        self.eyebrow_threshold = 0.15
        self.last_eyebrow_click = 0
        
        # Threading per performance
        self.mouse_lock = threading.Lock()
        
        self.show_window = show_window
        self.paused = False
        
        print("=== HEAD MOUSE CONTROLLER OTTIMIZZATO ===")
        print("Basato sui principi del progetto di riferimento:")
        print("- Tracking fronte per stabilità")
        print("- Sensitivity personalizzabile per direzione")
        print("- Sistema smoothing anti-jitter")
        print("- Click personalizzabili (dwell/blink/gesture)")
        print("- Calibrazione automatica")

    def calculate_eye_aspect_ratio(self, landmarks):
        """Calcola EAR medio per entrambi gli occhi per maggiore accuratezza."""
        try:
            # Occhio sinistro
            left_top = landmarks[self.LEFT_EYE_TOP]
            left_bottom = landmarks[self.LEFT_EYE_BOTTOM]
            left_ear = abs(left_top[1] - left_bottom[1]) / 25.0
            
            # Occhio destro
            right_top = landmarks[self.RIGHT_EYE_TOP]
            right_bottom = landmarks[self.RIGHT_EYE_BOTTOM]
            right_ear = abs(right_top[1] - right_bottom[1]) / 25.0
            
            # Media per maggiore stabilità
            avg_ear = (left_ear + right_ear) / 2.0
            return avg_ear
        except:
            return 0.2  # Valore default sicuro

    def detect_voluntary_blink(self, landmarks):
        """Rileva solo blink volontari lunghi, non quelli naturali."""
        if not self.blink_mode_enabled:
            return False
            
        ear = self.calculate_eye_aspect_ratio(landmarks)
        self.ear_history.append(ear)
        
        # Stabilizza con media
        if len(self.ear_history) >= 2:
            stable_ear = np.mean(list(self.ear_history))
        else:
            stable_ear = ear
        
        current_time = time.time()
        
        # Inizio blink volontario
        if stable_ear < self.blink_threshold and not self.eye_closed:
            self.eye_closed = True
            self.blink_start_time = current_time
            return False
        
        # Fine blink - controlla se è volontario
        elif stable_ear >= self.blink_threshold and self.eye_closed:
            self.eye_closed = False
            
            if (self.blink_start_time is not None and 
                current_time - self.blink_start_time >= self.blink_duration_required and
                current_time - self.last_click_time > self.click_cooldown):
                
                self.perform_click("left")
                return True
        
        return False

    def detect_eyebrow_gesture(self, landmarks):
        """Rileva alzata di sopracciglia per click destro (gesture personalizzabile)."""
        if not self.eyebrow_click_enabled:
            return False
        
        try:
            # Usa punti sopra gli occhi per rilevare movimento sopracciglia
            eyebrow_left = landmarks[70]  # Sopra occhio sinistro
            eyebrow_right = landmarks[300]  # Sopra occhio destro
            eye_left = landmarks[self.LEFT_EYE_TOP]
            eye_right = landmarks[self.RIGHT_EYE_TOP]
            
            # Calcola distanza sopracciglia-occhi
            left_dist = abs(eyebrow_left[1] - eye_left[1])
            right_dist = abs(eyebrow_right[1] - eye_right[1])
            avg_dist = (left_dist + right_dist) / 2.0
            
            current_time = time.time()
            
            # Soglia per alzata sopracciglia
            if (avg_dist > self.eyebrow_threshold and 
                current_time - self.last_eyebrow_click > self.click_cooldown):
                
                self.last_eyebrow_click = current_time
                self.perform_click("right")
                return True
        except:
            pass
        
        return False

    def perform_click(self, click_type="left"):
        """Esegue click con gestione errori."""
        try:
            with self.mouse_lock:
                x, y = int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1])
            
            if click_type == "right":
                pyautogui.rightClick(x=x, y=y)
                print(f"Right click: ({x}, {y})")
            else:
                pyautogui.click(x=x, y=y)
                print(f"Left click: ({x}, {y})")
            
            self.last_click_time = time.time()
            return True
        except Exception as e:
            print(f"Errore click: {e}")
            return False

    def auto_calibrate_center(self, tracking_point):
        """Calibrazione centro migliorata con più campioni."""
        if not self.center_calculated:
            self.center_samples.append(tracking_point.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                # Usa mediana per robustezza contro outlier
                self.center_position = np.median(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"✓ Centro calibrato dopo {len(self.center_samples)} campioni")
                print(f"Posizione centro: {self.center_position}")
                return True
        return False

    def update_mouse_position(self, tracking_point):
        """Aggiornamento posizione con sensitivity personalizzabile per direzione."""
        if self.center_position is None or self.paused:
            return
        
        # Calcola offset dal centro
        offset = tracking_point - self.center_position
        distance = np.linalg.norm(offset)
        
        # Applica deadzone
        if distance < self.deadzone_radius:
            return
        
        # Sensitivity separata per X e Y (come nel progetto originale)
        adjusted_offset = offset.copy()
        adjusted_offset[0] *= self.sensitivity_x
        adjusted_offset[1] *= self.sensitivity_y
        
        # Calcola movimento con factor
        movement_factor = (distance - self.deadzone_radius) / distance
        screen_movement = adjusted_offset * movement_factor * self.movement_sensitivity
        
        # Smoothing avanzato anti-jitter
        self.position_history.append(screen_movement)
        if len(self.position_history) > 1:
            # Pesi decrescenti per smoothing più naturale
            weights = np.array([0.05, 0.1, 0.15, 0.2, 0.25, 0.25])[:len(self.position_history)]
            weights = weights / weights.sum()
            smoothed_movement = np.average(list(self.position_history), axis=0, weights=weights)
        else:
            smoothed_movement = screen_movement
        
        # Aggiorna posizione
        with self.mouse_lock:
            new_pos = self.current_mouse_pos + smoothed_movement
            
            # Limiti schermo
            new_pos[0] = np.clip(new_pos[0], 0, self.screen_w - 1)
            new_pos[1] = np.clip(new_pos[1], 0, self.screen_h - 1)
            
            # Movimento fluido finale
            move_vector = new_pos - self.current_mouse_pos
            self.current_mouse_pos += move_vector * self.smoothing_factor
            
            try:
                pyautogui.moveTo(int(self.current_mouse_pos[0]), int(self.current_mouse_pos[1]))
            except Exception as e:
                print(f"Errore movimento: {e}")

    def dwell_click_check(self):
        """Sistema dwell clicking personalizzabile."""
        if self.click_mode != "dwell" or self.paused:
            return False
        
        current_time = time.time()
        
        with self.mouse_lock:
            current_pos = self.current_mouse_pos.copy()
        
        # Inizializza o reset posizione dwell
        if self.dwell_position is None:
            self.dwell_position = current_pos
            self.dwell_start_time = current_time
            return False
        
        # Controlla se mouse si è mosso troppo
        distance = np.linalg.norm(current_pos - self.dwell_position)
        if distance > self.dwell_threshold:
            self.dwell_position = current_pos
            self.dwell_start_time = current_time
            return False
        
        # Controlla tempo per click
        if current_time - self.dwell_start_time >= self.dwell_time:
            if current_time - self.last_click_time > self.click_cooldown:
                self.perform_click("left")
                self.dwell_start_time = current_time  # Reset
                return True
        
        return False

    def toggle_click_mode(self):
        """Cambia modalità click tra le opzioni disponibili."""
        modes = ["dwell", "blink", "gesture"]
        current_idx = modes.index(self.click_mode)
        next_idx = (current_idx + 1) % len(modes)
        self.click_mode = modes[next_idx]
        
        # Reset stati
        self.blink_mode_enabled = self.click_mode == "blink"
        self.eyebrow_click_enabled = self.click_mode == "gesture" or self.click_mode == "dwell"
        
        mode_descriptions = {
            "dwell": "DWELL (permanenza 1.2s)",
            "blink": "BLINK volontario (250ms)",
            "gesture": "GESTURE (blink=left, eyebrow=right)"
        }
        
        print(f"Modalità click: {mode_descriptions[self.click_mode]}")

    def adjust_sensitivity(self, direction="both", increase=True):
        """Regola sensitivity con controllo separato per direzioni."""
        delta = 0.2 if increase else -0.2
        
        if direction == "both":
            self.movement_sensitivity = np.clip(self.movement_sensitivity + delta, 0.5, 5.0)
            print(f"Sensitivity generale: {self.movement_sensitivity:.1f}")
        elif direction == "x":
            self.sensitivity_x = np.clip(self.sensitivity_x + delta, 0.3, 3.0)
            print(f"Sensitivity X (orizzontale): {self.sensitivity_x:.1f}")
        elif direction == "y":
            self.sensitivity_y = np.clip(self.sensitivity_y + delta, 0.3, 3.0)
            print(f"Sensitivity Y (verticale): {self.sensitivity_y:.1f}")

    def adjust_dwell_time(self, increase=True):
        """Regola tempo dwell per personalizzazione."""
        delta = 0.2 if increase else -0.2
        self.dwell_time = np.clip(self.dwell_time + delta, 0.5, 3.0)
        print(f"Tempo dwell: {self.dwell_time:.1f}s")

    def toggle_pause(self):
        """Pausa/riprendi controllo mouse."""
        self.paused = not self.paused
        status = "PAUSATO" if self.paused else "ATTIVO"
        print(f"Controller: {status}")

    def draw_interface(self, frame, tracking_point, landmarks=None):
        """Interfaccia migliorata con più informazioni."""
        if not self.show_window:
            return

        h, w = frame.shape[:2]

        if not self.center_calculated:
            # Fase calibrazione
            cv2.circle(frame, tuple(tracking_point.astype(int)), 15, (0, 165, 255), 3)
            cv2.circle(frame, tuple(tracking_point.astype(int)), 5, (0, 165, 255), -1)
            
            progress = len(self.center_samples)
            percentage = int((progress / self.max_center_samples) * 100)
            
            # Barra progresso
            bar_width = 300
            bar_height = 20
            bar_x, bar_y = 20, 70
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * progress / self.max_center_samples), bar_y + bar_height), (0, 255, 0), -1)
            
            cv2.putText(frame, f"CALIBRAZIONE: {percentage}%", 
                       (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
            cv2.putText(frame, "Tieni la testa FERMA al centro", 
                       (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Questa posizione = centro schermo", 
                       (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        else:
            # Stato attivo
            if self.paused:
                cv2.putText(frame, "CONTROLLER PAUSATO", (20, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                color = (128, 128, 128)
            else:
                color = (0, 255, 0)
            
            # Punto tracking
            cv2.circle(frame, tuple(tracking_point.astype(int)), 8, color, -1)
            
            # Centro e deadzone
            if self.center_position is not None:
                center_pt = tuple(self.center_position.astype(int))
                cv2.circle(frame, center_pt, int(self.deadzone_radius), (255, 255, 0), 2)
                cv2.circle(frame, center_pt, 3, (255, 255, 0), -1)
                
                # Freccia movimento
                distance = np.linalg.norm(tracking_point - self.center_position)
                if distance > self.deadzone_radius and not self.paused:
                    cv2.arrowedLine(frame, center_pt, tuple(tracking_point.astype(int)), (0, 255, 255), 3)

            # Indicatori click mode
            if landmarks is not None and not self.paused:
                if self.blink_mode_enabled:
                    # Indicatori occhi per blink
                    left_eye = tuple(landmarks[self.LEFT_EYE_TOP].astype(int))
                    right_eye = tuple(landmarks[self.RIGHT_EYE_TOP].astype(int))
                    eye_color = (0, 0, 255) if self.eye_closed else (0, 255, 0)
                    cv2.circle(frame, left_eye, 6, eye_color, -1)
                    cv2.circle(frame, right_eye, 6, eye_color, -1)
                
                if self.eyebrow_click_enabled:
                    # Indicatori sopracciglia
                    try:
                        eyebrow_l = tuple(landmarks[70].astype(int))
                        eyebrow_r = tuple(landmarks[300].astype(int))
                        cv2.circle(frame, eyebrow_l, 4, (255, 0, 255), -1)
                        cv2.circle(frame, eyebrow_r, 4, (255, 0, 255), -1)
                    except:
                        pass

            # Indicatore dwell
            if self.click_mode == "dwell" and self.dwell_position is not None and not self.paused:
                dwell_cam_x = int(self.dwell_position[0] * w / self.screen_w)
                dwell_cam_y = int(self.dwell_position[1] * h / self.screen_h)
                dwell_pos = (dwell_cam_x, dwell_cam_y)
                
                if self.dwell_start_time is not None:
                    elapsed = time.time() - self.dwell_start_time
                    progress = min(1.0, elapsed / self.dwell_time)
                    
                    # Cerchio progresso
                    angle = int(360 * progress)
                    cv2.ellipse(frame, dwell_pos, (30, 30), 0, 0, angle, (255, 255, 0), 4)
                    
                    # Countdown
                    remaining = max(0, self.dwell_time - elapsed)
                    cv2.putText(frame, f"{remaining:.1f}", 
                               (dwell_pos[0] - 15, dwell_pos[1] + 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Status principale
            if not self.paused:
                status_text = f"ATTIVO - {self.click_mode.upper()}"
                status_color = (0, 255, 0)
            else:
                status_text = "PAUSATO"
                status_color = (0, 0, 255)
            
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Parametri
            info_y = 80
            cv2.putText(frame, f"Sens: {self.movement_sensitivity:.1f} | X: {self.sensitivity_x:.1f} | Y: {self.sensitivity_y:.1f}", 
                       (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if self.click_mode == "dwell":
                cv2.putText(frame, f"Dwell: {self.dwell_time:.1f}s", 
                           (20, info_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Controlli
        controls = [
            "=== CONTROLLI ===",
            "SPAZIO = Pausa/Riprendi",
            "C = Cambia click mode",
            "+/- = Sensitivity generale",
            "X/Z = Sensitivity X (H/L)",
            "Y/U = Sensitivity Y (A/B)", 
            "D/F = Dwell time (+/-)",
            "R = Reset calibrazione",
            "ESC = Esci"
        ]
        
        y_start = h - len(controls) * 22 - 10
        for i, control in enumerate(controls):
            color = (255, 255, 0) if i == 0 else (255, 255, 255)
            weight = 2 if i == 0 else 1
            cv2.putText(frame, control, (20, y_start + i * 22),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, weight)


def main():
    print("="*70)
    print("HEAD MOUSE CONTROLLER - VERSIONE OTTIMIZZATA")
    print("="*70)
    print("Miglioramenti implementati:")
    print("✓ Tracking fronte per maggiore stabilità")
    print("✓ Sensitivity personalizzabile per direzione (X/Y)")
    print("✓ Sistema smoothing anti-jitter avanzato")
    print("✓ Click personalizzabili: dwell/blink/gesture")
    print("✓ Calibrazione robusta con più campioni")
    print("✓ Controlli completi in tempo reale")
    print("✓ Sistema pausa per comodità")
    print("="*70)

    # Scelta modalità display
    while True:
        choice = input("Mostrare finestra webcam? (s/n): ").lower().strip()
        if choice in ['s', 'n']:
            show_window = choice == 's'
            break
        print("Inserisci 's' per sì o 'n' per no")

    controller = OptimizedHeadMouse(show_window=show_window)
    
    # Setup webcam con ricerca automatica
    cap = None
    for source in [0, 1, 2, -1]:
        test_cap = cv2.VideoCapture(source)
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret and frame is not None:
                cap = test_cap
                print(f"✓ Webcam trovata su fonte: {source}")
                break
        if 'test_cap' in locals():
            test_cap.release()
    
    if cap is None:
        print("❌ ERRORE: Nessuna webcam trovata!")
        return

    # Configurazione ottimale webcam
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("\n🎮 CONTROLLI DISPONIBILI:")
    print("SPAZIO = Pausa/Riprendi | C = Cambia click mode")
    print("+/- = Sensitivity | X/Z = Sens.X | Y/U = Sens.Y")
    print("D/F = Dwell time | R = Reset | ESC = Esci")
    print("\n▶️ Avvio controller...")
    
    try:
        frame_count = 0
        last_fps_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = controller.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                # Usa punto fronte per tracking (più stabile)
                tracking_point = landmarks_np[controller.FOREHEAD_CENTER]

                # Calibrazione o controllo
                if not controller.center_calculated:
                    controller.auto_calibrate_center(tracking_point)
                else:
                    controller.update_mouse_position(tracking_point)
                    
                    # Sistema click basato su modalità
                    if controller.click_mode == "dwell":
                        controller.dwell_click_check()
                    elif controller.click_mode == "blink":
                        controller.detect_voluntary_blink(landmarks_np)
                    elif controller.click_mode == "gesture":
                        controller.detect_voluntary_blink(landmarks_np)
                        controller.detect_eyebrow_gesture(landmarks_np)

                if show_window:
                    controller.draw_interface(frame, tracking_point, landmarks_np)
            else:
                if show_window:
                    cv2.putText(frame, "VISO NON RILEVATO", (20, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                    cv2.putText(frame, "Posizionati davanti alla camera", (20, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if show_window:
                # FPS counter
                frame_count += 1
                if frame_count % 30 == 0:
                    current_time = time.time()
                    fps = 30 / (current_time - last_fps_time)
                    last_fps_time = current_time
                
                cv2.imshow('Head Mouse Controller - Ottimizzato', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord(' '):  # SPAZIO
                    controller.toggle_pause()
                elif key == ord('c') or key == ord('C'):  # C
                    controller.toggle_click_mode()
                elif key == ord('+') or key == ord('='):  # +
                    controller.adjust_sensitivity("both", True)
                elif key == ord('-'):  # -
                    controller.adjust_sensitivity("both", False)
                elif key == ord('x'):  # X
                    controller.adjust_sensitivity("x", True)
                elif key == ord('z'):  # Z
                    controller.adjust_sensitivity("x", False)
                elif key == ord('y'):  # Y
                    controller.adjust_sensitivity("y", True)
                elif key == ord('u'):  # U
                    controller.adjust_sensitivity("y", False)
                elif key == ord('d'):  # D
                    controller.adjust_dwell_time(True)
                elif key == ord('f'):  # F
                    controller.adjust_dwell_time(False)
                elif key == ord('r'):  # R
                    controller.center_calculated = False
                    controller.center_samples = []
                    controller.center_position = None
                    print("🔄 Calibrazione resettata")
            else:
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n⏹️ Interruzione da tastiera")
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("👋 Controller chiuso correttamente")


if __name__ == "__main__":
    main()