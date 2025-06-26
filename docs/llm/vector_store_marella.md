# **Vector Store**

## **Cosa sono?**  
I **Vector Store** (o "archivi di vettori") sono come dei **magazzini digitali** che contengono informazioni sotto forma di **numeri** (chiamati **vettori**). Questi numeri rappresentano il significato di parole, frasi o documenti in un modo che i computer possono capire e confrontare facilmente.  

Immagina di dover cercare un libro in una biblioteca: invece di sfogliare ogni pagina, un Vector Store ti permette di trovare libri **simili** tra loro in base al loro contenuto, grazie a questi "numeri magici" (vettori).  

## **A cosa servono?**  
- **Ricerca intelligente**: trovare testi simili anche se non contengono le stesse parole (es. *"cane"* e *"cucciolo"* possono essere vicini nel vettore).  
- **Chatbot e assistenti virtuali**: per dare risposte più accurate basate su conoscenze memorizzate.  
- **Raccomandazioni**: come quando Netflix o Spotify ti suggeriscono contenuti simili a quelli che ti piacciono.  

## **Come si costruisce un Vector Store?**    

### **1. Creare gli embeddings (i "vettori")**  
- Un **embedding** è una sequenza di numeri che rappresenta il significato di un testo.  
- Si usano modelli come **Word2Vec**, **GloVe**, o più moderni come **BERT** e **OpenAI Embeddings** per trasformare parole/frasi in numeri.  
- Esempio:  
  - Frase: "Il gatto è sul divano" → Diventa un vettore come `[0.24, -0.57, 0.89, ...]` (centinaia di numeri!).  

### **2. Salvare i vettori in un database speciale**  
- I normali database (come MySQL) non sono ottimizzati per cercare vettori. Si usano invece:  
  - **Vector Database**: come Pinecone, Weaviate, Milvus, FAISS (di Facebook).  
  - **Strumenti semplici**: anche librerie come Annoy o ScaNN possono aiutare.  

### **3. Fare ricerche per somiglianza**  
- Quando cerchi qualcosa (es. *"animale domestico peloso"*), il sistema:  
  1. Trasforma la tua domanda in un **vettore**.  
  2. Confronta questo **vettore** con quelli nel database.  
  3. Ti restituisce i testi con i vettori **più vicini** (es. documenti che parlano di "gatti" o "cani").  

---

### **Esempio Pratico**  
Se volessi costruire un Vector Store per un assistente che risponde a domande su film:  
1. **Raccogli testi**: schede di film (trame, generi, attori).  
2. **Genera embeddings**: usa un modello come OpenAI Embeddings per trasformare ogni trama in un vettore.  
3. **Salva in un Vector DB**: inserisci tutti i vettori in Pinecone o FAISS.  
4. **Interroga il DB**: quando un utente chiede "film d'amore con attori famosi", il sistema trova i vettori più vicini e suggerisce "Titanic" o "Notting Hill".  

## **Costo Computazionale**   

Creare un Vector Store ha tre fasi principali, ognuna con un suo impatto computazionale:  

1. **Generazione degli embeddings** (da testo a vettori)  
2. **Indicizzazione dei vettori** (per renderli ricercabili)  
3. **Querying** (ricerca nel Vector Store)

## **1. Generazione degli Embeddings (la parte più costosa)**  
Questa fase trasforma testi in vettori numerici. Il costo dipende da:  

### **A. Modello di Embedding Usato**  
- **Modelli leggeri** (*es. Word2Vec, GloVe, SentenceTransformers*):  
  - **Basso costo**, possono girare su **CPU**.  
  - *Esempio*: 10.000 frasi generati con *`all-MiniLM-L6-v2`* (modello efficiente) → **pochi secondi/minuti su un laptop**.  
  - **Costo GPU**: quasi **nullo** (va bene anche solo la CPU).  

- **Modelli pesanti** (*es. OpenAI `text-embedding-3-large`, BERT, Cohere*):  
  - Richiedono GPU o API a pagamento.  
  - Esempio:  
    - OpenAI Embeddings: **~$1 ogni 10.000 pagine** (prezzo: $0,10 per 1M token).  
    - Modelli locali come `BAAI/bge-large` → necessitano di una GPU (es. NVIDIA T4, ~$0,50/ora su cloud).  

