import asyncio
from bleak import BleakServer, BleakGATTCharacteristic
import pyautogui
import sys
import struct

# UUID per il servizio e la caratteristica personalizzati
SERVICE_UUID = "00001101-0000-1000-8000-00805F9B34FB"  # Sostituisci con il tuo UUID
CHARACTERISTIC_UUID = "00001102-0000-1000-8000-00805F9B34FB"  # Sostituisci con il tuo UUID

class BluetoothMouseServer:
    def __init__(self):
        self.server = None
        self.connected = False
        self.running = False

    async def start(self):
        self.server = BleakServer()
        
        # Aggiungi un servizio personalizzato
        await self.server.add_service(
            SERVICE_UUID,
            [
                {
                    "uuid": CHARACTERISTIC_UUID,
                    "properties": ["read", "write", "notify"],
                    "value": None,
                    "descriptors": [],
                }
            ],
        )

        # Callback per gestire le connessioni
        self.server.set_connection_callback(self.connection_callback)
        
        # Callback per gestire le scritture sulla caratteristica
        await self.server.set_write_callback(CHARACTERISTIC_UUID, self.handle_mouse_data)

        try:
            print("Avvio del server BLE...")
            await self.server.start()
            print(f"Server BLE avviato. In attesa di connessioni...")
            self.running = True
            
            # Mantieni il server in esecuzione
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Errore server: {e}")
        finally:
            await self.stop()

    async def connection_callback(self, client, connected):
        self.connected = connected
        if connected:
            print(f"Dispositivo connesso: {client}")
        else:
            print("Dispositivo disconnesso")

    async def handle_mouse_data(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        try:
            # Decodifica i dati (esempio: "MOVE dx dy" come bytes)
            command = data.decode('utf-8').strip()
            
            if command.startswith("MOVE"):
                _, dx, dy = command.split()
                dx, dy = int(dx), int(dy)
                current_x, current_y = pyautogui.position()
                pyautogui.moveTo(current_x + dx, current_y + dy)
                
        except Exception as e:
            print(f"Errore elaborazione movimento: {e}")

    async def stop(self):
        self.running = False
        if self.server:
            await self.server.stop()
        print("Server BLE fermato")

async def main():
    # Verifica dipendenze
    try:
        import pyautogui
    except ImportError as e:
        print(f"Errore: {e}")
        print("Installa i pacchetti necessari:")
        print("pip install bleak pyautogui")
        sys.exit(1)
    
    server = BluetoothMouseServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nServer interrotto dall'utente")
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())