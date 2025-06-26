# Vector store
## Cos'è

Un **Vector Store** (in italiano: archivio di vettori) è come una **memoria intelligente** usata nei modelli linguistici (LLM), ad esempio ChatGPT, per ricordare informazioni che non conosce in partenza.

In pratica:
- Un testo (frase, paragrafo o documento) viene trasformato in un **vettore**, cioè una lista di numeri che ne rappresentano il **significato**.
- Anche una domanda dell’utente viene trasformata in un vettore.
- Il sistema **confronta** il vettore della domanda con quelli salvati e restituisce i testi più simili per contenuto.

È un po' come cercare un libro in biblioteca usando il significato della trama, non il titolo esatto.

## A cosa serve

- **Ricerca intelligente**: trova testi simili anche se non usano le stesse parole.
- **Chatbot più precisi**: rispondono su contenuti esterni (es. documenti caricati).
- **Raccomandazioni**: come Netflix o Spotify che suggeriscono contenuti simili a quelli che ti piacciono.

## Come si crea

### 1 - Generazione degli embeddings
- Un **embedding** è un vettore che rappresenta un testo.
- Modelli usati: `Word2Vec`, `GloVe`, `BERT`, `all-MiniLM-L6-v2`, `OpenAI Embeddings`, ecc.
- Esempio:  
  Frase "Il gatto è sul divano" → `[0.24, -0.57, 0.89, ...]` (centinaia di numeri!)

### 2 - Salvataggio dei vettori
- Si usano **database speciali** (Vector Database), non i classici SQL.
- Esempi: `FAISS`, `Qdrant`, `Pinecone`, `Weaviate`, `Milvus`.

### 3 - Ricerca per somiglianza
- La tua richiesta viene convertita in un vettore.
- Il sistema cerca nel database i vettori più **vicini**.
- Restituisce i testi associati a quei vettori.

---

## Tecniche di divisione del testo

Per migliorare la qualità delle ricerche, i documenti vengono divisi in **blocchi (chunk)**. Esistono diversi metodi:

- **Chunking semplice**: divide in paragrafi o sezioni. Facile, ma può perdere contesto.
- **Sliding Window**: i blocchi si sovrappongono, migliorando il contesto ma aumentando il numero di vettori.
- **Clustering semantico**: raggruppa parti simili prima di creare i vettori (più preciso, ma complesso).
- **Prompt-to-vector diretto**: trasforma direttamente la domanda in un vettore da confrontare.

---

## Costo computazionale

### 1 - Generazione degli embeddings
È la parte più costosa, dipende da:
- **Modello usato**:
  - Modelli leggeri (es. `MiniLM`, `Word2Vec`): gratis, girano anche su un portatile.
  - Modelli pesanti (es. `OpenAI`): più precisi, ma costosi e richiedono GPU o cloud.
- **Lunghezza del testo**: più parole = più tempo e memoria.
- **Batch processing**: processare più testi insieme riduce i tempi.

Esempi:
- `all-MiniLM-L6-v2` su 10.000 testi: pochi minuti su CPU.
- `text-embedding-3-small` di OpenAI: ~$0,00002 per 1.000 token (circa 750 parole).

### 2 - Indicizzazione
Serve per cercare in modo veloce:
- Strumenti come `FAISS` o `HNSW` costruiscono **indici** ottimizzati.
- Costruire l’indice per 1 milione di vettori richiede pochi minuti su CPU, secondi su GPU.

### 3 - Ricerca
Una volta costruito tutto:
- La ricerca è **molto veloce**: da 5 a 200 millisecondi, anche con milioni di vettori.
- Costi bassi, anche su cloud (es. $0,50 per 1.000 query su Pinecone).

## Dimensioni e memoria

Un vector store occupa spazio in base a:
- **Numero di vettori**
- **Lunghezza dei vettori** (es. 384 o 1536 dimensioni)
- **Formato dei dati** (es. float32 = 4 byte per numero)

Esempi:
- 100.000 paragrafi:
  - Con MiniLM (384 dimensioni): ~150 MB
  - Con OpenAI (1536 dimensioni): ~600 MB
- Aggiungendo metadati e indici, può arrivare a 200 MB – 3 GB.
- Progetti aziendali arrivano anche a decine o centinaia di GB.

Per lavorare bene:
- Usa **SSD** e almeno **8–16 GB di RAM**.
- I modelli leggeri funzionano bene anche su PC di fascia media.