### **B. Lunghezza del Testo**  
- Più lungo è il testo, più token devono essere elaborati (aumento lineare del costo).  
- Esempio:  
  - 1.000 documenti da **100 parole** → ~10 secondi (CPU).  
  - 1.000 documenti da **10.000 parole** → ~10 minuti (CPU) o pochi secondi (GPU).  

### **C. Batch Processing (elaborare più testi insieme)**  
- Se possibile, processare più documenti in batch riduce il tempo totale.  
- Esempio:  
  - Senza batch: 1.000 documenti uno alla volta → **10 minuti**.  
  - Con batch (es. 100 alla volta) → **1 minuto**.  

---

## **2. Indicizzazione dei Vettori (organizzarli per la ricerca)**  
Una volta creati gli embeddings, vanno organizzati in strutture efficienti per la ricerca.  

### **A. Algoritmi di Indicizzazione**  
- **FAISS** (Facebook AI Similarity Search):  
  - Richiede **O(n log n)** tempo per costruire l’indice (n = numero di vettori).  
  - Esempio: 1 milione di vettori → **pochi minuti su CPU, secondi su GPU**.  
- **HNSW** (Hierarchical Navigable Small World):  
  - Più veloce per indicizzazione, ma occupa più memoria.  
  - Esempio: 1M vettori → **~5-10 minuti su CPU**.  
- **Pinecone/Weaviate** (cloud):  
  - Loro gestiscono l’indicizzazione, paghi in base all’uso.  

### **B. Memoria Necessaria**  
- Dipende dalla **dimensione dei vettori** e dal **numero di vettori**.  
- Esempio:  
  - 1 milione di vettori da 768 dimensioni (float32) →  
    - **~3 GB** in memoria (768 × 4 byte × 1M = 3.072 MB).  
  - Se compressi (es. con **quantizzazione a 8-bit**), si riduce a **~0,75 GB**.  

---

## **3. Querying (ricerca nel Vector Store)**  
Una volta costruito, interrogare il Vector Store ha un costo minimo:  

- **Tempo di ricerca**:  
  - FAISS/HNSW: **O(log n)** → quasi istantaneo anche con milioni di vettori.  
  - Senza indicizzazione: **O(n)** (scansione lineare, lento per grandi dataset).  
- **Costo Cloud**:  
  - Pinecone: ~$0,50 per 1.000 query (se usi il tier pay-as-you-go).  

---

## **Esempio di Costo Totale**  
Supponiamo di voler creare un Vector Store con:  
- **100.000 documenti** (1.000 parole ciascuno).  
- **Embedding model**: `all-MiniLM-L6-v2` (locale, gratuito).  

### **Fase 1: Generazione Embeddings**  
- **Tempo**: ~2 ore su CPU, ~10 minuti con GPU.  
- **Costo**: $0 (se locale), ~$0,50 se usi una GPU cloud per 1 ora.  

### **Fase 2: Indicizzazione con FAISS**  
- **Tempo**: ~5 minuti (CPU).  
- **Memoria**: ~300 MB (100K vettori da 384 dimensioni).  

### **Fase 3: Querying**  
- **Tempo per query**: ~10 ms (istantaneo per l’utente).  

### **Costo Alternativo con OpenAI Embeddings**  
- **Generazione embeddings**: $0,10 per 1M token → ~$10 (100K doc × 1K parole ≈ 100M token).  
- **Pinecone per storage**: ~$50/mese per 1M vettori.  

---

## **Riassunto dei Costi**  
| Fase | Costo Computazionale | Memoria Occupata |  
|------|----------------------|------------------|  
| **Generazione embeddings** | Da gratis (CPU) a $10+ (API/GPU) | Temporaneo (solo durante l'elaborazione) |  
| **Indicizzazione** | Minuti su CPU, secondi su GPU | 0,3 GB - 6 GB per 1M vettori |  
| **Querying** | Quasi zero (microsecondi) | Dipende dall'indice (FAISS/Pinecone) |