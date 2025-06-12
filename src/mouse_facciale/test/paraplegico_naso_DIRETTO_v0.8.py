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
            print(f"Failed to play beep on Linux: {e}. Ensure 'aplay' or 'sox' is installed.")
    elif platform.system() == "Darwin":
        try:
            import os
            os.system('afplay /System/Library/Sounds/Tink.aiff')
        except Exception as e:
            print(f"Failed to play beep on macOS: {e}")

class HeadMouseController:
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
        self.screen_center = np.array([self.screen_w // 2, self.screen_h // 2], dtype=np.float64)

        self.pos_filter = self.screen_center.copy()
        self.prev_pos = self.screen_center.copy()
        self.deadzone_radius = 0.005 * min(self.screen_w, self.screen_h)  # Reduced deadzone

        self.NOSE_TIP = 1

        self.LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]
        self.MOUTH_POINTS = [13, 14, 78, 308]

        # Default values for when no face is detected
        self.last_nose_pos = np.array([320.0, 240.0])
        self.last_left_ear = 0.3
        self.last_right_ear = 0.3
        self.last_mouth_ratio = 0.1

        self.calibrated = False
        self.calibration_stage = 0
        self.calibration_data = {
            'center': [],
            'left': [],
            'right': [],
            'up': [],
            'down': [],
            'closed_eyes': [],
            'open_mouth': []
        }
        self.current_calibration_stage_frames = 0
        self.CALIBRATION_STAGE_DURATION = 90
        self.CALIBRATION_GUIDE_TEXTS = {
            0: "Preparazione calibrazione...",
            1: "GUARDA DRITTO AL CENTRO",
            2: "GUARDA IL PIÙ A SINISTRA POSSIBILE",
            3: "GUARDA IL PIÙ A DESTRA POSSIBILE",
            4: "GUARDA IL PIÙ IN ALTO POSSIBILE",
            5: "GUARDA IL PIÙ IN BASSO POSSIBILE",
            6: "CHIUDI GLI OCCHI (per calibrazione click)",
            7: "APRI LA BOCCA (per calibrazione doppio click)",
            8: "Elaborazione dati...",
            9: "CALIBRATO! Mouse Attivo."
        }
        self.last_calibration_stage_start_time = time.time()
        self.calibration_beep_played = False

        self.movement_range = {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}
        self.MARGIN_FACTOR = 0.12  # Increased margin for better range

        # Improved stillness detection
        self.nose_pos_history = deque(maxlen=45)  # Reduced for faster response
        self.STILLNESS_HISTORY_LENGTH = 30  # Reduced duration (0.5s at 60 FPS)
        self.STILL_MOVEMENT_THRESHOLD_PIXELS = 3.0  # Slightly more tolerant

        self.calibrated_blink_threshold = 0.25
        self.calibrated_mouth_threshold = 0.40
        
        # Improved gesture detection
        self.eye_history = deque(maxlen=20)  # Increased for better detection
        self.mouth_history = deque(maxlen=20)
        self.EYE_MOUTH_HISTORY_LENGTH = 12  # Increased for more reliable detection

        # Improved timing
        self.STILL_TIME_THRESHOLD = 0.8  # Reduced for faster clicks
        self.last_movement_time = time.time()
        self.is_still = False

        self.last_left_click_time = 0.0
        self.last_right_click_time = 0.0
        self.last_double_click_time = 0.0
        self.CLICK_COOLDOWN = 1.0  # Increased cooldown

        self.FILTER_STRENGTH = 0.25  # Increased for smoother movement

        # Blink detection improvements
        self.consecutive_blinks = {'left': 0, 'right': 0}
        self.REQUIRED_CONSECUTIVE_BLINKS = 8  # Need consistent blinks
        self.normal_ear_baseline = 0.3  # Baseline for open eyes

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
            return 0.3  # Default open eye value

    def _get_mar(self, landmarks):
        try:
            p_top = landmarks[self.MOUTH_POINTS[0]]
            p_bottom = landmarks[self.MOUTH_POINTS[1]]
            p_right = landmarks[self.MOUTH_POINTS[2]]
            p_left = landmarks[self.MOUTH_POINTS[3]]

            vertical_dist = np.linalg.norm(p_top - p_bottom)
            horizontal_dist = np.linalg.norm(p_right - p_left)

            mar = vertical_dist / horizontal_dist if horizontal_dist != 0 else 0
            return mar
        except (IndexError, ValueError):
            return 0.1  # Default closed mouth value

    def calibrate_movement_range(self, nose_pos, left_ear, right_ear, mouth_ratio):
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

        stage_key_map = {
            1: 'center', 2: 'left', 3: 'right', 4: 'up', 5: 'down',
            6: 'closed_eyes', 7: 'open_mouth'
        }
        current_stage_key = stage_key_map.get(self.calibration_stage)

        if current_stage_key:
            if current_stage_key in ['center', 'left', 'right', 'up', 'down']:
                self.calibration_data[current_stage_key].append(nose_pos.copy())
            elif current_stage_key == 'closed_eyes':
                self.calibration_data[current_stage_key].append((left_ear + right_ear) / 2)
            elif current_stage_key == 'open_mouth':
                self.calibration_data[current_stage_key].append(mouth_ratio)

            self.current_calibration_stage_frames += 1

            if self.current_calibration_stage_frames >= self.CALIBRATION_STAGE_DURATION:
                self.calibration_stage += 1
                self.current_calibration_stage_frames = 0
                self.last_calibration_stage_start_time = current_time
                self.calibration_beep_played = False
                self.nose_pos_history.clear()
                self.eye_history.clear()
                self.mouth_history.clear()
                self.pos_filter = self.screen_center.copy()
                self.prev_pos = self.screen_center.copy()

        if self.calibration_stage == 8:
            print("Elaborando dati di calibrazione...")
            self._process_calibration_data(nose_pos)

    def _process_calibration_data(self, current_nose_pos):
        """Process calibration data and set up movement ranges"""
        all_x_head = []
        all_y_head = []

        # Get center position
        center_data = np.array(self.calibration_data['center'])
        if center_data.size > 0:
            center_x_avg = np.mean(center_data[:, 0])
            center_y_avg = np.mean(center_data[:, 1])
        else:
            center_x_avg = current_nose_pos[0]
            center_y_avg = current_nose_pos[1]
            print("Warning: Insufficient center calibration data.")

        # Collect all movement data
        for key in ['left', 'right', 'up', 'down']:
            if self.calibration_data[key]:
                data = np.array(self.calibration_data[key])
                all_x_head.extend(data[:, 0])
                all_y_head.extend(data[:, 1])

        if not all_x_head or not all_y_head:
            print("Error: Insufficient movement calibration data.")
            self.calibrated = False
            self.calibration_stage = 0
            return

        # Set movement ranges with improved scaling
        self.movement_range['min_x'] = min(all_x_head)
        self.movement_range['max_x'] = max(all_x_head)
        self.movement_range['min_y'] = min(all_y_head)
        self.movement_range['max_y'] = max(all_y_head)

        # Add margins
        x_range = self.movement_range['max_x'] - self.movement_range['min_x']
        y_range = self.movement_range['max_y'] - self.movement_range['min_y']

        self.movement_range['min_x'] -= x_range * self.MARGIN_FACTOR
        self.movement_range['max_x'] += x_range * self.MARGIN_FACTOR
        self.movement_range['min_y'] -= y_range * self.MARGIN_FACTOR
        self.movement_range['max_y'] += y_range * self.MARGIN_FACTOR

        # Center the range around the calibrated center position
        current_mid_x = (self.movement_range['min_x'] + self.movement_range['max_x']) / 2
        current_mid_y = (self.movement_range['min_y'] + self.movement_range['max_y']) / 2

        offset_x = center_x_avg - current_mid_x
        offset_y = center_y_avg - current_mid_y

        self.movement_range['min_x'] += offset_x
        self.movement_range['max_x'] += offset_x
        self.movement_range['min_y'] += offset_y
        self.movement_range['max_y'] += offset_y

        # Process gesture thresholds
        self._calibrate_gesture_thresholds()

        self.calibrated = True
        self.calibration_stage = 9
        print("Calibration completed successfully!")
        
        # Clear calibration data
        self.calibration_data = {k: [] for k in self.calibration_data}

    def _calibrate_gesture_thresholds(self):
        """Calibrate gesture detection thresholds"""
        closed_eyes_data = np.array(self.calibration_data['closed_eyes'])
        open_mouth_data = np.array(self.calibration_data['open_mouth'])

        if closed_eyes_data.size > 0:
            avg_closed_ear = np.mean(closed_eyes_data)
            self.calibrated_blink_threshold = avg_closed_ear + 0.03
            self.normal_ear_baseline = avg_closed_ear + 0.15  # Set baseline for open eyes
            print(f"Blink threshold: {self.calibrated_blink_threshold:.3f}")
        else:
            print("Warning: Insufficient closed eyes data.")

        if open_mouth_data.size > 0:
            avg_open_mar = np.mean(open_mouth_data)
            self.calibrated_mouth_threshold = avg_open_mar * 0.75
            print(f"Mouth threshold: {self.calibrated_mouth_threshold:.3f}")
        else:
            print("Warning: Insufficient open mouth data.")

        # Ensure reasonable thresholds
        self.calibrated_blink_threshold = np.clip(self.calibrated_blink_threshold, 0.05, 0.25)
        self.calibrated_mouth_threshold = np.clip(self.calibrated_mouth_threshold, 0.25, 0.6)

    def smooth_movement(self, target_pos):
        """Improved smooth movement with better responsiveness"""
        # Apply exponential smoothing
        self.pos_filter = self.pos_filter * (1 - self.FILTER_STRENGTH) + target_pos * self.FILTER_STRENGTH

        movement_vector = self.pos_filter - self.prev_pos
        distance_sq = np.dot(movement_vector, movement_vector)

        # Smaller deadzone for better responsiveness
        if distance_sq < self.deadzone_radius**2:
            return self.prev_pos.copy()

        distance = np.sqrt(distance_sq)
        
        # Improved acceleration curve
        acceleration_distance = self.deadzone_radius * 2
        raw_acceleration = min(1.0, (distance - self.deadzone_radius) / acceleration_distance)
        acceleration = raw_acceleration ** 0.8  # Smoother acceleration curve

        new_pos = self.prev_pos + movement_vector * acceleration

        # Ensure bounds
        new_pos[0] = np.clip(new_pos[0], 0, self.screen_w - 1)
        new_pos[1] = np.clip(new_pos[1], 0, self.screen_h - 1)

        return new_pos

    def _is_still_enough(self):
        """Improved stillness detection"""
        if len(self.nose_pos_history) < self.STILLNESS_HISTORY_LENGTH:
            return False
        
        recent_positions = list(self.nose_pos_history)[-self.STILLNESS_HISTORY_LENGTH:]
        recent_x = [p[0] for p in recent_positions]
        recent_y = [p[1] for p in recent_positions]
        
        std_dev_x = np.std(recent_x)
        std_dev_y = np.std(recent_y)
        
        return (std_dev_x < self.STILL_MOVEMENT_THRESHOLD_PIXELS and 
                std_dev_y < self.STILL_MOVEMENT_THRESHOLD_PIXELS)

    def _is_deliberate_blink(self, ear_history, eye_index):
        """Improved blink detection - requires deliberate, sustained blinks"""
        if len(ear_history) < self.REQUIRED_CONSECUTIVE_BLINKS:
            return False
        
        recent_ears = [ear[eye_index] for ear in list(ear_history)[-self.REQUIRED_CONSECUTIVE_BLINKS:]]
        other_eye_ears = [ear[1-eye_index] for ear in list(ear_history)[-self.REQUIRED_CONSECUTIVE_BLINKS:]]
        
        # Check if target eye is consistently closed
        target_eye_closed = all(ear < self.calibrated_blink_threshold for ear in recent_ears)
        
        # Check if other eye is consistently open
        other_eye_open = all(ear > self.calibrated_blink_threshold + 0.05 for ear in other_eye_ears)
        
        return target_eye_closed and other_eye_open

    def _is_mouth_open(self, mouth_history):
        """Improved mouth open detection"""
        if len(mouth_history) < self.EYE_MOUTH_HISTORY_LENGTH:
            return False
        
        recent_mouth = list(mouth_history)[-self.EYE_MOUTH_HISTORY_LENGTH:]
        return all(mr > self.calibrated_mouth_threshold for mr in recent_mouth)

    def _check_left_click(self, current_time):
        """Left click via stillness"""
        if self._is_still_enough():
            if not self.is_still:
                self.last_movement_time = current_time
                self.is_still = True
            elif (current_time - self.last_movement_time) >= self.STILL_TIME_THRESHOLD:
                if (current_time - self.last_left_click_time) > self.CLICK_COOLDOWN:
                    try:
                        pyautogui.click()
                        self.last_left_click_time = current_time
                        self.is_still = False
                        print(f"[ACTION] Left Click (Still for {self.STILL_TIME_THRESHOLD:.1f}s)")
                    except Exception as e:
                        print(f"Left click failed: {e}")
        else:
            self.is_still = False

    def _check_right_click(self, current_time):
        """Improved right click via deliberate single-eye blink"""
        if len(self.eye_history) < self.REQUIRED_CONSECUTIVE_BLINKS:
            return
            
        is_left_eye_blink = self._is_deliberate_blink(self.eye_history, 0)
        is_right_eye_blink = self._is_deliberate_blink(self.eye_history, 1)

        if (is_left_eye_blink and not is_right_eye_blink) or \
           (is_right_eye_blink and not is_left_eye_blink):
            if (current_time - self.last_right_click_time) > self.CLICK_COOLDOWN:
                try:
                    pyautogui.click(button='right')
                    self.last_right_click_time = current_time
                    print("[ACTION] Right Click (Deliberate wink)")
                    # Clear history to prevent multiple triggers
                    self.eye_history.clear()
                except Exception as e:
                    print(f"Right click failed: {e}")

    def _check_double_click(self, current_time):
        """Double click via mouth opening"""
        if self._is_mouth_open(self.mouth_history):
            if (current_time - self.last_double_click_time) > self.CLICK_COOLDOWN:
                try:
                    pyautogui.doubleClick()
                    self.last_double_click_time = current_time
                    print("[ACTION] Double Click (Mouth open)")
                    # Clear history to prevent multiple triggers
                    self.mouth_history.clear()
                except Exception as e:
                    print(f"Double click failed: {e}")

    def detect_gestures(self, nose_pos, left_ear, right_ear, mouth_ratio):
        """Main gesture detection function"""
        self.nose_pos_history.append(nose_pos.copy())
        self.eye_history.append((left_ear, right_ear))
        self.mouth_history.append(mouth_ratio)

        current_time = time.time()

        self._check_left_click(current_time)
        self._check_right_click(current_time)
        self._check_double_click(current_time)

    def draw_interface(self, frame, nose_pos, left_ear, right_ear, mouth_ratio):
        """Draw the user interface"""
        h, w = frame.shape[:2]

        # Draw movement range if calibrated
        if self.calibrated:
            cv2.rectangle(frame,
                        (int(self.movement_range['min_x']), int(self.movement_range['min_y'])),
                        (int(self.movement_range['max_x']), int(self.movement_range['max_y'])),
                        (0, 255, 0), 2)
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 255, 0), -1)
        else:
            cv2.circle(frame, tuple(nose_pos.astype(int)), 8, (0, 165, 255), -1)

        # Status text
        status_text = self.CALIBRATION_GUIDE_TEXTS.get(self.calibration_stage, "Unknown stage")
        color = (0, 255, 255) if not self.calibrated else (0, 255, 0)
        
        if 0 < self.calibration_stage < 8 and not self.calibrated:
            progress_text = f" ({self.current_calibration_stage_frames}/{self.CALIBRATION_STAGE_DURATION})"
            status_text += progress_text
            
        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Debug information if calibrated
        if self.calibrated:
            cv2.putText(frame, f"Pos: {int(nose_pos[0])},{int(nose_pos[1])}", (20, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cv2.putText(frame, f"Eyes: L={left_ear:.2f} R={right_ear:.2f} (Thresh: {self.calibrated_blink_threshold:.2f})", 
                       (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Mouth: {mouth_ratio:.2f} (Thresh: {self.calibrated_mouth_threshold:.2f})", 
                       (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            still_status = "STILL" if self.is_still else "MOVING"
            still_color = (0, 255, 0) if self.is_still else (0, 165, 255)
            still_time = current_time - self.last_movement_time if hasattr(self, 'last_movement_time') else 0
            cv2.putText(frame, f"State: {still_status} ({still_time:.1f}s)", 
                       (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, still_color, 1)

            # Instructions
            cv2.putText(frame, "Stay STILL (>=0.8s): Left Click", (20, h-100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Deliberate Wink: Right Click", (20, h-70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, "Open Mouth Wide: Double Click", (20, h-40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

def main():
    print("="*60)
    print("OPTIMIZED HEAD MOUSE CONTROLLER")
    print("="*60)
    print("Enhanced mouse control via head movements and facial gestures.")
    print("Improved calibration and gesture detection.")
    print("="*60)

    controller = HeadMouseController()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Cannot open webcam. Check connection and permissions.")
        sys.exit(1)

    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency

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
                mouth_ratio = controller._get_mar(landmarks_np)

                # Update last known values
                controller.last_nose_pos = nose_pos.copy()
                controller.last_left_ear = left_ear
                controller.last_right_ear = right_ear
                controller.last_mouth_ratio = mouth_ratio

                if not controller.calibrated:
                    controller.calibrate_movement_range(nose_pos, left_ear, right_ear, mouth_ratio)
                else:
                    # Map nose position to screen coordinates
                    norm_x = np.interp(nose_pos[0],
                                       [controller.movement_range['min_x'], controller.movement_range['max_x']],
                                       [0, controller.screen_w])
                    norm_y = np.interp(nose_pos[1],
                                       [controller.movement_range['min_y'], controller.movement_range['max_y']],
                                       [0, controller.screen_h])

                    target_pos = np.array([norm_x, norm_y], dtype=np.float64)
                    smooth_pos = controller.smooth_movement(target_pos)
                    
                    try:
                        pyautogui.moveTo(smooth_pos[0], smooth_pos[1])
                    except Exception as e:
                        print(f"Mouse movement failed: {e}")
                        
                    controller.prev_pos = smooth_pos
                    controller.detect_gestures(nose_pos, left_ear, right_ear, mouth_ratio)

            else:
                # No face detected - clear gesture histories
                controller.nose_pos_history.clear()
                controller.eye_history.clear()
                controller.mouth_history.clear()
                controller.is_still = False
                
                if controller.calibrated:
                    controller.pos_filter = controller.screen_center.copy()
                    controller.prev_pos = controller.screen_center.copy()

            # Use last known values for display
            controller.draw_interface(frame, 
                                    controller.last_nose_pos, 
                                    controller.last_left_ear, 
                                    controller.last_right_ear, 
                                    controller.last_mouth_ratio)

            cv2.imshow('Optimized Head Mouse', frame)
            
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