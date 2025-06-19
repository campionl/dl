# web_server.py
from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
import threading
import time
import bluetooth
import pyautogui
from test10 import HeadMouseController, LeftEye_event, RightEye_event, LeftClick_action, RightClick_action

app = Flask(__name__)

# Configurazione Bluetooth
BT_DEVICE_ADDRESS = "00:11:22:33:44:55"  # SOSTITUISCI con l'indirizzo del PC ricevente
BT_UUID = "00001101-0000-1000-8000-00805F9B34FB"

class BluetoothMouseController:
    def __init__(self, bt_address):
        self.bt_address = bt_address
        self.socket = None
        self.connected = False
        self.connect()
        
    def connect(self):
        """Connessione al dispositivo Bluetooth"""
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((self.bt_address, 1))
            self.connected = True
            print(f"Connesso al dispositivo Bluetooth {self.bt_address}")
            return True
        except Exception as e:
            print(f"Errore di connessione Bluetooth: {e}")
            self.connected = False
            return False
            
    def send_command(self, command):
        """Invia comando mouse via Bluetooth"""
        try:
            if self.socket and self.connected:
                self.socket.send(command.encode())
                return True
            return False
        except Exception as e:
            print(f"Errore invio comando Bluetooth: {e}")
            self.connected = False
            # Tentativo di riconnessione
            time.sleep(1)
            self.connect()
            return False
            
    def move(self, dx, dy):
        """Muove il cursore remoto"""
        return self.send_command(f"MOVE {dx} {dy}\n")
        
    def click(self, button="left"):
        """Click remoto"""
        return self.send_command(f"CLICK {button}\n")
        
    def scroll(self, dy):
        """Scroll remoto"""
        return self.send_command(f"SCROLL {dy}\n")

class WebHeadMouseController(HeadMouseController):
    def __init__(self, bt_address=None):
        super().__init__(show_window=False)
        
        # Inizializza il controller Bluetooth se specificato
        self.bt_controller = BluetoothMouseController(bt_address) if bt_address else None
        self.use_bluetooth = bt_address is not None
        
        self.setup_event_mappings()
        
        self.current_status = {
            'mode': self.current_mode,
            'paused': self.paused,
            'calibrated': self.calibration.center_calculated,
            'calibration_progress': 0,
            'sensitivity': self.mouse_cursor.base_sensitivity,
            'scroll_sensitivity': self.scroll_action.scroll_sensitivity,
            'bluetooth_connected': bt_address is not None and self.bt_controller.connected,
            'bluetooth_address': bt_address
        }
    
    def move_mouse(self, dx, dy):
        """Override del movimento del mouse per usare Bluetooth"""
        if self.use_bluetooth and self.bt_controller:
            return self.bt_controller.move(dx, dy)
        else:
            return super().move_mouse(dx, dy)
    
    def mouse_click(self, button="left"):
        """Override del click del mouse per usare Bluetooth"""
        if self.use_bluetooth and self.bt_controller:
            return self.bt_controller.click(button)
        else:
            return super().mouse_click(button)
    
    def mouse_scroll(self, dy):
        """Override dello scroll del mouse per usare Bluetooth"""
        if self.use_bluetooth and self.bt_controller:
            return self.bt_controller.scroll(dy)
        else:
            return super().mouse_scroll(dy)
    
    def update_status(self, tracking_point):
        """Aggiorna lo stato connessione Bluetooth"""
        super().update_status(tracking_point)
        if self.use_bluetooth:
            self.current_status['bluetooth_connected'] = self.bt_controller.connected

# Inizializza il controller con Bluetooth
controller = WebHeadMouseController(bt_address=BT_DEVICE_ADDRESS)

# Inizializza webcam
cap = cv2.VideoCapture(0)
if cap.isOpened():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break

        processed_frame = controller.process_frame(frame)
        ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify(controller.current_status)

@app.route('/toggle_pause')
def toggle_pause():
    paused = controller.toggle_pause_web()
    return jsonify({'paused': paused})

@app.route('/adjust_sensitivity/<direction>')
def adjust_sensitivity(direction):
    amount = 0.2 if direction == 'up' else -0.2
    if controller.current_mode == 'scroll':
        amount *= 2.5
    status = controller.adjust_sensitivity_web(amount)
    return jsonify(status)

@app.route('/reset_calibration')
def reset_calibration():
    success = controller.reset_calibration_web()
    return jsonify({'success': success})

@app.route('/force_mode_switch')
def force_mode_switch():
    old_mode = controller.current_mode
    controller.current_mode = 'scroll' if old_mode == 'pointer' else 'pointer'
    return jsonify({'old_mode': old_mode, 'new_mode': controller.current_mode})

if __name__ == '__main__':
    try:
        print("🌐 Starting Head Mouse Web Server with Bluetooth...")
        print(f"📶 Bluetooth target: {BT_DEVICE_ADDRESS}")
        print("📹 Webcam initialized")
        print("🎮 Controller ready")
        print("🔗 Access at: http://localhost:5000")
        
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    finally:
        if cap.isOpened():
            cap.release()
        print("✅ Server closed")