import cv2
import mediapipe as mp
import numpy as np
import time
import sys
import subprocess
import threading
import select
import termios
import tty


class VirtualMouseController:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        # Ottieni dimensioni schermo da xrandr
        self.screen_w, self.screen_h = self.get_screen_size()
        print(f"Dimensioni schermo rilevate: {self.screen_w}x{self.screen_h}")

        # Landmark del naso e occhio
        self.NOSE_TIP = 1
        self.LEFT_EYE_TOP = 159
        self.LEFT_EYE_BOTTOM = 145
        
        # Sistema di controllo
        self.center_position = None
        self.last_nose_pos = np.array([320.0, 240.0])
        self.movement_sensitivity = 3.0
        self.deadzone_radius = 15.0
        
        # Calibrazione
        self.center_samples = []
        self.max_center_samples = 30
        self.center_calculated = False
        
        # Posizione corrente del cursore
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        
        # Sistema di click
        self.eye_closed_threshold = 0.02
        self.last_click_time = 0
        self.click_cooldown = 0.5
        self.eye_aspect_ratios = []
        self.ear_buffer_size = 3
        
        # Sistema di terminazione
        self.should_exit = False
        self.keyboard_thread = None
        self.old_settings = None
        
        # Visualizzazione cursore
        # Questi devono essere inizializzati prima di chiamare self.move_mouse
        self.cursor_visible = True
        self.cursor_toggle_time = time.time()
        self.cursor_blink_interval = 0.5
        
        # Sposta il mouse alla posizione iniziale dopo aver inizializzato gli attributi del cursore
        self.move_mouse(self.current_cursor_pos[0], self.current_cursor_pos[1])

    def get_screen_size(self):
        """Ottiene le dimensioni dello schermo usando xrandr"""
        try:
            output = subprocess.check_output(['xrandr']).decode('utf-8')
            primary_line = [l for l in output.splitlines() if ' connected primary' in l][0]
            resolution = primary_line.split()[3]  # Es: 1920x1080+0+0
            width, height = map(int, resolution.split('+')[0].split('x'))
            return width, height
        except:
            # Fallback se xrandr non funziona
            return 1920, 1080

    def setup_keyboard_listener(self):
        """Configura il listener per l'input da tastiera"""
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        self.keyboard_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        self.keyboard_thread.start()

    def keyboard_listener(self):
        """Thread per ascoltare l'input da tastiera"""
        while not self.should_exit:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1)
                if key == '\x1b':  # ESC key
                    print("\n\nTasto ESC premuto. Uscita in corso...")
                    self.should_exit = True
                    break
                elif key.lower() == 'q':  # Alternativa con 'q'
                    print("\n\nTasto 'Q' premuto. Uscita in corso...")
                    self.should_exit = True
                    break

    def restore_terminal(self):
        """Ripristina le impostazioni del terminale"""
        if self.old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def draw_cursor_indicator(self):
        """Disegna un indicatore visivo del cursore usando caratteri ASCII"""
        # Lampeggia il cursore per renderlo più visibile
        current_time = time.time()
        if current_time - self.cursor_toggle_time > self.cursor_blink_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_toggle_time = current_time
            
        if self.cursor_visible:
            # Crea un piccolo quadrato colorato come indicatore del cursore
            try:
                # Usa xdotool per creare un overlay temporaneo
                subprocess.run([
                    'xdotool', 'mousemove', 
                    str(int(self.current_cursor_pos[0])), 
                    str(int(self.current_cursor_pos[1]))
                ], check=True)
                
                # Alternativa: usa notify-send per mostrare la posizione (meno invasivo)
                # subprocess.run([
                #     'notify-send', 
                #     f"Mouse: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}",
                #     '--expire-time=100'
                # ], check=False)
                
            except:
                pass

    def create_cursor_overlay(self):
        """Crea un overlay temporaneo per mostrare la posizione del cursore"""
        try:
            # Crea una piccola finestra overlay con xdotool e zenity
            x, y = int(self.current_cursor_pos[0]), int(self.current_cursor_pos[1])
            
            # Usa un approccio più semplice: muovi il mouse e mostra coordinate
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
            
        except:
            pass

    def move_mouse(self, x, y):
        """Muove il mouse usando xdotool"""
        try:
            subprocess.run(['xdotool', 'mousemove', str(int(x)), str(int(y))], check=True)
            
            # Aggiorna l'indicatore visivo ogni pochi movimenti per non sovraccaricare
            if hasattr(self, '_move_counter'):
                self._move_counter += 1
            else:
                self._move_counter = 0
                
            if self._move_counter % 5 == 0:  # Aggiorna ogni 5 movimenti
                self.draw_cursor_indicator()
                
        except subprocess.CalledProcessError as e:
            print(f"Errore movimento mouse: {e}")
        except FileNotFoundError:
            print("xdotool non installato. Installalo con: sudo apt install xdotool")

    def perform_click(self):
        """Esegue un click usando xdotool"""
        try:
            # Prima assicurati che il mouse sia nella posizione corretta
            self.move_mouse(self.current_cursor_pos[0], self.current_cursor_pos[1])
            
            # Esegui il click
            subprocess.run(['xdotool', 'click', '1'], check=True)
            print(f"\n🖱️  CLICK! Posizione: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Errore nel click: {e}")
            return False
        except FileNotFoundError:
            print("xdotool non installato. Installalo con: sudo apt install xdotool")
            return False

    def calculate_eye_aspect_ratio(self, eye_top, eye_bottom):
        """Calcola l'Eye Aspect Ratio"""
        vertical_distance = abs(eye_top[1] - eye_bottom[1])
        reference_width = 20.0
        ear = vertical_distance / reference_width
        return ear

    def detect_left_eye_blink(self, landmarks):
        """Rileva l'ammiccamento per il click"""
        left_eye_top = landmarks[self.LEFT_EYE_TOP]
        left_eye_bottom = landmarks[self.LEFT_EYE_BOTTOM]
        
        ear = self.calculate_eye_aspect_ratio(left_eye_top, left_eye_bottom)
        
        self.eye_aspect_ratios.append(ear)
        if len(self.eye_aspect_ratios) > self.ear_buffer_size:
            self.eye_aspect_ratios.pop(0)
        
        avg_ear = np.mean(self.eye_aspect_ratios)
        
        current_time = time.time()
        if (avg_ear < self.eye_closed_threshold and 
            current_time - self.last_click_time > self.click_cooldown):
            
            if self.perform_click():
                self.last_click_time = current_time
                return True
        
        return False

    def auto_set_center(self, nose_pos):
        """Calibrazione automatica del centro"""
        if not self.center_calculated:
            self.center_samples.append(nose_pos.copy())
            
            progress = len(self.center_samples)
            print(f"\r🎯 Calibrazione in corso... {progress}/{self.max_center_samples} campioni", end='', flush=True)
            
            if len(self.center_samples) >= self.max_center_samples:
                self.center_position = np.mean(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"\n✅ Calibrazione completata! Centro: ({self.center_position[0]:.1f}, {self.center_position[1]:.1f})")
                print("💡 Ora puoi muovere la testa per controllare il mouse")
                print("👁️  Ammicca con l'occhio sinistro per fare click")
                print("🔴 Premi ESC per uscire")
                return True
        return False

    def update_cursor_position(self, nose_pos):
        """Aggiorna la posizione del cursore"""
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
        
        self.move_mouse(self.current_cursor_pos[0], self.current_cursor_pos[1])

