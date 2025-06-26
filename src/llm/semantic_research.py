import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy

# Carica il modello per l'embedding delle frasi
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

# Carica il modello linguistico spaCy per la lemmatizzazione
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

# Calcola gli embedding per le frasi predefinite
embeddings_frasi = model.encode(frasi_predefinite)

def preprocessa_testo(testo):
    """Esegue la lemmatizzazione del testo"""
    doc = nlp(testo.lower())
    return " ".join([token.lemma_ for token in doc])

def trova_frase_piu_simile(input_utente):
    # Preprocessa l'input con lemmatizzazione
    input_lemmatizzato = preprocessa_testo(input_utente)
    
    # Calcola l'embedding per l'input dell'utente (usando sia originale che lemmatizzato)
    embedding_input = model.encode([input_utente, input_lemmatizzato]).mean(axis=0).reshape(1, -1)
    
    # Calcola la similarità del coseno
    similarita = cosine_similarity(embedding_input, embeddings_frasi)
    
    # Trova la frase più simile
    indice_max = np.argmax(similarita)
    return frasi_predefinite[indice_max], similarita[0][indice_max]

# Interazione con l'utente
print("Benvenuto nel sistema di ricerca semantica avanzata!")
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
    
    frase_simile, punteggio = trova_frase_piu_simile(input_utente)

    if punteggio >= 0.3:
        print(f"\nFrase più attinente: '{frase_simile}'")
        print(f"Punteggio di similarità: {punteggio:.4f}")
    else:
        print(f"Nessuna corrispondenza significativa trovata. Punteggio: {punteggio}")