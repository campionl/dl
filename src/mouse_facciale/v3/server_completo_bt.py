import bluetooth
import pyautogui
import threading
import time
import queue

class BluetoothMouseServer:
    def __init__(self):
        self.server_sock = None
        self.client_sock = None
        self.running = False
        self.command_queue = queue.Queue()  
        self.executor_thread = None
        
        # Configurazione pyautogui per performance migliori
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0  # Rimuovi pause automatiche
        
        # Parametri di smoothing
        self.MOVEMENT_SMOOTHING = True
        self.MAX_MOVEMENT_PER_STEP = 50  # Pixel massimi per movimento
        
    def setup_server(self):
        """Configura il server Bluetooth"""
        try:
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_sock.bind(("", 1))
            self.server_sock.listen(1)
            return True
        except Exception as e:
            print(f"❌ Errore setup server: {e}")
            return False
    
    def wait_for_connection(self):
        """Attende connessione client"""
        print("🔍 In attesa di connessione Bluetooth...")
        print("💡 Assicurati che il client sia in modalità discovery")
        
        try:
            self.client_sock, address = self.server_sock.accept()
            print(f"✅ Client connesso: {address}")
            return True
        except Exception as e:
            print(f"❌ Errore connessione: {e}")
            return False
    
    def smooth_move(self, dx, dy):
        """Movimento fluido per grandi spostamenti"""
        if not self.MOVEMENT_SMOOTHING:
            pyautogui.moveRel(dx, dy)
            return
            
        # Se il movimento è piccolo, eseguilo direttamente
        if abs(dx) <= self.MAX_MOVEMENT_PER_STEP and abs(dy) <= self.MAX_MOVEMENT_PER_STEP:
            pyautogui.moveRel(dx, dy)
            return
        
        # Altrimenti, dividilo in passi più piccoli
        steps = max(abs(dx), abs(dy)) // self.MAX_MOVEMENT_PER_STEP + 1
        step_dx = dx / steps
        step_dy = dy / steps
        
        for _ in range(steps):
            pyautogui.moveRel(int(step_dx), int(step_dy))
            time.sleep(0.001)  # Piccola pausa tra i passi
    
    def execute_command(self, command_line):
        """Esegue un comando ricevuto"""
        try:
            parts = command_line.strip().split()
            if not parts:
                return
                
            command = parts[0]
            
            if command == "MOVE":
                if len(parts) >= 3:
                    dx, dy = int(parts[1]), int(parts[2])
                    # Limita movimenti estremi
                    dx = max(-200, min(200, dx))
                    dy = max(-200, min(200, dy))
                    self.smooth_move(dx, dy)
            
            elif command == "GOTO":
                if len(parts) >= 3:
                    x, y = int(parts[1]), int(parts[2])
                    # Verifica che le coordinate siano valide
                    screen_width, screen_height = pyautogui.size()
                    x = max(0, min(screen_width - 1, x))
                    y = max(0, min(screen_height - 1, y))
                    pyautogui.moveTo(x, y)
            
            elif command == "CLICK":
                pyautogui.click()
            
            elif command == "RIGHT_CLICK":
                pyautogui.rightClick()
            
            elif command == "MIDDLE_CLICK":
                pyautogui.middleClick()
            
            elif command == "DOUBLE_CLICK":
                pyautogui.doubleClick()
            
            elif command == "DOWN":
                button = parts[1] if len(parts) > 1 else 'left'
                if button in ['left', 'right', 'middle']:
                    pyautogui.mouseDown(button=button)
            
            elif command == "UP":
                button = parts[1] if len(parts) > 1 else 'left'
                if button in ['left', 'right', 'middle']:
                    pyautogui.mouseUp(button=button)
            
            elif command == "SCROLL":
                if len(parts) >= 3:
                    dx, dy = int(parts[1]), int(parts[2])
                    # Limita i valori di scroll
                    dx = max(-10, min(10, dx))
                    dy = max(-10, min(10, dy))
                    
                    if dx != 0:
                        pyautogui.hscroll(dx)
                    if dy != 0:
                        pyautogui.scroll(dy)
            
            else:
                print(f"⚠️  Comando sconosciuto: {command}")
                
        except (ValueError, IndexError) as e:
            print(f"⚠️  Formato comando non valido: {command_line.strip()} - {e}")
        except Exception as e:
            print(f"❌ Errore esecuzione comando '{command_line.strip()}': {e}")
    
    def command_executor(self):
        """Thread separato per esecuzione comandi"""
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.1)
                if command:
                    self.execute_command(command)
                self.command_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Errore executor: {e}")
                break
    
    def receive_commands(self):
        """Riceve comandi dal client"""
        buffer = ""
        
        while self.running:
            try:
                # Ricevi dati
                data = self.client_sock.recv(1024)
                if not data:
                    print("❌ Connessione persa")
                    break
                
                buffer += data.decode('utf-8', errors='ignore')
                
                # Processa comandi completi (terminati da \n)
                while '\n' in buffer:
                    command_line, buffer = buffer.split('\n', 1)
                    command_line = command_line.strip()
                    
                    if command_line:
                        # Aggiungi alla coda per esecuzione asincrona
                        try:
                            self.command_queue.put_nowait(command_line)
                        except queue.Full:
                            # Se coda piena, scarta comando più vecchio
                            try:
                                self.command_queue.get_nowait()
                                self.command_queue.put_nowait(command_line)
                            except queue.Empty:
                                pass
                
            except bluetooth.btcommon.BluetoothError as e:
                print(f"❌ Errore Bluetooth: {e}")
                break
            except Exception as e:
                print(f"❌ Errore ricezione: {e}")
                break
    
    def run(self):
        """Avvia il server"""
        print("🔷 Bluetooth Mouse Server")
        print("=" * 30)
        
        if not self.setup_server():
            return
        
        if not self.wait_for_connection():
            return
        
        self.running = True
        
        # Avvia thread executor
        self.executor_thread = threading.Thread(target=self.command_executor)
        self.executor_thread.daemon = True
        self.executor_thread.start()
        
        print("\n🖱️  Server pronto a ricevere comandi mouse!")
        print("📋 Funzionalità attive:")
        print("   • Movimento fluido del cursore")
        print("   • Click sinistro/destro/centrale")  
        print("   • Scroll verticale/orizzontale")
        print("   • Movimento ottimizzato e limitato")
        print("\n⚠️  Premi Ctrl+C per disconnettere")
        
        try:
            self.receive_commands()
        except KeyboardInterrupt:
            print("\n🔚 Interruzione richiesta dall'utente...")
        finally:
            self.stop()
    
    def stop(self):
        """Chiude tutte le connessioni"""
        print("🔄 Chiusura server...")
        self.running = False
        
        # Svuota la coda
        while not self.command_queue.empty():
            try:
                self.command_queue.get_nowait()
                self.command_queue.task_done()
            except queue.Empty:
                break
        
        if self.client_sock:
            try:
                self.client_sock.close()
            except:
                pass
            self.client_sock = None
        
        if self.server_sock:
            try:
                self.server_sock.close()
            except:
                pass
            self.server_sock = None
        
        print("✅ Server chiuso!")

if __name__ == "__main__":
    server = BluetoothMouseServer()
    server.run()
