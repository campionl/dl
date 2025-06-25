

# Istruzioni per l'Uso

Istruzioni di utilizzo aggiornate:
Prima esecuzione:

bash
# Installa le dipendenze
pip install pyautogui pynput

# Su macOS
pip install pyobjc

# Su Linux (permessi)
sudo apt install libbluetooth-dev
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))

## Sul computer con il mouse fisico
1. Seleziona opzione 1 (SERVER)
2. Il sistema mostrerà il nome del dispositivo

## Sul computer che riceve il movimento
1. Seleziona opzione 2 (CLIENT)
2. Scegli il server dalla lista
3. Assicurati di aver effettuato il pairing Bluetooth

---

# Risoluzione Problemi Comuni

## Connessione fallita su macOS
1. Installa Xcode Command Line Tools:
```bash
xcode-select --install
```
2. Abilita "Accesso completo al disco" per il terminale

## Permessi insufficienti su Linux
```bash
sudo apt install libbluetooth-dev
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
```

## Latenza elevata
- Riduci la distanza tra i dispositivi
- Chiudi applicazioni Bluetooth pesanti (es. cuffie)
- Modifica `SEND_INTERVAL` (valori più bassi = più frequenza)

## Movimento a scatti
- Regola `DEADZONE_THRESHOLD` (valori più alti = meno sensibilità)
- Usa un mousepad con superficie uniforme
---


L'errore "bad bluetooth address" è comune nei sistemi Linux e può essere risolto seguendo questi passaggi:

### Cause principali dell'errore:
1. **Permessi insufficienti**  
2. **Driver Bluetooth non installati correttamente**  
3. **Adapter Bluetooth non rilevato**  
4. **Conflitti con altri servizi Bluetooth**

### Soluzioni passo-passo:

#### 1. Verifica lo stato del servizio Bluetooth (Linux)
```bash
sudo systemctl status bluetooth
```
Se non è attivo:
```bash
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
```

#### 2. Installa i driver necessari (Linux)
```bash
sudo apt update
sudo apt install bluez bluez-tools libbluetooth-dev
```

#### 3. Configura i permessi
```bash
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
```

#### 4. Verifica l'indirizzo Bluetooth del sistema
```bash
hciconfig
```
Dovresti vedere un output simile:
```
hci0:	Type: Primary  Bus: USB
	BD Address: 00:1A:7D:DA:71:13  ACL MTU: 310:10  SCO MTU: 64:8
	UP RUNNING PSCAN ISCAN
```

#### 5. Abilita l'adapter
```bash
sudo hciconfig hci0 up
```

### Passaggi aggiuntivi per Windows:

1. **Abilita il servizio Bluetooth**:
   - Premi `Win + R` → `services.msc`
   - Cerca "Bluetooth Support Service"
   - Imposta "Tipo di avvio" su "Automatico"
   - Riavvia il servizio

2. **Aggiorna i driver**:
   - Device Manager → Bluetooth
   - Click destro → "Update driver"

### Dopo queste modifiche:

1. **Riavvia entrambi i computer**
2. **Esegui il pairing prima di avviare lo script**:
   - Connetti i due computer via Bluetooth dalle impostazioni di sistema
   - Accetta la richiesta di pairing su entrambi i dispositivi
3. **Avvia prima il server, poi il client**

### Se il problema persiste:

1. Prova a cambiare la porta:
```python
# Modifica la porta da 4 a un valore tra 1-30
PORT = 8
```

2. Disabilita temporaneamente firewall:
```bash
# Linux
sudo ufw disable

# Windows
netsh advfirewall set allprofiles state off
```
