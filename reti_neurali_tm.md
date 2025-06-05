# Reti neurali
Le reti neurali artificiali (**ANN**, Artificial Neural Networks) sono modelli matematici ispirati al cervello umano. Sono una parte fondamentale dell’intelligenza artificiale e vengono utilizzate per riconoscere schemi, prendere decisioni e risolvere problemi complessi in modo automatico.

## Definizione
Una rete neurale è composta da neuroni artificiali, organizzati in strati:
- Uno strato di **input** (*dati in ingresso*),
- Uno o più strati **nascosti** (*elaborazione*),
- Uno strato di **output** (*risultato*).

Ogni connessione ha un peso, che regola quanto un'informazione è importante. Durante l’addestramento, la rete impara modificando questi pesi per migliorare i risultati.

## Ispirazione biologica
Questo modello si ispira al cervello umano, dove i neuroni comunicano tra loro tramite sinapsi. Infatti anche nelle reti neurali i neuroni artificiali ricevono segnali, li elaborano e trasmettono il risultato. Sebbene molto semplificata, questa struttura consente di simulare meccanismi di apprendimento simili a quelli biologici.

## Perché studiare le reti neurali?
Le reti neurali sono oggi molto usate perché possono apprendere direttamente dai dati. Le loro applicazioni sono ovunque:
- **Medicina**: diagnosi da immagini (radiografie, TAC)
- **Tecnologia**: assistenti vocali, riconoscimento facciale
- **Industria**: manutenzione predittiva, controllo qualità
- **Finanza**: analisi di mercato, prevenzione frodi
- **Automobili**: guida autonoma

Studiare le reti neurali significa capire come rendere i computer più intelligenti e capaci di imparare, contribuendo all’innovazione in molti settori.

## Nascita delle reti neurali
Le reti neurali artificiali nascono tra gli anni '40 e '60, grazie ai primi studi che cercavano di imitare il cervello umano usando modelli matematici. Tra i primi studiosi troviamo:
- **Warren McCulloch e Walter Pitts**: nel 1943 propongono il primo modello di neurone artificiale. Questo modello era molto semplice:
    - Riceveva segnali in **ingresso**,
    - Li **sommava**,
    - E se superavano una certa soglia, generava un **output** (come un “sì” o “no”).

    È il primo tentativo di rappresentare il funzionamento di un neurone biologico in modo matematico.
- **Frank Rosenblatt**: Nel 1958 sviluppa il perceptron, un modello un pò più avanzato.
Il perceptron è una rete neurale molto semplice, con:
    - Uno strato di **input**,
    - Uno strato di **output**,
    - Un **algoritmo** per apprendere dai dati modificando i pesi.

È il primo vero modello di rete neurale in grado di imparare.

## Limitazioni iniziali
Nonostante l'entusiasmo iniziale, il perceptron aveva un grosso limite: non riusciva a risolvere problemi non linearmente separabili, come il famoso problema **XOR** (dove non basta tracciare una linea per separare le due classi).  
Questo portò a una fase di stallo (chiamato AI winter) nella ricerca sulle reti neurali, fino agli anni ’80, quando vennero introdotti modelli più complessi con strati nascosti e nuovi algoritmi di apprendimento.

## Il periodo di stallo
Uno dei motivi principali di questa crisi fu la pubblicazione del libro **"Perceptrons"** di Marvin Minsky e Seymour Papert nel 1969.  
Nel libro, gli autori dimostrarono matematicamente i limiti del perceptron, spiegando che:
- Non può risolvere problemi **non linearmente separabili** (come il già citato problema XOR),
- E che non era possibile superare questi limiti con la **struttura semplice del perceptron a uno strato**.

Anche se le loro critiche erano corrette solo per i modelli più semplici, molti interpretarono il messaggio come: **le reti neurali non funzionano** e quindi molti ricercatori e agenzie di finanziamento persero fiducia nelle reti neurali spostando l'attenzione su altri approcci (come la logica simbolica e i sistemi esperti). Questo provocò una vera e propria pausa nello sviluppo pratico delle reti neurali per quasi due decenni.  
In questo periodo ci fu comunque un'importante riflessione teorica:
- Si compresero meglio i **limiti** delle reti semplici.
- Si iniziò a esplorare l’idea di reti con **più strati**.
- Si gettarono le **basi** per lo sviluppo futuro di algoritmi come il **backpropagation**, che avrebbe rilanciato l’interesse negli anni ’80.

