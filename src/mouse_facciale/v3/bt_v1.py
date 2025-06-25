import sys
import socket
import threading
import time
import struct
import platform
import subprocess
from collections import deque
import pyautogui
from pynput import mouse

# Configurazione
BUFFER_SIZE = 128
PORT = 4
SEND_INTERVAL = 0.008
DEADZONE_THRESHOLD = 1.5
SCROLL_SCALE = 0.1

# --------------------------------------------------
# Funzioni Bluetooth Cross-Platform (Aggiornate per Arch)
# --------------------------------------------------
def get_bluetooth_address():
    system = platform.system()
    try:
        if system == 'Linux':
            # Metodo specifico per Arch Linux
            result = subprocess.run(
                ['bluetoothctl', 'list'],
                capture_output=True,
                text=True
            )
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Controller' in line:
                    parts = line.split()
                    return parts[1].strip()
            return None
                
        elif system == 'Windows':
            # PowerShell per ottenere l'indirizzo Bluetooth
            ps_command = (
                "Get-WmiObject -Class Win32_NetworkAdapter | "
                "Where-Object { $_.PNPDeviceID -like '*BLUETOOTH*' } | "
                "Select-Object -ExpandProperty MacAddress"
            )
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True
            )
            addresses = result.stdout.strip().split('\n')
            return addresses[0].replace(':', '-') if addresses else None
            
        elif system == 'Darwin':
            # macOS: system_profiler
            result = subprocess.run(
                ['system_profiler', 'SPBluetoothDataType', '-json'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                controllers = data.get('SPBluetoothDataType', [])
                for controller in controllers:
                    address = controller.get('device_address', '')
                    if address:
                        return address
            return None
            
    except Exception as e:
        print(f"Errore ottenimento indirizzo Bluetooth: {e}")
        return None

def get_bluetooth_socket():
    """Crea un socket Bluetooth con fallback a PyBluez per Arch"""
    system = platform.system()
    try:
        if system == 'Linux':
            try:
                # Prova prima con i socket standard
                sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                return sock
            except AttributeError:
                # Fallback a PyBluez se AF_BLUETOOTH non è disponibile
                import bluetooth
                sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                return sock
                
        elif system == 'Windows':
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            return sock
            
        elif system == 'Darwin':
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return sock
            
        else:
            raise OSError("Sistema operativo non supportato")
    except Exception as e:
        print(f"Errore creazione socket: {e}")
        return None

def discover_devices():
    """Scopri dispositivi Bluetooth con PyBluez per Linux"""
    devices = []
    system = platform.system()
    
    try:
        if system == 'Linux':
            # Usa PyBluez per Arch Linux
            import bluetooth
            nearby_devices = bluetooth.discover_devices(lookup_names=True, duration=8, flush_cache=True)
            devices = [(addr, name) for addr, name in nearby_devices]
            
        elif system == 'Windows':
            from bluetooth import discover_devices
            nearby_devices = discover_devices(lookup_names=True)
            devices = [(addr, name) for addr, name in nearby_devices]
            
        elif system == 'Darwin':
            result = subprocess.run(
                ["system_profiler", "SPBluetoothDataType", "-json"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                devices_data = data.get('SPBluetoothDataType', [{}])[0].get('devices', [])
                for device in devices_data:
                    if 'device_address' in device and 'device_name' in device:
                        devices.append((device['device_address'], device['device_name']))
                    
    except Exception as e:
        print(f"Errore scoperta dispositivi: {e}")
    
    return devices

# --------------------------------------------------
# Parte Server (Computer con Mouse Fisico)
# --------------------------------------------------
class MouseServer:
    def __init__(self):
        self.client_sock = None
        self.running = False
        self.last_x, self.last_y = pyautogui.position()
        self.buttons = {'left': 0, 'right': 0, 'middle': 0}
        self.scroll_dx = 0
        self.scroll_dy = 0
        self.mouse_listener = None
        self.send_queue = deque()
        self.lock = threading.Lock()

    def start_mouse_listener(self):
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.mouse_listener.start()

    def on_move(self, x, y):
        dx = x - self.last_x
        dy = y - self.last_y
        self.last_x, self.last_y = x, y
        
        if abs(dx) > DEADZONE_THRESHOLD or abs(dy) > DEADZONE_THRESHOLD:
            with self.lock:
                self.send_queue.append(('m', dx, dy, 0, 0))

    def on_click(self, x, y, button, pressed):
        btn_code = {
            mouse.Button.left: 'left',
            mouse.Button.right: 'right',
            mouse.Button.middle: 'middle'
        }.get(button)
        
        if btn_code:
            self.buttons[btn_code] = 1 if pressed else 0
            with self.lock:
                self.send_queue.append(('b', 0, 0, self.buttons['left'], 
                                      self.buttons['right'], self.buttons['middle']))

    def on_scroll(self, x, y, dx, dy):
        with self.lock:
            self.scroll_dx += dx * SCROLL_SCALE
            self.scroll_dy += dy * SCROLL_SCALE
            if abs(self.scroll_dx) > 0.5 or abs(self.scroll_dy) > 0.5:
                self.send_queue.append(('s', self.scroll_dx, self.scroll_dy, 0, 0))
                self.scroll_dx = 0
                self.scroll_dy = 0

    def send_data(self):
        while self.running:
            with self.lock:
                if self.send_queue and self.client_sock:
                    try:
                        data = self.send_queue.popleft()
                        if data[0] == 'm':
                            packed = struct.pack('cffff', b'm', data[1], data[2], 0.0, 0.0)
                        elif data[0] == 'b':
                            packed = struct.pack('cffff', b'b', 0.0, 0.0, float(data[3]), float(data[4]))
                        elif data[0] == 's':
                            packed = struct.pack('cffff', b's', data[1], data[2], 0.0, 0.0)
                        else:
                            continue
                            
                        self.client_sock.sendall(packed)
                    except (ConnectionResetError, BrokenPipeError):
                        self.stop()
                    except Exception as e:
                        print(f"Errore invio dati: {e}")
            
            time.sleep(SEND_INTERVAL)

    def start(self):
        self.running = True
        self.start_mouse_listener()
        
        server_sock = get_bluetooth_socket()
        if not server_sock:
            return

        try:
            bt_address = get_bluetooth_address()
            print(f"Indirizzo Bluetooth: {bt_address or 'Sistema predefinito'}")
            
            if platform.system() == 'Darwin':
                server_sock.bind(('0.0.0.0', PORT))
            else:
                server_sock.bind((bt_address, PORT) if bt_address else ('', PORT))
                
            server_sock.listen(1)
            print(f"Server in ascolto su porta {PORT}")
            print(f"Nome dispositivo: {socket.gethostname()}")
            
            self.client_sock, client_addr = server_sock.accept()
            print(f"Connesso a {client_addr}")
            
            send_thread = threading.Thread(target=self.send_data, daemon=True)
            send_thread.start()
            
            while self.running:
                time.sleep(1)
                
        except OSError as e:
            print(f"Errore di binding: {e}")
            print("Soluzioni possibili:")
            print("1. Verifica che il Bluetooth sia attivo: sudo systemctl start bluetooth")
            print("2. Prova una porta diversa (modifica PORT nello script)")
            print("3. Riavvia il servizio: sudo systemctl restart bluetooth")
        except Exception as e:
            print(f"Errore server: {e}")
        finally:
            if server_sock:
                server_sock.close()
            if self.client_sock:
                self.client_sock.close()
            self.stop()

    def stop(self):
        self.running = False
        if self.mouse_listener:
            self.mouse_listener.stop()

# --------------------------------------------------
# Parte Client (Computer che Riceve)
# --------------------------------------------------
class MouseClient:
    def __init__(self, target_addr):
        self.target_addr = target_addr
        self.sock = None
        self.running = False
        self.last_buttons = [0, 0, 0]

    def process_data(self, data):
        if len(data) < 17:
            return
            
        data_type = data[0:1]
        floats = struct.unpack('ffff', data[1:17])
        
        if data_type == b'm':
            dx, dy, _, _ = floats
            pyautogui.moveRel(dx, dy, _pause=False)
            
        elif data_type == b'b':
            _, _, left, right = floats
            buttons = [int(round(left)), int(round(right)), 0]
            
            for i, (last, current) in enumerate(zip(self.last_buttons, buttons)):
                if current != last:
                    button = ['left', 'right', 'middle'][i]
                    if current == 1:
                        pyautogui.mouseDown(button=button)
                    else:
                        pyautogui.mouseUp(button=button)
            
            self.last_buttons = buttons
            
        elif data_type == b's':
            dx, dy, _, _ = floats
            pyautogui.scroll(int(dy * 40))

    def start(self):
        self.running = True
        self.sock = get_bluetooth_socket()
        if not self.sock:
            return

        try:
            if platform.system() == 'Darwin':
                self.sock.connect((self.target_addr, PORT))
            else:
                self.sock.connect((self.target_addr, PORT))
                
            print(f"Connesso a {self.target_addr}")
            
            buffer = b''
            while self.running:
                try:
                    data = self.sock.recv(BUFFER_SIZE)
                    if not data:
                        break
                        
                    buffer += data
                    
                    while len(buffer) >= 17:
                        self.process_data(buffer[:17])
                        buffer = buffer[17:]
                        
                except (ConnectionResetError, BrokenPipeError):
                    break
                except Exception as e:
                    print(f"Errore ricezione dati: {e}")
                    break
                    
        except Exception as e:
            print(f"Errore connessione: {e}")
            print("Assicurati di:")
            print("1. Aver effettuato il pairing Bluetooth")
            print("2. Aver avviato prima il server")
            print("3. Aver inserito l'indirizzo corretto")
        finally:
            if self.sock:
                self.sock.close()

# --------------------------------------------------
# Interfaccia Utente
# --------------------------------------------------
def main_menu():
    print("\n=== Mouse Bluetooth Condiviso ===")
    print("1. Avvia come SERVER (mouse fisico)")
    print("2. Avvia come CLIENT (riceve movimento)")
    print("3. Esci")
    
    choice = input("Scelta [1/2/3]: ")
    return choice

def run_server():
    print("\nModalità SERVER attivata")
    print("Assicurati che il Bluetooth sia attivo e visibile")
    server = MouseServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("Server fermato")

def run_client():
    print("\nModalità CLIENT attivata")
    print("Ricerca dispositivi Bluetooth...")
    
    devices = discover_devices()
    if not devices:
        print("Nessun dispositivo trovato. Verifica:")
        print("- Server attivo e visibile")
        print("- Dispositivi accoppiati")
        print("- Bluetooth attivato")
        return
        
    print("\nDispositivi trovati:")
    for i, (addr, name) in enumerate(devices):
        print(f"{i+1}. {name} ({addr})")
    
    try:
        choice = int(input("\nSeleziona un dispositivo: ")) - 1
        if 0 <= choice < len(devices):
            target_addr, target_name = devices[choice]
            print(f"Connessione a {target_name}...")
            client = MouseClient(target_addr)
            client.start()
        else:
            print("Selezione non valida")
    except ValueError:
        print("Input non valido")

def check_dependencies():
    required = ['pyautogui', 'pynput']
    missing = []
    
    if platform.system() == 'Darwin':
        required.append('pyobjc')
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

# --------------------------------------------------
# Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    missing_deps = check_dependencies()
    if missing_deps:
        print("Dipendenza mancante:", ", ".join(missing_deps))
        print("Installa con: pip install", " ".join(missing_deps))
        sys.exit(1)
    
    if platform.system() == 'Darwin':
        print("Nota: Su macOS la connessione avverrà via rete")
    
    if platform.system() == 'Linux':
        print("Verifica permessi Bluetooth...")
        try:
            subprocess.run(['bluetoothctl', '--version'], check=True, stdout=subprocess.DEVNULL)
        except:
            print("Potrebbero essere necessari permessi elevati")
            print("Prova: sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))")
    
    while True:
        choice = main_menu()
        if choice == '1':
            run_server()
        elif choice == '2':
            run_client()
        elif choice == '3':
            print("Arrivederci!")
            break
        else:
            print("Scelta non valida")
