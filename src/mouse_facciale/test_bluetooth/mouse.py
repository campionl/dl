import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import subprocess
from flask import Flask, Response
import os
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

# Configurazione Bluetooth
BUS_NAME = 'org.bluez'
ADAPTER_INTERFACE = 'org.bluez.Adapter1'
DEVICE_INTERFACE = 'org.bluez.Device1'
INPUT_INTERFACE = 'org.bluez.Input1'

# Inizializzazione Flask per lo streaming
app = Flask(__name__)

class BluetoothMouse:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.adapter_path = self.find_adapter()
        self.input_path = None
        self.connected = False
        
    def find_adapter(self):
        try:
            manager = dbus.Interface(self.bus.get_object(BUS_NAME, '/'), 'org.freedesktop.DBus.ObjectManager')
            objects = manager.GetManagedObjects()
            
            for path, interfaces in objects.items():
                if ADAPTER_INTERFACE in interfaces:
                    return path
        except Exception as e:
            print(f"Errore ricerca adattatore Bluetooth: {e}")
        return None
    
    def connect(self, device_address):
        try:
            manager = dbus.Interface(self.bus.get_object(BUS_NAME, '/'), 'org.freedesktop.DBus.ObjectManager')
            objects = manager.GetManagedObjects()
            
            for path, interfaces in objects.items():
                if DEVICE_INTERFACE in interfaces:
                    addr = interfaces[DEVICE_INTERFACE].get('Address')
                    if addr == device_address:
                        device = dbus.Interface(self.bus.get_object(BUS_NAME, path), DEVICE_INTERFACE)
                        device.Connect()
                        print(f"Connesso al dispositivo {device_address}")
                        self.connected = True
                        self.input_path = path
                        return True
        except Exception as e:
            print(f"Errore connessione Bluetooth: {e}")
        return False
    
    def send_mouse_event(self, dx, dy, buttons=0):
        if not self.connected or not self.input_path:
            return False
        
        try:
            input_device = dbus.Interface(self.bus.get_object(BUS_NAME, self.input_path), INPUT_INTERFACE)
            # Invia movimento del mouse (formato: [buttons, dx, dy])
            input_device.SendMouseEvent([buttons, dx, dy])
            return True
        except Exception as e:
            print(f"Errore invio evento mouse: {e}")
            return False

# Inizializzazione Bluetooth
bluetooth_mouse = BluetoothMouse()

# Configurazione MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Configurazione globale
screen_w, screen_h = 1920, 1080  # Modificare secondo lo schermo
current_mode = 'pointer'
cursor_position_locked = None
calibrated = False
nose_center = None
dead_zone_radius = 0.02

# Configurazione webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# Variabili per il frame globale
latest_frame = None
frame_lock = threading.Lock()

def generate_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            ret, buffer = cv2.imencode('.jpg', latest_frame)
            if not ret:
                continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True)

def calculate_distance(point1, point2):
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def get_eye_aspect_ratio(eye_landmarks, landmarks):
    if len(eye_landmarks) < 6:
        return 1.0
        
    p1 = landmarks[eye_landmarks[1]]
    p2 = landmarks[eye_landmarks[5]]
    p3 = landmarks[eye_landmarks[2]]
    p4 = landmarks[eye_landmarks[4]]
    p5 = landmarks[eye_landmarks[0]]
    p6 = landmarks[eye_landmarks[3]]
    
    vertical_dist1 = calculate_distance(p1, p2)
    vertical_dist2 = calculate_distance(p3, p4)
    horizontal_dist = calculate_distance(p5, p6)
    
    if horizontal_dist == 0:
        return 1.0
        
    ear = (vertical_dist1 + vertical_dist2) / (2.0 * horizontal_dist)
    return ear

def get_mouth_aspect_ratio(landmarks):
    top = landmarks[13]
    bottom = landmarks[14]
    vertical_dist = calculate_distance(top, bottom)
    horizontal_dist = calculate_distance(landmarks[61], landmarks[291])
    
    if horizontal_dist == 0:
        return 0.0
        
    return vertical_dist / horizontal_dist

