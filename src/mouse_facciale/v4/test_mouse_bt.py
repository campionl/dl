#!/usr/bin/env python3

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import uuid
import subprocess
import sys
import struct
import socket
import threading
import time

class BluetoothService:
    def __init__(self):
        self.bus = dbus.SystemBus()
        try:
            self.adapter_path = "/org/bluez/hci0"
            self.adapter_obj = self.bus.get_object("org.bluez", self.adapter_path)
            self.adapter = dbus.Interface(self.adapter_obj, "org.bluez.Adapter1")
            
            # Ottieni l'indirizzo dell'adapter
            adapter_props = dbus.Interface(self.adapter_obj, "org.freedesktop.DBus.Properties")
            self.adapter_address = str(adapter_props.Get("org.bluez.Adapter1", "Address"))
            print(f"Indirizzo adapter: {self.adapter_address}")
            
            self.setup_adapter()
            self.app = MouseApplication(self.bus)
            self.hid_server = HIDServer(self.adapter_address)
        except dbus.exceptions.DBusException as e:
            print(f"Errore DBus: {e}")
            sys.exit(1)
        
    def setup_adapter(self):
        adapter_props = dbus.Interface(self.adapter_obj, "org.freedesktop.DBus.Properties")
        try:
            adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
            adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "PairableTimeout", dbus.UInt32(0))
            print("Adapter configurato: discoverable e pairable")
        except dbus.exceptions.DBusException as e:
            print(f"Avviso configurazione adapter: {e}")
        
        # Imposta la classe del dispositivo tramite bluetoothctl se possibile
        try:
            subprocess.run(["sudo", "bluetoothctl", "system-alias", "Linux Bluetooth Mouse"], 
                         check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            pass

class HIDServer:
    def __init__(self, adapter_address):
        self.control_sock = None
        self.interrupt_sock = None
        self.client_control = None
        self.client_interrupt = None
        self.running = False
        self.adapter_address = adapter_address
        
    def start_server(self):
        try:
            # Socket per control channel (PSM 17)
            self.control_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            self.control_sock.bind((self.adapter_address, 17))
            self.control_sock.listen(1)
            
            # Socket per interrupt channel (PSM 19)
            self.interrupt_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            self.interrupt_sock.bind((self.adapter_address, 19))
            self.interrupt_sock.listen(1)
            
            self.running = True
            print("Server HID avviato su PSM 17 (control) e PSM 19 (interrupt)")
            
            # Thread per gestire le connessioni
            threading.Thread(target=self.accept_connections, daemon=True).start()
            
        except Exception as e:
            print(f"Errore avvio server HID: {e}")
    
    def accept_connections(self):
        while self.running:
            try:
                print("In attesa di connessioni...")
                self.client_control, addr = self.control_sock.accept()
                print(f"Connessione control da {addr}")
                
                self.client_interrupt, addr = self.interrupt_sock.accept()
                print(f"Connessione interrupt da {addr}")
                
                # Avvia thread per gestire i dati
                threading.Thread(target=self.handle_client, daemon=True).start()
                
            except Exception as e:
                if self.running:
                    print(f"Errore accettazione connessione: {e}")
    
    def handle_client(self):
        try:
            while self.running and self.client_control and self.client_interrupt:
                # Invia report di movimento del mouse ogni secondo (per test)
                self.send_mouse_report(1, 0, 0)  # Movimento minimo a destra
                time.sleep(1)
                
        except Exception as e:
            print(f"Errore gestione client: {e}")
    
    def send_mouse_report(self, buttons, x_movement, y_movement):
        """Invia un report HID del mouse"""
        try:
            if self.client_interrupt:
                # Formato report HID per mouse: [buttons, x_movement, y_movement]
                # buttons: bit 0=left, bit 1=right, bit 2=middle
                # x_movement, y_movement: signed 8-bit (-127 to 127)
                report = struct.pack('bbb', buttons, x_movement, y_movement)
                
                # Header HID: 0xA1 (INPUT report) + report data
                hid_report = b'\xa1\x01' + report
                
                self.client_interrupt.send(hid_report)
                print(f"Inviato report mouse: buttons={buttons}, x={x_movement}, y={y_movement}")
                
        except Exception as e:
            print(f"Errore invio report: {e}")
    
    def stop_server(self):
        self.running = False
        if self.client_control:
            self.client_control.close()
        if self.client_interrupt:
            self.client_interrupt.close()
        if self.control_sock:
            self.control_sock.close()
        if self.interrupt_sock:
            self.interrupt_sock.close()

class MouseApplication(dbus.service.Object):
    def __init__(self, bus):
        self.path = "/org/bluez/mouse"
        self.bus = bus
        bus_name = dbus.service.BusName("org.bluez.mouse", bus=bus)
        dbus.service.Object.__init__(self, bus_name, self.path)
        self.agent = NoAuthAgent(bus)
        self.setup_hid_profile()

    def setup_hid_profile(self):
        try:
            profile_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/org/bluez"),
                "org.bluez.ProfileManager1"
            )
            
            uuid_hid = "00001124-0000-1000-8000-00805f9b34fb"
            
            # Prima prova a deregistrare il profilo se già esistente
            try:
                profile_manager.UnregisterProfile(self.path)
                print("Profilo HID precedente deregistrato")
            except:
                pass
            
            hid_profile = {
                "ServiceRecord": self.get_sdp_record(),
                "Role": "server",
                "RequireAuthentication": False,
                "RequireAuthorization": False,
                "AutoConnect": True,
                "Name": "Bluetooth Mouse",
                "Channel": dbus.UInt16(0),
                "PSM": dbus.UInt16(17),  # Control PSM
                "Version": dbus.UInt16(0x0100)
            }
            
            profile_manager.RegisterProfile(self.path, uuid_hid, hid_profile)
            print("Profilo HID registrato")
            
        except Exception as e:
            print(f"Errore registrazione profilo: {e}")
            # Non terminiamo il programma, proviamo a continuare

    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        print(f"Nuova connessione da {path}")
        
    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print(f"Richiesta disconnessione da {path}")
        
    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        print("Release del profilo")

    def get_sdp_record(self):
        # Record SDP corretto per un dispositivo HID (mouse)
        return """
<?xml version="1.0" encoding="UTF-8"?>
<record>
  <attribute id="0x0001">
    <sequence>
      <uuid value="0x1124"/>
    </sequence>
  </attribute>
  <attribute id="0x0004">
    <sequence>
      <sequence>
        <uuid value="0x0100"/>
        <uint16 value="0x0011"/>
      </sequence>
      <sequence>
        <uuid value="0x0011"/>
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0005">
    <sequence>
      <uuid value="0x1002"/>
    </sequence>
  </attribute>
  <attribute id="0x0006">
    <sequence>
      <uint16 value="0x656e"/>
      <uint16 value="0x006a"/>
      <uint16 value="0x0100"/>
    </sequence>
  </attribute>
  <attribute id="0x0009">
    <sequence>
      <sequence>
        <uuid value="0x1124"/>
        <uint16 value="0x0100"/>
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x000d">
    <sequence>
      <sequence>
        <sequence>
          <uuid value="0x0100"/>
          <uint16 value="0x0013"/>
        </sequence>
        <sequence>
          <uuid value="0x0011"/>
        </sequence>
      </sequence>
    </sequence>
  </attribute>
  <attribute id="0x0100">
    <text value="Linux Bluetooth Mouse"/>
  </attribute>
  <attribute id="0x0101">
    <text value="Mouse Emulator"/>
  </attribute>
  <attribute id="0x0102">
    <text value="1.0"/>
  </attribute>
  <attribute id="0x0200">
    <uint16 value="0x0100"/>
  </attribute>
  <attribute id="0x0201">
    <uint16 value="0x0111"/>
  </attribute>
  <attribute id="0x0202">
    <uint8 value="0x40"/>
  </attribute>
  <attribute id="0x0203">
    <uint8 value="0x00"/>
  </attribute>
  <attribute id="0x0204">
    <boolean value="false"/>
  </attribute>
  <attribute id="0x0205">
    <boolean value="false"/>
  </attribute>
  <attribute id="0x0206">
    <sequence>
      <sequence>
        <uint8 value="0x22"/>
        <text encoding="hex" value="05010902a1010901a1000509190129051500250175019508810205010930093109381581257f750895038106c0c0"/>
      </sequence>
    </sequence>
  </attribute>
</record>
"""

