import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity

# Check if sentence_transformers is available, provide fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: sentence_transformers not available. Install with: pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# 1. Definizione dei documenti (italiano e inglese)
documenti = [
    # Animali terrestri
    "Il gatto si arrampica sull'albero",
    "Il cane abbaia nel giardino", 
    "Il leone ruggisce nella savana",
    "Il ghepardo è l'animale terrestre più veloce",
    "L'orso cerca pesci nei fiumi",
    "The elephant is the largest land mammal",
    "Tigers are powerful predators in the jungle",
    "Wolves hunt in packs across the forest",
    "Giraffes are the tallest animals on Earth",
    
    # Animali acquatici
    "Il delfino nuota velocemente nel mare",
    "La balena è il mammifero più grande del mondo",
    "Lo squalo è un predatore marino temibile",
    "Le meduse galleggiano negli oceani",
    "I pinguini sono uccelli acquatici che non volano",
    "Whales migrate thousands of miles across oceans",
    "Dolphins are intelligent marine mammals",
    "Sharks are apex predators in the sea",
    "Octopuses are highly intelligent sea creatures",
    "Sea turtles navigate vast ocean distances",
    
    # Animali volanti
    "L'aquila vola alta nel cielo",
    "Il pappagallo imita la voce umana",
    "I colibrì battono le ali molto velocemente",
    "Eagles soar high above mountains",
    "Owls are nocturnal hunters with excellent vision",
    "Swallows migrate across continents",
    
    # Tecnologia e programmazione
    "Programmare in Python è divertente",
    "I neural network sono rivoluzionari", 
    "Sviluppare applicazioni AI è complesso",
    "I modelli linguistici sono potenti",
    "Machine learning richiede grandi quantità di dati",
    "Deep learning utilizza reti neurali profonde",
    "Python is a versatile programming language",
    "Artificial intelligence transforms industries",
    "Neural networks learn from data patterns",
    "Natural language processing enables human-computer interaction",
    "Computer vision recognizes images and objects",
    "Reinforcement learning teaches agents through trial and error",
    
    # Natura e ambiente
    "La foresta pluviale è ricca di biodiversità",
    "I deserti sono ambienti estremi e aridi",
    "Le montagne offrono paesaggi mozzafiato",
    "Rainforests are the lungs of our planet",
    "Coral reefs are underwater ecosystems",
    "Mountains provide fresh water sources",
    "Deserts showcase nature's resilience",
    
    # Scienza e ricerca
    "La fisica quantistica studia il mondo subatomico",
    "L'astronomia esplora l'universo e le stelle",
    "La biologia marina studia la vita negli oceani",
    "Quantum physics reveals the nature of reality",
    "Astronomy explores distant galaxies and stars",
    "Marine biology studies ocean life forms",
    "Genetics unlock the secrets of DNA"
]

def create_simple_embeddings(texts):
    """
    Fallback function to create simple word-based embeddings
    when sentence_transformers is not available
    """
    from collections import Counter
    import re
    
    # Create vocabulary from all texts
    vocab = set()
    processed_texts = []
    for text in texts:
        words = re.findall(r'\w+', text.lower())
        processed_texts.append(words)
        vocab.update(words)
    
    vocab = sorted(list(vocab))
    vocab_size = len(vocab)
    word_to_idx = {word: i for i, word in enumerate(vocab)}
    
    # Create embeddings as word frequency vectors
    embeddings = np.zeros((len(texts), vocab_size))
    for i, words in enumerate(processed_texts):
        word_counts = Counter(words)
        for word, count in word_counts.items():
            embeddings[i, word_to_idx[word]] = count
    
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    embeddings = embeddings / norms
    
    return embeddings

# 2. Inizializzazione del modello
print("Caricamento modello di embedding...")
if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        # Using multilingual model for better Italian/English support
        modello = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        use_transformer = True
        print("Modello multilingue SentenceTransformer caricato con successo.")
        print("Supporto per italiano e inglese attivo.")
    except Exception as e:
        print(f"Errore nel caricamento del modello: {e}")
        print("Utilizzo embedding semplificato...")
        use_transformer = False
