import chromadb
from chromadb.utils import embedding_functions

frase = input("Inserisci la frase che desideri chiedere: ")

# 1. Inizializza il client Chroma
client = chromadb.Client()

# 2. Crea una collection (il tuo "vector store")
embedding_func = embedding_functions.DefaultEmbeddingFunction()  # Usa un modello locale
collection = client.create_collection(name="my_documents", embedding_function=embedding_func)

# 3. Aggiungi documenti (con embedding automatico)
documents = [
    "Il libro è a casa",
    "Il cane abbaia nel giardino",
    "Roma è la capitale d'Italia",
    "Napoli è bellissima",
    "Oggi a calcio ho fatto gol!!!"
]
collection.add(
    documents=documents,
    ids=["doc1", "doc2", "doc3", "doc4", "doc5"]  # ID univoci
)

# 4. Interroga il Vector Store
results = collection.query(
    query_texts=[frase],
    n_results=1  # Numero di risultati
)

print(results['documents'][0][0])