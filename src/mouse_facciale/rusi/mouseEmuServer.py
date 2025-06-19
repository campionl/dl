import bluetooth
import time
from ctypes import Structure, c_uint8, c_int16, c_uint16, LittleEndianStructure

# Bluetooth HID Mouse Report
class MouseReport(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("buttons", c_uint8),
        ("dx", c_int16),
        ("dy", c_int16),
    ]

def connect_to_device(target_name="Your Phone"):
    print("Searching for devices...")
    nearby_devices = bluetooth.discover_devices(lookup_names=True)
    
    for addr, name in nearby_devices:
        if target_name.lower() in name.lower():
            print(f"Found target: {name} ({addr})")
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((addr, 1))  # Channel 1 (HID)
            return sock
    
    print("Device not found. Ensure Bluetooth is ON and discoverable.")
    return None

def send_mouse_event(sock, dx=0, dy=0):
    report = MouseReport(0, dx, dy)
    sock.send(bytes(report))

if __name__ == "__main__":
    sock = connect_to_device()
    if sock:
        try:
            print("Move your mouse (Ctrl+C to stop)...")
            while True:
                # Example: Move cursor right (dx=10, dy=0)
                send_mouse_event(sock, 10, 0)
                time.sleep(0.1)
        except KeyboardInterrupt:
            sock.close()