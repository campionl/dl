# RETI NEURALI

Le **reti neurali artificiali** (Artificial Neural Networks, ANN) sono modelli computazionali ispirati al cervello umano, utilizzati in ambito informatico per risolvere problemi complessi come riconoscimento vocale, visione artificiale, traduzione automatica e molti altri.

Le reti neurali **cercano di imitare il funzionamento del cervello umano**, dove milioni di neuroni biologici comunicano tra loro attraverso connessioni chiamate **sinapsi**. Allo stesso modo, in una ANN ci sono **unità di calcolo artificiali** (i neuroni) collegate tra loro da **pesi sinaptici** che trasmettono e trasformano le informazioni.

*Essenzialmente le reti neurali sono ispirate al cervello umano, quindi alle reti neuronali, una rete neurale è formata da tanti neuroni che operano insieme per fornire un output con una semplice formula*

## Le Fondamenta Teoriche e i Primi Modelli (Anni '40 - '60)

### La Regola di Hebb (1949)

Un passo concettuale fondamentale fu la "Regola di Hebb", proposta da Donald Hebb nel 1949 nel suo libro *The Organization of Behavior*. Questa regola postulava che quando due neuroni si attivano contemporaneamente e ripetutamente, la connessione sinaptica tra di essi si rafforza. Hebb suggerì che questo meccanismo fosse alla base dell'apprendimento e della memoria nel cervello. Per le reti neurali artificiali, ciò significò l'introduzione del concetto di **pesi** per gli input, permettendo che alcuni input avessero un'influenza maggiore o minore sulla somma totale che determinava l'attivazione del neurone.  

### Il Perceptron di Rosenblatt (1958)

Basandosi sui lavori di McCulloch-Pitts e sulle intuizioni di Hebb, Frank Rosenblatt sviluppò il Perceptron nel 1958. Questa fu la prima vera rete neurale artificiale capace di apprendere. Il Perceptron era un modello feedforward con uno strato di input e un nodo di output, e i suoi pesi sinaptici erano dinamici, permettendo alla macchina di apprendere in modo elementare. Il suo campo di applicazione iniziale era il riconoscimento di forme e la classificazione binaria. Nonostante il suo potenziale e l'iniziale entusiasmo, il Perceptron ereditava la limitazione fondamentale del modello di McCulloch-Pitts: l'incapacità di risolvere problemi non lineari come il problema XOR.  

La narrazione di questo periodo mostra una chiara progressione: McCulloch-Pitts ha stabilito l'unità computazionale di base, Hebb ha introdotto il concetto cruciale di apprendimento attraverso la modifica della forza sinaptica, e Rosenblatt ha combinato queste intuizioni per creare la prima rete neurale "apprendente". Questa non è una serie di scoperte isolate, ma una costruzione continua in cui ogni idea ha informato e abilitato la successiva, evidenziando la natura cumulativa del progresso scientifico. L'iniziale ottimismo per il Perceptron, che "rivitalizzò lo studio delle ANN" e "dimostrò il potenziale delle macchine di mimare certi aspetti del processo decisionale umano" , fu rapidamente temperato dalle sue limitazioni. Questo stabilisce un modello ricorrente nel campo: l'entusiasmo iniziale e le affermazioni audaci spesso superano le attuali capacità tecnologiche, portando a periodi di disillusione che prefigurano gli "inverni dell'IA".

### Il concetto alla base

Il concetto alla base delle reti neurali è la modellazione matematica di un **neurone umano**.
Il **neurone artificiale** calcola l'output dall'input attraverso una funzione.

$$z = \chi(\sum_{i=0}^{m} w_i x_i + b)$$

dove:  
$
z = uscita\
m = numero\ di\ ingressi\ 
x_i = segnale\
w_i = peso\ del\ segnale\
b = bias\ (termine\ costante\ indipendente)\
\chi = funzione\ di\ output\
$