class NoAuthAgent(dbus.service.Object):
    def __init__(self, bus):
        self.path = "/test/agent"
        self.bus = bus
        dbus.service.Object.__init__(self, bus, self.path)
        
        try:
            agent_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/org/bluez"),
                "org.bluez.AgentManager1"
            )
            agent_manager.RegisterAgent(self.path, "NoInputNoOutput")
            agent_manager.RequestDefaultAgent(self.path)
            print("Agent registrato")
        except Exception as e:
            print(f"Errore registrazione agent: {e}")

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        print("Release agent")

    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel agent")

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"Authorizing service {uuid} for device {device}")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print(f"Requesting authorization for device {device}")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        print(f"Requesting PIN code for device {device}")
        raise dbus.exceptions.DBusException("org.bluez.Error.Rejected")

    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print(f"Requesting passkey for device {device}")
        raise dbus.exceptions.DBusException("org.bluez.Error.Rejected")

    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
    def DisplayPasskey(self, device, passkey):
        print(f"DisplayPasskey ({passkey})")

    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        print(f"DisplayPinCode ({pincode})")

def main():
    # Verifica dipendenze
    try:
        subprocess.run(["bluetoothctl", "--version"], check=True, stdout=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Errore: bluez non è installato o non funziona")
        sys.exit(1)
    
    # Avvia servizio Bluetooth
    try:
        subprocess.run(["sudo", "systemctl", "start", "bluetooth"], check=True)
    except subprocess.CalledProcessError:
        print("Errore: impossibile avviare il servizio Bluetooth")
        sys.exit(1)
    
    # Configura mainloop DBus
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    print("Configurazione del mouse Bluetooth...")
    try:
        service = BluetoothService()
        
        # Avvia server HID
        service.hid_server.start_server()
        
        print("Mouse Bluetooth pronto per l'associazione")
        print("Il dispositivo è discoverable e accetterà automaticamente le connessioni")
        print("Premi Ctrl+C per terminare")
        
        # Avvia mainloop
        GLib.MainLoop().run()
        
    except KeyboardInterrupt:
        print("\nInterruzione ricevuta, terminando...")
        if 'service' in locals():
            service.hid_server.stop_server()
        sys.exit(0)
    except Exception as e:
        print(f"Errore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()