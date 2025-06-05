## Architetture innovative e il loro impatto

Negli ultimi 10-15 anni c'è stata un esplosione di nuove architetture cambiando il modo di affrontare l'inteligenza artificiale.
Queste nuove architetture inolte hanno portato ad un miglioramento in termini di prestazioni, capacità applicative e applicazioni pratiche.

Le architetture principali sono:
- Reti convoluzionali (CNN)  
Specializzate per elaborare dati con struttura spaziale (immagini e video).
- Reti ricorrenti (RNN)  e LSTM/GRU
Specializzate per elaborare dati sequenziali (audio, testo, segnali temporali), avevano il problema del vanishing gradient ovvero difficolta ad apprendere le dipendenze a lungo termine ma LSTM e GRU risolvono il problema, in generale questi sono utili per riconoscimento vocale e traduzione automatica.
- Trasformers  
Abbandonano la struttura ricorrente per una chiamata self-attention, permettono di parallelizzare il calcolo e sono a oggi giorno tra i più utilizzati (ChatGPT, Alexa, Google assistente, Google translate)
- Reti neurali su Grafi (GNN)
Le reti neurali sono nate per eseguire operazioni complesse sui grafi invece che su testi o immagini.  
*Un grafo è composto da nodi e archi*  
Questa architettura viene usata in:  
    - Chimica per prevedere le proprietà di molecole;
    - Social per raccomandazioni o rilevamento di fake news;
    - Trasporti per ottimizzazioni logistiche;
    - Finanza per analisi di reti di transazioni;
    - Informatica per analisi del codice;

- Architetture ibride  
Queste sono architetture che fondono i concetti delle precedenti alcuni esempi sono le GAN per la generazione di immagini, auto encoder, variational encoder (VAE), permettono poi reti neurali quantistiche e reti biologicamente ispirate

## Il ruolo dell'hardware

Ovviamente con l'evoluzione dell'AI c'è stato un bisogno anche per l'hardware di evolversi, questo legame porta ad un parallelismo tra i due.

Le CPU ovvero i normali processori non erano abbastanza potenti e veloci per gestire le migliaia di operazioni parallele, d'altro canto le GPU ovvero le schede video nate per i videogiochi erano perfette per il calcolo parallelo dei dati.

Possiamo poi affermare che in questo campo NVIDIA è il campione indiscusso, assieme al suo CUDA infatti fù capace di ridurre il tempo degli addestramenti da quelli che prima erano giorni o settimane in ore.

Le GPU servono quindi ad addestrare i modelli ed eseguire inferenze in tempo reale.

Le TPU, creazione di google, sono state create **specificatamente** per il machine learning.

Sono poi stati creati servizi in cloud come AWS, Google Cloud, OpenAI e Azure che permettono di addestrare un modello senza il bisogno di possedere un supercomputer.

## Problemi etici e sociali

Le reti neurali apprendono il comportamento umano, ma così facendo apprendono anche i pregiudizi e li amplificano penalizzando per esempio individui con nomi stranieri, anche se non c'è intenzione.

#### Mancanza di trasparenza

I ragionamenti di un algoritmo non sono sempre spiegabili essendo che operano con logica propria, il che non ci permette di capire chiaramente perchè il modello abbia fatto una scelta invece che un altra e rende difficile capire se ci siano state manipolazioni interne.
Ciò mina la fiducia che si può arrecare ad un modello di intelligenza artificiale.

#### Impatto sul lavoro

Vista la rapida crescita nella potenza dell'ai essa può sostituire gran parte dei lavori umani, in particolare quelli ripetitivi ciò porta a disoccupazione.

#### Privacy

La privacy è un problema dell'ai in quanto analizza ogni giorno una valanga di dati personali come foto, video, chat, comportamenti e questo porta a rischi come tracciamento di massa, profilazione aggressiva e manipolazione politica.

#### Disinformazione

Le reti neurali generative (GAN) sono in grado di creare immagini e video che oggigiorno sono diventati alquanto realistici, l'uso di questi prodotti dell'ai, i deepfake, può portare a fake news, rovina di reputazioni e contenuti pericolosi.

#### Chi ne ha il controllo?

I modelli più potenti di IA sono sviluppati da grandi aziende come OpenAI, google, meta, etc..  
Questo porta a una centralizzazione del potere centrologico e rende meno accessibile l'ai per i paesi poveri.

#### Abuso militare

Le reti neurali vengono utilizzate per:
- Droni autonomi da guerra
- Sorveglianza predittiva
- Simulazioni belliche avanzate

## Sfide e possibili futuri sviluppi

Le reti neurali sonogià molto avanzate ma restano in continua evoluzione e nuove sfide da affrontare per migliorarle ulteriormente.
I principali miglioramenti che si vogliono apportare alle reti neurali sono:
- Generalizzazione  
Le reti neurali sono addestrate per risolvere problemi specifici ma si sta puntando alla creazione di un modello capace di risolvere problemi di vario tipo.
- Efficienza energetica e ambientale  
Le reti neurali consumano quantità enormi di energia per restare in funzione, l'obbiettivo e di creare modelli più efficienti in futuro.
- Comprensione
Come detto prima *<-inserire link a black box* è difficile capire come ragiona un modello, motivo per qui si lavora su tecniche di **Explainable AI** per aumentarne fiducia e trasparenza.
- Sicurezza  
Vengono studiati metodi per rendere i modelli più sicuri e meno soggetti ad attacchi.
- Bias e giustizia algoritmica  
Si cerca di creare modelli che non assorbano i pregiudizi per renderli più equi.
- Apprendimento continuo  
Si tenta di ideare modelli capaci di ricordare dalle vecchie versioni e di imparare da soli.
- Apprendimento con pochi dati  
Si vuole creare modelli che non richiedono migliaia di dati per imparare un compito.
- Coesistenza con l'essere umano  
Uno dei passi più importanti è anche capire il modo in qui l'ai potrà collaborare con l'essere umano se come copiloti inteligenti o solo sistemi che potenziano invece che sostituire.

## Conclusione
Le reti neurali artificiali, nate da idee semplici negli anni ‘60, hanno compiuto un percorso straordinario fino a diventare oggi il cuore pulsante dell’intelligenza artificiale moderna. La svolta degli ultimi anni — grazie a big data, nuove architetture come i Transformer e una potenza di calcolo mai vista prima — ha permesso di ottenere risultati prima impensabili, come la traduzione automatica fluida, la generazione di immagini e testi realistici, e la diagnosi medica assistita.

Tuttavia, insieme a queste opportunità emergono sfide profonde: il bisogno di modelli più sostenibili, equi e interpretabili; la gestione dei rischi legati all’uso improprio; e la ricerca di un equilibrio tra innovazione tecnologica e responsabilità etica.

Il futuro dell’IA non sarà solo una questione di quanto sarà potente, ma anche di come verrà guidata e integrata nella società. Le reti neurali continueranno ad evolversi, ma sarà il nostro approccio umano a determinarne l’impatto.