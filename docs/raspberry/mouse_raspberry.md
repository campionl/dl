# Progetto: Mouse Bluetooth per Persone Tetraplegiche con Raspberry Pi

Ecco una guida passo-passo per creare un dispositivo basato su Raspberry Pi che funzioni come mouse Bluetooth controllato dai movimenti del viso utilizzando MediaPipe.

## Materiali Necessari
- Raspberry Pi 4 (consigliato) o 3B+
- Camera Raspberry Pi (o webcam USB compatibile)
- Alimentazione per Raspberry Pi
- Scheda microSD (minimo 16GB)
- Dissipatori e ventola (opzionali ma consigliati)
- Custodio (opzionale)

## Parte 1: Configurazione del Raspberry Pi

### 1. Installazione del Sistema Operativo
1. Scarica Raspberry Pi Imager da [questo sito](https://www.raspberrypi.com/software/)
2. Inserisci la microSD nel computer
3. Apri Raspberry Pi Imager e seleziona:
   - Sistema operativo: Raspberry Pi OS (64-bit)
   - Memoria: la tua microSD
4. Prima di scrivere, clicca sull'icona dell'ingranaggio per configurare:
   - Abilita SSH
   - Configura nome utente e password
   - Configura WiFi (se vuoi connessione wireless)
5. Scrivi l'immagine sulla SD

### 2. Primo Avvio e Configurazione
1. Inserisci la microSD nel Raspberry Pi e accendilo
2. Connettiti via SSH o direttamente con monitor/tastiera
3. Esegui gli aggiornamenti:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
4. Installa le dipendenze necessarie:
   ```bash
   sudo apt install -y python3-pip python3-dev libatlas-base-dev libjasper-dev libqtgui4 libqt4-test
   ```

## Parte 2: Configurazione Bluetooth

### 1. Abilita Bluetooth
```bash
sudo apt install -y pi-bluetooth bluez blueman
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 2. Configura il dispositivo come HID (Human Interface Device)
Dovremo far sembrare il Raspberry Pi un mouse Bluetooth:

1. Installa i pacchetti necessari:
   ```bash
   sudo apt install -y git libbluetooth-dev
   pip3 install pybluez
   ```

2. Clona il repository per l'emulazione HID:
   ```bash
   git clone https://github.com/rikmasters/bluez.git
   cd bluez/test
   make
   ```

## Parte 3: Installazione di MediaPipe e Programmazione

### 1. Installa MediaPipe e OpenCV
```bash
pip3 install mediapipe opencv-python numpy
```

### 2. Crea lo script Python

Crea un nuovo file chiamato `face_mouse.py` con il seguente contenuto:

```python
import cv2
import mediapipe as mp
import numpy as np
import time
import subprocess
from bluetooth import *

# Configurazione MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_faces=1)

mp_drawing = mp.solutions.drawing_utils
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)

# Connessione Bluetooth
def connect_bluetooth():
    # Sostituire con l'indirizzo MAC del dispositivo target
    bd_addr = "00:00:00:00:00:00"  # MODIFICARE
    port = 1
    sock = BluetoothSocket(RFCOMM)
    sock.connect((bd_addr, port))
    return sock

# Inizializza la connessione Bluetooth
# sock = connect_bluetooth()  # Decommentare dopo configurazione

# Variabili per il tracking
prev_time = 0
prev_x, prev_y = 0, 0
left_eye_closed = False
right_eye_closed = False
mouth_open = False

# Landmark indices per occhi e bocca
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
LIPS = [61, 291, 39, 181, 0, 17, 269, 405]

# Inizializza la webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Larghezza
cap.set(4, 480)  # Altezza

def send_mouse_move(dx, dy):
    # Invia comando movimento mouse via Bluetooth
    # Implementazione dipende dal protocollo HID
    pass

def send_mouse_click(button="left"):
    # Invia comando click mouse
    pass

def send_double_click():
    # Invia comando doppio click
    pass

