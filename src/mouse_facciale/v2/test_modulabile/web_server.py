from flask import Flask, render_template, Response, jsonify
import cv2
import numpy as np
import threading
import time

# Importa le classi dal tuo file test13.py (nuova versione)
from test13 import HeadMouseController, LeftEyeEvent, RightEyeEvent, OpenMouthEvent, LeftClickAction, RightClickAction, ScrollAction, ToggleModeAction

app = Flask(__name__)

# Questa classe estende HeadMouseController per aggiungere funzionalità specifiche per il web.
# Le funzioni _web servono per incapsulare le chiamate e gli aggiornamenti di stato per il frontend.
class WebHeadMouseController(HeadMouseController):
    def __init__(self):
        # Inizializza il HeadMouseController con show_window=False
        # Le configurazioni dei gesti possono essere passate o definite qui
        super().__init__(show_window=False, user_config={
            'left_click': 'left eye', 
            'right_click': 'right eye',
            'mode_switch': 'mouth open',
            'scroll_direction': 'nose up/down'
        })
        self.update_status_lock = threading.Lock() # Lock per prevenire race conditions nell'aggiornamento dello stato web
        self.start_webcam() # Avvia la webcam e il thread di elaborazione all'avvio del server

    def toggle_pause_web(self):
        result = self.toggle_pause() # Chiama il metodo nella classe base
        self.update_web_status()
        return result

    def adjust_sensitivity_web(self, control_type, amount):
        if control_type == 'pointer':
            result = self.adjust_pointer_sensitivity(amount)
        elif control_type == 'scroll':
            result = self.adjust_scroll_sensitivity(amount)
        else:
            return {'success': False, 'message': 'Invalid control type'}
        self.update_web_status()
        return result

    def reset_calibration_web(self):
        result = self.reset_calibration()
        self.update_web_status()
        return result

    def reset_mouse_position_web(self):
        result = self.reset_mouse_position()
        self.update_web_status()
        return result

    def set_mode_web(self, mode):
        result = self.set_mode(mode)
        self.update_web_status()
        return result

    def get_web_status(self):
        # Restituisce l'ultimo stato noto, aggiornato dal thread di elaborazione
        with self.status_lock: # Usa il lock per accedere in sicurezza allo stato
            return self.current_status.copy()

# Inizializza il controller globale per il server web
controller = WebHeadMouseController()

# --- Rotte Flask ---
@app.route('/')
def index():
    """Renderizza la pagina HTML principale."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Genera il flusso video MJPEG per il browser."""
    def generate_frames():
        while True:
            # Assicurati che il frame video sia disponibile e non None
            if controller.video_frame is not None:
                ret, buffer = cv2.imencode('.jpg', controller.video_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03) # Regola per il frame rate desiderato

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def get_status():
    """Restituisce lo stato corrente del controller come JSON."""
    return jsonify(controller.get_web_status())

@app.route('/toggle_pause')
def toggle_pause():
    """Togglia lo stato di pausa."""
    status = controller.toggle_pause_web()
    return jsonify(status)

@app.route('/adjust_sensitivity/<control_type>/<float:amount>')
def adjust_sensitivity(control_type, amount):
    """Regola la sensibilità del puntatore o dello scroll."""
    status = controller.adjust_sensitivity_web(control_type, amount)
    return jsonify(status)

@app.route('/reset_calibration')
def reset_calibration():
    """Resetta la calibrazione."""
    status = controller.reset_calibration_web()
    return jsonify(status)

@app.route('/reset_mouse_position')
def reset_mouse_position():
    """Resetta la posizione del cursore del mouse."""
    success_status = controller.reset_mouse_position_web()
    return jsonify(success_status)

@app.route('/set_mode/<mode>')
def set_mode(mode):
    """Forza il cambio di modalità."""
    status = controller.set_mode_web(mode)
    return jsonify(status)


if __name__ == '__main__':
    try:
        print("🚀 Avvio del Head Mouse Web Server (Controllo PyAutoGUI Locale)...")
        print("🌐 Inizializzazione della webcam e del controller...")
        # La webcam viene avviata nell'__init__ di WebHeadMouseController
        print("⚙️ Controller pronto")
        print("🔗 Accedi all'interfaccia web su: http://localhost:5000")
        print("\n💡 Controlli disponibili tramite interfaccia web:")
        print("   - Pausa/Riprendi")
        print("   - Regola Sensibilità (Puntatore/Scroll)")
        print("   - Resetta Calibrazione")
        print("   - Resetta Posizione Mouse")
        print("   - Cambio Modalità")
        print("   - Visualizza Stato")
        
        # Avvia l'applicazione Flask in modalità threaded per non bloccare l'elaborazione video
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Interruzione da tastiera. Chiusura del server...")
    finally:
        controller.stop_webcam() # Assicurati di fermare la webcam quando il server si spegne
        print("Server Flask e webcam chiusi.")