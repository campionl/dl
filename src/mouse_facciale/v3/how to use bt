

# Istruzioni per l'Uso

## Installazione dipendenze (su entrambi i computer)
```bash
pip install pyautogui pynput pyobjc  # macOS richiede pyobjc
```

## Sul computer con il mouse fisico
1. Seleziona opzione 1 (SERVER)
2. Il sistema mostrerà il nome del dispositivo

## Sul computer che riceve il movimento
1. Seleziona opzione 2 (CLIENT)
2. Scegli il server dalla lista
3. Assicurati di aver effettuato il pairing Bluetooth

---

# Caratteristiche Avanzate

## Cross-Platform
- Supporto nativo per Windows, Linux e macOS
- Gestione automatica delle differenze tra sistemi operativi

## Performance Ottimizzate
- Frequenza aggiornamento 120Hz (8ms)
- Deadzone per eliminare il jitter
- Coda di invio per gestire picchi di traffico

## Funzionalità Complete
- Movimento fluido del cursore
- Supporto pulsanti (sinistro, destro, centrale)
- Scrolling verticale/orizzontale
- Gestione connessioni robusta

## Sicurezza
- Utilizza il pairing Bluetooth del sistema
- Chiusura pulita delle connessioni
- Gestione errori avanzata

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

Questo Markdown è organizzato in sezioni chiare con:
1. Titoli principali (`#`) e secondari (`##`)
2. Elenchi puntati per le istruzioni
3. Blocchi di codice per i comandi terminale
4. Evidenziazione dei parametri di configurazione con backtick (`` ` ``)
5. Separatori visivi (`---`) tra le sezioni principali
6. Struttura gerarchica per una lettura intuitiva

Puoi copiare questo testo direttamente in un file `.md` o incollarlo in qualsiasi editor che supporti Markdown.
