##  **1. FASE DI APPRENDIMENTO (TRAINING)**

> Il modello impara dai dati (es. libri, articoli, siti, codice…)

###  COSA AVVIENE IN FASE DI INPUT?

* I testi vengono **spezzati in "token"** (piccoli pezzi di parole, simili a sillabe o parole intere).
* Ogni token viene convertito in un **numero** (tramite un vocabolario chiamato tokenizer).
* Questi numeri vengono trasformati in **vettori** (array di numeri) tramite **embedding**, cioè una rappresentazione matematica dello “spazio del significato”.

###  COSA AVVIENE IN FASE DI ELABORAZIONE?

* I token trasformati in vettori entrano nel **modello Transformer**, che è composto da molti **strati (layers)**.
* Ogni strato applica operazioni come:

  * **Attenzione (Self-Attention)** → il modello valuta quali parole sono importanti per capire il contesto.
  * **Somme, moltiplicazioni, pesi e bias** → il modello fa calcoli matematici per aggiornare le sue rappresentazioni.
* Alla fine, il modello **prevede il prossimo token** (es: “Il gatto mi…” → “a”, “a”, “o”?).
* Viene calcolata l’**errore** tra ciò che il modello ha previsto e la parola vera.
* Questo errore serve per **aggiornare i pesi** del modello usando **backpropagation** e **ottimizzazione (es: Adam)**.

###  COSA AVVIENE IN FASE DI OUTPUT?

* L'output è la **probabilità** di ogni parola possibile (es: 80% “miao”, 15% “ama”, 5% “morde”).
* Ma durante l'addestramento, non si genera davvero testo: si usa l'output solo per **correggere il modello** e migliorarlo.
* Dopo milioni di testi, il modello “impara” quali parole seguono meglio altre, capisce la **struttura della lingua**, nozioni di logica, stile, ecc.

---

##  **2. FASE DI INFERENZA (QUANDO GLI MANDI UN PROMPT)**

> Il modello è già addestrato e lo stai usando per generare un output

###  COSA AVVIENE IN FASE DI INPUT?

* Il tuo testo viene convertito in token (es: “ciao” → `[1342]`, “come” → `[229]`...).
* I token sono trasformati in **embedding** (come nel training).
* Questi vettori entrano nel modello pre-addestrato.

###  COSA AVVIENE IN FASE DI ELABORAZIONE?

* Il modello passa i vettori nei suoi strati Transformer, **usando i pesi che ha imparato** durante il training.
* Calcola **quale token è più probabile come prossimo passo** nel testo.
* Ripete il processo token per token: ogni nuova parola generata viene aggiunta al prompt e rielaborata per generare la successiva.

###  COSA AVVIENE IN FASE DI OUTPUT?

* Il modello restituisce **uno o più token** (che sono numeri).
* Questi token vengono **riconvertiti in testo leggibile** tramite il tokenizer inverso.
* Il risultato è quello che leggi come risposta del modello.

---

##  ESEMPIO PRATICO SEMPLIFICATO

Immagina di inviare questo prompt:
**"Il Sole è una"**

### Durante il training (fatto in passato):

* Il modello ha visto frasi simili e ha imparato che “stella” ha alta probabilità dopo “Il Sole è una”.

### Durante l’uso (inference):

* Input: `"Il Sole è una"` → tokenizzato → elabora → genera `"stella"`.

---

##  Come il modello "impara a fare matematica"?

Anche se non ha visto direttamente formule, ha letto moltissimi testi dove si parlava di numeri, calcoli, problemi logici.
Quindi, **non “fa i calcoli” come una calcolatrice**, ma **imita il comportamento** che ha visto spesso in quei testi.
Per problemi semplici (tipo 2 + 2) è affidabile.
Per problemi più complessi, può sbagliare — proprio perché **non capisce la matematica come un umano o un software matematico, ma la simula statisticamente.**

---

```mermaid  
flowchart TD
    A[FASE DI APPRENDIMENTO (Training)] --> B[Input]
    A --> C[Elaborazione]
    A --> D[Output]
    E[FASE DI INFERENZA (Inference)] --> F[Input]
    E --> G[Elaborazione]
    E --> H[Output]

    %% Training Phase
    B --> B1["Testo originale (e.g., libri, codice)"]
    B --> B2["Tokenizzazione (spezzare in 'token')"]
    B --> B3["Embedding (token → vettori numerici)"]
    
    C --> C1["Transformer Layers"]
    C1 --> C1a["Self-Attention (pesi delle parole)"]
    C1 --> C1b["Calcoli matematici (pesi, bias)"]
    C1 --> C1c["Predizione del token successivo"]
    C --> C2["Backpropagation (aggiornamento pesi)"]
    
    D --> D1["Probabilità dei token (e.g., 80% 'miao')"]
    D --> D2["Nessun testo generato: solo ottimizzazione"]

    %% Inference Phase
    F --> F1["Prompt utente (e.g., 'Il Sole è una')"]
    F --> F2["Tokenizzazione + Embedding"]
    
    G --> G1["Transformer Layers (pesi fissi)"]
    G1 --> G1a["Self-Attention (contesto)"]
    G1 --> G1b["Generazione token step-by-step"]
    
    H --> H1["Decoding (token → testo)"]
    H --> H2["Risposta generata (e.g., 'stella')"]

    %% Esempio Matematico
    I["Esempio: Matematica"] --> I1["Training: Ha visto '2+2=4' in molti testi"]
    I --> I2["Inference: Simula la risposta (non calcola)"]
```

---
