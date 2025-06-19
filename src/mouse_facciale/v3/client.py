# client_mirror.py
import bluetooth
import pyautogui
import time
import sys

class BluetoothMouseMirror:
    def __init__(self):
        self.running = False
        self.socket = None
        self.last_position = pyautogui.position()
        self.device_address = None
        self.port = 4  # Deve corrispondere alla porta del server

    def discover_devices(self):
        print("Ricerca dispositivi Bluetooth nelle vicinanze...")
        nearby_devices = bluetooth.discover_devices(lookup_names=True, duration=8, flush_cache=True)
        
        if not nearby_devices:
            print("Nessun dispositivo trovato. Assicurati che il dispositivo target sia rilevabile.")
            return None
        
        print("\nDispositivi trovati:")
        for i, (addr, name) in enumerate(nearby_devices):
            print(f"{i+1}. {name} ({addr})")
        
        while True:
            try:
                choice = int(input("\nSeleziona il numero del dispositivo a cui connettersi: "))
                if 1 <= choice <= len(nearby_devices):
                    return nearby_devices[choice-1][0]
                print("Selezione non valida. Riprova.")
            except ValueError:
                print("Inserisci un numero valido.")

    def connect(self):
        device_address = self.discover_devices()
        if not device_address:
            return False
        
        self.device_address = device_address
        print(f"Connessione a {self.device_address}...")
        
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((self.device_address, self.port))
            print("Connessione riuscita!")
            return True
        except Exception as e:
            print(f"Connessione fallita: {e}")
            self.socket = None
            return False

    def start_mirroring(self):
        if not self.connect():
            return
        
        self.running = True
        print("Mirroring movimenti mouse attivo (Ctrl+C per fermare)...")
        
        try:
            while self.running:
                current_position = pyautogui.position()
                if current_position != self.last_position:
                    dx = current_position[0] - self.last_position[0]
                    dy = current_position[1] - self.last_position[1]
                    
                    # Invia movimento relativo
                    message = f"MOVE {dx} {dy}\n"
                    try:
                        self.socket.send(message)
                    except Exception as e:
                        print(f"Errore invio dati: {e}")
                        self.running = False
                        break
                    
                    self.last_position = current_position
                
                time.sleep(0.01)  # Piccola pausa per ridurre l'uso della CPU
        except KeyboardInterrupt:
            self.running = False
            print("\nMirroring fermato dall'utente")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None
        print("Client fermato")

if __name__ == "__main__":
    # Verifica dipendenze
    try:
        import bluetooth
        import pyautogui
    except ImportError as e:
        print(f"Errore: {e}")
        print("Installa i pacchetti necessari:")
        print("pip install PyBluez pyautogui")
        sys.exit(1)
    
    mirror = BluetoothMouseMirror()
    try:
        mirror.start_mirroring()
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        mirror.stop()