while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    # Converti l'immagine e processala
    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = face_mesh.process(image)

    # Ripristina l'immagine
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Estrai punti chiave
            landmarks = face_landmarks.landmark
            mesh_points = np.array([np.multiply([p.x, p.y], [640, 480]).astype(int) for p in landmarks])

            # Calcola inclinazione testa (per movimento cursore)
            nose_tip = mesh_points[4]
            forehead = mesh_points[10]
            dx = (nose_tip[0] - prev_x) * 5
            dy = (nose_tip[1] - prev_y) * 5
            prev_x, prev_y = nose_tip[0], nose_tip[1]
            
            # Muovi il mouse
            send_mouse_move(dx, dy)

            # Rilevamento ammiccamento occhio sinistro
            left_eye_ratio = (np.linalg.norm(mesh_points[LEFT_EYE[0]] - mesh_points[LEFT_EYE[3]]) / 
                            np.linalg.norm(mesh_points[LEFT_EYE[1]] - mesh_points[LEFT_EYE[5]]))
            
            # Rilevamento ammiccamento occhio destro
            right_eye_ratio = (np.linalg.norm(mesh_points[RIGHT_EYE[0]] - mesh_points[RIGHT_EYE[3]]) / 
                             np.linalg.norm(mesh_points[RIGHT_EYE[1]] - mesh_points[RIGHT_EYE[5]]))
            
            # Rilevamento bocca aperta
            mouth_ratio = (np.linalg.norm(mesh_points[LIPS[0]] - mesh_points[LIPS[2]]) / 
                         np.linalg.norm(mesh_points[LIPS[1]] - mesh_points[LIPS[3]]))
            
            # Logica per i comandi
            if left_eye_ratio < 2.5:  # Soglia da calibrare
                if not left_eye_closed:
                    send_mouse_click("left")
                    left_eye_closed = True
            else:
                left_eye_closed = False
                
            if right_eye_ratio < 2.5:  # Soglia da calibrare
                if not right_eye_closed:
                    send_mouse_click("right")
                    right_eye_closed = True
            else:
                right_eye_closed = False
                
            if mouth_ratio > 1.5:  # Soglia da calibrare
                if not mouth_open:
                    send_double_click()
                    mouth_open = True
            else:
                mouth_open = False

    # Calcola FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time
    
    # Mostra FPS
    cv2.putText(image, f'FPS: {int(fps)}', (20, 70), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
    
    # Mostra l'immagine
    cv2.imshow('Face Mouse', image)
    
    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
```

## Parte 4: Implementazione Bluetooth HID

Per implementare correttamente l'emulazione HID Bluetooth, dobbiamo usare il protocollo HID over GATT (HOGP):

1. Installa i pacchetti aggiuntivi:
   ```bash
   sudo apt install -y python3-dbus python3-gi
   pip3 install pygobject
   ```

2. Modifica lo script per includere l'invio effettivo dei comandi HID. Ecco una possibile implementazione:

```python
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

class BTHID:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.btkservice = self.bus.get_object('org.bluez', '/org/bluez/hci0')
        self.btkdevice = dbus.Interface(self.btkservice, 'org.bluez.Device1')
        self.btkproperties = dbus.Interface(self.btkservice, 'org.freedesktop.DBus.Properties')
        
        # Configurazione HID
        self.caps_lock = False
        self.ctrl_keys = 0
        self.report = [0] * 8
        
    def send_mouse_event(self, dx, dy, buttons=0):
        # Formato report HID per mouse
        report = [
            buttons & 0x07,  # Button 1, 2, 3
            dx & 0xFF,       # Movement X
            dy & 0xFF,       # Movement Y
            0                # Wheel
        ]
        
        # Invia il report (implementazione dipende dalla libreria)
        # Esempio semplificato:
        try:
            self.btkdevice.SendReport(0x02, dbus.Array(report, signature='y'))
        except Exception as e:
            print(f"Errore invio report: {e}")
            # Potrebbe essere necessario riconnettersi
```

## Parte 5: Calibrazione e Test

1. Esegui lo script:
   ```bash
   python3 face_mouse.py
   ```

2. Calibra le soglie:
   - Modifica i valori delle soglie per ammiccamento e apertura bocca
   - Testa la sensibilità del movimento della testa

3. Connetti il dispositivo al computer target:
   - Accoppia il Raspberry Pi come dispositivo HID
   - Su Windows/macOS/Linux, dovrebbe apparire come "Face Mouse"

## Parte 6: Avvio Automatico

Per far partire lo script automaticamente all'avvio:

1. Crea un servizio systemd:
   ```bash
   sudo nano /etc/systemd/system/facemouse.service
   ```

2. Aggiungi questo contenuto:
   ```
   [Unit]
   Description=Face Mouse Service
   After=network.target bluetooth.service

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/face_mouse.py
   WorkingDirectory=/home/pi
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

3. Abilita e avvia il servizio:
   ```bash
   sudo systemctl enable facemouse.service
   sudo systemctl start facemouse.service
   ```

## Note Finali

1. **Ottimizzazione**: Potresti dover ottimizzare lo script per ottenere prestazioni migliori sul Raspberry Pi.

2. **Batteria**: Se vuoi usare il dispositivo con batteria, considera l'uso di un power bank.

3. **Privacy**: Tutta l'elaborazione avviene localmente sul Raspberry Pi, nessun dato viene inviato online.

4. **Personalizzazione**: Puoi modificare le soglie e i comandi in base alle esigenze specifiche dell'utente.

Questo progetto combina computer vision, elaborazione in tempo reale e interfaccia Bluetooth per creare uno strumento di accessibilità potenzialmente molto utile.