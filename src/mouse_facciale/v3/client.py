import bluetooth
import pyautogui
import time

SERVER_ADDRESS = "00:00:00:00:00:00"  # Sostituisci con l'indirizzo Bluetooth del server
PORT = 1

def run_client():
    # Ottieni dimensioni schermo
    w, h = pyautogui.size()
    
    # Connetti al server
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((SERVER_ADDRESS, PORT))
    
    # Invia dimensioni schermo
    sock.send(f"{w},{h}".encode('utf-8'))
    
    # Attendi conferma
    if sock.recv(1024).decode('utf-8') != "OK":
        print("Errore di connessione")
        sock.close()
        return

    try:
        while True:
            x, y = pyautogui.position()
            sock.send(f"{x},{y}".encode('utf-8'))
            time.sleep(0.03)  # Aggiornamento a ~33fps
    except:
        sock.close()

if __name__ == "__main__":
    run_client()