def main():
    print("="*70)
    print("🎮 VIRTUAL HEAD MOUSE CONTROLLER (Versione Migliorata)")
    print("="*70)
    print("🔧 Funzionalità:")
    print("   • Controllo mouse con movimenti della testa")
    print("   • Click con ammiccamento occhio sinistro")
    print("   • Indicatore visivo della posizione del cursore")
    print("   • Uscita con tasto ESC o 'Q'")
    print("="*70)
    print("📋 Requisiti:")
    print("   sudo apt install xdotool")
    print("="*70)
    print("🚀 Avvio del sistema...")

    controller = VirtualMouseController()
    
    # Configura il listener per la tastiera
    try:
        controller.setup_keyboard_listener()
    except Exception as e:
        print(f"⚠️  Avviso: Non è possibile configurare l'input da tastiera: {e}")
        print("   Usa CTRL+C per uscire")
    
    # Prova diverse fonti video
    cap = None
    for source in [0, 1, 2, '/dev/video0', '/dev/video1', '/dev/video2']:
        print(f"🔍 Provo fonte video: {source}")
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print(f"📹 Webcam trovata su: {source}")
                break
            cap.release()
    
    if not cap or not cap.isOpened():
        print("❌ ERRORE: Nessuna webcam trovata!")
        controller.restore_terminal()
        sys.exit(1)

    # Configurazione camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    try:
        frame_count = 0
        last_status_time = time.time()
        
        print("\n🎯 Posizionati davanti alla camera e tieni la testa ferma per la calibrazione...")
        
        while not controller.should_exit:
            ret, frame = cap.read()
            if not ret:
                print("❌ Errore lettura frame")
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

                if not controller.center_calculated:
                    controller.auto_set_center(nose_pos)
                else:
                    controller.update_cursor_position(nose_pos)
                    controller.detect_left_eye_blink(landmarks_np)

            # Mostra stato nella console (ogni secondo per non sovraccaricare)
            current_time = time.time()
            if controller.center_calculated and current_time - last_status_time > 1.0:
                x, y = int(controller.current_cursor_pos[0]), int(controller.current_cursor_pos[1])
                screen_percent_x = (x / controller.screen_w) * 100
                screen_percent_y = (y / controller.screen_h) * 100
                
                status = (f"🖱️  Mouse: ({x:4d},{y:4d}) | "
                          f"Schermo: {screen_percent_x:5.1f}%,{screen_percent_y:5.1f}% | "
                          f"ESC per uscire")
                print(f"\r{status}", end='', flush=True)
                last_status_time = current_time

            frame_count += 1
            
            # Piccola pausa per non sovraccaricare la CPU
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\n⏹️  Interrotto dall'utente (CTRL+C)")
    except Exception as e:
        print(f"\n\n❌ Errore imprevisto: {e}")
    finally:
        controller.should_exit = True
        controller.restore_terminal()
        cap.release()
        print("\n✅ Rilascio risorse completato")
        print("👋 Arrivederci!")

if __name__ == "__main__":
    main()