## Il backpropagation 
Negli anni '80, le reti neurali tornarono al centro dell’attenzione grazie a una scoperta fondamentale: l’algoritmo di retropropagazione del gradiente, noto anche come **backpropagation**.  
Nel 1986 **David Rumelhart**, **Geoffrey Hinton** e **Ronald Williams** pubblicano un articolo che mostra come usare il backpropagation per addestrare reti con più strati (multi-layer perceptron). Anche se l’algoritmo era noto da prima, questa pubblicazione ne ha mostrato l’efficacia in pratica, rendendolo popolare e utile.  
Grazie a questo algoritmo diventa possibile:
- Usare reti con **più strati nascosti**,
- **Regolare i pesi** in ogni strato in modo efficiente,
- Risolvere problemi **non lineari** (come il problema XOR), cosa che il perceptron semplice non riusciva a fare.

Questo ha segnato un enorme passo avanti per l’intelligenza artificiale e questo permise di affrontare problemi più realistici e complessi come:
- **Riconoscimento vocale**,
- **Classificazione di immagini**,
- **Previsione di dati complessi**.

## Nuove limitazioni
Anche se il backpropagation aveva riacceso l’interesse negli anni ’80, negli anni ’90 e nei primi 2000 le reti neurali hanno incontrato nuovi ostacoli, che ne hanno limitato la diffusione come ad esempio:
- **Problemi di scalabilità**: le reti neurali di quel periodo erano spesso **piccole** (poche decine o centinaia di neuroni) perché:
    - I computer erano **lenti**,
    - La memoria era **limitata**,
    - Gli algoritmi erano **troppo lenti** per reti grandi.

    Questo rendeva difficile applicarle a problemi reali su larga scala (es. immagini ad alta risoluzione o grandi dataset).

- **Overfitting e generalizzazione**: le reti imparavano **troppo bene** i dati di addestramento, ma poi **non riuscivano a generalizzare** su nuovi dati. In pratica: sembravano “intelligenti” in fase di test, ma “fallivano” con dati mai visti prima. Questo rendeva le reti **poco affidabili** in molti casi pratici.

Questo periodo è stato utile per:
- **Migliorare** le basi teoriche,
- **Sviluppare** nuove tecniche per prevenire **l’overfitting** (es. regularizzazione),
- **Preparare** il campo alla grande **rinascita** del deep learning nel 2010, grazie a dati, hardware e algoritmi migliori.

## Il grande salto qualitativo
Dopo anni di sviluppo teorico e progresso tecnologico, dagli anni 2010 in poi le reti neurali hanno fatto un grande balzo in avanti. Questo periodo segna l’inizio dell’era del **Deep Learning**. Si svilupparono quindi le **reti neurali profonde** (reti con molti strati nascosti) che permettono di:
- Imparare **caratteristiche complesse** dai dati,
- Affrontare problemi **non lineari e ad alta dimensione**,
- Raggiungere **prestazioni molto elevate** in compiti difficili.

Questa **rivoluzione** è stata possibile grazie a **due fattori chiave**:
- **Big Data**: grandi quantità di dati disponibili (*immagini, testo, audio, ecc.*)
- **Hardware più potenti**: uso di GPU e TPU che accelerano enormemente l’addestramento delle reti neurali.

Per migliorare le prestazioni e risolvere vecchi problemi (come l’overfitting), sono stati introdotti nuovi strumenti:
- **ReLU**: funzione di attivazione **semplice ma efficace**;
- **Dropout**: spegne casualmente alcuni neuroni durante l’addestramento per **migliorare la generalizzazione**;
- **Batch Normalization**: **stabilizza e velocizza** l’apprendimento.

Grazie al deep learning, le reti neurali hanno raggiunto **risultati straordinari** in molti settori:
- **Riconoscimento immagini**: reti CNN per classificazione visiva;
- **Linguaggio naturale**: traduzioni, chatbot, assistenti vocali;
- **Gioco e intelligenza strategica**: AlphaGo di DeepMind (che ha battuto campioni umani nel gioco del Go);
- **Medicina, finanza, robotica** e molto altro.

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