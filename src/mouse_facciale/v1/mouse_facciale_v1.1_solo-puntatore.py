import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys
import platform

def play_beep():
    """
    Plays a short beep sound depending on the operating system.
    """
    if platform.system() == "Windows":
        try:
            import winsound
            winsound.Beep(300, 150) # Frequency (Hz), Duration (ms)
        except ImportError:
            print("winsound not available. Install it for Windows beeps.")
    elif platform.system() == "Linux":
        try:
            import subprocess
            # Play a default system sound on Linux
            subprocess.Popen(['aplay', '-q', '/usr/share/sounds/alsa/Front_Left.wav'])
        except Exception as e:
            print(f"Failed to play beep on Linux: {e}")
    elif platform.system() == "Darwin": # macOS
        try:
            import os
            # Play a default system sound on macOS
            os.system('afplay /System/Library/Sounds/Tink.aiff')
        except Exception as e:
            print(f"Failed to play beep on macOS: {e}")

class JoystickNoseMouseController:
    def __init__(self):
        """
        Initializes the Nose Mouse Controller with MediaPipe, PyAutoGUI,
        and calibration parameters.
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        # Initialize MediaPipe Face Mesh model
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,                # Detect only one face
            refine_landmarks=True,          # Refine landmark detection around eyes and lips
            min_detection_confidence=0.6,   # Lowered for potentially better initial detection
            min_tracking_confidence=0.6     # Lowered for potentially better tracking stability
        )

        pyautogui.FAILSAFE = False  # Disable PyAutoGUI failsafe (moving mouse to screen corner)
        pyautogui.PAUSE = 0.001     # Small pause after PyAutoGUI calls for stability

        self.screen_w, self.screen_h = pyautogui.size() # Get current screen resolution
        
        # Define MediaPipe landmark index for nose tip
        self.NOSE_TIP = 1

        # Default value for last known nose position (used when no face is detected)
        self.last_nose_pos = np.array([320.0, 240.0]) # Center of a typical 640x480 frame

        # Calibration system parameters
        self.calibrated = False         # Flag to indicate if calibration is complete
        self.calibration_stage = 0      # Current stage of calibration (0-6)
        self.calibration_data = {       # Dictionary to store collected calibration data
            'center': [], 'left': [], 'right': [], 'up': [], 'down': []
        }
        self.current_calibration_stage_frames = 0 # Frames collected in current stage
        self.CALIBRATION_STAGE_DURATION = 60      # Number of frames for each data collection stage
        self.CALIBRATION_GUIDE_TEXTS = {          # User-facing instructions for each stage
            0: "Preparazione calibrazione...",
            1: "GUARDA DRITTO AL CENTRO \n (prossimo: guarda a sinistra)",
            2: "GUARDA A SINISTRA \n (prossimo: guarda a destra)", 
            3: "GUARDA A DESTRA \n (prossimo: guarda in alto)",
            4: "GUARDA IN ALTO \n (prossimo: guarda in basso)",
            5: "GUARDA IN BASSO \n (elaborazione dati...)",
            6: "Elaborazione dati...",
            7: "CALIBRATO! Joystick Attivo."
        }
        self.last_calibration_stage_start_time = time.time() # Timestamp for current stage start
        self.calibration_beep_played = False                 # Flag to ensure beep plays once per stage

        # Joystick control parameters
        self.center_position = np.array([0.0, 0.0])  # Calibrated center nose position
        self.movement_sensitivity = 2.0              # Speed multiplier (reduced for less sensitivity)
        self.deadzone_radius = 12.0                  # Pixels of deadzone around center (increased for more stability)
        
        # Current cursor position (initialized to screen center)
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)

    def calibrate_system(self, nose_pos):
        """
        Manages the multi-stage calibration process to set up joystick control.
        """
        current_time = time.time()

        # Play a beep at the start of each new calibration stage (after a brief delay)
        if not self.calibration_beep_played and current_time - self.last_calibration_stage_start_time > 0.5:
            play_beep()
            self.calibration_beep_played = True

        # Stage 0: Initial preparation delay
        if self.calibration_stage == 0:
            if current_time - self.last_calibration_stage_start_time > 2.0:
                self.calibration_stage = 1
                self.current_calibration_stage_frames = 0
                self.last_calibration_stage_start_time = current_time
                self.calibration_beep_played = False
            return # Exit early for stage 0

        # Map calibration stages to their corresponding data keys
        stage_key_map = {
            1: 'center', 2: 'left', 3: 'right', 4: 'up', 5: 'down'
        }
        
        current_stage_key = stage_key_map.get(self.calibration_stage)

        if current_stage_key:
            # Collect nose position data for the current stage
            self.calibration_data[current_stage_key].append(nose_pos.copy())
            self.current_calibration_stage_frames += 1

            # Transition to the next stage after collecting enough frames
            if self.current_calibration_stage_frames >= self.CALIBRATION_STAGE_DURATION:
                self.calibration_stage += 1
                self.current_calibration_stage_frames = 0
                self.last_calibration_stage_start_time = current_time
                self.calibration_beep_played = False # Reset beep flag for the new stage

        # Stage 6: Process all collected data
        if self.calibration_stage == 6:
            print("Processing calibration data...")
            self._process_calibration_data()

    def _process_calibration_data(self):
        """
        Analyzes collected calibration data to set the center position
        and movement sensitivity.
        """
        
        # Set center position from 'center' calibration data
        center_data = np.array(self.calibration_data['center'])
        if center_data.size > 0:
            self.center_position = np.mean(center_data, axis=0)
            print(f"Center position set to: {self.center_position}")
        else:
            print("Warning: No center calibration data. Using default last nose position.")
            self.center_position = self.last_nose_pos.copy()

        # Calculate movement sensitivity based on the range of head movements
        all_positions = []
        for key in ['left', 'right', 'up', 'down']:
            if self.calibration_data[key]:
                all_positions.extend(self.calibration_data[key])
        
        if all_positions:
            positions = np.array(all_positions)
            # Calculate average distance of calibration points from the determined center
            distances = [np.linalg.norm(pos - self.center_position) for pos in positions]
            avg_distance = np.mean(distances)
            
            # Adjust sensitivity: larger avg_distance (more movement) leads to lower sensitivity multiplier
            # Clamped between 1.0 and 5.0 to prevent extreme values.
            self.movement_sensitivity = max(1.0, min(5.0, 100.0 / avg_distance))
            print(f"Movement sensitivity adjusted to: {self.movement_sensitivity:.2f}")
        else:
            print("Warning: No directional calibration data. Using default movement sensitivity.")
        
        self.calibrated = True       # Mark calibration as complete
        self.calibration_stage = 7   # Move to the final "CALIBRATED!" stage
        print("Calibration completed successfully! Joystick Active.")
        
        # Set initial cursor position to screen center after calibration
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])

    def update_cursor_position(self, nose_pos):
        """
        Updates the virtual cursor position based on head movement (nose position)
        relative to the calibrated center, applying deadzone and sensitivity.
        """
        
        offset = nose_pos - self.center_position # Vector from center to current nose position
        distance = np.linalg.norm(offset)      # Magnitude of the offset

        # Apply deadzone: no movement if within the deadzone radius
        if distance < self.deadzone_radius:
            return  
        
        # Calculate movement factor: movement starts only after deadzone is exited
        # This creates a "ramping up" effect as you move further from the center
        movement_factor = (distance - self.deadzone_radius) / distance
        movement_vector = offset * movement_factor * self.movement_sensitivity
        
        self.current_cursor_pos += movement_vector # Update internal cursor position
        
        # Constrain cursor position to screen bounds
        self.current_cursor_pos[0] = np.clip(self.current_cursor_pos[0], 0, self.screen_w - 1)
        self.current_cursor_pos[1] = np.clip(self.current_cursor_pos[1], 0, self.screen_h - 1)
        
        # Move the actual system mouse cursor
        try:
            pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        except Exception as e:
            print(f"Mouse movement failed: {e}")

    def draw_interface(self, frame, nose_pos):
        """
        Draws visual feedback and instructional text on the webcam frame for the user.
        """
        h, w = frame.shape[:2]

        # Draw current nose position
        if self.calibrated:
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 255, 0), -1) # Green circle when calibrated
            
            # Draw calibrated center position and deadzone
            center_screen = self.center_position.astype(int)
            cv2.circle(frame, tuple(center_screen), int(self.deadzone_radius), (255, 255, 0), 2) # Yellow deadzone circle
            cv2.circle(frame, tuple(center_screen), 3, (255, 255, 0), -1) # Small yellow center dot
            
            # Draw movement vector if outside deadzone
            if np.linalg.norm(nose_pos - self.center_position) > self.deadzone_radius:
                cv2.arrowedLine(frame, tuple(center_screen), tuple(nose_pos.astype(int)), (0, 255, 255), 2) # Yellow arrow
        else:
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1) # Orange circle during calibration

        # Display calibration status or active mode instructions
        status_text_raw = self.CALIBRATION_GUIDE_TEXTS.get(self.calibration_stage, "Unknown stage")
        color = (0, 255, 255) if not self.calibrated else (0, 255, 0) # Yellow during calibration, Green when active

        # Add progress counter during data collection stages
        if 0 < self.calibration_stage < 6 and not self.calibrated:
            progress_text = f" ({self.current_calibration_stage_frames}/{self.CALIBRATION_STAGE_DURATION})"
            # Split the text for multi-line display if needed
            lines = status_text_raw.split('\n')
            if len(lines) > 1:
                cv2.putText(frame, lines[0], (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.putText(frame, lines[1] + progress_text, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
            else:
                cv2.putText(frame, status_text_raw + progress_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        else:
            # Single line display for other stages
            cv2.putText(frame, status_text_raw, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Debug and instructional information (only if calibrated)
        if self.calibrated:
            offset_y = 70 # Starting Y position for calibrated info
            # Current position info
            cv2.putText(frame, f"Naso: {int(nose_pos[0])},{int(nose_pos[1])}", (20, offset_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Cursore: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}", (20, offset_y + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Movement info
            offset = nose_pos - self.center_position
            distance = np.linalg.norm(offset)
            cv2.putText(frame, f"Distanza dal centro: {distance:.1f}px", (20, offset_y + 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Sensitivity info
            cv2.putText(frame, f"Sensibilita': {self.movement_sensitivity:.2f}", (20, offset_y + 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Instructions at the bottom of the screen
            cv2.putText(frame, "MODALITA' JOYSTICK - Muovi la testa per muovere il cursore", (20, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Usa i click del mouse fisico per interagire", (20, h-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

def main():
    print("="*60)
    print("CONTROLLORE MOUSE CON NASO - MODALITA' JOYSTICK")
    print("="*60)
    print("Movimento joystick: Muovi la testa rispetto alla posizione centrale.")
    print("Per i click usa il mouse fisico o altri metodi di input.")
    print("="*60)

    controller = JoystickNoseMouseController()
    cap = cv2.VideoCapture(0) # Initialize webcam capture (0 is default webcam)
    
    if not cap.isOpened():
        print("Errore: Impossibile aprire la webcam. Controlla la connessione e i permessi.")
        sys.exit(1)

    # Set camera properties for better performance and consistency
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduce buffer to get most recent frames

    print("Premi ESC per uscire")
    
    try:
        while True:
            ret, frame = cap.read() # Read a frame from the webcam
            if not ret:
                print("Avviso: Impossibile leggere il frame. Uscita.")
                break

            frame = cv2.flip(frame, 1) # Flip frame horizontally (mirror effect)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB for MediaPipe
            results = controller.face_mesh.process(rgb_frame) # Process frame with face mesh model

            if results.multi_face_landmarks:
                # If a face is detected, get the first face's landmarks
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                # Convert normalized landmark coordinates to pixel coordinates
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                nose_pos = landmarks_np[controller.NOSE_TIP] # Get nose tip position

                # Always update last known value regardless of calibration state
                controller.last_nose_pos = nose_pos.copy()

                if not controller.calibrated:
                    controller.calibrate_system(nose_pos) # Run calibration
                else:
                    controller.update_cursor_position(nose_pos) # Control cursor movement

            # Always draw the interface using the last known values (even if no face is detected currently)
            controller.draw_interface(frame, controller.last_nose_pos)

            cv2.imshow('Joystick Nose Mouse', frame) # Display the processed frame
            
            # Check for ESC key press to exit
            if cv2.waitKey(1) & 0xFF == 27:  
                break

    except KeyboardInterrupt:
        print("\nInterrotto dall'utente")
    except Exception as e:
        print(f"Errore imprevisto: {e}")
    finally:
        # Release webcam and destroy all OpenCV windows on exit
        cap.release()
        cv2.destroyAllWindows()
        print("Pulizia completata.")

if __name__ == "__main__":
    main()