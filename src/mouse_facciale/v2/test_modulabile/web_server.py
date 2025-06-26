# web_server.py
from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
import threading
import time
# ***CHANGED: Import from test13.py and include all necessary classes***
from test13 import HeadMouseController, LeftEyeEvent, RightEyeEvent, OpenMouthEvent, LeftClickAction, RightClickAction, ScrollAction, ToggleModeAction # Updated class names

app = Flask(__name__)

class WebHeadMouseController(HeadMouseController):
    def __init__(self):
        # Pass a dummy user_config for initialization as the web interface doesn't set it initially
        # If you want to configure gestures via the web, you'd need to load/save them here.
        # For now, it will use the default gesture mappings defined in test13.py's HeadMouseController
        # and then override in setup_event_mappings if needed, or simply assume fixed ones for web.
        # Let's keep it simple and make WebHeadMouseController rely on default mappings for now.
        super().__init__(show_window=False, user_config={
            'left_click': 'left eye', # Default for web, puoi cambiarlo qui!
            'right_click': 'right eye', # Default for web, puoi cambiarlo qui!
            'mode_switch': 'mouth open', # Default for web, puoi cambiarlo qui!
            'scroll_direction': 'nose up/down' # Default scroll direction
        })
        
        # ***CORREZIONE QUI: Chiamare setup_event_action_mappings() invece di setup_event_mappings()***
        self.setup_event_action_mappings() # Questo è cruciale per applicare le configurazioni!


# Create a single instance of the controller that will be used by the Flask app
controller = WebHeadMouseController()
controller_started = False
controller_lock = threading.Lock() # To manage starting/stopping the controller thread safely

def generate_frames():
    """Generates JPEG frames from the webcam feed for the browser."""
    global controller_started
    with controller_lock:
        if not controller_started:
            controller.start_webcam()
            controller_started = True

    while True:
        # ***CORREZIONE QUI: Usa controller.processed_frame_for_display per il feed video***
        if controller.processed_frame_for_display is not None:
            ret, buffer = cv2.imencode('.jpg', controller.processed_frame_for_display)
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03) # Adjust frame rate for streaming


@app.route('/')
def index():
    """Renders the main web interface."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Provides the video streaming endpoint."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def get_status():
    """Returns the current status of the head mouse controller."""
    return jsonify(controller.get_current_status())

@app.route('/toggle_pause')
def toggle_pause():
    """Toggles the pause state of the controller."""
    return jsonify(controller.toggle_pause())

@app.route('/reset_calibration')
def reset_calibration():
    """Resets the facial calibration."""
    # Ensure this calls the method on the controller instance
    return jsonify(controller.reset_calibration())

@app.route('/reset_mouse_position') # Route for resetting mouse position
def reset_mouse_position():
    return jsonify(controller.reset_mouse_position())

@app.route('/adjust_sensitivity/<sensitivity_type>/<float:amount>')
def adjust_sensitivity(sensitivity_type, amount):
    if sensitivity_type == 'pointer':
        return jsonify(controller.adjust_pointer_sensitivity(amount))
    elif sensitivity_type == 'scroll':
        return jsonify(controller.adjust_scroll_sensitivity(amount))
    return jsonify({'success': False, 'message': 'Invalid sensitivity type.'})

@app.route('/set_mode/<mode>')
def set_mode_route(mode):
    return jsonify(controller.set_mode(mode))

@app.route('/get_gesture_mappings')
def get_gesture_mappings():
    """Returns the current gesture mappings configuration."""
    return jsonify({
        'left_click': controller.user_config.get('left_click', 'left eye'),
        'right_click': controller.user_config.get('right_click', 'right eye'),
        'mode_switch': controller.user_config.get('mode_switch', 'mouth open'),
        'scroll_direction': controller.user_config.get('scroll_direction', 'nose up/down')
    })

@app.route('/set_gesture_mapping/<action>/<gesture>')
def set_gesture_mapping(action, gesture):
    """Sets a new gesture mapping for an action."""
    valid_actions = ['left_click', 'right_click', 'mode_switch', 'scroll_direction']
    valid_gestures = {
        'left_click': ['left eye', 'right eye', 'mouth open'],
        'right_click': ['left eye', 'right eye', 'mouth open'],
        'mode_switch': ['left eye', 'right eye', 'mouth open'],
        'scroll_direction': ['nose up/down', 'mouth up/down', 'eyes up/down (average)']
    }
    
    if action not in valid_actions:
        return jsonify({'success': False, 'message': 'Invalid action type'})
    
    if gesture not in valid_gestures[action]:
        return jsonify({'success': False, 'message': 'Invalid gesture for this action'})
    
    # Update the configuration
    controller.user_config[action] = gesture
    
    # Reinitialize the controller with new mappings
    controller.setup_event_action_mappings()
    
    return jsonify({
        'success': True,
        'message': f'Mapping updated: {action} now triggered by {gesture}',
        'current_mappings': controller.user_config
    })

if __name__ == '__main__':
    try:
        print("🚀 Avvio del Web Server del Mouse Facciale (Controllo PyAutoGUI Locale)...")
        print("🌐 Webcam inizializzata (tentativo)")
        print("⚙️ Controller pronto")
        print("🔗 Accedi all'interfaccia web su: http://localhost:5000")
        print("\n💡 Controlli disponibili tramite interfaccia web:")
        print("   - Pausa/Riprendi")
        print("   - Regola Sensibilità (usando i bottoni +/-)")
        print("   - Resetta Calibrazione")
        print("   - Resetta Posizione Mouse")
        print("   - Cambia Modalità (Puntatore/Scroll)")
        print("   - Visualizza Stato")
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Spegnimento del server...")
    finally:
        with controller_lock:
            if controller_started:
                controller.stop_webcam()
        print("Server arrestato.")