else:
    use_transformer = False
    print("Utilizzo embedding semplificato basato su frequenza delle parole...")

# 3. Calcolo degli embedding
print("Calcolo embeddings per i documenti...")
if use_transformer:
    embedding = modello.encode(documenti)
else:
    embedding = create_simple_embeddings(documenti)

print(f"Embedding calcolati per {len(documenti)} documenti ({embedding.shape[1]} dimensioni)")

# 4. Creazione del vector store
vector_store = {
    "vectors": embedding,
    "metadata": [{"id": i, "testo": doc} for i, doc in enumerate(documenti)]
}

# 5. Funzione di ricerca
def cerca(query, vector_store, top_k=3):
    if use_transformer:
        query_embed = modello.encode([query])
    else:
        query_embed = create_simple_embeddings([query])
    
    sims = cosine_similarity(query_embed, vector_store["vectors"])
    indici_simil = np.argsort(sims[0])[::-1][:top_k]
    
    risultati = []
    for idx in indici_simil:
        risultati.append({
            "id": idx,
            "testo": vector_store["metadata"][idx]["testo"],
            "similarity": float(sims[0][idx])
        })
    return risultati

# 6. Input della query dall'utente
print("\n" + "="*50)
print("🔍 SISTEMA DI RICERCA SEMANTICA MULTILINGUE")
print("Supporta italiano e inglese - Semantic Search System")
print("="*50)
try:
    query = input("Inserisci la tua query di ricerca / Enter your search query: ").strip()
except (EOFError, KeyboardInterrupt):
    query = ""

if not query:
    query = "What is the largest marine animal?"
    print(f"Utilizzo query di default / Using default query: '{query}'")

try:
    top_k_input = input("Quanti risultati vuoi visualizzare? (default 3): ").strip()
    top_k = int(top_k_input) if top_k_input.isdigit() and int(top_k_input) > 0 else 3
except (EOFError, KeyboardInterrupt, ValueError):
    top_k = 3
    print("Utilizzo valore di default: 3 risultati")

# 7. Esecuzione della ricerca
print("\n" + "="*50)
print(f"Esecuzione ricerca per: '{query}'")
risultati = cerca(query, vector_store, top_k=top_k)

print("\nTOP RISULTATI:")
for i, res in enumerate(risultati, 1):
    print(f"{i}. [ID:{res['id']}] {res['testo']} (similarità: {res['similarity']:.4f})")

