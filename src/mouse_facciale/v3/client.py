import asyncio
from bleak import BleakClient, BleakScanner
import pyautogui
import sys

# UUID devono corrispondere a quelli usati nel server
SERVICE_UUID = "00001101-0000-1000-8000-00805F9B34FB"
CHARACTERISTIC_UUID = "00001102-0000-1000-8000-00805F9B34FB"

class BluetoothMouseMirror:
    def __init__(self):
        self.running = False
        self.client = None
        self.last_position = pyautogui.position()
        self.device_address = None

    async def discover_devices(self):
        print("Ricerca dispositivi BLE nelle vicinanze...")
        devices = await BleakScanner.discover()
        
        if not devices:
            print("Nessun dispositivo trovato. Assicurati che il dispositivo target sia rilevabile.")
            return None
        
        print("\nDispositivi trovati:")
        for i, device in enumerate(devices):
            print(f"{i+1}. {device.name} ({device.address})")
        
        while True:
            try:
                choice = int(input("\nSeleziona il numero del dispositivo a cui connettersi: "))
                if 1 <= choice <= len(devices):
                    return devices[choice-1].address
                print("Selezione non valida. Riprova.")
            except ValueError:
                print("Inserisci un numero valido.")

    async def connect(self):
        device_address = await self.discover_devices()
        if not device_address:
            return False
        
        self.device_address = device_address
        print(f"Connessione a {self.device_address}...")
        
        try:
            self.client = BleakClient(self.device_address)
            await self.client.connect()
            print("Connessione riuscita!")
            return True
        except Exception as e:
            print(f"Connessione fallita: {e}")
            self.client = None
            return False

    async def send_mouse_movement(self, dx, dy):
        if not self.client or not self.client.is_connected:
            print("Client non connesso")
            return False
        
        try:
            # Invia il comando come stringa (es. "MOVE 10 5")
            message = f"MOVE {dx} {dy}\n".encode('utf-8')
            await self.client.write_gatt_char(CHARACTERISTIC_UUID, message)
            return True
        except Exception as e:
            print(f"Errore invio dati: {e}")
            return False

    async def start_mirroring(self):
        if not await self.connect():
            return
        
        self.running = True
        print("Mirroring movimenti mouse attivo (Ctrl+C per fermare)...")
        
        try:
            while self.running:
                current_position = pyautogui.position()
                if current_position != self.last_position:
                    dx = current_position[0] - self.last_position[0]
                    dy = current_position[1] - self.last_position[1]
                    
                    if not await self.send_mouse_movement(dx, dy):
                        self.running = False
                        break
                    
                    self.last_position = current_position
                
                await asyncio.sleep(0.01)  # Piccola pausa per ridurre l'uso della CPU
        except KeyboardInterrupt:
            self.running = False
            print("\nMirroring fermato dall'utente")
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        if self.client and self.client.is_connected:
            await self.client.disconnect()
        print("Client fermato")

async def main():
    # Verifica dipendenze
    try:
        import pyautogui
    except ImportError as e:
        print(f"Errore: {e}")
        print("Installa i pacchetti necessari:")
        print("pip install bleak pyautogui")
        sys.exit(1)
    
    mirror = BluetoothMouseMirror()
    try:
        await mirror.start_mirroring()
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        await mirror.stop()

if __name__ == "__main__":
    asyncio.run(main())