## **Cos’è un Raspberry Pi?**

Il Raspberry Pi è un **microcomputer** delle dimensioni di una carta di credito, economico e versatile. Si collega a monitor, tastiera, mouse e funziona come un PC, ma consuma pochissima energia.

---

## **1. Scegli il tuo modello**

### I più recenti (2024-2025):

* **Raspberry Pi 5** → ultra potente (fino a 8GB RAM), perfetto per AI e media
* **Raspberry Pi 4** → ottimo per progetti generici e server locali
* **Raspberry Pi Zero 2 W** → minuscolo, ideale per progetti compatti (tipo droni o AI portatile)

Ti consiglio il **Pi 4 (4GB o 8GB)** se vuoi fare AI, coding e automazione.

---

## **2. Cosa ti serve per iniziare**

| Componente         | Dettagli                                     |
| ------------------ | -------------------------------------------- |
| Raspberry Pi       | Il modello scelto (es. Pi 4)                 |
| Scheda microSD     | Almeno 32GB Classe 10 (più veloce = meglio)  |
| Alimentatore       | Ufficiale Pi 5 (27W USB-C) o Pi 4 (5V 3A)    |
| Case + dissipatore | Per evitare surriscaldamenti                 |
| Cavi HDMI          | Mini-HDMI (Pi 4) → HDMI standard per monitor |
| Tastiera/mouse     | USB o wireless                               |
| Connessione        | Ethernet o WiFi                              |

---

## **3. Installa il sistema operativo (Raspberry Pi OS)**

### Opzione A – **Metodo semplice via Raspberry Pi Imager**

1. Scarica **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)**
2. Inserisci la microSD nel PC
3. Seleziona:

   * OS: “Raspberry Pi OS (64-bit)”
   * Storage: microSD
   * Opzioni: puoi preconfigurare WiFi, username, password
4. Scrivi sulla microSD
5. Inserisci la SD nel Pi e avvialo!

### Opzione B – Immagine manuale (per sistemi diversi come Ubuntu Server o Kali Linux)

1. Scarica l'immagine ISO del sistema
2. Usa Balena Etcher per scriverla sulla microSD

---

## **4. Prime configurazioni**

Una volta avviato il Pi:

* Configura **WiFi, layout tastiera, fuso orario**

* Aggiorna tutto:

  ```bash
  sudo apt update && sudo apt full-upgrade -y
  ```

* Abilita SSH se vuoi accedere da remoto:

  ```bash
  sudo raspi-config → Interfacing Options → SSH → Enable
  ```

---

## **5. Cosa puoi fare con il tuo Raspberry Pi?**

### Progetti base:

* Web server (con Flask o Node.js)
* Media center (Kodi o Plex)
* NAS (server di backup personale)
* VPN personale (con PiVPN)
* Automazione casa (Home Assistant)

### Progetti AI:

* Assistente vocale locale (Mycroft AI o Voice2Command)
* Riconoscimento facciale con OpenCV
* Oggetto smart che reagisce a suoni/gesti
* TensorFlow Lite + Coral USB accelerator per modelli AI

---

## **6. Linguaggi e tool utili**

* **Python** (principale per Raspberry)
* **Bash** (script di sistema)
* **GPIO Zero**: controlla LED, motori, sensori
* **OpenCV**: visione artificiale
* **Flask / FastAPI**: interfacce web
* **Node-RED**: automazione visuale

---

## **7. GPIO: collegare sensori e attuatori**

I **GPIO** sono pin fisici che puoi usare per controllare luci, leggere pulsanti, sensori, ecc.

Esempio: accendere un LED

```python
from gpiozero import LED
from time import sleep

led = LED(17)

while True:
    led.on()
    sleep(1)
    led.off()
    sleep(1)
```

Puoi creare:

* Allarmi
* Sensori di movimento
* Robot
* Bracci meccanici
* ...e qualsiasi cosa tu possa immaginare

---

## **8. Idee per progetti concreti**

| Nome progetto         | Descrizione                               |
| --------------------- | ----------------------------------------- |
| AI clone assistant | Assistente vocale AI custom, offline      |
| Smart room         | Luci, ventole e allarmi controllati da AI |
| Retro console      | Emulatore console (RetroPie)              |
| Pi-Cam con AI      | Sorveglianza + riconoscimento facce/gatti |
| Mini robot         | Robot con webcam e AI che evita ostacoli  |
| Stazione meteo    | Rileva temperatura, umidità, pressione    |

---

## Vuoi approfondire?

* Tutorial ufficiale Raspberry Pi: [raspberrypi.org](https://www.raspberrypi.com/)
* Libro consigliato: *Raspberry Pi User Guide* – Eben Upton (creatore)
* Corsi YouTube consigliati:

  * “Raspberry Pi for Beginners” – The Raspberry Pi Guy
  * “Raspberry Pi Projects” – Tech With Tim

---

## Vuoi che ti prepari un progetto chiavi in mano?

Posso farti:

* Una demo con codice Python
* Una guida passo-passo con schema GPIO
* Un’idea di AI originale integrata

Ti andrebbe qualcosa a tema **Digimon / Anime / Cloni / Tempo**? Posso unire queste cose in un progetto Raspberry AI. Fammi sapere!