![schema](https://ars.els-cdn.com/content/image/3-s2.0-B9780128234884000011-f01-07-9780128234884.jpg)

---

#### Come Funziona il Perceptron

Immagina il percettrone come un piccolo robot con un cervello molto semplice. Questo robot riceve informazioni (numeri) e poi decide "Sì" o "No", tipo come se fosse una lucina che si accende o resta spenta.

---

#### Passo 1: Riceve i numeri
Il percettrone ha delle antenne (che chiamiamo input), tipo:

È caldo oggi? (1 se sì, 0 se no)

C'è sole? (1 se sì, 0 se no)

Hai dormito bene? (1 o 0)

Questi numeri sono segnali che arrivano.

---

#### Passo 2: Pesa i segnali
Ogni antenna ha un peso (come se ci fosse un volume). Il percettrone moltiplica ogni numero ricevuto per il suo peso.

Esempio:

Sole 1 × peso 0.6 = 0.6

Caldo 1 × peso 0.3 = 0.3

Dormito male 0 × peso 0.9 = 0

Poi somma tutto: 0.6 + 0.3 + 0 = 0.9

---

#### Passo 3: Confronta con una soglia
Il robot ha una soglia. Se il risultato totale è più grande della soglia, decide:

`"Sì" (accende la luce)`

`"No" (lascia la luce spenta)`

```
Esempio:

Totale = 0.9

Soglia = 0.5

È più grande? Sì!

Il robot dice "Sì!"
```

---

#### Cosa può fare?
Il percettrone può imparare a:

Riconoscere se un'email è spam o no

Dire se una foto è un gatto o un cane

Capire se devi saltare in un gioco o no

Ma è molto semplice, e può fare solo cose base.

---

#### Come migliora?
Quando sbaglia, cambia i suoi pesi un po’, come un bambino che impara dai suoi errori. Col tempo diventa più bravo.

---

## Multilayer Perceptron (MLP)

---

#### Cos'è un MLP?

Un **Multilayer Perceptron** è una rete neurale artificiale formata da più strati di **neuroni** (o nodi). È un'estensione del percettrone semplice e permette di risolvere problemi **non lineari** grazie all'uso di **layer nascosti**.

---

#### Struttura

| Tipo di Layer        | Funzione                                                                 |
|----------------------|--------------------------------------------------------------------------|
| **Input Layer**       | Riceve i dati in ingresso (es. numeri, pixel, valori di sensori)        |
| **Hidden Layer(s)**   | Uno o più strati che elaborano i dati, applicando trasformazioni        |
| **Output Layer**      | Restituisce il risultato finale (es. classificazione o valore previsto) |

Ogni neurone in un layer è **completamente connesso** a tutti i neuroni del layer successivo.

---

#### Esempio semplice

Input:  
- Battito cardiaco  
- Pressione sanguigna  
- Temperatura corporea

Output:  
- Persona sana  
- Persona non sana  

---

#### Perché è utile?

| Vantaggio                       | Descrizione                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|
| **Non lineare**              | Impara relazioni complesse, non solo lineari                                |
| **Generalizza bene**         | Sa rispondere anche su esempi mai visti prima                               |
| **Modulo base di altri modelli** | È la base di reti più evolute (CNN, RNN, Transformer)                     |
| **Applicabile a molti campi** | Finanza, medicina, marketing, robotica, ecc.                               |

---

#### Limiti

- Poco adatto per immagini o sequenze lunghe
- Richiede molti dati e potenza di calcolo
- Rischio di **overfitting** se troppo complesso

---

#### Applicazioni pratiche

- Riconoscimento vocale
- Classificazione email (spam/non-spam)
- Previsioni finanziarie
- Analisi mediche
- Moduli interni in modelli NLP e visione artificiale

---

#### Conclusione

Il **MLP** è un modello fondamentale del deep learning. Anche se da solo non è sempre sufficiente per problemi complessi come immagini o testi lunghi, rappresenta il punto di partenza per comprendere architetture moderne come le **reti convoluzionali** e i **transformer**.

---

## Il Perceptrone, il Problema dell'XOR e la Grande Rinascita

#### Cos'è un perceptrone?

Immagina un piccolo robot (o un bambino) a cui dai dei numeri, e lui prova a dirti se qualcosa è vero o falso. Ad esempio:

> Se gli dai 2 voti scolastici e lui deve dire se sei promosso.

Il **perceptrone** è questo piccolo robot: prende dei numeri in ingresso, fa qualche calcolo molto semplice, e ti dà una risposta (0 o 1).

---

#### Il problema dello XOR: il rompicapo che lo ha bloccato

Il perceptrone funzionava bene per problemi semplici, ma... poi arrivò un problema molto speciale: **XOR** (si legge "ex-or").

#### Cos'è XOR?

Ecco la tabella:

| Input 1 | Input 2 | Risposta giusta (XOR) |
|---------|---------|------------------------|
|   0     |    0    |           0            |
|   0     |    1    |           1            |
|   1     |    0    |           1            |
|   1     |    1    |           0            |

Il problema? Non puoi **disegnare una riga dritta** che separi i numeri che danno 1 da quelli che danno 0. E il perceptrone sa usare solo **una riga dritta**.

---

#### La crisi del perceptrone (1969)

Due scienziati, **Marvin Minsky** e **Seymour Papert**, scrissero un libro chiamato **"Perceptrons"** e dissero:

> "Ehi, questo robottino non potrà mai imparare cose complicate come XOR!"

Risultato?

- Le persone smisero di investire nei robot intelligenti
- Per anni nessuno credeva più nelle **reti neurali**
- Fu come se il sogno dell’intelligenza artificiale fosse morto

---

#### La rinascita: Backpropagation (1986)

Anni dopo, alcuni scienziati (Rumelhart, Hinton e Williams) dissero:

> "E se invece mettessimo **più robottini in fila**, uno dietro l’altro? E se insegnassimo loro a **collaborare**?"

Ecco che nasce il **Multilayer Perceptron** (MLP): tanti robottini in strati!

Ma serviva un trucco magico per insegnargli bene. Così tirarono fuori un vecchio trucco:

#### Il trucco: **Backpropagation**

# Come funziona il Backpropagation

## Cos’è il Backpropagation?

Il backpropagation è un metodo che permette a una rete neurale di **imparare dai propri errori**.  
È il processo con cui la rete aggiusta i suoi pesi per migliorare le sue risposte.

---

## Il processo in 3 passaggi

1. **Forward Pass (Prova a indovinare)**  
   La rete prende un input, lo elabora e produce un output (una previsione).

2. **Calcolo dell’errore**  
   Confronta l’output prodotto con la risposta corretta e calcola l’errore (quanto si è sbagliato).

3. **Backward Pass (Impara dagli errori)**  
   L’errore viene "propagato all’indietro" nella rete per capire quali pesi hanno causato l’errore.  
   La rete modifica quei pesi per sbagliare meno la prossima volta.

---

## Spiegazione tecnica semplificata

- La rete è fatta di strati con **neuroni** collegati da **pesi**.
- Ogni neurone riceve input, li moltiplica per i pesi, somma il tutto e applica una funzione di attivazione.
- Nel **forward pass**, la rete calcola il risultato finale.
- Nel **backward pass**, il sistema usa la **derivata della funzione di attivazione** e la **regola della catena** per calcolare quanto ogni peso ha contribuito all’errore.
- I pesi vengono aggiornati usando la **discesa del gradiente**:
  
  \[
  w := w - \eta \cdot \frac{\partial \text{Loss}}{\partial w}
  \]

  Dove:  
  - \( w \) è il peso  
  - \( \eta \) è il learning rate (quanto velocemente impariamo)  
  - \( \frac{\partial \text{Loss}}{\partial w} \) è la pendenza dell’errore rispetto al peso

---

## Riassunto

| Fase           | Cosa succede                                           |
|----------------|--------------------------------------------------------|
| Forward pass   | Calcola l’output a partire dall’input                   |
| Calcolo errore | Confronta output e risultato atteso                    |
| Backward pass  | Calcola come ogni peso ha influenzato l’errore         |
| Aggiornamento  | Modifica i pesi per migliorare la rete la prossima volta|

---

## Perché è importante?

Senza il backpropagation, la rete non saprebbe come migliorare, quindi non imparerebbe mai bene.  
È il cuore dell’apprendimento nelle reti neurali moderne!

---

#### Perché il Multilayer Perceptron ha risolto tutto?

Perché, a differenza del percettrone singolo, usa **strati nascosti**.

Immagina una squadra di bambini, dove ognuno si occupa di una parte del problema:

- Uno guarda solo le orecchie
- Uno guarda il muso
- Uno guarda la coda

Insieme, mettono insieme le informazioni per prendere decisioni più **intelligenti e complesse**.

---

#### Conclusione

- Il percettrone è stato il primo passo.
- Ha fallito su problemi come **XOR**.
- Per questo tutti avevano perso fiducia.
- Ma grazie a **più strati** e al **backpropagation**, le reti neurali sono tornate più forti che mai!
- Oggi sono il cuore dell’**intelligenza artificiale moderna**: traduzioni, immagini, robot, auto che guidano da sole... tutto parte da lì!

---

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

## Architetture di Reti Neurali

Negli ultimi 10-15 anni c'è stata un esplosione di nuove architetture cambiando il modo di affrontare l'inteligenza artificiale.
Queste nuove architetture inolte hanno portato ad un miglioramento in termini di prestazioni, capacità applicative e applicazioni pratiche.

#### 1. Perceptron
- **Nome completo:** Perceptron (o MLP: Multi-Layer Perceptron)
- **Uso:** Classificazione base, regressione
- **Descrizione:** Rete completamente connessa (fully-connected). Usata per problemi semplici e strutturati (dati tabellari).
- **Limiti:** Non scala bene su dati complessi (es. immagini, testo)

#### 2. CNN - Convolutional Neural Network
- **Uso:** Immagini, video, visione artificiale
- **Descrizione:** Usa **strati convoluzionali** per riconoscere pattern spaziali locali.
- **Componenti chiave:**
  - Convoluzione
  - Pooling
  - Flatten → Dense
- **Esempi famosi:** LeNet, AlexNet, VGG, ResNet

#### 3. RNN - Recurrent Neural Network
- **Uso:** Dati sequenziali (testo, serie temporali, audio)
- **Descrizione:** Ha una **memoria interna** che considera lo stato precedente per produrre l’output.
- **Problema:** Soffre di vanishing gradient.
- **Varianti migliorate:** LSTM, GRU

#### 4. LSTM - Long Short-Term Memory
- **Uso:** Traduzione, generazione testo, audio, classificazione sequenze
- **Descrizione:** Variante di RNN che risolve il problema del vanishing gradient grazie a **gates** (porte logiche: input, forget, output)
- **Punti di forza:** Ottima per sequenze lunghe e contesti di memoria persistente

#### 5. GRU - Gated Recurrent Unit
- **Uso:** Simile a LSTM, ma più leggero
- **Descrizione:** RNN con meno porte rispetto a LSTM (solo update e reset). Più veloce e meno costoso computazionalmente.
- **Pro:** Compromesso tra performance e velocità

#### 6. Autoencoder
- **Uso:** Compressione, riduzione dimensionale, denoising, anomaly detection
- **Descrizione:** Rete simmetrica (Encoder → Bottleneck → Decoder). Impara a ricostruire input.
- **Varianti:** Denoising Autoencoder, Variational Autoencoder (VAE)

#### 7. GAN - Generative Adversarial Network
- **Uso:** Generazione di immagini, deepfake, super-risoluzione
- **Descrizione:** Due reti che competono: **Generatore** vs **Discriminatore**
- **Output:** Immagini realistiche da rumore
- **Problema:** Instabilità nel training

#### 8. ResNet - Residual Network
- **Uso:** Visione artificiale avanzata (ImageNet, classificazione immagini)
- **Descrizione:** Rete CNN profonda con **residual connections** (skip connections) per evitare vanishing gradient.
- **Pro:** Permette reti con 50+ layer senza degrado

#### 9. Transformer
- **Uso:** NLP, traduzione, sintesi, codifica testo, anche visione (Vision Transformer)
- **Descrizione:** Basato su **self-attention**, non usa RNN
- **Esempi:** BERT, GPT, T5
- **Punti di forza:** Parallelizzabile, gestisce contesti lunghi
- **Formula chiave:** `Attention(Q, K, V) = softmax(QKᵀ / √d) * V`

#### 10. BERT - Bidirectional Encoder Representations from Transformers
- **Uso:** NLP: classificazione, estrazione, risposta a domande
- **Descrizione:** Solo encoder dei Transformer, preaddestrato con masked language modeling
- **Pro:** Capisce il **contesto bidirezionale** di una frase

#### 11. GPT - Generative Pretrained Transformer
- **Uso:** Generazione testo, chatbot, completamento
- **Descrizione:** Solo decoder dei Transformer, addestrato in modo autoregressivo
- **Pro:** Eccellente per generazione creativa e linguaggio naturale

#### 12. ViT - Vision Transformer
- **Uso:** Visione artificiale avanzata, classificazione immagini
- **Descrizione:** Applica il meccanismo dei Transformer alle immagini suddivise in patch
- **Pro:** Supera le CNN in alcuni task di visione, ma richiede molti dati

#### 13. Capsule Network (CapsNet)
- **Uso:** Riconoscimento immagini avanzato (es. rotazioni, affini)
- **Descrizione:** Mantiene la relazione spaziale tra le feature usando "capsule" invece dei semplici neuroni
- **Pro:** Più resistente alle trasformazioni rispetto a CNN
- **Contro:** Computazionalmente pesante, difficile da allenare

#### 14. Siamese Network
- **Uso:** Verifica di similarità (es. riconoscimento facciale, firma)
- **Descrizione:** Due sottoreti con pesi condivisi che producono embedding confrontabili
- **Output:** Distanza tra due input (simili o diversi)

#### 15. Reti Neurali Spiking (SNN)
- **Uso:** Neuroscienze, simulazioni cervello umano, robotica neurale
- **Descrizione:** I neuroni comunicano tramite spike (impulsi discreti). Ispirati al cervello biologico.
- **Pro:** Basso consumo energetico
- **Contro:** Difficile da addestrare con backpropagation standard

---

## Il ruolo dell'hardware
Con l'evoluzione dell'AI c'è stato bisogno anche per l'hardware di evolversi, questo legame porta ad un parallelismo tra i due.  
Le **CPU** ovvero i normali processori non erano abbastanza potenti e veloci per gestire le migliaia di operazioni parallele, d'altro canto le **GPU** ovvero le schede video nate per i videogiochi erano perfette per il calcolo parallelo dei dati.  
Possiamo affermare che in questo campo **NVIDIA** è il campione indiscusso, assieme al suo **CUDA** infatti fù capace di ridurre il tempo degli addestramenti da quelli che prima erano giorni o settimane in ore.  
Le **GPU** servono quindi ad addestrare i modelli ed eseguire inferenze in tempo reale. Le TPU, creazione di google, sono state create **specificatamente** per il machine learning. Sono poi stati creati servizi in cloud come AWS, Google Cloud, OpenAI e Azure che permettono di addestrare un modello senza il bisogno di possedere un supercomputer.

---

## Il ruolo del software


#### Evoluzione del Software: La Chiave per il Salto del Deep Learning

Lo sviluppo del deep learning non sarebbe mai esploso senza una rivoluzione parallela nel **software**. Per quanto l’hardware (GPU, CPU, TPU) sia stato fondamentale, è il **software** che ha reso davvero accessibili e gestibili reti neurali sempre più complesse anche a chi non era un esperto.

#### Dagli Anni ‘60 ai Primi Tool

Nei primi decenni, le reti neurali venivano costruite **a mano**, spesso scrivendo codice in linguaggi complessi come **Fortran** o **C**. Non c’erano strumenti per calcolare automaticamente i gradienti, né per visualizzare cosa accadeva dentro la rete. Tutto era artigianale, lento, e poco flessibile.

Inoltre, mancava **una comunità di sviluppo unificata** e il software era spesso scritto per un solo esperimento, senza riutilizzabilità.

#### La Prima Svolta: Theano e Torch (2007-2015)

L'arrivo di **Theano** (dall’università di Montreal) e **Torch** (originariamente sviluppato a NYU) ha segnato una svolta:

- **Theano** permetteva il calcolo simbolico dei gradienti (backpropagation automatica).
- **Torch**, basato su Lua, era uno dei primi framework orientati agli oggetti e alla modularità.
  
Questi strumenti hanno permesso ai ricercatori di **astrarre la matematica** e concentrarsi sulla struttura della rete.

#### La Rivoluzione Accessibile: TensorFlow e PyTorch

A partire dal 2015-2016, due nuovi strumenti hanno cambiato tutto:

#### TensorFlow (Google, 2015)
- Offre calcolo distribuito su CPU/GPU/TPU.
- Ha un sistema di grafi statici (TensorFlow 1.x), ottimo per la produzione.
- Più difficile da debuggare inizialmente, ma molto potente.
  
#### PyTorch (Meta/Facebook, 2016)
- Usa grafi dinamici → il codice si comporta in modo simile a Python nativo.
- Facilissimo da testare, modificare e capire → **ha conquistato il mondo della ricerca**.
- È oggi uno standard di fatto per la maggior parte dei modelli open source.

#### Funzionalità Chiave Introdotte

Questi software hanno reso possibili:
- **Backpropagation automatica**: non serve più calcolare a mano i gradienti.
- **Layer modulari**: le reti possono essere costruite con blocchi riutilizzabili.
- **Training parallelo**: sfruttano le GPU per allenare modelli in pochi minuti invece che giorni.
- **Framework high-level** come Keras (per TensorFlow) semplificano ancora di più il lavoro.

#### Il Salto di Qualità

Con queste librerie, anche un liceale o uno studente universitario può:
- Costruire una rete neurale in 5 righe di codice.
- Caricare un modello preaddestrato (es. GPT, ResNet) e usarlo per i propri dati.
- Allenare modelli su dataset reali senza bisogno di creare tutto da zero.

In pratica, il software ha **democratizzato l'intelligenza artificiale**.

#### In Sintesi

| Epoca | Strumento | Vantaggi principali |
|-------|-----------|---------------------|
| Anni '60-'90 | Codice manuale in C/Fortran | Lento, complesso, nessuna astrazione |
| 2007-2015 | Theano, Torch | Calcolo automatico, modularità |
| 2015-2020 | TensorFlow, PyTorch | Accessibilità, flessibilità, potenza |
| 2020+ | Hugging Face, AutoML, Lightning | Modelli pronti all’uso, semplificazione estrema |

---

> Senza questa evoluzione del software, le reti neurali profonde sarebbero rimaste nei laboratori. Invece, grazie a strumenti potenti e aperti, oggi chiunque può contribuire all’AI.

