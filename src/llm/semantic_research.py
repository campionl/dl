import chromadb
from sentence_transformers import SentenceTransformer
import spacy
from typing import List

# Configurazione ChromaDB
chroma_client = chromadb.PersistentClient(path=".chromadb")  # Directory per salvare i dati

# Crea/ottieni la collection
collection = chroma_client.get_or_create_collection(
    name="semantic_search",
    metadata={"hnsw:space": "cosine"}  # Configurazione per similarità del coseno
)

# Carica i modelli
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
nlp = spacy.load("it_core_news_lg")

# Definizione delle frasi predefinite
frasi_predefinite = [
    "Il cane abbaia nel cortile",
    "Il gatto miagola sul divano",
    "Il sole splende nel cielo azzurro",
    "La pioggia cade dolcemente sui tetti",
    "Studiare machine learning è molto interessante",
    "Python è un linguaggio di programmazione popolare",
    "Mi piace camminare nel parco la mattina",
    "La pizza margherita è la mia preferita"
]

def inizializza_database():
    """Aggiunge le frasi predefinite al database"""
    embeddings = model.encode(frasi_predefinite).tolist()
    ids = [str(i) for i in range(len(frasi_predefinite))]
    metadati = [{"source": "predefinito"} for _ in frasi_predefinite]
    
    collection.add(
        embeddings=embeddings,
        documents=frasi_predefinite,
        metadatas=metadati,
        ids=ids
    )

def preprocessa_testo(testo: str) -> str:
    """Esegue la lemmatizzazione del testo"""
    doc = nlp(testo.lower())
    return " ".join([token.lemma_ for token in doc])

def cerca_frasi_simili(input_utente: str, n_risultati: int = 3) -> List[dict]:
    """Cerca frasi simili usando ChromaDB"""
    # Preprocessa l'input
    input_lemmatizzato = preprocessa_testo(input_utente)
    print("Lemmatizzato:", input_lemmatizzato)
    
    # Calcola l'embedding per la query
    query_embedding = model.encode([input_utente, input_utente]).mean(axis=0).tolist()
    
    # Esegui la query
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_risultati,
        include=["documents", "distances"]
    )
    
    # Formatta i risultati (converti distanze in similarità)
    return [
        {"documento": doc, "similarita": 1 - dist}
        for doc, dist in zip(results["documents"][0], results["distances"][0])
    ]

# Inizializza il database (solo alla prima esecuzione)
if collection.count() == 0:
    inizializza_database()

# Interazione con l'utente
print("Benvenuto nel sistema di ricerca semantica con ChromaDB!")
print("Frasi disponibili nel database:")
for i, frase in enumerate(frasi_predefinite, 1):
    print(f"{i}. {frase}")

while True:
    print("\nInserisci una parola o frase (o 'exit' per uscire):")
    input_utente = input("> ")
    
    if input_utente.lower() == 'exit':
        break
    
    if not input_utente.strip():
        print("Per favore inserisci del testo.")
        continue
    
    risultati = cerca_frasi_simili(input_utente)
    
    if not risultati or risultati[0]["similarita"] < 0.3:
        print("Nessuna corrispondenza significativa trovata.")
        continue
    
    print("\nRisultati più attinenti:")
    for i, risultato in enumerate(risultati, 1):
        print(f"{i}. {risultato['documento']} (similarità: {risultato['similarita']:.4f})")