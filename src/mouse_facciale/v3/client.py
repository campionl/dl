"""
Client Bluetooth per inviare posizione del mouse in tempo reale
Rileva la posizione del mouse locale e la invia al server via Bluetooth
"""

import bluetooth
import pyautogui
import json
import time
import threading

class MouseClient:
    def __init__(self, server_address=None):
        self.server_address = server_address
        self.sock = None
        self.running = False
        self.send_rate = 0.02  # Invio ogni 20ms per movimento fluido
        
        # Ottieni dimensioni schermo del client
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"Risoluzione schermo client: {self.screen_width}x{self.screen_height}")
        
        # Configura pyautogui
        pyautogui.FAILSAFE = True
    
    def discover_devices(self):
        """Scopre dispositivi Bluetooth disponibili"""
        print("Ricerca dispositivi Bluetooth...")
        devices = bluetooth.discover_devices(duration=8, lookup_names=True)
        
        if not devices:
            print("Nessun dispositivo trovato")
            return None
        
        print("Dispositivi trovati:")
        for i, (addr, name) in enumerate(devices):
            print(f"{i+1}. {name} ({addr})")
        
        while True:
            try:
                choice = input("\nSeleziona dispositivo (numero): ")
                index = int(choice) - 1
                if 0 <= index < len(devices):
                    return devices[index][0]  # Ritorna l'indirizzo
                else:
                    print("Scelta non valida")
            except ValueError:
                print("Inserisci un numero valido")
    
    def connect_to_server(self, port=3):
        """Connette al server Bluetooth"""
        if not self.server_address:
            self.server_address = self.discover_devices()
            if not self.server_address:
                return False
        
        try:
            print(f"Connessione a {self.server_address}...")
            
            # Crea socket Bluetooth RFCOMM
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.sock.connect((self.server_address, port))
            
            print("Connesso al server!")
            return True
            
        except bluetooth.BluetoothError as e:
            print(f"Errore connessione Bluetooth: {e}")
            return False
        except Exception as e:
            print(f"Errore generico: {e}")
            return False
    
    def send_mouse_position(self):
        """Invia continuamente la posizione del mouse"""
        last_position = None
        
        while self.running:
            try:
                # Ottieni posizione corrente del mouse
                current_x, current_y = pyautogui.position()
                current_position = (current_x, current_y)
                
                # Invia solo se la posizione è cambiata (ottimizzazione)
                if current_position != last_position:
                    # Crea pacchetto dati
                    mouse_data = {
                        'x': current_x,
                        'y': current_y,
                        'screen_width': self.screen_width,
                        'screen_height': self.screen_height,
                        'timestamp': time.time()
                    }
                    
                    # Converti in JSON e invia
                    json_data = json.dumps(mouse_data) + '\n'
                    self.sock.send(json_data.encode('utf-8'))
                    
                    last_position = current_position
                
                # Attendi prima del prossimo invio
                time.sleep(self.send_rate)
                
            except bluetooth.BluetoothError as e:
                print(f"Errore invio Bluetooth: {e}")
                break
            except Exception as e:
                print(f"Errore nel tracking mouse: {e}")
                break
        
        print("Invio posizione mouse terminato")
    
    def start_tracking(self):
        """Avvia il tracking del mouse"""
        if not self.connect_to_server():
            return False
        
        self.running = True
        
        # Avvia thread per invio posizione
        tracking_thread = threading.Thread(target=self.send_mouse_position)
        tracking_thread.daemon = True
        tracking_thread.start()
        
        return True
    
    def stop_tracking(self):
        """Ferma il tracking del mouse"""
        print("Fermando il tracking...")
        self.running = False
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
    
    def set_send_rate(self, rate):
        """Imposta la frequenza di invio (in secondi)"""
        self.send_rate = max(0.01, rate)  # Minimo 10ms
        print(f"Frequenza invio impostata a {1/self.send_rate:.1f} FPS")

def main():
    # Chiedi indirizzo server se specifico
    server_addr = input("Indirizzo server Bluetooth (lascia vuoto per ricerca automatica): ").strip()
    if not server_addr:
        server_addr = None
    
    client = MouseClient(server_addr)
    
    # Opzioni di configurazione
    while True:
        rate_input = input("Frequenza invio (1-100 FPS, default 50): ").strip()
        if not rate_input:
            break
        try:
            fps = int(rate_input)
            if 1 <= fps <= 100:
                client.set_send_rate(1.0 / fps)
                break
            else:
                print("Inserisci un valore tra 1 e 100")
        except ValueError:
            print("Inserisci un numero valido")
    
    try:
        if client.start_tracking():
            print("Tracking del mouse avviato!")
            print("Muovi il mouse per inviare la posizione al server")
            print("Premi Ctrl+C per fermare")
            
            # Mantieni il client attivo
            while client.running:
                time.sleep(1)
        else:
            print("Impossibile avviare il tracking")
            
    except KeyboardInterrupt:
        print("\nInterruzione da tastiera ricevuta")
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        client.stop_tracking()

if __name__ == "__main__":
    main()