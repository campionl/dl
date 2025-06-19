# client.py
import bluetooth
import time

# Indirizzo del server (la tua macchina)
SERVER_ADDR = "XX:XX:XX:XX:XX:XX"
PSM_INTERRUPT = 0x13

def send_mouse_move(dx=0, dy=0, buttons=0):
    # HID report: [Buttons, dx, dy, wheel]
    b = bytes([buttons & 0x07, dx & 0xFF, dy & 0xFF, 0x00])
    sock.send(b)
    print(f"[client] Sent: {b.hex()}")

sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
sock.connect((SERVER_ADDR, PSM_INTERRUPT))
print("[client] Connected. Inviando movimenti...")

try:
    for _ in range(10):
        send_mouse_move(dx=10, dy=0)
        time.sleep(0.5)
    send_mouse_move(buttons=1)  # click sinistro
finally:
    sock.close()
