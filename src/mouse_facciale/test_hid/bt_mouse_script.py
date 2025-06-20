#!/usr/bin/env python3
"""
Script per trasformare il PC in un mouse Bluetooth HID
Cattura i movimenti del mouse locale e li trasmette via Bluetooth
"""

import bluetooth
import socket
import threading
import time
import sys
import struct
from pynput import mouse
from pynput.mouse import Listener

class BluetoothHIDMouse:
    def __init__(self):
        # Porte HID standard
        self.P_CTRL = 17  # Porta di controllo HID
        self.P_INTR = 19  # Porta interrupt HID
        
        # Socket Bluetooth
        self.csk = None  # Control socket
        self.isk = None  # Interrupt socket
        self.client_sock = None
        self.client_info = None
        
        # Stato del mouse
        self.last_x = 0
        self.last_y = 0
        self.mouse_listener = None
        self.connected = False
        
        # HID Report Descriptor per mouse standard
        self.mouse_report_desc = bytes([
            0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
            0x09, 0x02,        # Usage (Mouse)
            0xA1, 0x01,        # Collection (Application)
            0x09, 0x01,        #   Usage (Pointer)
            0xA1, 0x00,        #   Collection (Physical)
            0x05, 0x09,        #     Usage Page (Button)
            0x19, 0x01,        #     Usage Minimum (0x01)
            0x29, 0x03,        #     Usage Maximum (0x03)
            0x15, 0x00,        #     Logical Minimum (0)
            0x25, 0x01,        #     Logical Maximum (1)
            0x95, 0x03,        #     Report Count (3)
            0x75, 0x01,        #     Report Size (1)
            0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
            0x95, 0x01,        #     Report Count (1)
            0x75, 0x05,        #     Report Size (5)
            0x81, 0x03,        #     Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
            0x05, 0x01,        #     Usage Page (Generic Desktop Ctrls)
            0x09, 0x30,        #     Usage (X)
            0x09, 0x31,        #     Usage (Y)
            0x15, 0x81,        #     Logical Minimum (-127)
            0x25, 0x7F,        #     Logical Maximum (127)
            0x75, 0x08,        #     Report Size (8)
            0x95, 0x02,        #     Report Count (2)
            0x81, 0x06,        #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position)
            0xC0,              #   End Collection
            0xC0,              # End Collection
        ])

    def setup_bluetooth(self):
        """Configura i socket Bluetooth per HID"""
        try:
            # Socket di controllo
            self.csk = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            self.csk.bind(("", self.P_CTRL))
            self.csk.listen(1)
            
            # Socket interrupt
            self.isk = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            self.isk.bind(("", self.P_INTR))
            self.isk.listen(1)
            
            print("Socket Bluetooth configurati correttamente")
            return True
        except Exception as e:
            print(f"Errore nella configurazione Bluetooth: {e}")
            return False

    def make_discoverable(self):
        """Rende il dispositivo visibile per il pairing"""
        try:
            # Imposta il dispositivo come visibile
            import subprocess
            subprocess.run(["sudo", "hciconfig", "hci0", "piscan"], check=True)
            print("Dispositivo reso visibile per il pairing")
            return True
        except Exception as e:
            print(f"Errore nel rendere il dispositivo visibile: {e}")
            print("Prova manualmente: sudo hciconfig hci0 piscan")
            return False

    def wait_for_connection(self):
        """Attende la connessione da un dispositivo client"""
        print("In attesa di connessione...")
        print("Connetti il tuo dispositivo a questo PC tramite Bluetooth")
        
        try:
            # Accetta connessione sul socket di controllo
            self.client_sock, self.client_info = self.csk.accept()
            print(f"Dispositivo connesso: {self.client_info}")
            
            # Accetta connessione sul socket interrupt
            self.int_sock, _ = self.isk.accept()
            print("Connessione HID stabilita!")
            
            self.connected = True
            return True
        except Exception as e:
            print(f"Errore durante la connessione: {e}")
            return False

    def send_mouse_report(self, buttons, dx, dy):
        """Invia un report del mouse via Bluetooth"""
        if not self.connected:
            return
        
        try:
            # Limita i valori del movimento
            dx = max(-127, min(127, dx))
            dy = max(-127, min(127, dy))
            
            # Crea il report HID (1 byte pulsanti + 2 byte movimento)
            report = struct.pack('bbb', buttons, dx, dy)
            
            # Invia tramite socket interrupt
            self.int_sock.send(report)
        except Exception as e:
            print(f"Errore nell'invio del report: {e}")
            self.connected = False

    def on_move(self, x, y):
        """Callback per il movimento del mouse"""
        if not self.connected:
            return
        
        # Calcola il movimento relativo
        dx = x - self.last_x
        dy = y - self.last_y
        
        # Invia solo se c'è movimento significativo
        if abs(dx) > 0 or abs(dy) > 0:
            self.send_mouse_report(0, dx, dy)
        
        self.last_x = x
        self.last_y = y

    def on_click(self, x, y, button, pressed):
        """Callback per i click del mouse"""
        if not self.connected:
            return
        
        # Mappa i pulsanti
        button_mask = 0
        if button == mouse.Button.left:
            button_mask = 0x01
        elif button == mouse.Button.right:
            button_mask = 0x02
        elif button == mouse.Button.middle:
            button_mask = 0x04
        
        # Invia solo se premuto
        if pressed:
            self.send_mouse_report(button_mask, 0, 0)
        else:
            self.send_mouse_report(0, 0, 0)

    def start_mouse_listener(self):
        """Avvia il listener per catturare i movimenti del mouse"""
        try:
            self.mouse_listener = Listener(
                on_move=self.on_move,
                on_click=self.on_click
            )
            self.mouse_listener.start()
            print("Listener del mouse avviato")
        except Exception as e:
            print(f"Errore nell'avvio del listener: {e}")

    def stop_mouse_listener(self):
        """Ferma il listener del mouse"""
        if self.mouse_listener:
            self.mouse_listener.stop()

    def run(self):
        """Esegue il loop principale"""
        print("=== Mouse Bluetooth HID ===")
        print("Questo script trasforma il PC in un mouse Bluetooth")
        
        # Configura Bluetooth
        if not self.setup_bluetooth():
            return
        
        # Rende il dispositivo visibile
        self.make_discoverable()
        
        # Attende connessione
        if not self.wait_for_connection():
            return
        
        # Avvia il listener del mouse
        self.start_mouse_listener()
        
        print("\n🎯 Mouse Bluetooth attivo!")
        print("Muovi il mouse su questo PC per controllare l'altro dispositivo")
        print("Premi Ctrl+C per uscire")
        
        try:
            while self.connected:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nInterruzione ricevuta...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Pulisce le risorse"""
        print("Pulizia in corso...")
        
        self.stop_mouse_listener()
        
        if self.client_sock:
            self.client_sock.close()
        if hasattr(self, 'int_sock') and self.int_sock:
            self.int_sock.close()
        if self.csk:
            self.csk.close()
        if self.isk:
            self.isk.close()
        
        print("Risorse pulite")

def check_dependencies():
    """Verifica le dipendenze necessarie"""
    try:
        import bluetooth
        import pynput
        return True
    except ImportError as e:
        print(f"Dipendenza mancante: {e}")
        print("Installa le dipendenze con:")
        print("pip install pybluez pynput")
        return False

def main():
    if not check_dependencies():
        return
    
    # Verifica privilegi root per Bluetooth
    import os
    if os.geteuid() != 0:
        print("⚠️  Questo script richiede privilegi di root per Bluetooth")
        print("Esegui con: sudo python3 bt_mouse.py")
        return
    
    mouse_hid = BluetoothHIDMouse()
    mouse_hid.run()

if __name__ == "__main__":
    main()
