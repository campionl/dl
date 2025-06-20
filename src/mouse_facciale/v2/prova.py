import cv2
import mediapipe as mp
import numpy as np
import time
import sys
from collections import deque
import threading
import json
import os
from flask import Flask, Response, render_template_string, request, jsonify
import signal
import pyautogui
import atexit

# Constants
CONFIG_FILE = '/tmp/headmouse_config.json'
DEFAULT_CONFIG = {
    "sensitivity": 4.0,
    "scroll_sensitivity": 2.0,
    "deadzone_radius": 15.0,
    "max_acceleration_distance": 200.0,
    "open_mouth_threshold": 0.15,
    "blink_threshold": 0.10,
    "event_action_mappings": [
        {
            "event_type": "left_eye_blink",
            "action_type": "left_click",
            "params": {}
        },
        {
            "event_type": "right_eye_blink",
            "action_type": "right_click",
            "params": {}
        },
        {
            "event_type": "open_mouth",
            "action_type": "switch_mode",
            "params": {}
        }
    ]
}

class BaseEvent:
    """Base class for all events"""
    def check_event(self, *args, **kwargs):
        """Abstract method to check if event is active"""
        raise NotImplementedError

class BaseAction:
    """Base class for all actions"""
    def execute(self, *args, **kwargs):
        """Abstract method to execute the action"""
        raise NotImplementedError

class CalibrationAction:
    """Class for center calibration management"""
    def __init__(self, max_samples=30):
        self.center_samples = []
        self.max_center_samples = max_samples
        self.center_calculated = False
        self.center_position = None
    
    def add_sample(self, tracking_point):
        """Add a sample for calibration"""
        if not self.center_calculated:
            self.center_samples.append(tracking_point.copy())
            
            if len(self.center_samples) >= self.max_center_samples:
                self.center_position = np.median(self.center_samples, axis=0)
                self.center_calculated = True
                print(f"Center calibrated: {self.center_position}")
                return True
        return False
    
    def reset_calibration(self):
        """Reset calibration"""
        self.center_calculated = False
        self.center_samples = []
        self.center_position = None
        print("Calibration reset")
    
    def set_new_center(self, new_center):
        """Set new center directly"""
        self.center_position = new_center.copy()
        self.center_calculated = True
        self.center_samples = [new_center] * self.max_center_samples
        print(f"New center set: {self.center_position}")

class NoseJoystickEvent(BaseEvent):
    """Class to detect nose joystick events"""
    def __init__(self, deadzone_radius=15.0, max_acceleration_distance=200.0):
        self.deadzone_radius = deadzone_radius
        self.max_acceleration_distance = max_acceleration_distance
        self.outside_deadzone_start_time = None
        self.edge_time_start = None
        self.edge_timeout = 5.0
    
    def is_outside_deadzone(self, tracking_point, center_position):
        """Check if point is outside deadzone"""
        if center_position is None:
            return False
        
        offset = tracking_point - center_position
        distance = np.linalg.norm(offset)
        return distance >= self.deadzone_radius
    
    def get_movement_vector(self, tracking_point, center_position):
        """Calculate movement vector based on nose position"""
        if center_position is None:
            return None, 0, 0
        
        offset = tracking_point - center_position
        distance = np.linalg.norm(offset)
        
        if distance < self.deadzone_radius:
            self.outside_deadzone_start_time = None
            return None, 0, 0
        
        current_time = time.time()
        if self.outside_deadzone_start_time is None:
            self.outside_deadzone_start_time = current_time
        
        effective_distance = distance - self.deadzone_radius
        normalized_distance = min(effective_distance / (self.max_acceleration_distance - self.deadzone_radius), 1.0)
        
        acceleration_factor = 1.0 + (3.0 * normalized_distance ** 2)
        direction = offset / distance
        
        return direction, acceleration_factor, effective_distance
    
    def check_event(self, tracking_point, center_position):
        """Implementation of base method to check event"""
        return self.is_outside_deadzone(tracking_point, center_position)

