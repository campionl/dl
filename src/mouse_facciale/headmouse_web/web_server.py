from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
import threading
import time
from test10 import HeadMouseController, LeftEye_event, RightEye_event, LeftClick_action, RightClick_action

app = Flask(__name__)

class WebHeadMouseController(HeadMouseController):
    def __init__(self):
        super().__init__(show_window=False)  # Always False for web
        
        # Add the event mappings like in the main function
        self.setup_event_mappings()
        
        # Web-specific attributes
        self.current_status = {
            'mode': self.current_mode,
            'paused': self.paused,
            'calibrated': self.calibration.center_calculated,
            'calibration_progress': 0,
            'sensitivity': self.mouse_cursor.base_sensitivity,
            'scroll_sensitivity': self.scroll_action.scroll_sensitivity
        }
        
    def setup_event_mappings(self):
        """Setup event mappings like in the original main function"""
        # Click events for pointer mode
        self.add_event_action_mapping(
            event=LeftEye_event(),
            action=LeftClick_action(),
            event_args_mapper=lambda tp, lm, mp: (lm,),
            action_args_mapper=lambda tp, lm, mp: (mp,)
        )
        
        self.add_event_action_mapping(
            event=RightEye_event(),
            action=RightClick_action(),
            event_args_mapper=lambda tp, lm, mp: (lm,),
            action_args_mapper=lambda tp, lm, mp: (mp,)
        )
    
    def process_frame(self, frame):
        """Process frame and return it with all visual elements"""
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            h, w = frame.shape[:2]
            landmarks_np = np.array(
                [[lm.x * w, lm.y * h] for lm in results.multi_face_landmarks[0].landmark],
                dtype=np.float64
            )
            tracking_point = landmarks_np[self.NOSE_TIP]

            # Update status
            self.update_status(tracking_point)

            if not self.paused:
                self.process_nose_movement(tracking_point)
                self.process_events(tracking_point, landmarks_np)

            # Draw minimal interface for web
            self.draw_minimal_interface(frame, tracking_point, landmarks_np)
        else:
            # Update status for no face detected
            self.update_status(None)

        return frame
    
    def draw_minimal_interface(self, frame, tracking_point, landmarks=None):
        """Draw only essential interface elements for web"""
        h, w = frame.shape[:2]

        if landmarks is not None:
            # Draw eye mesh (lines between landmarks)
            for i in range(0, len(landmarks)):
                if i in [33, 133, 159, 145, 386, 374]:  # Key eye landmarks
                    cv2.circle(frame, tuple(landmarks[i].astype(int)), 1, (0, 255, 0), -1)
            
            # Connect eye landmarks with lines
            left_eye_indices = [33, 159, 145, 133]
            right_eye_indices = [263, 386, 374, 362]
            
            for i in range(len(left_eye_indices)):
                cv2.line(frame, 
                        tuple(landmarks[left_eye_indices[i]].astype(int)),
                        tuple(landmarks[left_eye_indices[(i+1)%4]].astype(int)),
                        (0, 255, 0), 1)
                cv2.line(frame, 
                        tuple(landmarks[right_eye_indices[i]].astype(int)),
                        tuple(landmarks[right_eye_indices[(i+1)%4]].astype(int)),
                        (0, 255, 0), 1)

            # Nose pointer
            cv2.circle(frame, tuple(tracking_point.astype(int)), 8, (0, 255, 0), -1)

            # Deadzone and movement arrow if calibrated
            if self.calibration.center_calculated:
                center_pt = tuple(self.calibration.center_position.astype(int))
                # Deadzone circle
                cv2.circle(frame, center_pt, int(self.nose_joystick.deadzone_radius), (255, 255, 0), 2)
                
                # Movement arrow if outside deadzone
                if self.nose_joystick.is_outside_deadzone(tracking_point, self.calibration.center_position):
                    cv2.arrowedLine(frame, center_pt, tuple(tracking_point.astype(int)), (0, 255, 255), 2)
    
    def update_status(self, tracking_point):
        """Update current status for web interface"""
        self.current_status.update({
            'mode': self.current_mode,
            'paused': self.paused,
            'calibrated': self.calibration.center_calculated,
            'calibration_progress': int((len(self.calibration.center_samples) / self.calibration.max_center_samples) * 100),
            'sensitivity': self.mouse_cursor.base_sensitivity,
            'scroll_sensitivity': self.scroll_action.scroll_sensitivity,
            'face_detected': tracking_point is not None
        })
    
    def toggle_pause_web(self):
        """Web-safe pause toggle"""
        self.toggle_pause()
        return self.paused
    
    def adjust_sensitivity_web(self, amount):
        """Web-safe sensitivity adjustment"""
        if self.current_mode == 'pointer':
            self.mouse_cursor.adjust_sensitivity(amount)
        else:
            self.scroll_action.adjust_sensitivity(amount)
        return self.current_status
    
    def reset_calibration_web(self):
        """Web-safe calibration reset"""
        self.calibration.reset_calibration()
        self.nose_joystick.reset_outside_timer()
        self.reset_mouse_position()
        return True

# Initialize controller
controller = WebHeadMouseController()

# Initialize webcam
cap = cv2.VideoCapture(0)
if cap.isOpened():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

def generate_frames():
    """Generate frames for video streaming"""
    while True:
        success, frame = cap.read()
        if not success:
            break

        # Process frame with minimal visual elements
        processed_frame = controller.process_frame(frame)

        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        frame_bytes = buffer.tobytes()

        # Yield frame for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    """Return current status as JSON"""
    return jsonify(controller.current_status)

@app.route('/toggle_pause')
def toggle_pause():
    """Toggle pause state"""
    paused = controller.toggle_pause_web()
    return jsonify({'paused': paused})

@app.route('/adjust_sensitivity/<direction>')
def adjust_sensitivity(direction):
    """Adjust sensitivity up or down"""
    amount = 0.2 if direction == 'up' else -0.2
    if controller.current_mode == 'scroll':
        amount *= 2.5  # Scroll sensitivity adjusts in larger increments
    
    status = controller.adjust_sensitivity_web(amount)
    return jsonify(status)

@app.route('/reset_calibration')
def reset_calibration():
    """Reset calibration"""
    success = controller.reset_calibration_web()
    return jsonify({'success': success})

@app.route('/force_mode_switch')
def force_mode_switch():
    """Force mode switch for testing"""
    old_mode = controller.current_mode
    controller.current_mode = 'scroll' if old_mode == 'pointer' else 'pointer'
    return jsonify({'old_mode': old_mode, 'new_mode': controller.current_mode})

if __name__ == '__main__':
    try:
        print("🌐 Starting Head Mouse Web Server...")
        print("📹 Webcam initialized")
        print("🎮 Controller ready")
        print("🔗 Access at: http://localhost:5000")
        print("\n🎯 Controls available via web interface:")
        print("   - Toggle Pause")
        print("   - Adjust Sensitivity")
        print("   - Reset Calibration")
        print("   - View Status")
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    finally:
        if cap.isOpened():
            cap.release()
        print("✅ Server closed")