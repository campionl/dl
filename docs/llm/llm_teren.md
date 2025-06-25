# Processo di Apprendimento dei Large Language Models (LLM)

## 1. Raccolta del Dataset
- **Obiettivo**: Fornire una base linguistica e conoscitiva al modello.
- **Contenuto**:
  - Libri, articoli, siti web, forum, codice sorgente, ecc.
  - Dati multilingua e multiformato (testo, codice, ecc.).
- **Pulizia**:
  - Rimozione di dati tossici, duplicati, spam, contenuti sensibili o inutili.

---

## 2. Tokenizzazione
- **Cos'è**: Suddividere il testo in unità chiamate _token_ (parole, sottoparole o caratteri).
- **Motivo**: I modelli lavorano sui token, non sul testo grezzo.
- **Tipo**:
  - Byte Pair Encoding (BPE)
  - SentencePiece (in alcuni modelli)

---

## 3. Pre-Addestramento (Pretraining)
- **Metodo principale**: Apprendimento auto-supervisionato.
- **Tecnica comune**: _Masked Language Modeling_ o _Causal Language Modeling_.
- **Obiettivo**: 
  - Imparare le strutture linguistiche, la sintassi, il contesto e il significato.
  - Esempio: "Il gatto __ sul tappeto." → Predire "dorme".

### Architettura usata
- **Transformer** (introduzione nel paper “Attention is All You Need”):
  - Struttura a strati.
  - Meccanismo di attenzione (self-attention).
  - Encoder (a volte) e Decoder (sempre nei LLM autoregressivi).

---

## 4. Fine-Tuning (Ottimizzazione Finita)
- **Cos'è**: Allenamento ulteriore su dataset più piccoli e mirati.
- **Motivo**: Specializzare il modello per compiti specifici (es. assistenza, codice, medicina).
- **Tecniche usate**:
  - Supervisione classica (con etichette).
  - _Reinforcement Learning from Human Feedback (RLHF)_.

---

## 5. Reinforcement Learning from Human Feedback (RLHF)
- **Fasi**:
  1. **Generazione di output** da parte del modello.
  2. **Feedback umano** o tramite modelli di preferenza.
  3. **Ottimizzazione**: usare il feedback per premiare o penalizzare risposte (tramite Proximal Policy Optimization - PPO).
- **Scopo**: Rendere il modello più utile, sicuro e allineato ai valori umani.

---

## 6. Valutazione e Deployment
- **Valutazione**:
  - Metriche automatiche (perplessità, accuratezza).
  - Test umani (qualità delle risposte).
  - Test di sicurezza e bias.
- **Deployment**:
  - Ottimizzazione per latenza.
  - Hosting su cloud, API, dispositivi locali.
  - Aggiornamenti e monitoraggio in tempo reale.

---

## Riassunto Fasi
1. Raccolta e pulizia dati
2. Tokenizzazione
3. Pretraining (linguaggio generale)
4. Fine-tuning (specializzazione)
5. RLHF (ottimizzazione comportamentale)
6. Valutazione e messa in produzione

---

## Curiosità
- **Addestramento**: richiede settimane/mesi, centinaia di GPU/TPU e milioni di euro.
- **Dataset**: può arrivare a centinaia di miliardi di token.
- **Capacità**: i modelli più avanzati (come GPT-4) superano i 100 miliardi di parametri.