class OpenMouthEvent(BaseEvent):
    """Class to detect mouth opening"""
    def __init__(self, upper_lip_index=13, lower_lip_index=14, threshold=0.15, duration=0.5):
        self.UPPER_LIP = upper_lip_index
        self.LOWER_LIP = lower_lip_index
        self.open_threshold = threshold
        self.open_duration_required = duration
        self.open_start_time = None
        self.mouth_open = False
        self.event_detected = False
        self.mouth_history = deque(maxlen=3)
    
    def calculate_mouth_openness(self, landmarks):
        """Calculate mouth openness"""
        try:
            upper_lip = landmarks[self.UPPER_LIP]
            lower_lip = landmarks[self.LOWER_LIP]
            openness = abs(upper_lip[1] - lower_lip[1]) / 25.0
            return openness
        except:
            return 0.0
    
    def detect_open_mouth(self, landmarks):
        """Detect mouth opening only if maintained for required time"""
        openness = self.calculate_mouth_openness(landmarks)
        self.mouth_history.append(openness)
        
        stable_openness = np.mean(list(self.mouth_history)) if self.mouth_history else openness
        current_time = time.time()
        
        if stable_openness > self.open_threshold:
            if not self.mouth_open and not self.event_detected:
                self.mouth_open = True
                self.open_start_time = current_time
            elif (self.mouth_open and 
                  not self.event_detected and 
                  self.open_start_time is not None and 
                  current_time - self.open_start_time >= self.open_duration_required):
                self.event_detected = True
                return True
        else:
            if self.mouth_open:
                self.mouth_open = False
                self.open_start_time = None
                self.event_detected = False
        
        return False
    
    def check_event(self, landmarks):
        """Implementation of base method to check event"""
        return self.detect_open_mouth(landmarks)

class SwitchModeAction(BaseAction):
    """Class to switch between pointer and scroll modes"""
    def __init__(self):
        self.last_switch_time = 0
        self.switch_cooldown = 1.0
    
    def switch_mode(self, current_mode):
        """Switch mode"""
        current_time = time.time()
        if current_time - self.last_switch_time < self.switch_cooldown:
            return current_mode
        
        new_mode = 'scroll' if current_mode == 'pointer' else 'pointer'
        print(f"Mode changed: {new_mode}")
        self.last_switch_time = current_time
        return new_mode
    
    def execute(self, current_mode):
        """Implementation of base method to execute action"""
        return self.switch_mode(current_mode)

class MouseCursorAction(BaseAction):
    """Class to translate nose movement to cursor movement"""
    def __init__(self, screen_w, screen_h, sensitivity=4.0):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.base_sensitivity = sensitivity
        self.position_history = deque(maxlen=5)
        self.mouse_lock = threading.Lock()
    
    def update_position(self, direction, acceleration_factor, effective_distance):
        """Update cursor position"""
        if direction is None:
            return

        movement = direction * self.base_sensitivity * acceleration_factor * effective_distance * 0.1
        self.position_history.append(movement)

        if len(self.position_history) > 1:
            smoothed_movement = np.mean(self.position_history, axis=0)
        else:
            smoothed_movement = movement

        with self.mouse_lock:
            try:
                current_pos = np.array(pyautogui.position())
                new_pos = current_pos + smoothed_movement
                new_pos[0] = np.clip(new_pos[0], 0, self.screen_w - 1)
                new_pos[1] = np.clip(new_pos[1], 0, self.screen_h - 1)
                pyautogui.moveTo(int(new_pos[0]), int(new_pos[1]))
            except Exception as e:
                print(f"Mouse movement error: {e}")
    
    def adjust_sensitivity(self, amount):
        """Adjust sensitivity"""
        self.base_sensitivity = np.clip(self.base_sensitivity + amount, 0.5, 5.0)
        print(f"Sensitivity updated: {self.base_sensitivity:.1f}")
    
    def execute(self, direction, acceleration_factor, effective_distance):
        """Implementation of base method to execute action"""
        self.update_position(direction, acceleration_factor, effective_distance)

