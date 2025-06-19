# Manda il segnale mouse 

import bluetooth
import pyautogui
import threading
import time 
import sys

class BluetoothMouseMirror:
    def __init__(self):
        self.running = False
        self.socket = None
        self.last_position = pyautogui.position()
        self.device_address = None
        self.port = 1  # RFCOMM port
    
    def discover_devices(self):
        print("Searching for nearby Bluetooth devices...")
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        print("Found devices:")
        for i, (addr, name) in enumerate(nearby_devices):
            print(f"{i+1}. {name} ({addr})")
        
        if not nearby_devices:
            print("No devices found. Make sure your target device is discoverable.")
            return None
        
        choice = input("Enter the number of the device to connect to: ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(nearby_devices):
                return nearby_devices[index][0]
        except ValueError:
            pass
        
        print("Invalid selection.")
        return None
    
    def connect(self, device_address=None):
        if not device_address:
            device_address = self.discover_devices()
            if not device_address:
                return False
        
        self.device_address = device_address
        print(f"Connecting to {self.device_address}...")
        
        try:
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((self.device_address, self.port))
            print("Connected successfully!")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.socket = None
            return False
    
    def start_mirroring(self):
        if not self.socket:
            if not self.connect():
                return
        
        self.running = True
        print("Mirroring mouse movements (press Ctrl+C to stop)...")
        
        try:
            while self.running:
                current_position = pyautogui.position()
                if current_position != self.last_position:
                    dx = current_position[0] - self.last_position[0]
                    dy = current_position[1] - self.last_position[1]
                    
                    # Send relative movement
                    message = f"MOVE {dx} {dy}\n"
                    try:
                        self.socket.send(message)
                    except Exception as e:
                        print(f"Error sending data: {e}")
                        self.running = False
                        break
                    
                    self.last_position = current_position
                
                time.sleep(0.01)  # Small delay to reduce CPU usage
        except KeyboardInterrupt:
            self.running = False
            print("\nMirroring stopped by user")
    
    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None

def main():
    mirror = BluetoothMouseMirror()
    
    try:
        mirror.start_mirroring()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        mirror.stop()

if __name__ == "__main__":
    # Check dependencies
    try:
        import bluetooth
        import pyautogui
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install required packages:")
        print("pip install PyBluez pyautogui")
        sys.exit(1)
    
<<<<<<< HEAD
    main()
=======
    main()
>>>>>>> e55f7f29220916172449b88027a537074c0fd8c1
