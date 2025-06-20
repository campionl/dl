# === SERVER (Trasmettitore) ===
import socket
import pygame
from pygame.math import Vector2

# 1. Configurazione
pygame.init()
screen = pygame.display.set_mode((100, 100))
pygame.display.set_caption("BT Mouse Server")

# 2. Setup Socket Bluetooth
server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
server_sock.bind(("", 4))  # Bind a tutti i dispositivi Bluetooth
server_sock.listen(1)
print("Server attivo! In attesa di connessioni...")

# 3. Accetta connessioni
client_sock, client_addr = server_sock.accept()
print(f"Connesso a: {client_addr}")

# 4. Trasmetti movimenti
last_pos = Vector2(pygame.mouse.get_pos())
try:
    while True:
        pygame.event.pump()  # Mantieni pygame reattivo
        current_pos = Vector2(pygame.mouse.get_pos())
        delta = current_pos - last_pos
        
        if delta.length() > 0:
            client_sock.send(f"{delta.x},{delta.y}".encode())
            last_pos = current_pos
        
        pygame.time.delay(10)

except (OSError, KeyboardInterrupt):
    client_sock.close()
    server_sock.close()
    pygame.quit()