# 8. Preparazione visualizzazione
print("\nPreparazione visualizzazione...")
try:
    pca = PCA(n_components=2)
    embedding_2d = pca.fit_transform(embedding)
    
    if use_transformer:
        query_embed_2d = pca.transform(modello.encode([query]))
    else:
        query_embed_2d = pca.transform(create_simple_embeddings([query]))
    
    # 9. Categorizzazione documenti (italiano e inglese)
    categorie = []
    for doc in documenti:
        doc_lower = doc.lower()
        
        # Animali terrestri
        if any(parola in doc_lower for parola in [
            'gatto', 'cane', 'leone', 'ghepardo', 'orso', 'elefante',
            'elephant', 'tiger', 'wolf', 'giraffe', 'cat', 'dog', 'lion', 'cheetah', 'bear'
        ]):
            categorie.append("Animali Terrestri")
        
        # Animali acquatici
        elif any(parola in doc_lower for parola in [
            'delfino', 'balena', 'squalo', 'meduse', 'pinguini', 'tartaruga',
            'whale', 'dolphin', 'shark', 'octopus', 'turtle', 'penguin', 'marine', 'sea', 'ocean'
        ]):
            categorie.append("Animali Acquatici")
        
        # Animali volanti
        elif any(parola in doc_lower for parola in [
            'aquila', 'pappagallo', 'colibrì', 'gufo', 'rondine',
            'eagle', 'owl', 'swallow', 'bird', 'fly', 'wing'
        ]):
            categorie.append("Animali Volanti")
        
        # Tecnologia
        elif any(parola in doc_lower for parola in [
            'python', 'network', 'ai', 'modelli', 'machine', 'deep', 'linguistici',
            'programming', 'artificial', 'intelligence', 'neural', 'computer', 'vision'
        ]):
            categorie.append("Tecnologia")
        
        # Natura e ambiente
        elif any(parola in doc_lower for parola in [
            'foresta', 'deserto', 'montagna', 'biodiversità',
            'rainforest', 'desert', 'mountain', 'coral', 'reef', 'ecosystem'
        ]):
            categorie.append("Natura")
        
        # Scienza
        elif any(parola in doc_lower for parola in [
            'fisica', 'astronomia', 'biologia', 'quantistica',
            'quantum', 'astronomy', 'genetics', 'dna', 'science'
        ]):
            categorie.append("Scienza")
        
        else:
            categorie.append("Altro")

    # 10. Creazione DataFrame per visualizzazione
    df = pd.DataFrame({
        "x": embedding_2d[:, 0],
        "y": embedding_2d[:, 1],
        "documento": [f"ID:{i} - {doc[:15]}{'...' if len(doc)>15 else ''}" for i, doc in enumerate(documenti)],
        "categoria": categorie,
        "is_result": [i in [res['id'] for res in risultati] for i in range(len(documenti))]
    })

    # 11. Creazione del plot
    plt.figure(figsize=(14, 9))
    plt.title(f"Visualizzazione Embedding: Query = '{query}'", fontsize=16)

    # Plot documenti normali
    normali = df[~df["is_result"]]
    if len(normali) > 0:
        plt.scatter(normali["x"], normali["y"], 
                    c=pd.factorize(normali["categoria"])[0], 
                    cmap="viridis", alpha=0.6, s=70)

    # Plot risultati (più grandi e con bordo)
    risultati_df = df[df["is_result"]]
    if len(risultati_df) > 0:
        plt.scatter(risultati_df["x"], risultati_df["y"], 
                    c=pd.factorize(risultati_df["categoria"])[0], 
                    cmap="viridis", s=200, edgecolor='red', linewidth=2)

    # Plot query
    plt.scatter(query_embed_2d[0, 0], query_embed_2d[0, 1], 
                color='red', s=300, marker='*', label=f'Query')

    # Annotazioni per tutti i punti
    for i, row in df.iterrows():
        plt.annotate(f"ID:{i}", (row['x'] + 0.02, row['y'] + 0.02), 
                     fontsize=8, 
                     fontweight='bold' if row['is_result'] else 'normal')

    # Legenda
    categorie_uniche = df['categoria'].unique()
    for i, cat in enumerate(categorie_uniche):
        plt.scatter([], [], color=plt.cm.viridis(i/len(categorie_uniche)), 
                    label=cat, alpha=0.8)
    plt.legend(title="Categorie", loc='best')

    plt.xlabel('Componente PCA 1', fontsize=12)
    plt.ylabel('Componente PCA 2', fontsize=12)
    plt.grid(alpha=0.1)

    # Informazioni aggiuntive nel plot
    plt.figtext(0.5, 0.01, 
                f"Query: '{query}'\nTop risultato: ID {risultati[0]['id']} - {risultati[0]['testo']}",
                ha="center", fontsize=11, bbox={"facecolor":"lightyellow", "alpha":0.7, "pad":5})

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    print("\nVisualizzazione pronta. Chiudere la finestra del grafico per terminare.")
    plt.show()
    
except Exception as e:
    print(f"Errore nella visualizzazione: {e}")
    print("I risultati della ricerca sono comunque disponibili sopra.")

print("\nProgramma completato!")
