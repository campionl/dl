from flask import Flask, Response, render_template_string
import cv2
import numpy as np
import time
from test10 import HeadMouseController  # Assicurati che test10.py sia nella stessa cartella

app = Flask(__name__)
controller = HeadMouseController(show_window=False)

# Setup webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# HTML base
HTML_PAGE = '''
<html>
<head>
    <title>HeadMouseController Live</title>
</head>
<body style="background-color: black; text-align: center; color: white;">
    <h1>🎥 Live Feed: Head Mouse Controller</h1>
    <img src="/video_feed" width="640" height="480" style="border:5px solid #fff;">
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

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

            controller.process_nose_movement(tracking_point)
            controller.process_events(tracking_point, landmarks_np)
            controller.draw_interface(frame, tracking_point, landmarks_np)
        else:
            cv2.putText(frame, "VISO NON RILEVATO", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        # Codifica il frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("Server avviato su http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)
