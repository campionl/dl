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
    # Animali (30 frasi)
    "Il gatto si arrampica sugli alberi con agilità",
    "I cani sono i migliori amici dell'uomo",
    "Il leone è considerato il re della savana",
    "Le aquile volano ad altezze impressionanti",
    "I delfini comunicano con un sistema complesso di suoni",
    "Le balene migrano per migliaia di chilometri",
    "I pinguini resistono a temperature polari",
    "I serpenti cambiano pelle periodicamente",
    "Le api sono fondamentali per l'impollinazione",
    "Le farfalle subiscono una metamorfosi completa",
    "I lupi cacciano in branchi organizzati",
    "Gli elefanti hanno una memoria eccezionale",
    "I canguri saltano usando potenti zampe posteriori",
    "Le giraffe hanno il collo lungo per raggiungere le foglie",
    "Le tigri sono predatori solitari e notturni",
    "I coccodrilli sono rettili antichissimi",
    "I pappagalli imitano la voce umana",
    "Le meduse sono composte principalmente d'acqua",
    "I ricci si appallottolano per difesa",
    "Le volpi sono animali molto adattabili",
    "I gufi ruotano la testa fino a 270 gradi",
    "I colibrì battono le ali fino a 80 volte al secondo",
    "Le tartarughe marine tornano a deporre uova dove sono nate",
    "I polpi hanno tre cuori e sangue blu",
    "Le lontre giocano con le pietre per rompere i gusci",
    "I pipistrelli si orientano con l'ecolocalizzazione",
    "Le formiche sollevano pesi 50 volte superiori al loro corpo",
    "I camaleonti cambiano colore per mimetizzarsi",
    "Gli orsi polari sono minacciati dallo scioglimento dei ghiacci",
    "I fenicotteri rosa devono il colore alla loro dieta",

    # Tecnologia (25 frasi)
    "L'intelligenza artificiale sta rivoluzionando molti settori",
    "Python è un linguaggio di programmazione versatile",
    "La blockchain garantisce transazioni sicure e trasparenti",
    "I droni vengono utilizzati per riprese aeree",
    "La realtà virtuale crea ambienti immersivi",
    "L'internet delle cose connette dispositivi quotidiani",
    "La stampa 3D permette di creare oggetti complessi",
    "I veicoli elettrici riducono le emissioni inquinanti",
    "La crittografia protegge i dati sensibili",
    "I big data analizzano enormi quantità di informazioni",
    "La fibra ottica garantisce connessioni ultra veloci",
    "La robotica automatizza processi industriali",
    "Gli assistenti vocali rispondono a comandi parlati",
    "La biometria identifica persone attraverso caratteristiche fisiche",
    "Le criptovalute sono monete digitali decentralizzate",
    "Il machine learning migliora con l'esperienza",
    "La nanoscala opera a dimensioni molecolari",
    "I satelliti GPS forniscono posizionamento globale",
    "La fotografia digitale ha sostituito la pellicola",
    "L'ingegneria genetica modifica il DNA degli organismi",
    "La cybersecurity protegge da attacchi informatici",
    "I social media hanno cambiato la comunicazione sociale",
    "Il cloud computing offre risorse informatiche on demand",
    "La realtà aumentata sovrappone elementi digitali al mondo reale",
    "Il quantum computing promette capacità di calcolo rivoluzionarie",

    # Cibo e Cucina (20 frasi)
    "La pizza napoletana è patrimonio UNESCO",
    "Il parmigiano reggiano stagiona minimo 12 mesi",
    "L'olio extravergine d'oliva è fondamentale nella dieta mediterranea",
    "Il tiramisù è un dolce italiano famoso nel mondo",
    "Il caffè espresso è una tradizione italiana",
    "La mozzarella di bufala proviene dalla Campania",
    "Il pesto genovese si prepara con basilico fresco",
    "I tortellini sono una specialità emiliana",
    "Il risotto allo zafferano è tipico milanese",
    "La bistecca alla fiorentina si serve al sangue",
    "La carbonara originale non contiene panna",
    "Il pane toscano è senza sale",
    "Il limoncello è un liquore a base di scorze di limone",
    "La nutella ha rivoluzionato le colazioni italiane",
    "Il vino Chianti viene prodotto in Toscana",
    "Il gelato artigianale usa ingredienti freschi",
    "L'aceto balsamico tradizionale di Modena è invecchiato anni",
    "I cannoli siciliani sono ripieni di ricotta",
    "Le arance di Sicilia sono famose per il loro sapore",
    "Il pane carasau è tipico della Sardegna",

    # Viaggi e Geografia (20 frasi)
    "Le Cinque Terre sono un parco nazionale ligure",
    "Il Colosseo è il simbolo di Roma antica",
    "Venezia è costruita su 118 isolette",
    "La Costiera Amalfitana offre panorami mozzafiato",
    "Le Dolomiti sono patrimonio naturale UNESCO",
    "La Valle dei Templi si trova in Sicilia",
    "Pompei conserva resti romani sotto la cenere",
    "Il Duomo di Milano ha richiesto 600 anni per essere completato",
    "La Torre di Pisa pende a causa del terreno molle",
    "Capri è famosa per i suoi faraglioni",
    "Il lago di Como ha una caratteristica forma a Y rovesciata",
    "Assisi è la città di San Francesco",
    "La Sardegna ha alcune delle spiagge più bianche del Mediterraneo",
    "La Toscana è celebre per i suoi paesaggi collinari",
    "Trentino-Alto Adige offre stazioni sciistiche all'avanguardia",
    "Le grotte di Castellana sono un complesso carsico pugliese",
    "Il Gargano è chiamato lo sperone d'Italia",
    "L'Etna è il vulcano attivo più alto d'Europa",
    "Le Langhe piemontesi sono famose per i vini e i tartufi",
    "Matera è nota per i suoi Sassi scavati nella roccia",

    # Arte e Cultura (20 frasi)
    "Leonardo da Vinci dipinse la Gioconda",
    "Michelangelo scolpì il David a Firenze",
    "Dante Alighieri scrisse la Divina Commedia",
    "La Scala di Milano è un teatro lirico famoso nel mondo",
    "Il Carnevale di Venezia attira turisti da tutto il mondo",
    "La Biennale d'Arte di Venezia è un appuntamento internazionale",
    "Fellini è considerato uno dei più grandi registi italiani",
    "La moda italiana è rinomata per qualità e stile",
    "Il design italiano combina estetica e funzionalità",
    "L'opera lirica nacque in Italia nel XVI secolo",
    "Il Palio di Siena si corre in Piazza del Campo",
    "Pavarotti portò la lirica al grande pubblico",
    "Botticelli dipinse la Nascita di Venere",
    "Il Festival di Sanremo è la kermesse musicale italiana più nota",
    "Il Rinascimento italiano rivoluzionò l'arte europea",
    "Il Vittoriale degli Italiani fu dimora di Gabriele D'Annunzio",
    "Il Teatro Olimpico di Vicenza è il più antico teatro coperto",
    "Pompei offre uno spaccato unico della vita romana",
    "La Cappella Sistina attira milioni di visitatori ogni anno",
    "Il futurismo fu un movimento artistico d'avanguardia italiano",

    # Ambiente e Natura (15 frasi)
    "I cambiamenti climatici minacciano gli ecosistemi",
    "Le foreste pluviali sono i polmoni del pianeta",
    "L'inquinamento plastico danneggia gli oceani",
    "Le energie rinnovabili riducono l'impatto ambientale",
    "La biodiversità è fondamentale per gli ecosistemi",
    "L'agricoltura biologica evita pesticidi chimici",
    "Lo scioglimento dei ghiacciai preoccupa gli scienziati",
    "Le barriere coralline ospitano un quarto delle specie marine",
    "L'economia circolare riduce gli sprechi di risorse",
    "La deforestazione aumenta l'anidride carbonica nell'atmosfera",
    "Le specie invasive danneggiano gli ecosistemi locali",
    "L'acqua dolce è una risorsa sempre più preziosa",
    "L'agricoltura sostenibile preserva il suolo",
    "Le città verdi migliorano la qualità della vita",
    "L'ecoturismo promuove viaggi responsabili",

    # Scienza e Salute (10 frasi)
    "La fisica quantistica studia il comportamento delle particelle",
    "La teoria della relatività di Einstein rivoluzionò la scienza",
    "La ricerca medica ha fatto passi da gigante",
    "Una dieta equilibrata previene molte malattie",
    "L'esercizio fisico regolare allunga la vita",
    "La meditazione riduce lo stress e l'ansia",
    "Il genoma umano è stato completamente mappato",
    "I vaccini hanno debellato malattie mortali",
    "La resistenza agli antibiotici è una minaccia globale",
    "La medicina personalizzata è il futuro delle cure",

    # Sport (10 frasi)
    "Il calcio è lo sport più popolare in Italia",
    "Il ciclismo ha grandi tradizioni nel Belpaese",
    "La scherma ha regalato all'Italia molte medaglie olimpiche",
    "Lo sci alpino è praticato sulle Alpi italiane",
    "La pallavolo italiana vanta squadre competitive a livello internazionale",
    "La Formula 1 ha il suo Gran Premio d'Italia a Monza",
    "Il basket italiano ha una solida tradizione",
    "Il nuoto è uno sport completo e salutare",
    "L'atletica leggera include diverse discipline",
    "La vela sfrutta la potenza del vento"
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
