import bluetooth

server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", 1))  # Porta 1 come nel tuo script
server_sock.listen(1)

print("In attesa di connessione...")
client_sock, address = server_sock.accept()
print(f"Connessione da {address}")

try:
    while True:
        data = client_sock.recv(1024)
        if not data:
            break
        print("Ricevuto:", data.decode().strip())
except KeyboardInterrupt:
    print("Interrotto da utente")
finally:
    client_sock.close()
    server_sock.close()
