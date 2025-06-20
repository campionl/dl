# client_auto.py
import socket
import pyautogui
import bluetooth
import sys

# Configurazione
PORT = 4
BUFFER_SIZE = 1024

print("=== Client Mouse Bluetooth - Ricerca Automatica ===")

# Trova tutti i dispositivi Bluetooth nelle vicinanze
print("Ricerca dispositivi Bluetooth...")
devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True)

if not devices:
    print("Nessun dispositivo trovato! Assicurati che il server sia acceso e visibile.")
    sys.exit(1)

# Filtra dispositivi che hanno un server in ascolto
available_servers = []
for addr, name in devices:
    try:
        sock_test = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock_test.settimeout(2)
        sock_test.connect((addr, PORT))
        sock_test.close()
        available_servers.append((addr, name))
    except:
        pass

if not available_servers:
    print("Nessun server mouse trovato! Avvia prima il server.")
    sys.exit(1)

# Se c'è un solo server, connettiti automaticamente
if len(available_servers) == 1:
    server_addr, server_name = available_servers[0]
    print(f"Trovato un server: {server_name}")
else:
    # Se ci sono più server, chiedi all'utente
    print("\nServer disponibili:")
    for i, (addr, name) in enumerate(available_servers):
        print(f"{i+1}. {name} [{addr}]")
    
    selection = int(input("\nSeleziona il server: ")) - 1
    server_addr, server_name = available_servers[selection]

# Connessione finale
print(f"Connessione a {server_name}...")
sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
sock.connect((server_addr, PORT))
print(f"Connesso! Muovi il mouse sul server per controllare questo computer.")
print("Premi CTRL+C per uscire")

try:
    while True:
        data = sock.recv(BUFFER_SIZE).decode('utf-8')
        if not data:
            break
        
        try:
            dx, dy = map(float, data.split(','))
            pyautogui.moveRel(dx, dy, _pause=False)
        except ValueError:
            pass

except (KeyboardInterrupt, OSError):
    print("Chiusura connessione...")
finally:
    sock.close()
    sys.exit()
