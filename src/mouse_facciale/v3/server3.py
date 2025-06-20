# server_auto.py
import socket
import pygame
import sys
import bluetooth

# Inizializza Pygame
pygame.init()
screen = pygame.display.set_mode((300, 200))
pygame.display.set_caption("BT Mouse Server - IN ESECUZIONE")
pygame.mouse.set_visible(True)

# Configura il server Bluetooth
server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
server_sock.bind(("", 4))
server_sock.listen(1)

# Ottieni il nome del dispositivo
device_name = bluetooth.read_local_bdaddr()[0] if sys.platform == "linux" else socket.gethostname()
print(f"Server attivo! Nome dispositivo: {device_name}")
print("In attesa di client...")

# Accetta connessioni
client_sock, client_addr = server_sock.accept()
print(f"Connesso a: {client_addr}")

# Trasmetti movimenti
try:
    last_pos = pygame.mouse.get_pos()
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
        
        current_pos = pygame.mouse.get_pos()
        dx, dy = current_pos[0] - last_pos[0], current_pos[1] - last_pos[1]
        
        if dx != 0 or dy != 0:
            try:
                client_sock.send(f"{dx},{dy}".encode('utf-8'))
                last_pos = current_pos
            except:
                break
        
        clock.tick(60)

except (KeyboardInterrupt, OSError):
    print("Chiusura connessione...")
finally:
    client_sock.close()
    server_sock.close()
    pygame.quit()
    sys.exit()
