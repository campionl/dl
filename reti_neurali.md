# RETI NEURALI

## Le Fondamenta Teoriche e i Primi Modelli (Anni '40 - '60)

Le **reti neurali artificiali** (Artificial Neural Networks, ANN) sono modelli computazionali ispirati al cervello umano, utilizzati in ambito informatico per risolvere problemi complessi come riconoscimento vocale, visione artificiale, traduzione automatica e molti altri.

Le reti neurali **cercano di imitare il funzionamento del cervello umano**, dove milioni di neuroni biologici comunicano tra loro attraverso connessioni chiamate **sinapsi**. Allo stesso modo, in una ANN ci sono **unità di calcolo artificiali** (i neuroni) collegate tra loro da **pesi sinaptici** che trasmettono e trasformano le informazioni.


### Il Neurone di McCulloch-Pitts (1943)

Nel 1943, Warren McCulloch e Walter Pitts proposero il primo modello matematico di neurone artificiale. Questo modello era estremamente semplice, concepito per eseguire computazioni binarie: riceveva più input binari (0 o 1) e produceva un singolo output binario contenente se la somma degli input raggiungeva o superava una soglia predefinita (T/F). La loro innovazione dimostrò come strutture neurali potessero elaborare operazioni logiche fondamentali, rappresentando funzioni booleane come AND, OR, NOT, NOR e NAND. Geometricamente, queste funzioni potevano essere visualizzate come confini di decisione lineari, ad esempio, una linea per AND e OR in uno spazio bidimensionale.  

Presentava però molti limiti: non aveva meccanismi di apprendimento, in quanto le soglie erano impostate tutte manualmente, e trattava gli input tutti allo stesso modo senza ponderazione.
Era quindi impossibile risolvere problemi di natura non lineare. 

### La Regola di Hebb (1949)

Un passo concettuale fondamentale fu la "Regola di Hebb", proposta da Donald Hebb nel 1949 nel suo libro *The Organization of Behavior*. Questa regola postulava che quando due neuroni si attivano contemporaneamente e ripetutamente, la connessione sinaptica tra di essi si rafforza. Hebb suggerì che questo meccanismo fosse alla base dell'apprendimento e della memoria nel cervello. Per le reti neurali artificiali, ciò significò l'introduzione del concetto di **pesi** per gli input, permettendo che alcuni input avessero un'influenza maggiore o minore sulla somma totale che determinava l'attivazione del neurone.  

### Il Perceptron di Rosenblatt (1958)

Basandosi sui lavori di McCulloch-Pitts e sulle intuizioni di Hebb, Frank Rosenblatt sviluppò il Perceptron nel 1958. Questa fu la prima vera rete neurale artificiale capace di apprendere. Il Perceptron era un modello feedforward con uno strato di input e un nodo di output, e i suoi pesi sinaptici erano dinamici, permettendo alla macchina di apprendere in modo elementare. Il suo campo di applicazione iniziale era il riconoscimento di forme e la classificazione binaria. Nonostante il suo potenziale e l'iniziale entusiasmo, il Perceptron ereditava la limitazione fondamentale del modello di McCulloch-Pitts: l'incapacità di risolvere problemi non lineari come il problema XOR.  

La narrazione di questo periodo mostra una chiara progressione: McCulloch-Pitts ha stabilito l'unità computazionale di base, Hebb ha introdotto il concetto cruciale di apprendimento attraverso la modifica della forza sinaptica, e Rosenblatt ha combinato queste intuizioni per creare la prima rete neurale "apprendente". Questa non è una serie di scoperte isolate, ma una costruzione continua in cui ogni idea ha informato e abilitato la successiva, evidenziando la natura cumulativa del progresso scientifico. L'iniziale ottimismo per il Perceptron, che "rivitalizzò lo studio delle ANN" e "dimostrò il potenziale delle macchine di mimare certi aspetti del processo decisionale umano" , fu rapidamente temperato dalle sue limitazioni. Questo stabilisce un modello ricorrente nel campo: l'entusiasmo iniziale e le affermazioni audaci spesso superano le attuali capacità tecnologiche, portando a periodi di disillusione che prefigurano gli "inverni dell'IA".  

