# server.py
import bluetooth

# PSM HID specifici: control=0x11, interrupt=0x13 (possono variare)
PSM_CONTROL = 0x11
PSM_INTERRUPT = 0x13

def start_server():
    # Socket L2CAP per interrupt channel (mouse data)
    sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    sock.bind(("", PSM_INTERRUPT))
    sock.listen(1)
    print(f"[server] Listening on PSM {hex(PSM_INTERRUPT)}...")
    client, addr = sock.accept()
    print(f"[server] Client connected: {addr}")
    try:
        while True:
            data = client.recv(1024)
            if not data: break
            print(f"[server] HID report received: {data.hex()}")
            # Qui potresti interpretarlo o inoltrarlo
    finally:
        client.close()
        sock.close()

if __name__ == "__main__":
    start_server()
