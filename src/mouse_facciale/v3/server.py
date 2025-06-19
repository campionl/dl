# server_mirror.py
import bluetooth
import pyautogui
import sys

class BluetoothMouseServer:
    def __init__(self):
        self.server_socket = None
        self.client_socket = None
        self.port = 4  # Porta RFCOMM comunemente disponibile su Windows
        self.running = False

    def start(self):
        # Configura il server
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        
        try:
            print(f"Tentativo di binding sulla porta {self.port}...")
            self.server_socket.bind(("", self.port))
            self.server_socket.listen(1)
            print(f"In attesa di connessioni sulla porta RFCOMM {self.port}")
            
            self.client_socket, address = self.server_socket.accept()
            print(f"Connesso a {address}")
            self.running = True
            
            while self.running:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                if data.startswith("MOVE"):
                    try:
                        _, dx, dy = data.split()
                        dx, dy = int(dx), int(dy)
                        current_x, current_y = pyautogui.position()
                        pyautogui.moveTo(current_x + dx, current_y + dy)
                    except Exception as e:
                        print(f"Errore elaborazione movimento: {e}")
                        
        except Exception as e:
            print(f"Errore server: {e}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        print("Server fermato")

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
    
    server = BluetoothMouseServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer interrotto dall'utente")
    finally:
        server.stop()