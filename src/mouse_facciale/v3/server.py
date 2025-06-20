import bluetooth
import pyautogui
import sys

SERVER_PORT = 1
SERVER_NAME = "MouseServer"

def run_server():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", SERVER_PORT))
    server_sock.listen(1)
    
    bluetooth.advertise_service(server_sock, SERVER_NAME,
                                service_classes=[bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE])
    
    print("In attesa di connessione...")
    client_sock, address = server_sock.accept()
    print(f"Connesso a: {address}")

    try:
        # Ricevi dimensioni schermo client
        dims = client_sock.recv(1024).decode('utf-8')
        client_w, client_h = map(int, dims.split(','))
        server_w, server_h = pyautogui.size()
        
        # Conferma ricezione
        client_sock.send("OK".encode('utf-8'))
        
        while True:
            data = client_sock.recv(1024).decode('utf-8')
            if not data:
                break
                
            x, y = map(int, data.split(','))
            target_x = int(x * server_w / client_w)
            target_y = int(y * server_h / client_h)
            pyautogui.moveTo(target_x, target_y)

    except Exception as e:
        print(f"Errore: {e}")
    finally:
        client_sock.close()
        server_sock.close()
        sys.exit()

if __name__ == "__main__":
    run_server()