class ScrollAction(BaseAction):
    """Class to perform scrolling"""
    def __init__(self, scroll_cooldown=0.03, sensitivity=2.0):
        self.scroll_cooldown = scroll_cooldown
        self.last_scroll_time = 0
        self.scroll_lock = threading.Lock()
        self.scroll_sensitivity = sensitivity
        self.scroll_history = deque(maxlen=3)
    
    def perform_scroll(self, direction, effective_distance):
        """Perform scrolling"""
        current_time = time.time()
        if current_time - self.last_scroll_time < self.scroll_cooldown:
            return False
        
        try:
            with self.scroll_lock:
                scroll_amount = -direction[1] * effective_distance * 0.1 * self.scroll_sensitivity
                self.scroll_history.append(scroll_amount)
                smoothed_scroll = np.mean(self.scroll_history) if self.scroll_history else scroll_amount
                
                scroll_value = int(smoothed_scroll)
                if abs(scroll_value) > 0:
                    pyautogui.scroll(scroll_value)
                    self.last_scroll_time = current_time
                    return True
        except Exception as e:
            print(f"Scroll error: {e}")
        return False
    
    def adjust_sensitivity(self, amount):
        """Adjust scroll sensitivity"""
        self.scroll_sensitivity = np.clip(self.scroll_sensitivity + amount, 1.0, 10.0)
        print(f"Scroll sensitivity updated: {self.scroll_sensitivity:.1f}")
    
    def execute(self, direction, effective_distance):
        """Implementation of base method to execute action"""
        return self.perform_scroll(direction, effective_distance)

