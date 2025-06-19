import bluetooth
import pyautogui
import threading
import time
import queue
import sys
import socket

class BluetoothMouseServer:
    def __init__(self):
        self.server_sock = None
        self.client_sock = None
        self.running = False
        self.command_queue = queue.Queue()  
        self.executor_thread = None
        self.client_address = None
        
        # Configurazione pyautogui per performance migliori
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0
        
        # Parametri di smoothing
        self.MOVEMENT_SMOOTHING = True
        self.MAX_MOVEMENT_PER_STEP = 50
        
    def get_local_bluetooth_info(self):
        """Ottiene informazioni sul dispositivo Bluetooth locale"""
        try:
            local_name = bluetooth.lookup_name(bluetooth.read_local_bdaddr()[0])
            local_addr = bluetooth.read_local_bdaddr()[0]
            print(f"📱 Dispositivo locale: {local_name} ({local_addr})")
            return local_addr, local_name
        except Exception as e:
            print(f"⚠️  Impossibile ottenere info Bluetooth locali: {e}")
            return None, None
        
    def setup_server(self):
        """Configura il server Bluetooth"""
        print("🔧 Configurazione server Bluetooth...")
        
        # Mostra info dispositivo locale
        local_addr, local_name = self.get_local_bluetooth_info()
        
        # Prova diverse porte se la prima non funziona
        ports_to_try = [1, 2, 3, 4, 5]
        
        for port in ports_to_try:
            try:
                if self.server_sock:
                    self.server_sock.close()
                    
                self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                
                # Permetti riutilizzo dell'indirizzo
                self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                print(f"🔗 Tentativo binding sulla porta {port}...")
                self.server_sock.bind(("", port))
                
                print(f"👂 Impostazione modalità ascolto sulla porta {port}...")
                self.server_sock.listen(1)
                
                print(f"✅ Server configurato correttamente sulla porta {port}")
                print(f"📡 In ascolto su porta RFCOMM {port}")
                
                # Salva la porta utilizzata
                self.port = port
                
                return True
                
            except bluetooth.btcommon.BluetoothError as e:
                print(f"❌ Porta {port} non disponibile: {e}")
                if "Permission denied" in str(e):
                    print("💡 Prova ad eseguire come amministratore")
                elif "Address already in use" in str(e):
                    print(f"💡 La porta {port} è già in uso")
                continue
            except Exception as e:
                print(f"❌ Errore porta {port}: {e}")
                continue
        
        print("❌ Impossibile configurare il server su tutte le porte disponibili")
        return False
    
    def wait_for_connection(self):
        """Attende connessione client"""
        print(f"\n🔍 In attesa di connessione Bluetooth sulla porta {getattr(self, 'port', 1)}...")
        print("💡 Istruzioni per il client:")
        print("   1. Avvia il client sull'altro dispositivo")
        print("   2. Seleziona questo dispositivo dalla lista")
        print("   3. La connessione si stabilirà automaticamente")
        print("\n⏳ Attendere connessione...")
        print("   (Il server rimarrà in attesa fino alla connessione o interruzione)")
        
        try:
            self.server_sock.settimeout(None)  # Attesa infinita
            print("📡 Server in ascolto...")
            
            self.client_sock, self.client_address = self.server_sock.accept()
            
            print(f"\n🎉 Client connesso con successo!")
            print(f"📱 Indirizzo client: {self.client_address}")
            
            # Configura socket client per comunicazione
            self.client_sock.settimeout(1.0)  # Timeout per operazioni di rete
            
            # Invia messaggio di benvenuto
            try:
                welcome_msg = "SERVER_READY\n"
                self.client_sock.send(welcome_msg.encode())
                print("📤 Messaggio di benvenuto inviato")
            except:
                print("⚠️ Impossibile inviare messaggio di benvenuto")
            
            return True
            
        except bluetooth.btcommon.BluetoothError as e:
            print(f"❌ Errore connessione Bluetooth: {e}")
            if "Operation was cancelled" in str(e):
                print("💡 Operazione annullata dall'utente")
            return False
        except KeyboardInterrupt:
            print("\n🔚 Attesa connessione interrotta dall'utente")
            return False
        except Exception as e:
            print(f"❌ Errore connessione: {e}")
            return False
    
    def smooth_move(self, dx, dy):
        """Movimento fluido per grandi spostamenti"""
        try:
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
                if not self.running:  # Verifica se dobbiamo fermarci
                    break
                pyautogui.moveRel(int(step_dx), int(step_dy))
                time.sleep(0.001)
                
        except Exception as e:
            print(f"❌ Errore movimento mouse: {e}")
    
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
                    dx = max(-500, min(500, dx))
                    dy = max(-500, min(500, dy))
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
            
            elif command == "PING":
                # Comando per test connessione
                pass
                
            else:
                print(f"⚠️  Comando sconosciuto: {command}")
                
        except (ValueError, IndexError) as e:
            print(f"⚠️  Formato comando non valido: {command_line.strip()} - {e}")
        except pyautogui.FailSafeException:
            print("🛡️  FailSafe attivata - mouse mosso nell'angolo dello schermo")
            self.running = False
        except Exception as e:
            print(f"❌ Errore esecuzione comando '{command_line.strip()}': {e}")
    
    def command_executor(self):
        """Thread separato per esecuzione comandi"""
        commands_processed = 0
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.1)
                if command:
                    self.execute_command(command)
                    commands_processed += 1
                    
                    # Mostra statistiche ogni 100 comandi
                    if commands_processed % 100 == 0:
                        print(f"📊 Comandi processati: {commands_processed}")
                        
                self.command_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Errore executor: {e}")
                break
    
    def receive_commands(self):
        """Riceve comandi dal client"""
        buffer = ""
        commands_received = 0
        last_activity = time.time()
        
        print("📡 Ricezione comandi attiva...")
        
        while self.running:
            try:
                # Ricevi dati con timeout
                self.client_sock.settimeout(1.0)
                data = self.client_sock.recv(1024)
                
                if not data:
                    print("❌ Connessione chiusa dal client")
                    break
                
                last_activity = time.time()
                buffer += data.decode('utf-8', errors='ignore')
                
                # Processa comandi completi (terminati da \n)
                while '\n' in buffer:
                    command_line, buffer = buffer.split('\n', 1)
                    command_line = command_line.strip()
                    
                    if command_line:
                        commands_received += 1
                        
                        # Aggiungi alla coda per esecuzione asincrona
                        try:
                            self.command_queue.put_nowait(command_line)
                        except queue.Full:
                            # Se coda piena, scarta comando più vecchio
                            try:
                                self.command_queue.get_nowait()
                                self.command_queue.put_nowait(command_line)
                                print("⚠️  Coda comandi piena - comando scartato")
                            except queue.Empty:
                                pass
                
                # Verifica timeout di inattività (30 secondi)
                if time.time() - last_activity > 30:
                    print("⏰ Timeout inattività - connessione chiusa")
                    break
                    
            except socket.timeout:
                # Timeout normale - continua il loop
                continue
            except bluetooth.btcommon.BluetoothError as e:
                print(f"❌ Errore Bluetooth ricezione: {e}")
                break
            except Exception as e:
                print(f"❌ Errore ricezione: {e}")
                break
        
        print(f"📊 Totale comandi ricevuti: {commands_received}")
    
    def run(self):
        """Avvia il server"""
        print("🔷 Bluetooth Mouse Server")
        print("=" * 30)
        print("💡 Requisiti:")
        print("   - Bluetooth attivo e funzionante")
        print("   - Permessi amministratore (se richiesti)")
        print("   - Client Bluetooth pronto per la connessione")
        print()
        
        if not self.setup_server():
            return
        
        if not self.wait_for_connection():
            self.stop()
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
        print("   • Monitoraggio stato connessione")
        print(f"\n📊 Stato: Connesso a {self.client_address}")
        print("⚠️  Premi Ctrl+C per disconnettere")
        
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
                print("🔌 Connessione client chiusa")
            except:
                pass
            self.client_sock = None
        
        if self.server_sock:
            try:
                self.server_sock.close()
                print("🏠 Server socket chiuso")
            except:
                pass
            self.server_sock = None
        
        print("✅ Server chiuso!")

if __name__ == "__main__":
    try:
        server = BluetoothMouseServer()
        server.run()
    except KeyboardInterrupt:
        print("\n🔚 Programma interrotto")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        sys.exit(1)
