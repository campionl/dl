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
SEND_INTERVAL = 0.008  # 8ms per 120fps
DEADZONE_THRESHOLD = 1.5
SCROLL_SCALE = 0.1

# --------------------------------------------------
# Funzioni Bluetooth Cross-Platform
# --------------------------------------------------
def get_bluetooth_address():
    """Ottieni l'indirizzo Bluetooth locale in modo affidabile"""
    system = platform.system()
    try:
        if system == 'Linux':
            # Prova a leggere da sysfs
            try:
                with open('/sys/class/bluetooth/hci0/address', 'r') as f:
                    return f.read().strip()
            except:
                # Fallback: usa hciconfig
                result = subprocess.run(
                    ['hciconfig', 'hci0'], 
                    capture_output=True, 
                    text=True
                )
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'BD Address' in line:
                        parts = line.split()
                        return parts[2].strip()
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
    """Crea un socket Bluetooth appropriato per il sistema operativo"""
    system = platform.system()
    try:
        if system == 'Linux':
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            return sock
        elif system == 'Windows':
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            return sock
        elif system == 'Darwin':  # macOS
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return sock
        else:
            raise OSError("Sistema operativo non supportato")
    except Exception as e:
        print(f"Errore creazione socket: {e}")
        return None

def discover_devices():
    """Scopri dispositivi Bluetooth nelle vicinanze"""
    devices = []
    system = platform.system()
    
    try:
        if system == 'Linux':
            import bluetooth
            nearby_devices = bluetooth.discover_devices(lookup_names=True, duration=8, flush_cache=True)
            devices = [(addr, name) for addr, name in nearby_devices]
            
        elif system == 'Windows':
            from bluetooth import discover_devices
            nearby_devices = discover_devices(lookup_names=True)
            devices = [(addr, name) for addr, name in nearby_devices]
            
        elif system == 'Darwin':
            # Utilizziamo il comando system_profiler su macOS
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
        """Avvia il listener per gli eventi del mouse"""
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.mouse_listener.start()

    def on_move(self, x, y):
        """Gestisce il movimento del mouse"""
        dx = x - self.last_x
        dy = y - self.last_y
        self.last_x, self.last_y = x, y
        
        # Applica deadzone per ridurre il jitter
        if abs(dx) > DEADZONE_THRESHOLD or abs(dy) > DEADZONE_THRESHOLD:
            with self.lock:
                self.send_queue.append(('m', dx, dy, 0, 0))

    def on_click(self, x, y, button, pressed):
        """Gestisce i click del mouse"""
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
        """Gestisce lo scrolling"""
        with self.lock:
            self.scroll_dx += dx * SCROLL_SCALE
            self.scroll_dy += dy * SCROLL_SCALE
            if abs(self.scroll_dx) > 0.5 or abs(self.scroll_dy) > 0.5:
                self.send_queue.append(('s', self.scroll_dx, self.scroll_dy, 0, 0))
                self.scroll_dx = 0
                self.scroll_dy = 0

    def send_data(self):
        """Invia i dati al client"""
        while self.running:
            with self.lock:
                if self.send_queue and self.client_sock:
                    try:
                        data = self.send_queue.popleft()
                        # Struttura dei dati:
                        # - Tipo: 1 byte (m=movimento, b=pulsanti, s=scrolling)
                        # - Dati: 4 float (16 byte)
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
        """Avvia il server"""
        self.running = True
        self.start_mouse_listener()
        
        server_sock = get_bluetooth_socket()
        if not server_sock:
            return

        try:
            # Binding affidabile con gestione indirizzo
            bt_address = get_bluetooth_address()
            print(f"Indirizzo Bluetooth rilevato: {bt_address or 'Sistema predefinito'}")
            
            if platform.system() == 'Darwin':
                server_sock.bind(('0.0.0.0', PORT))
            elif bt_address:
                server_sock.bind((bt_address, PORT))
            else:
                server_sock.bind(('', PORT))
                
            server_sock.listen(1)
            print(f"Server in ascolto su porta {PORT}...")
            print(f"Nome dispositivo: {socket.gethostname()}")
            print("In attesa di connessioni...")
            
            self.client_sock, client_addr = server_sock.accept()
            print(f"Connesso a {client_addr}")
            
            # Avvia thread per l'invio dati
            send_thread = threading.Thread(target=self.send_data, daemon=True)
            send_thread.start()
            
            # Mantieni il server attivo
            while self.running:
                time.sleep(1)
                
        except OSError as e:
            print(f"Errore di binding: {e}")
            print("Prova queste soluzioni:")
            print("1. Verifica che il Bluetooth sia attivo")
            print("2. Prova una porta diversa (modifica PORT nello script)")
            print("3. Riavvia il servizio Bluetooth")
        except Exception as e:
            print(f"Errore server: {e}")
        finally:
            if server_sock:
                server_sock.close()
            if self.client_sock:
                self.client_sock.close()
            self.stop()

    def stop(self):
        """Ferma il server"""
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
        self.last_buttons = [0, 0, 0]  # [left, right, middle]

    def process_data(self, data):
        """Elabora i dati ricevuti dal server"""
        if len(data) < 17:  # 1 byte tipo + 4 float (16 byte)
            return
            
        data_type = data[0:1]
        floats = struct.unpack('ffff', data[1:17])
        
        if data_type == b'm':  # Movimento
            dx, dy, _, _ = floats
            pyautogui.moveRel(dx, dy, _pause=False)
            
        elif data_type == b'b':  # Pulsanti
            _, _, left, right = floats
            buttons = [int(round(left)), int(round(right)), 0]  # Middle non gestito qui
            
            # Gestisci cambiamenti stato pulsanti
            for i, (last, current) in enumerate(zip(self.last_buttons, buttons)):
                if current != last:
                    button = ['left', 'right', 'middle'][i]
                    if current == 1:
                        pyautogui.mouseDown(button=button)
                    else:
                        pyautogui.mouseUp(button=button)
            
            self.last_buttons = buttons
            
        elif data_type == b's':  # Scrolling
            dx, dy, _, _ = floats
            pyautogui.scroll(int(dy * 40))

    def start(self):
        """Avvia il client"""
        self.running = True
        self.sock = get_bluetooth_socket()
        if not self.sock:
            return

        try:
            if platform.system() == 'Darwin':
                # Connessione TCP su macOS
                self.sock.connect((self.target_addr, PORT))
            else:
                # Connessione Bluetooth standard
                self.sock.connect((self.target_addr, PORT))
                
            print(f"Connesso a {self.target_addr}")
            
            # Loop principale di ricezione dati
            buffer = b''
            while self.running:
                try:
                    data = self.sock.recv(BUFFER_SIZE)
                    if not data:
                        break
                        
                    buffer += data
                    
                    # Elabora tutti i pacchetti completi
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
            print("1. Aver effettuato il pairing Bluetooth tra i dispositivi")
            print("2. Aver avviato prima il server")
            print("3. Aver inserito l'indirizzo corretto")
        finally:
            if self.sock:
                self.sock.close()

