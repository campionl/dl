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
graph TD
    A1[📘 FASE 1: TRAINING] --> A2[📥 INPUT<br>• Testi in linguaggio naturale<br>• Tokenizzazione<br>• Embedding numerico]
    A2 --> A3[⚙️ ELABORAZIONE<br>• Transformer con self-attention<br>• Previsione del token successivo<br>• Calcolo errore]
    A3 --> A4[🔁 BACKPROPAGATION<br>• Aggiornamento pesi<br>• Ottimizzazione (es: Adam)]
    A4 --> A5[✅ OUTPUT<br>• Probabilità dei token<br>• Nessun testo generato, solo apprendimento]

    B1[💬 FASE 2: INFERENZA] --> B2[📥 INPUT<br>• Prompt utente<br>• Tokenizzazione<br>• Embedding]
    B2 --> B3[⚙️ ELABORAZIONE<br>• Transformer con pesi già appresi<br>• Previsione token successivo]
    B3 --> B4[🔁 LOOP<br>• Aggiunta token generato al contesto<br>• Nuova previsione]
    B4 --> B5[📤 OUTPUT<br>• Token generati → Testo leggibile<br>• Risposta del modello]

    style A1 fill:#c2f0c2,stroke:#333,stroke-width:2
    style B1 fill:#cce5ff,stroke:#333,stroke-width:2

```

---
