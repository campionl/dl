# client.py
import bluetooth, time, threading

SERVER = "AA:BB:CC:DD:EE:FF"  # MAC server
PSM_INTR = 0x13

def stream_loop(sock):
    try:
        while True:
            dx, dy = 5, 0
            sock.send(bytes([0, dx & 0xFF, dy & 0xFF, 0]))
            time.sleep(0.02)
    except Exception: pass

if __name__ == "__main__":
    sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    sock.connect((SERVER, PSM_INTR))
    print("Connesso, streaming…")
    stream_loop(sock)
    sock.close()