# --------------------------------------------------
# Interfaccia Utente
# --------------------------------------------------
def main_menu():
    """Mostra il menu principale"""
    print("\n=== Mouse Bluetooth Condiviso ===")
    print("1. Avvia come SERVER (questo computer ha il mouse fisico)")
    print("2. Avvia come CLIENT (questo computer riceve il movimento)")
    print("3. Esci")
    
    choice = input("Scelta [1/2/3]: ")
    return choice

def run_server():
    """Avvia il server"""
    print("\nModalità SERVER attivata")
    print("Assicurati che il Bluetooth sia attivo e visibile")
    server = MouseServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("Server fermato")

def run_client():
    """Avvia il client"""
    print("\nModalità CLIENT attivata")
    print("Ricerca dispositivi Bluetooth...")
    
    devices = discover_devices()
    if not devices:
        print("Nessun dispositivo trovato. Assicurati che:")
        print("- Il server sia attivo e visibile")
        print("- I dispositivi siano accoppiati")
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

# --------------------------------------------------
# Configurazione iniziale
# --------------------------------------------------
def check_dependencies():
    """Verifica le dipendenze necessarie"""
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
    # Verifica dipendenze
    missing_deps = check_dependencies()
    if missing_deps:
        print("Dipendenza mancante:", ", ".join(missing_deps))
        print("Installa con: pip install", " ".join(missing_deps))
        sys.exit(1)
    
    # Avviso per macOS
    if platform.system() == 'Darwin':
        print("Attenzione: Su macOS la connessione avverrà via rete")
        print("Assicurati che entrambi i computer siano sulla stessa rete")
    
    # Verifica permessi Linux
    if platform.system() == 'Linux':
        print("Verifica permessi Bluetooth...")
        try:
            subprocess.run(['hciconfig'], check=True, stdout=subprocess.DEVNULL)
        except:
            print("Potrebbero essere necessari permessi elevati")
            print("Prova: sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))")
    
    # Loop principale
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
