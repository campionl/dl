# Glossario dei Termini Chiave sugli LLM

---

### **LLM** (Large Language Model)
**Modello** di intelligenza artificiale addestrato su enormi quantità di **testo** per comprendere e generare *linguaggio naturale*.

---

### *Transformer*
**Architettura** alla base dei moderni LLM. Usa il meccanismo di **attenzione** per gestire *relazioni tra parole* in modo efficiente, anche a distanza.

---

### *Token*
*Unità base di input* per un LLM. Può essere una parola intera, parte di parola o anche punteggiatura.  
Esempio: “ChatGPT è forte.” → [Chat, GPT, è, forte, .] → 5 token.

---

### *Pretraining*
Fase in cui il modello viene addestrato su testi generici per "imparare il linguaggio". Non è ancora specializzato.

---

### *Fine-tuning*
Fase di specializzazione. Il modello viene "rifinito" su compiti specifici (es. medicina, legge, chatbot, ecc.).

---

### *Prompt*
Il testo che dai in **input** al modello.  
Esempio: `Scrivi una poesia su un drago.` → il prompt guida l’output del modello.

---

### *Zero-shot / Few-shot*
- **Zero-shot**: il modello risponde senza esempi.  
- **Few-shot**: riceve 1–3 esempi per capire il tipo di risposta attesa.

---

### **RLHF** (Reinforcement Learning from Human Feedback)
*Tecnica di addestramento* dove gli umani valutano le risposte del modello e lo guidano a migliorare usando rinforzo.

---

### *Contesto*
La quantità di token che un modello può "tenere a mente" per generare output coerente.  
Esempio: GPT-4 Turbo → 128.000 token di contesto.

---

### *Hallucination*
Quando il modello inventa risposte false ma convincenti.  
Esempio: dire che Napoleone è nato in Germania = allucinazione.

---

### *Multimodale*
Capacità del modello di gestire più tipi di input: **testo, immagini, audio, video**, ecc.

---

### **MoE** (Mixture of Experts)
Tecnica in cui solo una parte del modello si attiva a ogni input, rendendo tutto più efficiente (es. Mixtral).

---

### *Allineamento* (Alignment)
Processo per far sì che un modello AI rispetti valori umani, etica e intenzioni dell'utente.  
Molto discusso in campo sicurezza AI.

---

### *Open-source*
Modelli il cui codice e pesi sono pubblici e riutilizzabili liberamente (es. Mistral, LLaMA, BLOOM).

---

### *Closed-source*
Modelli proprietari con codice e dati nascosti (es. GPT-4, Claude, Gemini).