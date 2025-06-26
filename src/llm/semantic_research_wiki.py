import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
import wikipedia
import re

# Configura Wikipedia
wikipedia.set_lang("it")

# Carica i modelli
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
nlp = spacy.load("it_core_news_lg")

def preprocessa_testo(testo):
    """Esegue la lemmatizzazione del testo"""
    doc = nlp(testo.lower())
    return " ".join([token.lemma_ for token in doc])

def ottieni_contenuto_wikipedia(concetto, num_sentences=5):
    """Ottiene contenuto rilevante da Wikipedia"""
    try:
        page = wikipedia.page(concetto, auto_suggest=True)
        # Prendiamo i primi paragrafi e puliamo il testo
        content = re.sub(r'\n|\'', ' ', page.content[:1000])  # Limita a 1000 caratteri
        sentences = [s.strip() for s in content.split('.') if s.strip()][:num_sentences]
        return sentences
    except:
        return []

def prepara_frasi_da_wikipedia(input_utente):
    """Prepara frasi rilevanti da Wikipedia basate sull'input"""
    concetti = [token.lemma_ for token in nlp(input_utente) if token.pos_ in ['NOUN', 'PROPN', 'VERB']]
    frasi = []
    
    for concetto in concetti[:3]:  # Considera massimo 3 concetti principali
        frasi += ottieni_contenuto_wikipedia(concetto)
    
    return list(set(frasi))  # Rimuove duplicati

def trova_frase_piu_simile(input_utente, embeddings_frasi, frasi_predefinite):
    # Preprocessa l'input con lemmatizzazione
    input_lemmatizzato = preprocessa_testo(input_utente)
    
    # Calcola l'embedding
    embedding_input = model.encode([input_utente, input_lemmatizzato]).mean(axis=0).reshape(1, -1)
    
    # Calcola la similarità
    similarita = cosine_similarity(embedding_input, embeddings_frasi)
    
    indice_max = np.argmax(similarita)
    return frasi_predefinite[indice_max], similarita[0][indice_max]

# Interazione con l'utente
print("Benvenuto nel sistema di ricerca semantica con Wikipedia!")
print("Il sistema cercherà informazioni rilevanti su Wikipedia basate sul tuo input.")

while True:
    print("\nInserisci un concetto o frase (o 'exit' per uscire):")
    input_utente = input("> ")
    
    if input_utente.lower() == 'exit':
        break
    
    if not input_utente.strip():
        print("Per favore inserisci del testo.")
        continue
    
    # Ottieni frasi da Wikipedia
    frasi_wikipedia = prepara_frasi_da_wikipedia(input_utente)
    
    if not frasi_wikipedia:
        print("Nessun risultato trovato su Wikipedia per il tuo input.")
        continue
    
    # Calcola embedding per le frasi di Wikipedia
    embeddings_wiki = model.encode(frasi_wikipedia)
    
    # Trova la frase più simile
    frase_simile, punteggio = trova_frase_piu_simile(input_utente, embeddings_wiki, frasi_wikipedia)

    print(f"\nInformazioni da Wikipedia per '{input_utente}':")
    for i, frase in enumerate(frasi_wikipedia, 1):
        print(f"{i}. {frase}")
    
    print(f"\nFrase più attinente: '{frase_simile}'")
    print(f"Punteggio di similarità: {punteggio:.4f}")