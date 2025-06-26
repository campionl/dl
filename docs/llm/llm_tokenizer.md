# Cos'è un Tokenizer negli LLM

## 1. Definizione

Il **tokenizer** è il modulo che trasforma il testo in **token**, cioè unità minime che il modello può leggere ed elaborare.  
I modelli di linguaggio non lavorano con parole o frasi intere, ma con questi "pezzi" codificati.

---

## 2. Cosa sono i Token?

Un **token** può essere:
- una parola intera (`"ciao"` → `ciao`)
- una parte di parola (`"gatto"` → `gat` + `to`)
- un singolo carattere (`"?"`, `","`, `#`)
- uno spazio (`" "`)

Dipende dal tipo di tokenizer usato.

---

## 3. Tipi di Tokenizer

### 3.1 Word-level (parola intera)
- Divide il testo in parole complete.
- Svantaggio: vocabolario enorme, ignora parole nuove.

### 3.2 Character-level (caratteri)
- Divide in singoli caratteri.
- Estremamente flessibile ma inefficiente: sequenze troppo lunghe.

### 3.3 Subword-level (es. BPE, SentencePiece)
- Divide le parole in parti frequenti.
- Esempio: `"impossibile"` → `im`, `poss`, `ibile`.
- Usato in modelli moderni (GPT usa **Byte Pair Encoding**, o BPE).

---

## 4. Perché è importante?

- **Efficienza**: meno token → meno lavoro per il modello.
- **Generalizzazione**: può gestire parole nuove, rare o create (tipo `"gattocane"`).
- **Lunghezza**: ogni modello ha un limite di token (es. GPT-4 ha ~128k token max), non caratteri o parole.

---

## 5. Esempio pratico

Testo: `"L'intelligenza artificiale è potente."`  
Token (semplificati):  
`["L", "'", "intelligenza", "artificiale", "è", "potente", "."]`  
Token ID (numeri per il modello):  
`[152, 39, 8813, 2204, 982, 4012, 4]`

Il modello lavora su questi numeri, non sul testo originale.

---

## 6. Tool Famosi

- **Hugging Face Tokenizers**: per modelli BERT, GPT, T5, ecc.
- **SentencePiece** (Google): usato in T5, mT5.
- **Byte-Level BPE**: usato in GPT-2/3/4, OpenAI Codex, ecc.

---

## 7. Conclusione

Il tokenizer è una delle **componenti chiave** nei modelli linguistici: una buona tokenizzazione migliora efficienza, capacità di apprendere, gestione del contesto e uso della memoria.

Capirlo è essenziale per chi sviluppa, addestra o semplicemente usa modelli LLM.

---