def calculate_speed_multiplier(distance_from_center):
    if distance_from_center <= dead_zone_radius:
        return 0.0
    
    normalized_distance = (distance_from_center - dead_zone_radius) / (0.15 - dead_zone_radius)
    normalized_distance = min(1.0, max(0.0, normalized_distance))
    
    if normalized_distance < 0.3:
        return normalized_distance * 0.5
    elif normalized_distance < 0.7:
        return 0.15 + (normalized_distance - 0.3) * 1.5
    else:
        return 0.75 + (normalized_distance - 0.7) * 2.5

def process_frame(frame):
    global current_mode, cursor_position_locked, calibrated, nose_center, latest_frame
    
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    with frame_lock:
        latest_frame = frame.copy()
    
    if results.multi_face_landmarks:
        face_landmarks = results.multi_face_landmarks[0]
        landmarks = []
        
        for lm in face_landmarks.landmark:
            landmarks.append([lm.x, lm.y])
        
        nose_pos = np.array(landmarks[4])  # Punto del naso
        
        # Calibrazione iniziale
        if not calibrated:
            print("Calibrazione in corso... Mantieni la testa ferma")
            time.sleep(2)
            nose_center = nose_pos.copy()
            calibrated = True
            return frame
        
        # Controlla apertura bocca per cambio modalità
        mouth_ratio = get_mouth_aspect_ratio(landmarks)
        if mouth_ratio > 0.15:  # Soglia apertura bocca
            time.sleep(0.5)  # Debounce
            current_mode = 'scroll' if current_mode == 'pointer' else 'pointer'
            print(f"Modalità cambiata a: {current_mode}")
            
            if current_mode == 'scroll':
                cursor_position_locked = bluetooth_mouse.get_current_position()
            else:
                cursor_position_locked = None
        
        # Controlla chiusura occhi per click
        left_ear = get_eye_aspect_ratio([33, 7, 163, 144, 145, 153], landmarks)
        right_ear = get_eye_aspect_ratio([362, 382, 381, 380, 374, 373], landmarks)
        
        if left_ear < 0.15 and right_ear > 0.2:  # Click sinistro
            bluetooth_mouse.send_mouse_event(0, 0, 1)  # Left click
            time.sleep(0.1)
            bluetooth_mouse.send_mouse_event(0, 0, 0)  # Release
        elif right_ear < 0.15 and left_ear > 0.2:  # Click destro
            bluetooth_mouse.send_mouse_event(0, 0, 2)  # Right click
            time.sleep(0.1)
            bluetooth_mouse.send_mouse_event(0, 0, 0)  # Release
        
        # Gestione movimento/scrolling
        nose_offset = nose_pos - nose_center
        distance_from_center = np.linalg.norm(nose_offset)
        
        if distance_from_center > dead_zone_radius:
            speed_multiplier = calculate_speed_multiplier(distance_from_center)
            
            if current_mode == 'pointer':
                # Movimento del mouse
                move_x = int(nose_offset[0] * 1200 * speed_multiplier)
                move_y = int(nose_offset[1] * 1200 * speed_multiplier)
                bluetooth_mouse.send_mouse_event(move_x, move_y)
            else:
                # Scrolling
                scroll_amount = int(-nose_offset[1] * 8 * speed_multiplier)
                if abs(scroll_amount) >= 1:
                    bluetooth_mouse.send_mouse_event(0, 0, 8 if scroll_amount > 0 else 16)  # Scroll up/down
    
    return frame

def main():
    # Avvia il server Flask in un thread separato
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("Connetti il dispositivo Bluetooth...")
    print("Indirizzo MAC del dispositivo da connettere (es: 00:11:22:33:44:55): ")
    device_address = input().strip()
    
    if not bluetooth_mouse.connect(device_address):
        print("Errore nella connessione Bluetooth")
        return
    
    print("Sistema avviato! Visita http://<indirizzo-raspberry>:5000/video_feed per lo streaming")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Errore acquisizione frame")
                break
            
            processed_frame = process_frame(frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nInterrotto dall'utente")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Sistema terminato")

if __name__ == "__main__":
    # Configurazione iniziale Bluetooth
    print("Configurazione iniziale Bluetooth...")
    subprocess.run(["sudo", "hciconfig", "hci0", "piscan"])
    
    main()