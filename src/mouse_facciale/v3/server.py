# server.py (Linux Arch)
import bluetooth
import threading
from pynput.mouse import Controller, Button

# Porta RFCOMM: di solito 1 per SPP
PORT = 1

def parse_report(data: bytes):
    """
    Interpreta report di 4 byte:
      byte0 = buttons bitmask (bit0=sinistro,1=destro,2=middle)
      byte1 = dx signed int8
      byte2 = dy signed int8
      byte3 = wheel signed int8
    Ritorna tuple (buttons, dx, dy, wheel) o None se data insufficiente.
    """
    if len(data) < 4:
        return None
    b0, b1, b2, b3 = data[0], data[1], data[2], data[3]
    # converti a signed
    def to_signed(x):
        return x - 256 if x > 127 else x
    dx = to_signed(b1)
    dy = to_signed(b2)
    wheel = to_signed(b3)
    return b0, dx, dy, wheel

def client_handler(client_sock, client_info):
    print(f"[Server] Connessione da {client_info}")
    mouse = Controller()
    try:
        while True:
            data = client_sock.recv(4)
            if not data:
                print("[Server] Connessione chiusa dal client")
                break
            rpt = parse_report(data)
            if rpt is None:
                continue
            buttons, dx, dy, wheel = rpt
            # Muovi cursore se differenza
            if dx != 0 or dy != 0:
                mouse.move(dx, dy)
            # Click semplici
            if buttons & 0x01:
                mouse.click(Button.left)
            if buttons & 0x02:
                mouse.click(Button.right)
            if buttons & 0x04:
                mouse.click(Button.middle)
            # Scroll wheel
            if wheel:
                mouse.scroll(0, wheel)
    except Exception as e:
        print(f"[Server] Errore: {e}")
    finally:
        client_sock.close()
        print("[Server] Thread client terminato")

def start_server():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", PORT))
    server_sock.listen(1)
    # Opzionale: pubblicizza il servizio SPP
    try:
        from bluetooth import advertise_service, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE
        advertise_service(
            server_sock,
            "MouseRemoteService",
            service_classes=[SERIAL_PORT_CLASS],
            profiles=[SERIAL_PORT_PROFILE]
        )
        print("[Server] Servizio SPP pubblicizzato")
    except Exception:
        # se fallisce, non critico: si può connettere ugualmente specificando MAC+porta
        pass

    print(f"[Server] In ascolto su RFCOMM canale {PORT}...")
    try:
        while True:
            client_sock, client_info = server_sock.accept()
            t = threading.Thread(
                target=client_handler, args=(client_sock, client_info), daemon=True
            )
            t.start()
    except KeyboardInterrupt:
        print("\n[Server] Chiusura server.")
    finally:
        server_sock.close()

if __name__ == "__main__":
    start_server()
