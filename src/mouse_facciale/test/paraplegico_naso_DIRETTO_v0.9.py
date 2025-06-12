import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import sys
from collections import deque
import platform

def play_beep():
    if platform.system() == "Windows":
        try:
            import winsound
            winsound.Beep(500, 200)
        except ImportError:
            print("winsound not available. Install it for Windows beeps.")
    elif platform.system() == "Linux":
        try:
            import subprocess
            subprocess.Popen(['aplay', '-q', '/usr/share/sounds/alsa/Front_Left.wav'])
        except Exception as e:
            print(f"Failed to play beep on Linux: {e}")
    elif platform.system() == "Darwin":
        try:
            import os
            os.system('afplay /System/Library/Sounds/Tink.aiff')
        except Exception as e:
            print(f"Failed to play beep on macOS: {e}")

class JoystickHeadMouseController:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.001

        self.screen_w, self.screen_h = pyautogui.size()
        
        self.NOSE_TIP = 1
        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]

        # Default values for when no face is detected
        self.last_nose_pos = np.array([320.0, 240.0])
        self.last_left_ear = 0.3
        self.last_right_ear = 0.3

        # Calibration system
        self.calibrated = False
        self.calibration_stage = 0
        self.calibration_data = {
            'center': [],
            'left': [],
            'right': [],
            'up': [],
            'down': [],
            'eyes_open': [],
            'left_eye_closed': [],
            'right_eye_closed': [],
            'both_eyes_closed': []
        }
        self.current_calibration_stage_frames = 0
        self.CALIBRATION_STAGE_DURATION = 60  # Reduced duration
        self.CALIBRATION_GUIDE_TEXTS = {
            0: "Preparazione calibrazione...",
            1: "GUARDA DRITTO AL CENTRO",
            2: "GUARDA IL PIÙ A SINISTRA POSSIBILE", 
            3: "GUARDA IL PIÙ A DESTRA POSSIBILE",
            4: "GUARDA IL PIÙ IN ALTO POSSIBILE",
            5: "GUARDA IL PIÙ IN BASSO POSSIBILE",
            6: "MANTIENI GLI OCCHI APERTI",
            7: "CHIUDI SOLO L'OCCHIO SINISTRO",
            8: "CHIUDI SOLO L'OCCHIO DESTRO", 
            9: "CHIUDI ENTRAMBI GLI OCCHI",
            10: "Elaborazione dati...",
            11: "CALIBRATO! Joystick Attivo."
        }
        self.last_calibration_stage_start_time = time.time()
        self.calibration_beep_played = False

        # Joystick control parameters
        self.center_position = np.array([0.0, 0.0])  # Calibrated center
        self.movement_sensitivity = 3.0  # Speed multiplier
        self.deadzone_radius = 8.0  # Pixels of deadzone around center
        
        # Current cursor position
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        
        # Eye detection thresholds
        self.eyes_open_threshold = 0.25
        self.eye_closed_threshold = 0.15
        
        # Click detection
        self.eye_history = deque(maxlen=10)
        self.REQUIRED_EYE_FRAMES = 8  # Frames to confirm eye state
        self.last_left_click_time = 0.0
        self.last_right_click_time = 0.0
        self.last_double_click_time = 0.0
        self.CLICK_COOLDOWN = 0.7

    def _get_ear(self, landmarks, eye_points):
        try:
            p1 = landmarks[eye_points[0]]
            p2 = landmarks[eye_points[1]]
            p3 = landmarks[eye_points[2]]
            p4 = landmarks[eye_points[3]]
            p5 = landmarks[eye_points[4]]
            p6 = landmarks[eye_points[5]]

            vertical1_dist = np.linalg.norm(p2 - p6)
            vertical2_dist = np.linalg.norm(p3 - p5)
            horizontal_dist = np.linalg.norm(p1 - p4)

            ear = (vertical1_dist + vertical2_dist) / (2.0 * horizontal_dist) if horizontal_dist != 0 else 0
            return ear
        except (IndexError, ValueError):
            return 0.3

    def calibrate_system(self, nose_pos, left_ear, right_ear):
        current_time = time.time()

        if not self.calibration_beep_played and current_time - self.last_calibration_stage_start_time > 0.5:
            play_beep()
            self.calibration_beep_played = True

        if self.calibration_stage == 0:
            if current_time - self.last_calibration_stage_start_time > 2.0:
                self.calibration_stage = 1
                self.current_calibration_stage_frames = 0
                self.last_calibration_stage_start_time = current_time
                self.calibration_beep_played = False
            return

        # Data collection for each stage
        stage_key_map = {
            1: 'center', 2: 'left', 3: 'right', 4: 'up', 5: 'down',
            6: 'eyes_open', 7: 'left_eye_closed', 8: 'right_eye_closed', 9: 'both_eyes_closed'
        }
        
        current_stage_key = stage_key_map.get(self.calibration_stage)

        if current_stage_key:
            if current_stage_key in ['center', 'left', 'right', 'up', 'down']:
                self.calibration_data[current_stage_key].append(nose_pos.copy())
            elif current_stage_key == 'eyes_open':
                self.calibration_data[current_stage_key].append((left_ear, right_ear))
            elif current_stage_key == 'left_eye_closed':
                self.calibration_data[current_stage_key].append((left_ear, right_ear))
            elif current_stage_key == 'right_eye_closed':
                self.calibration_data[current_stage_key].append((left_ear, right_ear))
            elif current_stage_key == 'both_eyes_closed':
                self.calibration_data[current_stage_key].append((left_ear, right_ear))

            self.current_calibration_stage_frames += 1

            if self.current_calibration_stage_frames >= self.CALIBRATION_STAGE_DURATION:
                self.calibration_stage += 1
                self.current_calibration_stage_frames = 0
                self.last_calibration_stage_start_time = current_time
                self.calibration_beep_played = False

        if self.calibration_stage == 10:
            print("Processing calibration data...")
            self._process_calibration_data()

    def _process_calibration_data(self):
        """Process calibration data and set up joystick parameters"""
        
        # Set center position
        center_data = np.array(self.calibration_data['center'])
        if center_data.size > 0:
            self.center_position = np.mean(center_data, axis=0)
            print(f"Center position set to: {self.center_position}")
        else:
            print("Warning: No center calibration data")
            self.center_position = self.last_nose_pos.copy()

        # Calculate movement sensitivity based on calibration range
        all_positions = []
        for key in ['left', 'right', 'up', 'down']:
            if self.calibration_data[key]:
                all_positions.extend(self.calibration_data[key])
        
        if all_positions:
            positions = np.array(all_positions)
            # Calculate average distance from center for sensitivity
            distances = [np.linalg.norm(pos - self.center_position) for pos in positions]
            avg_distance = np.mean(distances)
            
            # Adjust sensitivity based on user's movement range
            self.movement_sensitivity = max(1.0, min(5.0, 100.0 / avg_distance))
            print(f"Movement sensitivity set to: {self.movement_sensitivity}")

        # Process eye thresholds
        self._process_eye_thresholds()
        
        self.calibrated = True
        self.calibration_stage = 11
        print("Calibration completed successfully!")
        
        # Set initial cursor position to screen center
        self.current_cursor_pos = np.array([self.screen_w // 2, self.screen_h // 2], dtype=float)
        pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])

    def _process_eye_thresholds(self):
        """Calculate eye detection thresholds from calibration data"""
        
        # Eyes open baseline
        if self.calibration_data['eyes_open']:
            open_ears = np.array(self.calibration_data['eyes_open'])
            avg_open_left = np.mean(open_ears[:, 0])
            avg_open_right = np.mean(open_ears[:, 1])
            self.eyes_open_threshold = (avg_open_left + avg_open_right) / 2
            print(f"Eyes open threshold: {self.eyes_open_threshold:.3f}")

        # Left eye closed
        if self.calibration_data['left_eye_closed']:
            left_closed_ears = np.array(self.calibration_data['left_eye_closed'])
            avg_left_closed = np.mean(left_closed_ears[:, 0])
            self.left_eye_closed_threshold = avg_left_closed + 0.02
            print(f"Left eye closed threshold: {self.left_eye_closed_threshold:.3f}")
        else:
            self.left_eye_closed_threshold = self.eyes_open_threshold * 0.6

        # Right eye closed  
        if self.calibration_data['right_eye_closed']:
            right_closed_ears = np.array(self.calibration_data['right_eye_closed'])
            avg_right_closed = np.mean(right_closed_ears[:, 0])
            self.right_eye_closed_threshold = avg_right_closed + 0.02
            print(f"Right eye closed threshold: {self.right_eye_closed_threshold:.3f}")
        else:
            self.right_eye_closed_threshold = self.eyes_open_threshold * 0.6

        # Both eyes closed
        if self.calibration_data['both_eyes_closed']:
            both_closed_ears = np.array(self.calibration_data['both_eyes_closed'])
            avg_both_closed = np.mean(both_closed_ears, axis=0)
            self.both_eyes_closed_threshold = np.mean(avg_both_closed) + 0.02
            print(f"Both eyes closed threshold: {self.both_eyes_closed_threshold:.3f}")
        else:
            self.both_eyes_closed_threshold = self.eyes_open_threshold * 0.6

        # Ensure reasonable thresholds
        self.left_eye_closed_threshold = np.clip(self.left_eye_closed_threshold, 0.05, 0.25)
        self.right_eye_closed_threshold = np.clip(self.right_eye_closed_threshold, 0.05, 0.25)
        self.both_eyes_closed_threshold = np.clip(self.both_eyes_closed_threshold, 0.05, 0.25)

    def update_cursor_position(self, nose_pos):
        """Update cursor position using joystick-style movement"""
        
        # Calculate offset from center
        offset = nose_pos - self.center_position
        
        # Apply deadzone
        distance = np.linalg.norm(offset)
        if distance < self.deadzone_radius:
            return  # No movement within deadzone
        
        # Calculate movement vector (reduce by deadzone)
        movement_factor = (distance - self.deadzone_radius) / distance
        movement_vector = offset * movement_factor * self.movement_sensitivity
        
        # Update cursor position
        self.current_cursor_pos += movement_vector
        
        # Constrain to screen bounds
        self.current_cursor_pos[0] = np.clip(self.current_cursor_pos[0], 0, self.screen_w - 1)
        self.current_cursor_pos[1] = np.clip(self.current_cursor_pos[1], 0, self.screen_h - 1)
        
        # Move the actual cursor
        try:
            pyautogui.moveTo(self.current_cursor_pos[0], self.current_cursor_pos[1])
        except Exception as e:
            print(f"Mouse movement failed: {e}")

    def detect_eye_clicks(self, left_ear, right_ear):
        """Detect clicks based on eye states"""
        
        self.eye_history.append((left_ear, right_ear))
        
        if len(self.eye_history) < self.REQUIRED_EYE_FRAMES:
            return
        
        current_time = time.time()
        
        # Get recent eye states
        recent_eyes = list(self.eye_history)[-self.REQUIRED_EYE_FRAMES:]
        recent_left = [eyes[0] for eyes in recent_eyes]
        recent_right = [eyes[1] for eyes in recent_eyes]
        
        # Check for consistent eye states
        left_consistently_closed = all(ear < self.left_eye_closed_threshold for ear in recent_left)
        right_consistently_closed = all(ear < self.right_eye_closed_threshold for ear in recent_right)
        both_consistently_closed = all((left + right) / 2 < self.both_eyes_closed_threshold 
                                     for left, right in recent_eyes)
        
        left_consistently_open = all(ear > self.eyes_open_threshold for ear in recent_left)
        right_consistently_open = all(ear > self.eyes_open_threshold for ear in recent_right)
        
        # Double click - both eyes closed
        if both_consistently_closed:
            if (current_time - self.last_double_click_time) > self.CLICK_COOLDOWN:
                try:
                    pyautogui.doubleClick()
                    self.last_double_click_time = current_time
                    print("[ACTION] Double Click (Both eyes closed)")
                    self.eye_history.clear()  # Clear to prevent multiple triggers
                except Exception as e:
                    print(f"Double click failed: {e}")
        
        # Left click - left eye closed, right eye open
        elif left_consistently_closed and right_consistently_open:
            if (current_time - self.last_left_click_time) > self.CLICK_COOLDOWN:
                try:
                    pyautogui.click()
                    self.last_left_click_time = current_time
                    print("[ACTION] Left Click (Left eye closed)")
                    self.eye_history.clear()  # Clear to prevent multiple triggers
                except Exception as e:
                    print(f"Left click failed: {e}")
        
        # Right click - right eye closed, left eye open  
        elif right_consistently_closed and left_consistently_open:
            if (current_time - self.last_right_click_time) > self.CLICK_COOLDOWN:
                try:
                    pyautogui.click(button='right')
                    self.last_right_click_time = current_time
                    print("[ACTION] Right Click (Right eye closed)")
                    self.eye_history.clear()  # Clear to prevent multiple triggers
                except Exception as e:
                    print(f"Right click failed: {e}")

    def draw_interface(self, frame, nose_pos, left_ear, right_ear):
        """Draw the user interface"""
        h, w = frame.shape[:2]

        # Draw nose position
        if self.calibrated:
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 255, 0), -1)
            
            # Draw center position and deadzone
            center_screen = self.center_position.astype(int)
            cv2.circle(frame, tuple(center_screen), int(self.deadzone_radius), (255, 255, 0), 2)
            cv2.circle(frame, tuple(center_screen), 3, (255, 255, 0), -1)
            
            # Draw movement vector
            if np.linalg.norm(nose_pos - self.center_position) > self.deadzone_radius:
                cv2.arrowedLine(frame, tuple(center_screen), tuple(nose_pos.astype(int)), (0, 255, 255), 2)
        else:
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)

        # Status text
        status_text = self.CALIBRATION_GUIDE_TEXTS.get(self.calibration_stage, "Unknown stage")
        color = (0, 255, 255) if not self.calibrated else (0, 255, 0)
        
        if 0 < self.calibration_stage < 10 and not self.calibrated:
            progress_text = f" ({self.current_calibration_stage_frames}/{self.CALIBRATION_STAGE_DURATION})"
            status_text += progress_text
            
        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Debug information if calibrated
        if self.calibrated:
            # Current position info
            cv2.putText(frame, f"Nose: {int(nose_pos[0])},{int(nose_pos[1])}", (20, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Cursor: {int(self.current_cursor_pos[0])},{int(self.current_cursor_pos[1])}", (20, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Eye states
            left_state = "CLOSED" if left_ear < self.left_eye_closed_threshold else "OPEN"
            right_state = "CLOSED" if right_ear < self.right_eye_closed_threshold else "OPEN"
            both_state = "CLOSED" if (left_ear + right_ear) / 2 < self.both_eyes_closed_threshold else "OPEN"
            
            cv2.putText(frame, f"Left Eye: {left_state} ({left_ear:.2f})", (20, 140),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if left_state == "OPEN" else (0, 0, 255), 1)
            cv2.putText(frame, f"Right Eye: {right_state} ({right_ear:.2f})", (20, 170),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if right_state == "OPEN" else (0, 0, 255), 1)
            cv2.putText(frame, f"Both Eyes: {both_state}", (20, 200),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if both_state == "OPEN" else (0, 0, 255), 1)

            # Movement info
            offset = nose_pos - self.center_position
            distance = np.linalg.norm(offset)
            cv2.putText(frame, f"Distance from center: {distance:.1f}px", (20, 230),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Instructions
            cv2.putText(frame, "JOYSTICK MODE - Move head to move cursor", (20, h-130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Close LEFT eye: Left Click", (20, h-100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Close RIGHT eye: Right Click", (20, h-70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Close BOTH eyes: Double Click", (20, h-40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

def main():
    print("="*60)
    print("JOYSTICK-STYLE HEAD MOUSE CONTROLLER")
    print("="*60)
    print("Joystick movement: Move head relative to center position")
    print("Left Click: Close left eye")
    print("Right Click: Close right eye") 
    print("Double Click: Close both eyes")
    print("="*60)

    controller = JoystickHeadMouseController()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Cannot open webcam. Check connection and permissions.")
        sys.exit(1)

    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("Press ESC to exit")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Warning: Cannot read frame. Exiting.")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = controller.face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                nose_pos = landmarks_np[controller.NOSE_TIP]
                left_ear = controller._get_ear(landmarks_np, controller.LEFT_EYE_POINTS)
                right_ear = controller._get_ear(landmarks_np, controller.RIGHT_EYE_POINTS)

                # Update last known values
                controller.last_nose_pos = nose_pos.copy()
                controller.last_left_ear = left_ear
                controller.last_right_ear = right_ear

                if not controller.calibrated:
                    controller.calibrate_system(nose_pos, left_ear, right_ear)
                else:
                    # Joystick movement
                    controller.update_cursor_position(nose_pos)
                    # Eye click detection
                    controller.detect_eye_clicks(left_ear, right_ear)

            else:
                # No face detected - clear eye history
                controller.eye_history.clear()

            # Draw interface using last known values
            controller.draw_interface(frame, 
                                    controller.last_nose_pos, 
                                    controller.last_left_ear, 
                                    controller.last_right_ear)

            cv2.imshow('Joystick Head Mouse', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Cleanup completed.")

if __name__ == "__main__":
    main()