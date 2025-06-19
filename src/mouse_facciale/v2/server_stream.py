from flask import Flask, Response, render_template_string, request, jsonify
import cv2
import numpy as np
import threading
from test10 import HeadMouseController  # Assicurati che test10.py sia nella stessa cartella

app = Flask(__name__)
controller = HeadMouseController(show_window=False)
lock = threading.Lock()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

HTML_PAGE = '''
<html>
<head>
    <title>HeadMouseController Live</title>
    <style>
        body { background-color: black; color: white; text-align: center; font-family: sans-serif; }
        button {
            font-size: 18px; margin: 10px; padding: 10px 20px;
            border-radius: 10px; border: none; cursor: pointer;
        }
        .green { background-color: #28a745; color: white; }
        .red { background-color: #dc3545; color: white; }
        .blue { background-color: #007bff; color: white; }
        .yellow { background-color: #ffc107; color: black; }
    </style>
</head>
<body>
    <h1>🎥 Live Feed: Head Mouse Controller</h1>
    <img src="/video_feed" width="640" height="480" style="border:5px solid #fff;"><br>

    <button class="green" onclick="sendCommand('toggle')">▶️ Avvia / Pausa</button>
    <button class="blue" onclick="sendCommand('sensitivity_up')">➕ Sensibilità</button>
    <button class="blue" onclick="sendCommand('sensitivity_down')">➖ Sensibilità</button>
    <button class="yellow" onclick="sendCommand('reset')">🔁 Reset calibrazione</button>

    <script>
        function sendCommand(cmd) {
            fetch('/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd })
            }).then(res => res.json()).then(data => {
                console.log('Risposta:', data.message);
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control', methods=['POST'])
def control():
    data = request.get_json()
    command = data.get('command')

    with lock:
        if command == 'toggle':
            controller.toggle_pause()
            return jsonify(message=f"{'Pausa' if controller.paused else 'Avvio'} attivata")
        elif command == 'sensitivity_up':
            if controller.current_mode == 'pointer':
                controller.mouse_cursor.adjust_sensitivity(0.2)
            else:
                controller.scroll_action.adjust_sensitivity(0.5)
            return jsonify(message="Sensibilità aumentata")
        elif command == 'sensitivity_down':
            if controller.current_mode == 'pointer':
                controller.mouse_cursor.adjust_sensitivity(-0.2)
            else:
                controller.scroll_action.adjust_sensitivity(-0.5)
            return jsonify(message="Sensibilità diminuita")
        elif command == 'reset':
            controller.calibration.reset_calibration()
            controller.nose_joystick.reset_outside_timer()
            controller.reset_mouse_position()
            return jsonify(message="Calibrazione resettata")
        else:
            return jsonify(message="Comando sconosciuto"), 400

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = controller.face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            h, w = frame.shape[:2]
            landmarks_np = np.array([[lm.x * w, lm.y * h] for lm in face_landmarks.landmark], dtype=np.float64)

            tracking_point = landmarks_np[controller.NOSE_TIP]

            with lock:
                if not controller.paused:
                    controller.process_nose_movement(tracking_point)
                    controller.process_events(tracking_point, landmarks_np)
                controller.draw_interface(frame, tracking_point, landmarks_np)
        else:
            cv2.putText(frame, "VISO NON RILEVATO", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

if __name__ == '__main__':
    print("Server avviato su http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)
