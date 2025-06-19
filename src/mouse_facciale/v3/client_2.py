import bluetooth
import pyautogui
import threading
import time
from pynput import mouse
import queue

class BluetoothMouseClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.last_position = pyautogui.position()
        self.device_address = None
        self.port = 1
        self.message_queue = queue.Queue(maxsize=50)  # Buffer limitato
        self.send_thread = None
        
        # Parametri di ottimizzazione
        self.MIN_MOVEMENT = 2  # Pixel minimi per considerare movimento
        self.UPDATE_RATE = 50  # Hz (era 100Hz, troppo alto)
        self.BATCH_SIZE = 5    # Raggruppa movimenti
        
        # Accumulo movimenti per batch
        self.accumulated_dx = 0
        self.accumulated_dy = 0
        self.last_send_time = time.time()
        self.lock = threading.Lock()
    
    def discover_devices(self):
        print("🔍 Cerca dispositivi Bluetooth...")
        try:
            devices = bluetooth.discover_devices(lookup_names=True, duration=8)
        except Exception as e:
            print(f"❌ Errore durante la ricerca: {e}")
            return None
            
        if not devices:
            print("❌ Nessun dispositivo trovato.")
            return None

        print("\n📱 Dispositivi trovati:")
        for i, (addr, name) in enumerate(devices):
            print(f"{i + 1}. {name} ({addr})")

        while True:
            try:
                choice = input("\n➤ Scegli il numero del dispositivo: ")
                index = int(choice) - 1
                if 0 <= index < len(devices):
                    return devices[index][0]
                else:
                    print("❌ Numero non valido, riprova.")
            except ValueError:
                print("❌ Inserisci un numero valido.")
    
    def connect(self):
        addr = self.discover_devices()
        if not addr:
            return False
        
        self.device_address = addr
        print(f"\n🔄 Connessione a {addr}...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.socket.settimeout(10)  # Timeout connessione
                self.socket.connect((addr, self.port))
                self.socket.settimeout(None)  # Rimuovi timeout dopo connessione
                print("✅ Connessione stabilita!")
                return True
            except Exception as e:
                print(f"❌ Tentativo {attempt + 1}/{max_retries} fallito: {e}")
                if self.socket:
                    self.socket.close()
                    self.socket = None
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        print("❌ Impossibile connettersi dopo tutti i tentativi.")
        return False

    def send_message(self, message):
        """Aggiunge messaggio alla coda per invio asincrono"""
        try:
            self.message_queue.put_nowait(message)
        except queue.Full:
            # Se la coda è piena, scarta il messaggio più vecchio
            try:
                self.message_queue.get_nowait()
                self.message_queue.put_nowait(message)
            except queue.Empty:
                pass

    def sender_worker(self):
        """Thread separato per invio messaggi"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=0.1)
                if message and self.socket:
                    self.socket.send(message.encode())
                self.message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Errore invio: {e}")
                self.running = False
                break

    def monitor_mouse_movement(self):
        """Monitor ottimizzato per movimenti mouse"""
        while self.running:
            try:
                current_pos = pyautogui.position()
                dx = current_pos[0] - self.last_position[0]
                dy = current_pos[1] - self.last_position[1]
                
                # Filtra movimenti troppo piccoli
                if abs(dx) >= self.MIN_MOVEMENT or abs(dy) >= self.MIN_MOVEMENT:
                    with self.lock:
                        self.accumulated_dx += dx
                        self.accumulated_dy += dy
                    
                    self.last_position = current_pos
                    
                    # Invia batch di movimenti
                    current_time = time.time()
                    if current_time - self.last_send_time >= (1.0 / self.UPDATE_RATE):
                        with self.lock:
                            if self.accumulated_dx != 0 or self.accumulated_dy != 0:
                                self.send_message(f"MOVE {self.accumulated_dx} {self.accumulated_dy}\n")
                                self.accumulated_dx = 0
                                self.accumulated_dy = 0
                                self.last_send_time = current_time
                
                time.sleep(1.0 / self.UPDATE_RATE)  # 50Hz invece di 100Hz
                
            except Exception as e:
                print(f"❌ Errore monitoring: {e}")
                break

    def start_mouse_listener(self):
        """Listener per click e scroll"""
        def on_click(x, y, button, pressed):
            if not self.running:
                return
                
            if pressed:
                if button.name == 'left':
                    self.send_message("CLICK\n")
                elif button.name == 'right':
                    self.send_message("RIGHT_CLICK\n")
                elif button.name == 'middle':
                    self.send_message("MIDDLE_CLICK\n")

        def on_scroll(x, y, dx, dy):
            if not self.running:
                return
            # Normalizza i valori di scroll
            scroll_dx = max(-3, min(3, dx))
            scroll_dy = max(-3, min(3, dy))
            self.send_message(f"SCROLL {scroll_dx} {scroll_dy}\n")

        self.mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
        self.mouse_listener.start()

    def run(self):
        if not self.connect():
            return

        self.running = True
        
        # Avvia thread per invio messaggi
        self.send_thread = threading.Thread(target=self.sender_worker)
        self.send_thread.daemon = True
        self.send_thread.start()
        
        # Avvia listener mouse
        self.start_mouse_listener()

        # Thread per monitoraggio movimento
        movement_thread = threading.Thread(target=self.monitor_mouse_movement)
        movement_thread.daemon = True
        movement_thread.start()

        print("\n🖱️  Mouse mirroring attivo!")
        print("📋 Comandi supportati:")
        print("   • Movimento mouse: tracciamento automatico")
        print("   • Click sinistro/destro/centrale")
        print("   • Scroll verticale/orizzontale")
        print("\n⚠️  Premi Ctrl+C per disconnettere")
        
        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n🔚 Disconnessione richiesta dall'utente...")
        finally:
            self.stop()

    def stop(self):
        print("🔄 Chiusura connessione...")
        self.running = False
        
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
        
        # Svuota la coda
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except queue.Empty:
                break
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("✅ Disconnesso!")

if __name__ == "__main__":
    print("🔷 Bluetooth Mouse Client")
    print("=" * 30)
    
    client = BluetoothMouseClient()
    client.run()
