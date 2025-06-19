# receiver_bt_mouse.py
import bluetooth
import pyautogui
import sys

# Configurazione
BLUETOOTH_UUID = "00001101-0000-1000-8000-00805F9B34FB"  # UUID standard per SPP

def main():
    # Inizializza il server Bluetooth
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)
    
    port = server_sock.getsockname()[1]
    
    # Annuncia il servizio
    bluetooth.advertise_service(server_sock, "MouseServer",
                              service_id=BLUETOOTH_UUID,
                              service_classes=[BLUETOOTH_UUID, bluetooth.SERIAL_PORT_CLASS],
                              profiles=[bluetooth.SERIAL_PORT_PROFILE])
    
    print(f"Server Bluetooth mouse in attesa su RFCOMM channel {port}")
    print("Assicurati che il PC sia accoppiato con il dispositivo mittente")
    print("Premi Ctrl+C per uscire")

    try:
        while True:
            print("\nIn attesa di connessione...")
            client_sock, client_info = server_sock.accept()
            print(f"Connesso a {client_info}")
            
            try:
                pyautogui.FAILSAFE = False
                while True:
                    # Ricevi i comandi
                    data = client_sock.recv(1024).decode().strip()
                    if not data:
                        print("Connessione chiusa dal client")
                        break
                    
                    # Elabora i comandi
                    try:
                        if data.startswith("MOVE"):
                            _, dx, dy = data.split()
                            pyautogui.moveRel(int(dx), int(dy))
                        elif data.startswith("CLICK"):
                            _, button = data.split()
                            pyautogui.click(button=button.lower())
                        elif data.startswith("SCROLL"):
                            _, dy = data.split()
                            pyautogui.scroll(int(dy))
                        elif data == "EXIT":
                            print("Richiesta di chiusura ricevuta")
                            break
                    except Exception as e:
                        print(f"Errore nell'eseguire il comando: {e}")
                        
            except bluetooth.btcommon.BluetoothError as e:
                print(f"Errore Bluetooth: {e}")
            except Exception as e:
                print(f"Errore: {e}")
            finally:
                client_sock.close()
                print("Client disconnesso")
                
    except KeyboardInterrupt:
        print("\nSpegnimento server...")
    finally:
        server_sock.close()
        print("Server chiuso")

if __name__ == "__main__":
    main()