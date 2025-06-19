import bluetooth
import pyautogui
import threading
import time
from pynput import mouse

class BluetoothMouseClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.last_position = pyautogui.position()
        self.device_address = None
        self.port = 1
        self.lock = threading.Lock()
    
    def discover_devices(self):
        print("Cerca dispositivi Bluetooth...")
        devices = bluetooth.discover_devices(lookup_names=True)
        if not devices:
            print("Nessun dispositivo trovato.")
            return None

        for i, (addr, name) in enumerate(devices):
            print(f"{i + 1}. {name} ({addr})")

        choice = input("Scegli il numero del dispositivo: ")
        try:
            index = int(choice) - 1
            return devices[index][0]
        except:
            print("Scelta non valida.")
            return None
    
    def connect(self):
        addr = self.discover_devices()
        if not addr:
            return False
        
        self.device_address = addr
        print(f"Connessione a {addr}...")
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((addr, self.port))
            print("✅ Connessione avvenuta.")
            return True
        except Exception as e:
            print(f"Errore nella connessione: {e}")
            return False

    def send(self, message):
        try:
            with self.lock:
                self.socket.send(message.encode())
        except Exception as e:
            print(f"Errore durante l'invio: {e}")
            self.running = False

    def monitor_mouse_movement(self):
        while self.running:
            current_pos = pyautogui.position()
            dx = current_pos[0] - self.last_position[0]
            dy = current_pos[1] - self.last_position[1]
            if dx != 0 or dy != 0:
                self.send(f"MOVE {dx} {dy}\n")
                self.last_position = current_pos
            time.sleep(0.01)  # 10ms = 100Hz, fluido

    def start_mouse_listener(self):
        def on_click(x, y, button, pressed):
            if pressed:
                if button.name == 'left':
                    self.send("CLICK\n")
                elif button.name == 'right':
                    self.send("RIGHT_CLICK\n")

        def on_scroll(x, y, dx, dy):
            self.send(f"SCROLL {dx} {dy}\n")

        listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
        listener.start()

    def run(self):
        if not self.connect():
            return

        self.running = True
        self.start_mouse_listener()

        # Thread separato per movimento fluido
        movement_thread = threading.Thread(target=self.monitor_mouse_movement)
        movement_thread.daemon = True
        movement_thread.start()

        print("🖱 Mouse mirroring in corso. Premi Ctrl+C per uscire.")
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("🔚 Interrotto da utente.")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None

if __name__ == "__main__":
    client = BluetoothMouseClient()
    client.run()