class LeftEyeEvent(BaseEvent):
    """Class to detect left eye blink"""
    def __init__(self, top_index=159, bottom_index=145, blink_duration=0.3, threshold=0.10):
        self.LEFT_EYE_TOP = top_index
        self.LEFT_EYE_BOTTOM = bottom_index
        self.blink_threshold = threshold
        self.blink_duration_required = blink_duration
        self.blink_start_time = None
        self.eye_closed = False
        self.blink_detected = False
        self.ear_history = deque(maxlen=3)
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calculate EAR for left eye"""
        try:
            top = landmarks[self.LEFT_EYE_TOP]
            bottom = landmarks[self.LEFT_EYE_BOTTOM]
            ear = abs(top[1] - bottom[1]) / 25.0
            return ear
        except:
            return 0.2
    
    def detect_blink(self, landmarks):
        """Detect left eye blink only if closed for required time"""
        ear = self.calculate_eye_aspect_ratio(landmarks)
        self.ear_history.append(ear)
        
        stable_ear = np.mean(list(self.ear_history)) if self.ear_history else ear
        current_time = time.time()
        
        if stable_ear < self.blink_threshold:
            if not self.eye_closed and not self.blink_detected:
                self.eye_closed = True
                self.blink_start_time = current_time
            elif (self.eye_closed and 
                  not self.blink_detected and 
                  self.blink_start_time is not None and 
                  current_time - self.blink_start_time >= self.blink_duration_required):
                self.blink_detected = True
                return True
        else:
            if self.eye_closed:
                self.eye_closed = False
                self.blink_start_time = None
                self.blink_detected = False
        
        return False
    
    def check_event(self, landmarks):
        """Implementation of base method to check event"""
        return self.detect_blink(landmarks)

class LeftClickAction(BaseAction):
    """Class to perform left click"""
    def __init__(self, click_cooldown=0.5):
        self.click_cooldown = click_cooldown
        self.last_click_time = 0
        self.mouse_lock = threading.Lock()
    
    def perform_click(self):
        """Perform left click"""
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            with self.mouse_lock:
                pyautogui.click(button='left')
                print("LEFT click")
                self.last_click_time = current_time
                return True
        except Exception as e:
            print(f"Left click error: {e}")
            return False
    
    def execute(self, *args, **kwargs):
        """Implementation of base method to execute action"""
        return self.perform_click()

class RightEyeEvent(BaseEvent):
    """Class to detect right eye blink"""
    def __init__(self, top_index=386, bottom_index=374, blink_duration=0.3, threshold=0.10):
        self.RIGHT_EYE_TOP = top_index
        self.RIGHT_EYE_BOTTOM = bottom_index
        self.blink_threshold = threshold
        self.blink_duration_required = blink_duration
        self.blink_start_time = None
        self.eye_closed = False
        self.blink_detected = False
        self.ear_history = deque(maxlen=3)
    
    def calculate_eye_aspect_ratio(self, landmarks):
        """Calculate EAR for right eye"""
        try:
            top = landmarks[self.RIGHT_EYE_TOP]
            bottom = landmarks[self.RIGHT_EYE_BOTTOM]
            ear = abs(top[1] - bottom[1]) / 25.0
            return ear
        except:
            return 0.2
    
    def detect_blink(self, landmarks):
        """Detect right eye blink only if closed for required time"""
        ear = self.calculate_eye_aspect_ratio(landmarks)
        self.ear_history.append(ear)
        
        stable_ear = np.mean(list(self.ear_history)) if self.ear_history else ear
        current_time = time.time()
        
        if stable_ear < self.blink_threshold:
            if not self.eye_closed and not self.blink_detected:
                self.eye_closed = True
                self.blink_start_time = current_time
            elif (self.eye_closed and 
                  not self.blink_detected and 
                  self.blink_start_time is not None and 
                  current_time - self.blink_start_time >= self.blink_duration_required):
                self.blink_detected = True
                return True
        else:
            if self.eye_closed:
                self.eye_closed = False
                self.blink_start_time = None
                self.blink_detected = False
        
        return False
    
    def check_event(self, landmarks):
        """Implementation of base method to check event"""
        return self.detect_blink(landmarks)

class RightClickAction(BaseAction):
    """Class to perform right click"""
    def __init__(self, click_cooldown=0.5):
        self.click_cooldown = click_cooldown
        self.last_click_time = 0
        self.mouse_lock = threading.Lock()
    
    def perform_click(self):
        """Perform right click"""
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            with self.mouse_lock:
                pyautogui.click(button='right')
                print("RIGHT click")
                self.last_click_time = current_time
                return True
        except Exception as e:
            print(f"Right click error: {e}")
            return False
    
    def execute(self, *args, **kwargs):
        """Implementation of base method to execute action"""
        return self.perform_click()

class HeadMouseController:
    def __init__(self, show_window=True):
        # MediaPipe setup
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )

        # PyAutoGUI setup
        import pyautogui
        self.pyautogui = pyautogui
        pyautogui.FAILSAFE = False
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Landmark indices
        self.NOSE_TIP = 4
        self.UPPER_LIP = 13
        self.LOWER_LIP = 14
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize components with config values
        self.calibration = CalibrationAction()
        self.nose_joystick = NoseJoystickEvent(
            deadzone_radius=self.config['deadzone_radius'],
            max_acceleration_distance=self.config['max_acceleration_distance']
        )
        self.mouse_cursor = MouseCursorAction(
            self.screen_w, 
            self.screen_h,
            sensitivity=self.config['sensitivity']
        )
        self.scroll_action = ScrollAction(
            sensitivity=self.config['scroll_sensitivity']
        )
        self.open_mouth_event = OpenMouthEvent(
            self.UPPER_LIP, 
            self.LOWER_LIP,
            threshold=self.config['open_mouth_threshold']
        )
        self.switch_mode_action = SwitchModeAction()
        
        # Event-action mappings
        self.event_action_mappings = []
        self.setup_event_action_mappings()
        
        # Application state
        self.show_window = show_window
        self.paused = False
        self.current_mode = 'pointer'
        self.last_mouse_pos_before_scroll = None
        self.streaming = False
        self.frame_lock = threading.Lock()
        self.current_frame = None
    
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with default to ensure all keys exist
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Return default if file doesn't exist or error
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def setup_event_action_mappings(self):
        """Setup event-action mappings based on config"""
        self.event_action_mappings = []
        
        for mapping in self.config['event_action_mappings']:
            event = None
            action = None
            
            # Create event instance
            if mapping['event_type'] == 'left_eye_blink':
                event = LeftEyeEvent(threshold=self.config['blink_threshold'])
            elif mapping['event_type'] == 'right_eye_blink':
                event = RightEyeEvent(threshold=self.config['blink_threshold'])
            elif mapping['event_type'] == 'open_mouth':
                event = self.open_mouth_event
            
            # Create action instance
            if mapping['action_type'] == 'left_click':
                action = LeftClickAction()
            elif mapping['action_type'] == 'right_click':
                action = RightClickAction()
            elif mapping['action_type'] == 'switch_mode':
                action = self.switch_mode_action
            
            if event and action:
                self.event_action_mappings.append({
                    'event': event,
                    'action': action,
                    'event_type': mapping['event_type'],
                    'action_type': mapping['action_type']
                })
    
    def update_config(self, new_config):
        """Update configuration and reload mappings"""
        self.config.update(new_config)
        if self.save_config():
            self.setup_event_action_mappings()
            return True
        return False
    
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        print(f"Application {'paused' if self.paused else 'resumed'}")
    
    def process_nose_movement(self, tracking_point):
        """Process nose movement"""
        if self.paused or self.current_mode != 'pointer':
            return
            
        if not self.calibration.center_calculated:
            self.calibration.add_sample(tracking_point)
            return
        
        direction, acceleration_factor, effective_distance = self.nose_joystick.get_movement_vector(
            tracking_point, self.calibration.center_position
        )
        
        self.mouse_cursor.update_position(direction, acceleration_factor, effective_distance)

    def process_events(self, tracking_point, landmarks):
        """Process all registered events"""
        if self.paused or not self.calibration.center_calculated:
            return

        # Handle mode switching
        if self.open_mouth_event.check_event(landmarks):
            old_mode = self.current_mode
            new_mode = self.switch_mode_action.execute(self.current_mode)
            if new_mode != old_mode:
                self.current_mode = new_mode
                if self.current_mode == 'scroll':
                    print("Switched to SCROLL mode")
                elif self.current_mode == 'pointer':
                    print("Switched to POINTER mode")

        # Process mode-specific events
        if self.current_mode == 'pointer':
            for mapping in self.event_action_mappings:
                if isinstance(mapping['event'], (LeftEyeEvent, RightEyeEvent)):
                    if mapping['event'].check_event(landmarks):
                        mapping['action'].execute()
        elif self.current_mode == 'scroll':
            direction, _, effective_distance = self.nose_joystick.get_movement_vector(
                tracking_point, self.calibration.center_position
            )
            if direction is not None:
                scroll_direction = np.array([0, direction[1]])
                self.scroll_action.execute(scroll_direction, effective_distance)

    def draw_interface(self, frame, tracking_point, landmarks=None):
        """Draw user interface"""
        if not self.show_window:
            return

        h, w = frame.shape[:2]

        if not self.calibration.center_calculated:
            # Calibration phase
            cv2.circle(frame, tuple(tracking_point.astype(int)), 15, (0, 165, 255), 3)
            progress = len(self.calibration.center_samples)
            percentage = int((progress / self.calibration.max_center_samples) * 100)
            
            cv2.putText(frame, f"CALIBRATION: {percentage}%", 
                       (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
        else:
            # Active state
            color = (128, 128, 128) if self.paused else (0, 255, 0)
            
            # Tracking point
            cv2.circle(frame, tuple(tracking_point.astype(int)), 8, color, -1)
            
            # Center and deadzone
            if self.calibration.center_position is not None:
                center_pt = tuple(self.calibration.center_position.astype(int))
                cv2.circle(frame, center_pt, int(self.nose_joystick.deadzone_radius), (255, 255, 0), 2)
                
                if (self.nose_joystick.is_outside_deadzone(tracking_point, self.calibration.center_position) 
                    and not self.paused):
                    cv2.arrowedLine(frame, center_pt, tuple(tracking_point.astype(int)), (0, 255, 255), 3)
                    cv2.circle(frame, center_pt, int(self.nose_joystick.max_acceleration_distance), (0, 100, 255), 1)

            # Status
            status_text = "PAUSED" if self.paused else "ACTIVE"
            mode_text = f"MODE: {self.current_mode.upper()}"
            status_color = (0, 0, 255) if self.paused else (0, 255, 0)
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            cv2.putText(frame, mode_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        # Controls
        controls = [
            "=== CONTROLS ===",
            "SPACE = Pause/Resume",
            "+/- = Adjust sensitivity",
            "R = Reset calibration",
            "Auto-recalibration after 5s on edge"
        ]
        
        y_start = h - len(controls) * 20 - 10
        for i, control in enumerate(controls):
            if i == 0:
                color, weight = (255, 255, 0), 2
            elif i == len(controls) - 1:
                color, weight = (255, 165, 0), 1
            else:
                color, weight = (255, 255, 255), 1
                
            cv2.putText(frame, control, (20, y_start + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, weight)

    def start_video_stream(self):
        """Start video capture and processing"""
        self.streaming = True
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Webcam not found!")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        try:
            while self.streaming:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame")
                    continue

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb_frame)

                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    h, w = frame.shape[:2]
                    landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

                    tracking_point = landmarks_np[self.NOSE_TIP]
                    
                    if not self.paused:
                        self.process_nose_movement(tracking_point)
                        self.process_events(tracking_point, landmarks_np)

                    if self.show_window:
                        self.draw_interface(frame, tracking_point, landmarks_np)
                else:
                    if self.show_window:
                        cv2.putText(frame, "FACE NOT DETECTED", (20, 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                
                # Update frame for streaming
                with self.frame_lock:
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    self.current_frame = jpeg.tobytes()
                
                if self.show_window:
                    cv2.imshow('Head Mouse Controller', frame)
                    key = cv2.waitKey(1) & 0xFF
                    
                    if key == 27:  # ESC
                        break
                    elif key == ord(' '):  # SPACE
                        self.toggle_pause()
                    elif key == ord('+'):  # +
                        if self.current_mode == 'pointer':
                            self.mouse_cursor.adjust_sensitivity(0.2)
                            self.config['sensitivity'] = self.mouse_cursor.base_sensitivity
                            self.save_config()
                        else:
                            self.scroll_action.adjust_sensitivity(0.5)
                            self.config['scroll_sensitivity'] = self.scroll_action.scroll_sensitivity
                            self.save_config()
                    elif key == ord('-'):  # -
                        if self.current_mode == 'pointer':
                            self.mouse_cursor.adjust_sensitivity(-0.2)
                            self.config['sensitivity'] = self.mouse_cursor.base_sensitivity
                            self.save_config()
                        else:
                            self.scroll_action.adjust_sensitivity(-0.5)
                            self.config['scroll_sensitivity'] = self.scroll_action.scroll_sensitivity
                            self.save_config()
                    elif key == ord('r'):  # R
                        self.calibration.reset_calibration()
                else:
                    time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nKeyboard interrupt")
        finally:
            self.streaming = False
            cap.release()
            if self.show_window:
                cv2.destroyAllWindows()

    def generate_frames(self):
        """Generate frames for web streaming"""
        while self.streaming:
            with self.frame_lock:
                if self.current_frame is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + self.current_frame + b'\r\n')
            time.sleep(0.05)

    def cleanup(self):
        """Clean up resources"""
        self.streaming = False
        print("Controller cleaned up")

# Web Server
app = Flask(__name__)
controller = None

# HTML Templates
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Head Mouse Controller</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { display: flex; flex-wrap: wrap; }
        .video-container { flex: 2; min-width: 640px; }
        .controls { flex: 1; min-width: 300px; padding: 20px; }
        .config-form { margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        button { padding: 5px 10px; margin: 5px; }
        select { padding: 5px; }
    </style>
</head>
<body>
    <h1>Head Mouse Controller</h1>
    <div class="container">
        <div class="video-container">
            <h2>Live Stream</h2>
            <img src="{{ url_for('video_feed') }}" width="640" height="480">
            <div>
                <button onclick="fetch('/pause')">Pause/Resume</button>
                <button onclick="fetch('/reset_calibration')">Reset Calibration</button>
            </div>
        </div>
        <div class="controls">
            <h2>Configuration</h2>
            <div class="config-form">
                <h3>Global Settings</h3>
                <form id="globalConfigForm">
                    <label for="sensitivity">Pointer Sensitivity:</label>
                    <input type="number" id="sensitivity" name="sensitivity" step="0.1" min="0.5" max="5.0" 
                           value="{{ config.sensitivity }}" required><br>
                    
                    <label for="scroll_sensitivity">Scroll Sensitivity:</label>
                    <input type="number" id="scroll_sensitivity" name="scroll_sensitivity" step="0.1" min="1.0" max="10.0" 
                           value="{{ config.scroll_sensitivity }}" required><br>
                    
                    <label for="deadzone_radius">Deadzone Radius:</label>
                    <input type="number" id="deadzone_radius" name="deadzone_radius" step="1" min="5" max="50" 
                           value="{{ config.deadzone_radius }}" required><br>
                    
                    <label for="max_acceleration_distance">Max Acceleration Distance:</label>
                    <input type="number" id="max_acceleration_distance" name="max_acceleration_distance" step="1" min="50" max="500" 
                           value="{{ config.max_acceleration_distance }}" required><br>
                    
                    <label for="open_mouth_threshold">Mouth Open Threshold:</label>
                    <input type="number" id="open_mouth_threshold" name="open_mouth_threshold" step="0.01" min="0.05" max="0.5" 
                           value="{{ config.open_mouth_threshold }}" required><br>
                    
                    <label for="blink_threshold">Blink Threshold:</label>
                    <input type="number" id="blink_threshold" name="blink_threshold" step="0.01" min="0.05" max="0.5" 
                           value="{{ config.blink_threshold }}" required><br>
                    
                    <button type="submit">Save Global Settings</button>
                </form>
            </div>
            
            <div class="event-mappings">
                <h3>Event-Action Mappings</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Event</th>
                            <th>Action</th>
                            <th>Options</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for mapping in config.event_action_mappings %}
                        <tr>
                            <td>
                                <select class="event-select" data-index="{{ loop.index0 }}">
                                    <option value="left_eye_blink" {% if mapping.event_type == 'left_eye_blink' %}selected{% endif %}>Left Eye Blink</option>
                                    <option value="right_eye_blink" {% if mapping.event_type == 'right_eye_blink' %}selected{% endif %}>Right Eye Blink</option>
                                    <option value="open_mouth" {% if mapping.event_type == 'open_mouth' %}selected{% endif %}>Open Mouth</option>
                                </select>
                            </td>
                            <td>
                                <select class="action-select" data-index="{{ loop.index0 }}">
                                    <option value="left_click" {% if mapping.action_type == 'left_click' %}selected{% endif %}>Left Click</option>
                                    <option value="right_click" {% if mapping.action_type == 'right_click' %}selected{% endif %}>Right Click</option>
                                    <option value="switch_mode" {% if mapping.action_type == 'switch_mode' %}selected{% endif %}>Switch Mode</option>
                                </select>
                            </td>
                            <td>
                                <button onclick="saveMapping({{ loop.index0 }})">Save</button>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('globalConfigForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            
            fetch('/update_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Configuration saved successfully!');
                } else {
                    alert('Error saving configuration: ' + data.message);
                }
            });
        });
        
        function saveMapping(index) {
            const eventSelect = document.querySelector(`.event-select[data-index="${index}"]`);
            const actionSelect = document.querySelector(`.action-select[data-index="${index}"]`);
            
            const mapping = {
                index: index,
                event_type: eventSelect.value,
                action_type: actionSelect.value
            };
            
            fetch('/update_mapping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(mapping)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Mapping updated successfully!');
                } else {
                    alert('Error updating mapping: ' + data.message);
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main configuration page"""
    return render_template_string(INDEX_TEMPLATE, config=controller.config)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(controller.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/pause', methods=['POST'])
def pause():
    """Toggle pause state"""
    controller.toggle_pause()
    return jsonify({'success': True})

@app.route('/reset_calibration', methods=['POST'])
def reset_calibration():
    """Reset calibration"""
    controller.calibration.reset_calibration()
    return jsonify({'success': True})

@app.route('/update_config', methods=['POST'])
def update_config():
    """Update global configuration"""
    try:
        data = request.get_json()
        # Convert numeric values
        numeric_fields = ['sensitivity', 'scroll_sensitivity', 'deadzone_radius', 
                         'max_acceleration_distance', 'open_mouth_threshold', 'blink_threshold']
        for field in numeric_fields:
            if field in data:
                data[field] = float(data[field])
        
        if controller.update_config(data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Failed to save config'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update_mapping', methods=['POST'])
def update_mapping():
    """Update event-action mapping"""
    try:
        data = request.get_json()
        index = data['index']
        
        if 0 <= index < len(controller.config['event_action_mappings']):
            controller.config['event_action_mappings'][index]['event_type'] = data['event_type']
            controller.config['event_action_mappings'][index]['action_type'] = data['action_type']
            
            if controller.save_config():
                controller.setup_event_action_mappings()
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'Invalid mapping index'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def run_web_server():
    """Run Flask web server"""
    app.run(host='0.0.0.0', port=5002, threaded=True)

def cleanup_resources():
    """Clean up resources on exit"""
    if controller:
        controller.cleanup()

def main():
    global controller
    
    # Register cleanup handler
    atexit.register(cleanup_resources)
    signal.signal(signal.SIGTERM, lambda signum, frame: cleanup_resources())
    signal.signal(signal.SIGINT, lambda signum, frame: cleanup_resources())
    
    print("=== HEAD MOUSE CONTROLLER ===")
    
    # Initialize controller
    controller = HeadMouseController(show_window=False)
    
    # Start video processing in a separate thread
    video_thread = threading.Thread(target=controller.start_video_stream)
    video_thread.daemon = True
    video_thread.start()
    
    # Start web server
    print("Starting web server on http://0.0.0.0:5001")
    run_web_server()

if __name__ == "__main__":
    main()