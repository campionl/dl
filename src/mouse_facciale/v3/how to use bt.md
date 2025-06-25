

# Istruzioni per l'Uso

Istruzioni di utilizzo aggiornate:
Prima esecuzione:

bash
# Installa le dipendenze
pip install pyautogui pynput

# Su macOS
pip install pyobjc

# Su Linux (permessi)
```bash
sudo apt install libbluetooth-dev
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
```
Per Arch Linux (in sostituzione di apt):
```bash
# Installa i pacchetti necessari
sudo pacman -S bluez bluez-utils python-pybluez

# Abilita e avvia il servizio Bluetooth
sudo systemctl enable --now bluetooth.service

# Verifica lo stato del servizio
sudo systemctl status bluetooth

# Configura i permessi per Python
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
```

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


L'errore `module "socket" has no attribute 'AF_BLUETOOTH'` indica che Python sul tuo sistema Arch non è stato compilato con il supporto per i socket Bluetooth. Ecco come risolvere:



### Modifiche chiave per Arch Linux:

1. **Supporto migliorato per PyBluez**:
   - Aggiunto fallback a `bluetooth.BluetoothSocket` quando `socket.AF_BLUETOOTH` non è disponibile
   - Gestione uniforme dei socket indipendentemente dall'implementazione

2. **Ottenimento indirizzo Bluetooth per Arch**:
   - Implementato metodo specifico usando `bluetoothctl list`
   - Formattazione corretta dell'indirizzo MAC

3. **Scoperta dispositivi ottimizzata**:
   - Utilizzo diretto di PyBluez per la scansione dispositivi
   - Migliore gestione degli errori

### Passaggi di installazione per Arch Linux:

```bash
# Installa le dipendenze necessarie
sudo pacman -S bluez bluez-utils python-pip

# Installa i pacchetti Python
pip install pyautogui pynput pybluez

# Configura i permessi Bluetooth
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))

# Abilita e avvia il servizio Bluetooth
sudo systemctl enable --now bluetooth.service

# Verifica lo stato
bluetoothctl --version
hciconfig
```

### Se persiste l'errore:

1. **Installa bluez-libs**:
   ```bash
   sudo pacman -S bluez-libs
   ```

2. **Ricompila PyBluez**:
   ```bash
   pip uninstall -y pybluez
   pip install git+https://github.com/pybluez/pybluez.git
   ```

3. **Verifica l'installazione**:
   ```python
   python -c "import bluetooth; print(bluetooth.__version__)"
   ```

### Note importanti:

1. Su Arch Linux, assicurati di aver abilitato il controller Bluetooth:
   ```bash
   sudo rfkill unblock bluetooth
   sudo hciconfig hci0 up
   ```

2. Se usi un ambiente virtuale, assicurati di avere i permessi necessari:
   ```bash
   sudo setcap 'cap_net_raw,cap_net_admin+eip' /percorso/venv/bin/python3
   ```

3. Per debugging avanzato:
   ```bash
   # Monitora i servizi Bluetooth
   journalctl -u bluetooth -f

   # Lista dispositivi
   bluetoothctl devices
   ```

Questo codice risolve il problema specifico di Arch Linux con i socket Bluetooth e fornisce un'implementazione robusta per tutte le piattaforme principali.
