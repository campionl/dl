from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import threading
import time
import json
from test10 import HeadMouseController, LeftEye_event, RightEye_event, LeftClick_action, RightClick_action, SwitchMode_action, OpenMouth_event

app = Flask(__name__)

class WebHeadMouseController(HeadMouseController):
    def __init__(self):
        super().__init__(show_window=False)
        
        # Web-specific attributes
        self.current_status = {
            'mode': self.current_mode,
            'paused': self.paused,
            'calibrated': False,
            'calibration_progress': 0,
            'sensitivity': self.mouse_cursor.base_sensitivity,
            'scroll_sensitivity': self.scroll_action.scroll_sensitivity,
            'face_detected': False
        }
        
        # Setup event mappings
        self.setup_event_mappings()
    
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

        face_detected = False
        if results.multi_face_landmarks:
            h, w = frame.shape[:2]
            landmarks_np = np.array(
                [[lm.x * w, lm.y * h] for lm in results.multi_face_landmarks[0].landmark],
                dtype=np.float64
            )
            tracking_point = landmarks_np[self.NOSE_TIP]
            face_detected = True

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
    
    def update_status(self, tracking_point):
        """Update current status for web interface"""
        face_detected = tracking_point is not None
        self.current_status.update({
            'mode': self.current_mode,
            'paused': self.paused,
            'calibrated': self.calibration.center_calculated,
            'calibration_progress': int((len(self.calibration.center_samples) / self.calibration.max_center_samples * 100),
            'sensitivity': self.mouse_cursor.base_sensitivity,
            'scroll_sensitivity': self.scroll_action.scroll_sensitivity,
            'face_detected': face_detected
        })

# Initialize controller
controller = WebHeadMouseController()

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open video device")
    exit()

# Set camera properties
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

def generate_frames():
    """Generate frames for video streaming"""
    while True:
        success, frame = cap.read()
        if not success:
            print("Error: Could not read frame from camera")
            break

        try:
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
        except Exception as e:
            print(f"Error processing frame: {e}")
            continue

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
    controller.toggle_pause()
    return jsonify({'paused': controller.paused})

@app.route('/adjust_sensitivity/<direction>')
def adjust_sensitivity(direction):
    """Adjust sensitivity up or down"""
    amount = 0.2 if direction == 'up' else -0.2
    if controller.current_mode == 'pointer':
        controller.mouse_cursor.adjust_sensitivity(amount)
    else:
        controller.scroll_action.adjust_sensitivity(amount * 2.5)  # Larger increments for scroll
    
    return jsonify(controller.current_status)

@app.route('/reset_calibration')
def reset_calibration():
    """Reset calibration"""
    controller.calibration.reset_calibration()
    controller.nose_joystick.reset_outside_timer()
    controller.reset_mouse_position()
    return jsonify({'success': True})

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
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    finally:
        cap.release()
        print("✅ Server closed")