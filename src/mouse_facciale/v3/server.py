"""
Server Bluetooth per ricevere coordinate del mouse e controllarle localmente
Riceve le coordinate dal client e muove il mouse di conseguenza
"""

import bluetooth
import pyautogui
import json
import threading
import time

class MouseServer:
    def __init__(self, port=3):
        self.port = port
        self.server_sock = None
        self.client_sock = None
        self.running = False
        self.max_port_attempts = 10
        
        # Configura pyautogui per movimento fluido
        pyautogui.FAILSAFE = True  # Muovi mouse nell'angolo per emergenza
        pyautogui.PAUSE = 0.01     # Pausa minima tra comandi
        
        # Ottieni dimensioni schermo del server
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"Risoluzione schermo server: {self.screen_width}x{self.screen_height}")
    
    def find_available_port(self):
        """Trova una porta Bluetooth disponibile"""
        for port in range(self.port, self.port + self.max_port_attempts):
            try:
                test_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                test_sock.bind(("", port))
                test_sock.close()
                return port
            except Exception:
                continue
        return None
    
    def start_server(self):
        """Avvia il server Bluetooth"""
        # Trova una porta disponibile
        available_port = self.find_available_port()
        if available_port is None:
            print(f"Nessuna porta disponibile nel range {self.port}-{self.port + self.max_port_attempts}")
            return False
        
        self.port = available_port
        
        try:
            # Crea socket Bluetooth RFCOMM
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            # Abilita riutilizzo dell'indirizzo
            self.server_sock.setsockopt(bluetooth.SOL_SOCKET, bluetooth.SO_REUSEADDR, 1)
            
            self.server_sock.bind(("", self.port))
            self.server_sock.listen(1)
            
            print(f"Server in ascolto sulla porta {self.port}")
            print("In attesa di connessioni...")
            
            # Accetta connessione dal client
            self.client_sock, client_info = self.server_sock.accept()
            print(f"Connessione accettata da {client_info}")
            
            self.running = True
            
            # Avvia thread per ricevere dati
            receive_thread = threading.Thread(target=self.receive_mouse_data)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Errore nell'avvio del server: {e}")
            self.cleanup()
            return False
    
    def receive_mouse_data(self):
        """Riceve continuamente i dati del mouse dal client"""
        buffer = ""
        
        while self.running:
            try:
                # Ricevi dati dal client
                data = self.client_sock.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                # Processa tutti i messaggi completi nel buffer
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self.process_mouse_data(line.strip())
                        
            except bluetooth.BluetoothError as e:
                print(f"Errore Bluetooth: {e}")
                break
            except Exception as e:
                print(f"Errore nella ricezione: {e}")
                break
        
        print("Disconnesso dal client")
        self.cleanup()
    
    def process_mouse_data(self, data):
        """Processa i dati ricevuti e muove il mouse"""
        try:
            # Decodifica JSON
            mouse_data = json.loads(data)
            
            # Estrai coordinate e dimensioni schermo client
            client_x = mouse_data['x']
            client_y = mouse_data['y']
            client_width = mouse_data['screen_width']
            client_height = mouse_data['screen_height']
            
            # Calcola posizione relativa (0.0 - 1.0)
            rel_x = client_x / client_width
            rel_y = client_y / client_height
            
            # Converti alla risoluzione del server
            server_x = int(rel_x * self.screen_width)
            server_y = int(rel_y * self.screen_height)
            
            # Assicurati che le coordinate siano nei limiti
            server_x = max(0, min(server_x, self.screen_width - 1))
            server_y = max(0, min(server_y, self.screen_height - 1))
            
            # Muovi il mouse del server
            pyautogui.moveTo(server_x, server_y)
            
        except json.JSONDecodeError:
            print("Errore nel parsing JSON")
        except KeyError as e:
            print(f"Chiave mancante nei dati: {e}")
        except Exception as e:
            print(f"Errore nel processare dati: {e}")
    
    def cleanup(self):
        """Pulisce le risorse"""
        self.running = False
        
        if self.client_sock:
            try:
                self.client_sock.close()
            except:
                pass
        
        if self.server_sock:
            try:
                self.server_sock.close()
            except:
                pass
    
    def stop(self):
        """Ferma il server"""
        print("Fermando il server...")
        self.cleanup()

def main():
    print("=== Server Bluetooth Mouse Control ===")
    
    # Verifica se ci sono processi in esecuzione
    print("Verificando porte disponibili...")
    
    server = MouseServer()
    
    try:
        if server.start_server():
            print("Server avviato con successo!")
            print(f"Il client deve connettersi alla porta {server.port}")
            print("Premi Ctrl+C per fermare il server")
            
            # Mantieni il server attivo
            while server.running:
                time.sleep(1)
        else:
            print("Impossibile avviare il server")
            print("\nPossibili soluzioni:")
            print("1. Chiudi altre applicazioni Bluetooth")
            print("2. Riavvia il servizio Bluetooth")
            print("3. Riavvia il computer")
            
    except KeyboardInterrupt:
        print("\nInterruzione da tastiera ricevuta")
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        server.stop()

if __name__ == "__main__":
    main()