### Il concetto alla base

Il concetto alla base delle reti neurali è la modellazione matematica di un **neurone umano**.  
Il **neurone artificiale** così costruito risulta un classificatore binario che calcola l'uscita attraverso la seguente **funzione lineare**:  

$$z = \chi(\sum_{i=0}^{m} w_i x_i + b)$$

dove:  

$z =$ uscita  
$m =$ numero di ingressi  
$x_i =$ segnale  
$w_i =$ peso del segnale  
$b =$ bias (termine costante indipendente)  
$\chi =$ funzione di output  

![schema](https://github.com/campionl/dl/blob/ac/images/perceptron.jpg)  

N.B.: Generalmente la funzione di output (nel disegno *activation funcion*) è:  
$\chi(y) = sign(y)\ oppure\\ \chi(y) = y \Theta(y)\ oppure\\ \chi(y) = y$  
dove $\Theta(y)$ è la funzione di Heaviside.

È possibile creare reti neurali complesse unendo più neuroni assieme, e concatenando le uscite di un gruppo di neuroni agli ingressi del successivo.

#### Come Funziona il Perceptron

1. Pesi iniziali: Assegna pesi casuali alle caratteristiche (es: w1=0.5, w2=−0.5).
- Pensa ai pesi come all'importanza che diamo a dolcezza e colore.

2. Decisione:

- Calcola:Score=(x1​ ⋅ w1)+(x2 ⋅ w2).
- Se Score > soglia (es: 0.5) → "Banana", altrimenti → "Mela".

3. Apprendimento:

- Se sbaglia, aggiusta i pesi per ridurre l’errore.
- Esempio:
	- Se scambia una banana per una mela, aumenta w1 e w2 per dare più peso a dolcezza e colore giallo.

### ️ Multi-layer Perceptron (MLP)

Grazie al backpropagation, fu possibile **addestrare reti a più strati** (MLP), superando i limiti del perceptron singolo:

* I MLP possono rappresentare **funzioni non lineari complesse**,
* Riescono a **risolvere problemi come l’XOR**.

Questo segnò una **svolta fondamentale** nello sviluppo dell’intelligenza artificiale.

![schema](https://github.com/campionl/dl/blob/ac/images/nodeNeural.jpg)  

#### Il Problema dello XOR: Il "Muro" del Perceptron

Ora proviamo a distinguere due gruppi di numeri:
XOR (O Esclusivo):

- Classifica (0,0) e (1,1) come 0.
- Classifica (0,1) e (1,0) come 1.

#### Perché il Perceptron Fallisce?

Con una retta: È impossibile separare i due gruppi.
Serve una curva: Per risolvere XOR, servono due rette (cioè uno strato nascosto).
Il perceptron a un solo strato non può farlo.


#### La Soluzione?

Servono più chef (neuroni) che lavorino insieme in strati nascosti per combinare le regole in modo non lineare. **Questo sarà il cuore delle reti neurali moderne!**

### La Crisi del Perceptron (1969): Perché quasi uccise l’AI

Nel 1969, Marvin Minsky e Seymour Papert pubblicarono il libro "Perceptrons", dimostrando matematicamente che:

- Un singolo perceptron può risolvere SOLO funzioni linearmente separabili.
- Lo XOR è un problema non linearmente separabile → Impossibile per un perceptron a 2 input.
- Risultato → crollano del tutto gli investimenti per le reti neurali


### Backpropagation (1986): Il motore segreto del Deep Learning

L’algoritmo di backpropagation (error backpropagation) fu reso popolare da Rumelhart, Hinton e Williams nel 1986, ma l’idea originale è di Paul Werbos (1974 nella tesi di dottorato).
Come funziona in 3 passi:

1. ##### Forward Pass (Prova a indovinare)

- Mostri una foto al bambino (input)
- Lui osserva le caratteristiche (orecchie a punta? muso lungo?) e fa una guess: "Penso sia un gatto!" (output)

3. ##### Calcolo dell'errore (Quanto ha sbagliato?)

- Se la foto era davvero di un cane, diciamo: "No, era un cane! L'errore è X"
- L'errore si misura come la differenza tra la risposta data e quella corretta

3. ##### Backward Pass (Impara dagli errori)

- Il bambino chiede: "Dove ho sbagliato?"
- Analizziamo insieme:

	- "Hai dato troppo peso alle orecchie a punta (che però anche alcuni cani hanno)"
	- "Non hai considerato abbastanza la forma del muso"

- Aggiustiamo l'importanza (pesi) data a ogni caratteristica

#### Il problema del Vanishing Gradient (Perché non impara bene)

- Se usiamo certi tipi di "ragionamenti" troppo complessi (funzioni sigmoide), le correzioni diventano microscopiche man mano che torniamo indietro
- Risultato: le prime caratteristiche (es. "ha 4 zampe") non vengono mai aggiustate!

#### La soluzione ReLU (Il trucco per far imparare meglio)

- Usiamo un metodo più semplice e diretto:
"Se questa caratteristica è importante? Sì/No" (come un interruttore)
- Così le correzioni rimangono chiare e forti in tutti gli strati


### AlexNet (2012): La "Big Bang" del Deep Learning Moderno

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

Negli ultimi 10-15 anni c'è stata un esplosione di nuove architetture cambiando il modo di affrontare l'inteligenza artificiale.
Queste nuove architetture inolte hanno portato ad un miglioramento in termini di prestazioni, capacità applicative e applicazioni pratiche.  
Le architetture principali sono:
# Architetture di Reti Neurali - Riassunto Dettagliato

## 1. Perceptron
- **Nome completo:** Perceptron (o MLP: Multi-Layer Perceptron)
- **Uso:** Classificazione base, regressione
- **Descrizione:** Rete completamente connessa (fully-connected). Usata per problemi semplici e strutturati (dati tabellari).
- **Limiti:** Non scala bene su dati complessi (es. immagini, testo)

---

## 2. CNN - Convolutional Neural Network
- **Uso:** Immagini, video, visione artificiale
- **Descrizione:** Usa **strati convoluzionali** per riconoscere pattern spaziali locali.
- **Componenti chiave:**
  - Convoluzione
  - Pooling
  - Flatten → Dense
- **Esempi famosi:** LeNet, AlexNet, VGG, ResNet

---

## 3. RNN - Recurrent Neural Network
- **Uso:** Dati sequenziali (testo, serie temporali, audio)
- **Descrizione:** Ha una **memoria interna** che considera lo stato precedente per produrre l’output.
- **Problema:** Soffre di vanishing gradient.
- **Varianti migliorate:** LSTM, GRU

---

## 4. LSTM - Long Short-Term Memory
- **Uso:** Traduzione, generazione testo, audio, classificazione sequenze
- **Descrizione:** Variante di RNN che risolve il problema del vanishing gradient grazie a **gates** (porte logiche: input, forget, output)
- **Punti di forza:** Ottima per sequenze lunghe e contesti di memoria persistente

---

## 5. GRU - Gated Recurrent Unit
- **Uso:** Simile a LSTM, ma più leggero
- **Descrizione:** RNN con meno porte rispetto a LSTM (solo update e reset). Più veloce e meno costoso computazionalmente.
- **Pro:** Compromesso tra performance e velocità

---

## 6. Autoencoder
- **Uso:** Compressione, riduzione dimensionale, denoising, anomaly detection
- **Descrizione:** Rete simmetrica (Encoder → Bottleneck → Decoder). Impara a ricostruire input.
- **Varianti:** Denoising Autoencoder, Variational Autoencoder (VAE)

---

## 7. GAN - Generative Adversarial Network
- **Uso:** Generazione di immagini, deepfake, super-risoluzione
- **Descrizione:** Due reti che competono: **Generatore** vs **Discriminatore**
- **Output:** Immagini realistiche da rumore
- **Problema:** Instabilità nel training

---

## 8. ResNet - Residual Network
- **Uso:** Visione artificiale avanzata (ImageNet, classificazione immagini)
- **Descrizione:** Rete CNN profonda con **residual connections** (skip connections) per evitare vanishing gradient.
- **Pro:** Permette reti con 50+ layer senza degrado

---

## 9. Transformer
- **Uso:** NLP, traduzione, sintesi, codifica testo, anche visione (Vision Transformer)
- **Descrizione:** Basato su **self-attention**, non usa RNN
- **Esempi:** BERT, GPT, T5
- **Punti di forza:** Parallelizzabile, gestisce contesti lunghi
- **Formula chiave:** `Attention(Q, K, V) = softmax(QKᵀ / √d) * V`

---

## 10. BERT - Bidirectional Encoder Representations from Transformers
- **Uso:** NLP: classificazione, estrazione, risposta a domande
- **Descrizione:** Solo encoder dei Transformer, preaddestrato con masked language modeling
- **Pro:** Capisce il **contesto bidirezionale** di una frase

---

## 11. GPT - Generative Pretrained Transformer
- **Uso:** Generazione testo, chatbot, completamento
- **Descrizione:** Solo decoder dei Transformer, addestrato in modo autoregressivo
- **Pro:** Eccellente per generazione creativa e linguaggio naturale

---

## 12. ViT - Vision Transformer
- **Uso:** Visione artificiale avanzata, classificazione immagini
- **Descrizione:** Applica il meccanismo dei Transformer alle immagini suddivise in patch
- **Pro:** Supera le CNN in alcuni task di visione, ma richiede molti dati

---

## 13. Capsule Network (CapsNet)
- **Uso:** Riconoscimento immagini avanzato (es. rotazioni, affini)
- **Descrizione:** Mantiene la relazione spaziale tra le feature usando "capsule" invece dei semplici neuroni
- **Pro:** Più resistente alle trasformazioni rispetto a CNN
- **Contro:** Computazionalmente pesante, difficile da allenare

---

## 14. Siamese Network
- **Uso:** Verifica di similarità (es. riconoscimento facciale, firma)
- **Descrizione:** Due sottoreti con pesi condivisi che producono embedding confrontabili
- **Output:** Distanza tra due input (simili o diversi)

---

## 15. Reti Neurali Spiking (SNN)
- **Uso:** Neuroscienze, simulazioni cervello umano, robotica neurale
- **Descrizione:** I neuroni comunicano tramite spike (impulsi discreti). Ispirati al cervello biologico.
- **Pro:** Basso consumo energetico
- **Contro:** Difficile da addestrare con backpropagation standard

### I Contributi dei Pionieri Moderni: John J. Hopfield e Geoffrey E. Hinton (Premio Nobel per la Fisica 2024)

Il riconoscimento dell'impatto fondamentale delle reti neurali ha raggiunto il suo apice nel 2024, quando John J. Hopfield e Geoffrey E. Hinton sono stati insigniti del Premio Nobel per la Fisica per i loro contributi pionieristici.  

John J. Hopfield: Ha introdotto la Rete di Hopfield nel 1982, un modello per la memoria associativa capace di salvare e ricostruire pattern anche da dati incompleti o corrotti. Questo modello, basato su concetti della fisica statistica, ha influenzato profondamente sia lo sviluppo delle reti neurali ricorrenti (RNN) che la comprensione delle reti neurali biologiche.  

Geoffrey E. Hinton: Ha sviluppato la Macchina di Boltzmann, una rete neurale stocastica che impiega principi della fisica statistica per elaborare informazioni autonomamente, introducendo il concetto di apprendimento non supervisionato. Hinton è riconosciuto come uno dei pionieri del deep learning e ha ricevuto il Turing Award nel 2018, il "Nobel dell'informatica", per il suo contributo rivoluzionario. Le loro ricerche non solo hanno gettato le basi teoriche, ma hanno anche portato a innovazioni pratiche che influenzano quotidianamente la vita delle persone, dal riconoscimento vocale all'analisi automatica dei dati medici e scientifici.  

Il conferimento del Premio Nobel per la Fisica a Hopfield e Hinton simboleggia il riconoscimento accademico dell'impatto profondo e pervasivo delle reti neurali. Le loro scoperte hanno trasceso i confini della ricerca pura, diventando il fondamento di tecnologie onnipresenti come il riconoscimento vocale, i chatbot e i sistemi di raccomandazione. Questo sottolinea come l'IA, e in particolare le reti neurali, siano passate da un concetto teorico a una realtà pratica e indispensabile, profondamente integrata nella vita quotidiana e nel panorama economico.  

#### Innovazioni tecniche:

- GPU NVIDIA GTX 580: Addestramento parallelo su 2 GPU (5 giorni vs. mesi su CPU).
- ReLU: Risolse il vanishing gradient per reti profonde (8 strati) (ReLU è il megafono che mantiene il messaggio forte e chiaro, strato dopo strato).
- Dropout (Srivastava et al.): Spegnimento casuale del 50% dei neuroni durante il training → riduce l’overfitting (Serve imparare a ragionare, non a ripetere).
- Data Augmentation: Rotazione/riflessione delle immagini per aumentare i dati.


## Applicazioni Attuali e Impatto Trasformativo

Le reti neurali artificiali trovano impiego in numerosi e eterogenei settori scientifici e industriali, dalla biomedicina al data mining, e il loro utilizzo è in crescita. I continui progressi permettono di ottenere circuiti sempre più sofisticati, rendendo le macchine capaci di osservare, ascoltare, comprendere e persino anticipare i bisogni umani.  

I principali settori di applicazione includono:

- Finanza: Previsioni sull'andamento dei mercati (inclusi quelli valutari), analisi del rischio di credito e analisi del portafoglio.   
- Riconoscimento ed elaborazione delle immagini e visione artificiale: Utilizzate per compiti come il riconoscimento facciale, la classificazione di oggetti, l'analisi di scene, le diagnosi mediche da immagini e le auto a guida autonoma.  
- Analisi del parlato e riconoscimento vocale: Permettono la trascrizione automatica del parlato, il riconoscimento del parlante e la comprensione del linguaggio naturale, come negli assistenti vocali (Siri, Alexa).  
- Diagnosi mediche: Includono l'analisi di referti di TAC e risonanze magnetiche, contribuendo alla diagnosi di malattie e migliorando l'accuratezza diagnostica.  
- Simulazione di sistemi biologici: Dalle simulazioni intracellulari alle reti neurali stesse.  
- Robotica: Controllo e navigazione di robot.  
- Controllo di qualità su scala industriale: Monitoraggio e miglioramento dei processi produttivi, con le reti neurali ricorrenti particolarmente utili per monitorare i flussi di produzione e analizzare grandi quantità di dati da sensori.  
- Data mining: Estrazione di pattern e informazioni da grandi insiemi di dati.  
- Simulazioni di varia natura: Anche quelle che comprendono un fattore temporale.  
- Sistemi di raccomandazione: Suggeriscono contenuti personalizzati basati sui comportamenti e preferenze degli utenti (es. suggerimenti di film su piattaforme di streaming, prodotti su e-commerce).  
- IA Generativa e Modelli Linguistici (GPT): Le reti neurali alimentano sistemi avanzati come quelli alla base dell'IA Generativa e dei modelli linguistici, come ChatGPT.  

Le reti ricorrenti (come SOM e Hopfield) sono più adatte per simulazioni e classificazioni, mentre le reti feedforward (MLP) sono valide in applicazioni come l'OCR (Optical Character Recognition). Le reti neurali hanno rivoluzionato il modo in cui si interagisce con il web, rendendo le esperienze online più efficienti, intuitive e personalizzate. Di conseguenza, l'Intelligenza Artificiale si è trasformata in uno strumento di uso quotidiano, spesso senza nemmeno rendersene conto. Questa onnipresenza dell'IA nella vita quotidiana sottolinea la necessità di consapevolezza sui suoi meccanismi e implicazioni.  

Le aziende che adottano queste tecnologie ottengono un vantaggio competitivo, prendendo decisioni più informate, automatizzando compiti complessi e sviluppando nuovi prodotti e servizi che rispondono meglio alle esigenze del mercato. Questo posiziona l'IA come un motore fondamentale di innovazione e competitività, trasformando il modo in cui le organizzazioni affrontano la complessità e sfruttano i dati.  

## Il ruolo dell'hardware
Con l'evoluzione dell'AI c'è stato bisogno anche per l'hardware di evolversi, questo legame porta ad un parallelismo tra i due.  
Le **CPU** ovvero i normali processori non erano abbastanza potenti e veloci per gestire le migliaia di operazioni parallele, d'altro canto le **GPU** ovvero le schede video nate per i videogiochi erano perfette per il calcolo parallelo dei dati.  
Possiamo affermare che in questo campo **NVIDIA** è il campione indiscusso, assieme al suo **CUDA** infatti fù capace di ridurre il tempo degli addestramenti da quelli che prima erano giorni o settimane in ore.  
Le **GPU** servono quindi ad addestrare i modelli ed eseguire inferenze in tempo reale. Le TPU, creazione di google, sono state create **specificatamente** per il machine learning. Sono poi stati creati servizi in cloud come AWS, Google Cloud, OpenAI e Azure che permettono di addestrare un modello senza il bisogno di possedere un supercomputer.

###  **Verso problemi più complessi**

Con questa nuova capacità, le reti neurali iniziarono ad affrontare:

* Riconoscimento di immagini e suoni,
* Previsioni,
* Classificazione di dati non lineari.

Fu l’inizio di una **nuova era per le reti neurali**, più potente e promettente.

## **Limitazioni e sfide (anni ’90 – primi 2000)**

Nonostante i progressi degli anni ’80, le reti neurali **non si affermarono subito** come tecnologia dominante. Negli anni ’90 e nei primi anni 2000, affrontarono vari problemi.

### **Problemi di scalabilità**

* Le reti neurali di allora erano **piccole** (pochi strati, pochi neuroni).
* L’**hardware** disponibile (CPU e RAM) non permetteva di gestire reti profonde o grandi quantità di dati.
* L’addestramento richiedeva **molto tempo** e spesso portava a risultati deludenti su problemi reali.

### **Overfitting e generalizzazione**

* Le reti tendevano a **memorizzare i dati di addestramento** (overfitting), perdendo capacità di **generalizzare su nuovi dati**.
* Mancavano tecniche avanzate di regolarizzazione come il **dropout** o l’**early stopping**, oggi comuni.

### **Concorrenza di altri algoritmi**

In questo periodo, altri metodi di machine learning **ottenevano migliori risultati** con meno risorse:

* **SVM (Support Vector Machines)**: ottimi per classificazione e separazione di dati.
* **Random Forest e alberi decisionali**: più semplici da addestrare e da interpretare.
* **k-NN, Naive Bayes, boosting**, ecc.

Questi metodi erano più **affidabili**, **veloci** e **facili da usare**, per cui vennero preferiti per molti anni.

Nonostante ciò, la ricerca sulle reti neurali **continuò in sottofondo**, in attesa di nuove idee e, soprattutto, di **hardware più potente**.

## Problemi etici e sociali
Le reti neurali apprendono il comportamento umano, ma così facendo apprendono anche i **pregiudizi** e li amplificano penalizzando per esempio individui con nomi stranieri, anche se non c'è intenzione creando così problemi etici come:
- **Mancanza di trasparenza**: i ragionamenti di un algoritmo non sono sempre spiegabili essendo che operano con logica propria, il che non ci permette di capire chiaramente perchè il modello abbia fatto una scelta invece che un altra e rende difficile capire se ci siano state manipolazioni interne.
Ciò mina la fiducia che si può arrecare ad un modello di intelligenza artificiale.
- **Impatto sul lavoro**: vista la rapida crescita nella potenza dell'ai essa può sostituire gran parte dei lavori umani, in particolare quelli ripetitivi ciò porta a disoccupazione.
- **Privacy**: la privacy è un problema dell'ai in quanto analizza ogni giorno una valanga di dati personali come foto, video, chat, comportamenti e questo porta a rischi come tracciamento di massa, profilazione aggressiva e manipolazione politica.
- **Disinformazione**: le reti neurali generative (*GAN*) sono in grado di creare immagini e video che oggigiorno sono diventati alquanto realistici, l'uso di questi prodotti dell'ai, i deepfake, può portare a fake news, rovina di reputazioni e contenuti pericolosi.
- **Chi ne ha il controllo?**: I modelli più potenti di IA sono sviluppati da grandi aziende come OpenAI, google, meta, etc. Questo porta a una centralizzazione del potere centrologico e rende meno accessibile l'ai per i paesi poveri.
- **Abuso militare**: le reti neurali vengono utilizzate per:
    - Droni autonomi da guerra
    - Sorveglianza predittiva
    - Simulazioni belliche avanzate

## Sfide e possibili futuri sviluppi
Le reti neurali sono già molto avanzate ma restano in continua evoluzione e nuove sfide da affrontare per migliorarle ulteriormente. I principali miglioramenti che si vogliono apportare alle reti neurali sono:
- **Generalizzazione**: e reti neurali sono addestrate per risolvere problemi specifici ma si sta puntando alla creazione di un modello capace di risolvere problemi di vario tipo.
- **Efficienza energetica e ambientale**: le reti neurali consumano quantità enormi di energia per restare in funzione, l'obbiettivo e di creare modelli più efficienti in futuro.
- **Comprensione**: come detto prima è difficile capire come ragiona un modello, motivo per qui si lavora su tecniche di **Explainable AI** per aumentarne fiducia e trasparenza.
- **Sicurezza**: vengono studiati metodi per rendere i modelli più sicuri e meno soggetti ad attacchi.
- **Bias e giustizia algoritmica**: si cerca di creare modelli che non assorbano i pregiudizi per renderli più equi.
- **Apprendimento continuo**: si tenta di ideare modelli capaci di ricordare dalle vecchie versioni e di imparare da soli.
- **Apprendimento con pochi dati**: si vuole creare modelli che non richiedono migliaia di dati per imparare un compito.
- **Coesistenza con l'essere umano**: uno dei passi più importanti è anche capire il modo in qui l'ai potrà collaborare con l'essere umano se come copiloti inteligenti o solo sistemi che potenziano invece che sostituire.

## Conclusioni

La storia delle reti neurali artificiali è un racconto di persistenza, innovazione e cicli di entusiasmo e disillusione. Dalle prime intuizioni biologiche e dai modelli computazionali rudimentali di McCulloch-Pitts e Rosenblatt, il campo ha affrontato sfide significative, culminate nei periodi noti come "inverni dell'IA", innescati da limiti tecnologici e aspettative non realistiche. Il problema della separabilità lineare, esemplificato dal problema XOR, ha agito da catalizzatore, spingendo la ricerca verso architetture multistrato e algoritmi di apprendimento più sofisticati come la retropropagazione.

La vera rivoluzione è giunta con la convergenza di potenza computazionale (soprattutto tramite le GPU), la disponibilità di vasti dataset e l'emergere di architetture specializzate come le Reti Neurali Convoluzionali (CNN) per le immagini e le Reti Ricorrenti con LSTM per i dati sequenziali. Il riconoscimento con il Premio Nobel per la Fisica a John J. Hopfield e Geoffrey E. Hinton nel 2024 ha sancito l'impatto fondamentale di queste scoperte, che hanno trasformato l'IA da un concetto teorico in una realtà pervasiva.

Oggi, le reti neurali sono al centro di innumerevoli applicazioni che vanno dalla finanza alla medicina, dal riconoscimento vocale alla guida autonoma, rendendo l'IA uno strumento quotidiano. Tuttavia, permangono sfide significative, in particolare la natura "black box" di molti modelli, i requisiti computazionali elevati e la necessità di gestire le aspettative per evitare futuri "inverni". La traiettoria futura delle reti neurali richiederà un continuo equilibrio tra innovazione tecnologica, comprensione dei loro limiti e un approccio etico e sostenibile al loro sviluppo.
