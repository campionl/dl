# web_server.py
from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
import threading
import time
# ***CHANGED: Import from test13.py and include all necessary classes***
from test13 import HeadMouseController, LeftEye_event, RightEye_event, OpenMouth_event, LeftClick_action, RightClick_action, ScrollAction, ToggleModeAction

app = Flask(__name__)

class WebHeadMouseController(HeadMouseController):
    def __init__(self):
        # Pass a dummy user_config for initialization as the web interface doesn't set it initially
        # If you want to configure gestures via the web, you'd need to load/save them here.
        # For now, it will use the default gesture mappings defined in test13.py's HeadMouseController
        # and then override in setup_event_mappings if needed, or simply assume fixed ones for web.
        # Let's keep it simple and make WebHeadMouseController rely on default mappings for now.
        super().__init__(show_window=False, user_config={
            'left_click': 'left eye', # Default for web, can be changed via user config if implemented
            'right_click': 'right eye',
            'mode_switch': 'mouth open',
            'scroll_direction': 'nose up/down' # Default scroll direction
        })  # Always False for web
        
        # ***It's crucial to call setup_event_mappings from within this class's __init__
        # to ensure it uses the correct instances of events and actions.***
        self.setup_event_mappings() # This will use the user_config passed to super()

        # Web-specific attributes are now already handled by the HeadMouseController's current_status
        # No need to duplicate them here. Call update_web_status from superclass.
        self.update_web_status() # Initial update of the status dictionary

    # No need to override process_frame specifically for status update,
    # as update_web_status is called inside HeadMouseController.process_frame.
    # We still need a minimal setup_event_mappings to ensure actions are correctly bound
    # for the web-controlled instance.

    def setup_event_mappings(self):
        """
        Setup event mappings for the web server's controller instance.
        This must mirror the mappings in test13.py to ensure consistency.
        It should ideally use the user_config from the super().__init__ call.
        """
        # Call the superclass method which uses self.user_config
        super().setup_event_action_mappings()


# Initialize the controller for the web server
controller = WebHeadMouseController()
# The initial status update is now handled within WebHeadMouseController's __init__
# controller.update_web_status() # Redundant now

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        # Instead of just returning, yield an empty frame or an error image
        # so the browser doesn't hang.
        while True: # Keep yielding an error frame
            # Create a black image with "No Webcam" text
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, "NO WEBCAM / WEBCAM IN USE", (80, 240), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
            ret, buffer = cv2.imencode('.jpg', error_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(1) # Don't flood with error frames
        # return # This return is unreachable but left for original context clarity

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Warning: Could not read frame from webcam.")
            break # Breaks the loop if frame read fails

        frame = cv2.flip(frame, 1) # Mirror the frame horizontally

        processed_frame = controller.process_frame(frame) # Process frame using the controller's new method

        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def get_status():
    # The controller's current_status is always up-to-date
    return jsonify(controller.current_status)

@app.route('/toggle_pause')
def toggle_pause():
    status = controller.toggle_pause_web() # Calls the web-specific wrapper
    return jsonify(status)

@app.route('/adjust_sensitivity/<direction>')
def adjust_sensitivity(direction):
    """Adjust sensitivity up or down"""
    amount = 0.2 if direction == 'up' else -0.2
    # The controller's adjust_sensitivity_web now handles the mode-specific adjustment
    status = controller.adjust_sensitivity_web(amount)
    return jsonify(status)

@app.route('/reset_calibration')
def reset_calibration():
    """Reset calibration"""
    # reset_calibration_web returns the updated status directly
    status = controller.reset_calibration_web() 
    return jsonify(status) 

@app.route('/reset_mouse_position') # New route for resetting mouse position
def reset_mouse_position():
    success_status = controller.reset_mouse_position_web()
    return jsonify(success_status)

@app.route('/force_mode_switch')
def force_mode_switch():
    """Force mode switch for testing"""
    old_mode = controller.current_mode
    controller.set_mode('scroll' if old_mode == 'pointer' else 'pointer') # Use set_mode method
    controller.update_web_status() # Update status after force switch
    return jsonify({'old_mode': old_mode, 'new_mode': controller.current_mode, **controller.current_status})


if __name__ == '__main__':
    try:
        print("🚀 Starting Head Mouse Web Server (Local PyAutoGUI Control)...") # Clarify local control
        print("🌐 Webcam initialized")
        print("⚙️ Controller ready")
        print("🔗 Access at: http://localhost:5000")
        print("\n💡 Controls available via web interface:")
        print("   - Toggle Pause")
        print("   - Adjust Sensitivity")
        print("   - Reset Calibration")
        print("   - Reset Mouse Position (NEW!)") # Added new control
        print("   - View Status")
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    finally:
        print("Controller closed")