# === CLIENT (Ricevitore) ===
import socket
import pyautogui
from bluetooth import *

# 1. Scansione dispositivi
print("Cerca dispositivi Bluetooth...")
devices = discover_devices(lookup_names=True, duration=5)

if not devices:
    print("Nessun dispositivo trovato!")
    exit()

# 2. Mostra lista dispositivi
print("\nDispositivi disponibili:")
for i, (addr, name) in enumerate(devices):
    print(f"{i+1}. {name} [{addr}]")

# 3. Selezione utente
selection = int(input("\nSeleziona il numero del server: ")) - 1
SERVER_ADDR = devices[selection][0]

# 4. Connessione
sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
sock.connect((SERVER_ADDR, 4))
print(f"Connesso a {devices[selection][1]}!")

# 5. Ricevi movimenti
try:
    while True:
        data = sock.recv(1024).decode()
        if not data: break
        
        try:
            dx, dy = map(float, data.split(','))
            pyautogui.moveRel(dx, dy, _pause=False)
        except:
            pass

except (KeyboardInterrupt, OSError):
    sock.close()