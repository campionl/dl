import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys
from collections import deque
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

class JoystickHeadMouseController:
    def __init__(self):
        """
        Initializes the Head Mouse Controller with MediaPipe, PyAutoGUI,
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
        
        # Define MediaPipe landmark indices for nose tip and eye EAR calculation
        self.NOSE_TIP = 1
        # Standard 6 points for Left Eye Aspect Ratio (EAR) calculation
        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144] 
        # Standard 6 points for Right Eye Aspect Ratio (EAR) calculation
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380] 

        # Default values for last known positions/states (used when no face is detected)
        self.last_nose_pos = np.array([320.0, 240.0]) # Center of a typical 640x480 frame
        self.last_left_ear = 0.3
        self.last_right_ear = 0.3

        # Calibration system parameters
        self.calibrated = False         # Flag to indicate if calibration is complete
        self.calibration_stage = 0      # Current stage of calibration (0-11)
        self.calibration_data = {       # Dictionary to store collected calibration data
            'center': [], 'left': [], 'right': [], 'up': [], 'down': [],
            'eyes_open': [], 'left_eye_closed': [], 'right_eye_closed': [], 'both_eyes_closed': []
        }
        self.current_calibration_stage_frames = 0 # Frames collected in current stage
        self.CALIBRATION_STAGE_DURATION = 60      # Number of frames for each data collection stage
        self.CALIBRATION_GUIDE_TEXTS = {          # User-facing instructions for each stage
            0: "Preparazione calibrazione...",
            1: "GUARDA DRITTO AL CENTRO \n (prossimo: guarda a sinistra)",
            2: "GUARDA A SINISTRA \n (prossimo: guarda a destra)", 
            3: "GUARDA A DESTRA \n (prossimo: guarda in alto)",
            4: "GUARDA IN ALTO \n (prossimo: guarda in basso)",
            5: "GUARDA IN BASSO \n (prossimo: tieni gli occhi aperti)",
            6: "TIENI GLI OCCHI APERTI \n (prossimo: chiudi solo l'occhio sinistro)",
            7: "CHIUDI SOLO L'OCCHIO SINISTRO \n (prossimo: chiudi solo l'occhio destro)",
            8: "CHIUDI SOLO L'OCCHIO DESTRO \n (prossimo: chiudi entrambi gli occhi)", 
            9: "CHIUDI ENTRAMBI GLI OCCHI \n (quasi finito!)",
            10: "Elaborazione dati...",
            11: "CALIBRATO! Joystick Attivo."
        }
        self.last_calibration_stage_start_time = time.time() # Timestamp for current stage start
        self.calibration_beep_played = False                 # Flag to ensure beep plays once per stage

        # Joystick control parameters
        self.center_position = np.array([0.0, 0.0])  # Calibrated center nose position
        self.movement_sensitivity = 2.0              # Speed multiplier (reduced for less sensitivity)
        self.deadzone_radius = 12.0                  # Pixels of deadzone around center (increased for more stability)
        
        # Current cursor position (initialized to screen center)
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        
        # Default Eye Aspect Ratio (EAR) thresholds (will be refined by calibration)
        self.eyes_open_threshold = 0.20
        self.eye_closed_threshold = 0.10
        
        # Click detection parameters
        self.eye_history = deque(maxlen=10)     # Stores recent EAR values for consistency checks
        self.REQUIRED_EYE_FRAMES = 10           # Number of consistent frames to confirm eye state (increased)
        self.last_left_click_time = 0.0         # Timestamp of last left click
        self.last_right_click_time = 0.0        # Timestamp of last right click
        self.last_double_click_time = 0.0       # Timestamp of last double click
        self.CLICK_COOLDOWN = 1.4               # Minimum time between clicks of the same type (increased)

    def _get_ear(self, landmarks, eye_points):
        """
        Calculates the Eye Aspect Ratio (EAR) for a given eye.
        The EAR is a measure of the openness of an eye based on 6 key landmarks.
        """
        try:
            # Extract the 6 key eye landmarks
            p1 = landmarks[eye_points[0]] # Outer corner
            p2 = landmarks[eye_points[1]] # Top-inner
            p3 = landmarks[eye_points[2]] # Top-outer
            p4 = landmarks[eye_points[3]] # Inner corner
            p5 = landmarks[eye_points[4]] # Bottom-outer
            p6 = landmarks[eye_points[5]] # Bottom-inner

            # Calculate the Euclidean distances between the vertical landmarks
            vertical1_dist = np.linalg.norm(p2 - p6)
            vertical2_dist = np.linalg.norm(p3 - p5)
            
            # Calculate the Euclidean distance between the horizontal landmarks
            horizontal_dist = np.linalg.norm(p1 - p4)

            # Calculate EAR, with protection against division by zero
            ear = (vertical1_dist + vertical2_dist) / (2.0 * horizontal_dist) if horizontal_dist > 1e-7 else 0
            return ear
        except (IndexError, ValueError, TypeError):
            # Return a default EAR in case of invalid landmark indices or calculation errors
            return 0.3

    def calibrate_system(self, nose_pos, left_ear, right_ear):
        """
        Manages the multi-stage calibration process to set up joystick and eye thresholds.
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
            1: 'center', 2: 'left', 3: 'right', 4: 'up', 5: 'down',
            6: 'eyes_open', 7: 'left_eye_closed', 8: 'right_eye_closed', 9: 'both_eyes_closed'
        }
        
        current_stage_key = stage_key_map.get(self.calibration_stage)

        if current_stage_key:
            # Collect data based on the current stage type
            if current_stage_key in ['center', 'left', 'right', 'up', 'down']:
                self.calibration_data[current_stage_key].append(nose_pos.copy())
            elif current_stage_key in ['eyes_open', 'left_eye_closed', 'right_eye_closed', 'both_eyes_closed']:
                self.calibration_data[current_stage_key].append((left_ear, right_ear))

            self.current_calibration_stage_frames += 1

            # Transition to the next stage after collecting enough frames
            if self.current_calibration_stage_frames >= self.CALIBRATION_STAGE_DURATION:
                self.calibration_stage += 1
                self.current_calibration_stage_frames = 0
                self.last_calibration_stage_start_time = current_time
                self.calibration_beep_played = False # Reset beep flag for the new stage

        # Stage 10: Process all collected data
        if self.calibration_stage == 10:
            print("Processing calibration data...")
            self._process_calibration_data()

    def _process_calibration_data(self):
        """
        Analyzes collected calibration data to set the center position,
        movement sensitivity, and eye detection thresholds.
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

        # Process eye thresholds from eye calibration data
        self._process_eye_thresholds()
        
        self.calibrated = True       # Mark calibration as complete
        self.calibration_stage = 11  # Move to the final "CALIBRATED!" stage
        print("Calibration completed successfully! Joystick Active.")
        
        # Set initial cursor position to screen center after calibration
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])

    def _process_eye_thresholds(self):
        """
        Calculates specific eye detection thresholds (open, closed) from calibration data.
        """
        
        # Baseline for eyes open
        if self.calibration_data['eyes_open']:
            open_ears = np.array(self.calibration_data['eyes_open'])
            avg_open_left = np.mean(open_ears[:, 0])
            avg_open_right = np.mean(open_ears[:, 1])
            self.eyes_open_threshold = (avg_open_left + avg_open_right) / 2
            print(f"Calibrated Eyes open threshold: {self.eyes_open_threshold:.3f}")
        else:
            print("Warning: No 'eyes open' calibration data. Using default.")

        # Threshold for left eye closed
        if self.calibration_data['left_eye_closed']:
            left_closed_ears = np.array(self.calibration_data['left_eye_closed'])
            avg_left_closed = np.mean(left_closed_ears[:, 0])
            self.left_eye_closed_threshold = avg_left_closed + 0.02 # Add a small buffer
            print(f"Calibrated Left eye closed threshold: {self.left_eye_closed_threshold:.3f}")
        else:
            self.left_eye_closed_threshold = self.eyes_open_threshold * 0.6 # Fallback
            print("Warning: No 'left eye closed' calibration data. Using derived default.")

        # Threshold for right eye closed  
        if self.calibration_data['right_eye_closed']:
            right_closed_ears = np.array(self.calibration_data['right_eye_closed'])
            avg_right_closed = np.mean(right_closed_ears[:, 0]) # Note: should be index 1 if tuple is (left, right)
            self.right_eye_closed_threshold = avg_right_closed + 0.02 # Add a small buffer
            print(f"Calibrated Right eye closed threshold: {self.right_eye_closed_threshold:.3f}")
        else:
            self.right_eye_closed_threshold = self.eyes_open_threshold * 0.6 # Fallback
            print("Warning: No 'right eye closed' calibration data. Using derived default.")

        # Threshold for both eyes closed
        if self.calibration_data['both_eyes_closed']:
            both_closed_ears = np.array(self.calibration_data['both_eyes_closed'])
            avg_both_closed = np.mean(both_closed_ears) # Average of both left and right for 'both closed'
            self.both_eyes_closed_threshold = avg_both_closed + 0.02 # Add a small buffer
            print(f"Calibrated Both eyes closed threshold: {self.both_eyes_closed_threshold:.3f}")
        else:
            self.both_eyes_closed_threshold = self.eyes_open_threshold * 0.6 # Fallback
            print("Warning: No 'both eyes closed' calibration data. Using derived default.")

        # Ensure all calculated thresholds are within a reasonable practical range
        self.left_eye_closed_threshold = np.clip(self.left_eye_closed_threshold, 0.05, 0.25)
        self.right_eye_closed_threshold = np.clip(self.right_eye_closed_threshold, 0.05, 0.25)
        self.both_eyes_closed_threshold = np.clip(self.both_eyes_closed_threshold, 0.05, 0.25)

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

    def detect_eye_clicks(self, left_ear, right_ear):
        """
        Detects and triggers mouse clicks (left, right, double) based on consistent eye states.
        """
        
        self.eye_history.append((left_ear, right_ear)) # Add current EARs to history
        
        # Require enough history frames to make a decision
        if len(self.eye_history) < self.REQUIRED_EYE_FRAMES:
            return
        
        current_time = time.time()
        
        # Get the most recent eye states for consistency check
        recent_eyes = list(self.eye_history)[-self.REQUIRED_EYE_FRAMES:]
        recent_left = [eyes[0] for eyes in recent_eyes]
        recent_right = [eyes[1] for eyes in recent_eyes]
        
        # Check for consistent eye states over the required number of frames
        left_consistently_closed = all(ear < self.left_eye_closed_threshold for ear in recent_left)
        right_consistently_closed = all(ear < self.right_eye_closed_threshold for ear in recent_right)
        both_consistently_closed = all((left + right) / 2 < self.both_eyes_closed_threshold 
                                     for left, right in recent_eyes)
        
        left_consistently_open = all(ear > self.eyes_open_threshold for ear in recent_left)
        right_consistently_open = all(ear > self.eyes_open_threshold for ear in recent_right)
        
        # Double click: triggered by both eyes consistently closed
        if both_consistently_closed:
            if (current_time - self.last_double_click_time) > self.CLICK_COOLDOWN:
                try:
                    pyautogui.doubleClick()
                    self.last_double_click_time = current_time
                    print("[ACTION] Double Click (Both eyes closed)")
                    self.eye_history.clear() # Clear history to prevent immediate re-trigger
                except Exception as e:
                    print(f"Double click failed: {e}")
        
        # Left click: triggered by left eye consistently closed and right eye open
        elif left_consistently_closed and right_consistently_open:
            if (current_time - self.last_left_click_time) > self.CLICK_COOLDOWN:
                try:
                    pyautogui.click()
                    self.last_left_click_time = current_time
                    print("[ACTION] Left Click (Left eye closed)")
                    self.eye_history.clear() # Clear history
                except Exception as e:
                    print(f"Left click failed: {e}")
        
        # Right click: triggered by right eye consistently closed and left eye open  
        elif right_consistently_closed and left_consistently_open:
            if (current_time - self.last_right_click_time) > self.CLICK_COOLDOWN:
                try:
                    pyautogui.click(button='right')
                    self.last_right_click_time = current_time
                    print("[ACTION] Right Click (Right eye closed)")
                    self.eye_history.clear() # Clear history
                except Exception as e:
                    print(f"Right click failed: {e}")

    def draw_interface(self, frame, nose_pos, left_ear, right_ear):
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
        if 0 < self.calibration_stage < 10 and not self.calibrated:
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
            
            # Eye states with color coding
            left_state = "CHIUSO" if left_ear < self.left_eye_closed_threshold else "APERTO"
            right_state = "CHIUSO" if right_ear < self.right_eye_closed_threshold else "APERTO"
            # Averaged EAR for both eyes for "both closed" state
            both_eyes_avg_ear = (left_ear + right_ear) / 2
            both_state = "CHIUSO" if both_eyes_avg_ear < self.both_eyes_closed_threshold else "APERTO"
            
            cv2.putText(frame, f"Occhio Sinistro: {left_state} ({left_ear:.2f})", (20, offset_y + 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if left_state == "APERTO" else (0, 0, 255), 1)
            cv2.putText(frame, f"Occhio Destro: {right_state} ({right_ear:.2f})", (20, offset_y + 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if right_state == "APERTO" else (0, 0, 255), 1)
            cv2.putText(frame, f"Entrambi gli Occhi: {both_state}", (20, offset_y + 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if both_state == "APERTO" else (0, 0, 255), 1)

            # Movement info
            offset = nose_pos - self.center_position
            distance = np.linalg.norm(offset)
            cv2.putText(frame, f"Distanza dal centro: {distance:.1f}px", (20, offset_y + 150),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Instructions at the bottom of the screen
            cv2.putText(frame, "MODALITA' JOYSTICK - Muovi la testa per muovere il cursore", (20, h-130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Chiudi Occhio SINISTRO: Click Sinistro", (20, h-100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Chiudi Occhio DESTRO: Click Destro", (20, h-70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Chiudi ENTRAMBI gli Occhi: Doppio Click", (20, h-40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

def main():
    print("="*60)
    print("CONTROLLORE MOUSE A TESTA STILE JOYSTICK")
    print("="*60)
    print("Movimento joystick: Muovi la testa rispetto alla posizione centrale.")
    print("Click Sinistro: Chiudi occhio sinistro")
    print("Click Destro: Chiudi occhio destro") 
    print("Doppio Click: Chiudi entrambi gli occhi")
    print("="*60)

    controller = JoystickHeadMouseController()
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
                left_ear = controller._get_ear(landmarks_np, controller.LEFT_EYE_POINTS) # Calculate left EAR
                right_ear = controller._get_ear(landmarks_np, controller.RIGHT_EYE_POINTS) # Calculate right EAR

                # Always update last known values regardless of calibration state
                controller.last_nose_pos = nose_pos.copy()
                controller.last_left_ear = left_ear
                controller.last_right_ear = right_ear

                if not controller.calibrated:
                    controller.calibrate_system(nose_pos, left_ear, right_ear) # Run calibration
                else:
                    controller.update_cursor_position(nose_pos) # Control cursor movement
                    controller.detect_eye_clicks(left_ear, right_ear) # Detect and perform clicks

            else:
                # If no face is detected, clear eye history to prevent false clicks on re-detection
                controller.eye_history.clear()

            # Always draw the interface using the last known values (even if no face is detected currently)
            controller.draw_interface(frame, 
                                    controller.last_nose_pos, 
                                    controller.last_left_ear, 
                                    controller.last_right_ear)

            cv2.imshow('Joystick Head Mouse', frame) # Display the processed frame
            
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