# RETI NEURALI
Le reti neurali artificiali nacquero dall'idea di replicare il funzionamento del cervello umano, dove i neuroni comunicano attraverso sinapsi. Questi modelli computazionali avrebbero poi rivoluzionato campi come il riconoscimento vocale e la visione artificiale.
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

![schema](https://github.com/campionl/dl/blob/develop/assets/neur_art.jpg)


### Le origini delle reti neurali
Tutto iniziò nel 1943 con il lavoro di McCulloch e Pitts, che crearono il primo modello matematico di neurone artificiale. Era un sistema semplice, basato su input e output binari, in grado di eseguire operazioni logiche di base come AND e OR. Tuttavia, questo neurone "statico" non poteva imparare autonomamente, poiché tutte le regole dovevano essere impostate manualmente.

### Legge di Hebb
Una svolta arrivò nel 1949 con Donald Hebb, che introdusse un principio fondamentale: se due neuroni si attivano insieme spesso, la loro connessione si rafforza. Questa intuizione gettò le basi per l'apprendimento automatico, permettendo alle reti neurali di adattarsi modificando l'importanza dei diversi pesi.

### Nascita del Percettrone
Nel 1958, Frank Rosenblatt combinò queste idee nel percettrone, la prima rete neurale in grado di apprendere.  
Il percettrone dimostrò che le macchine potevano migliorare con l'esperienza, suscitando grande entusiasmo.

Questi primi decenni mostrano come il progresso scientifico sia un processo cumulativo, dove ogni scoperta, anche se imperfetta, apre la strada a sviluppi futuri.
### Il Problema del percettrone
Ora proviamo a distinguere due gruppi di numeri:
XOR (OR Esclusivo):
- Classifica (0,0) e (1,1) come 0.
- Classifica (0,1) e (1,0) come 1.
### Esempio visivo
Ecco il disegno che spiega il problema XOR al percettrone:

```
  Y 
 1|     🟢(0,1)       🔴(1,1)
  |
 0|     🔴(0,0)       🟢(1,0)
  |
  +-----------------------> X
         0             1
```

### Soluzione?
```
       
1 |    🟢 | 🔴
  |   ----+----
0 |    🔴 | 🟢
```
Una linea deve separare 🔴 da 🟢. Non è possibile, servono 2 linee.

Per risolvere XOR servono almeno 2 linee (2 strati) che lavorino insieme!

### La Crisi del percettrone (1969): Perché quasi uccise l’AI
- Un singolo percettrone può risolvere SOLO funzioni linearmente separabili.
- Lo XOR è un problema non linearmente separabile → Impossibile per un percettrone a 2 input.
- Crollano del tutto gli investimenti per le reti neurali.

### Backpropagation - spiegazione
Backpropagation è un algoritmo che calcola l'errore commesso da una rete neurale, tornando indietro per capire dove e come ha sbagliato.  
**Esempio concreto**: immagina di avere una ricetta a strati e il risultato finale è troppo salato.  
Per correggere l'errore parte dal risultato finale (la torta è salata), analizza ogni strato uno per uno dall'ultimo al primo e aggiusta ogni passaggio per evitare l'errore.  
**Come ha risolto il problema del percettrone?**
- Con la backpropagation si sono potuti aggiungere strati nascosti, creando reti più potenti
- Ha permesso di calcolare quanto ogni strato nascosto ha contribuito all'errore così tutti i pesi possono essere aggiustati per minimizzare l'errore
- Grazie a questo meccanismo, le reti MLP hanno imparato a separare dati non linearmente divisibili  

**Problematiche**  
- Vanishing/Exploding Gradients: i gradienti (usati per aggiornare i pesi) diventavano troppo piccoli (vanishing) o troppo grandi (exploding) quando propagati attraverso molti strati.
- Dipendenza dai Dati di Training
- Overfitting: la rete memorizza i dati invece di generalizzare
### ️Multi-layer percettrone (MLP)
È possibile creare reti neurali complesse unendo più neuroni assieme, e concatenando le uscite di un gruppo di neuroni agli ingressi del successivo.  

Grazie al backpropagation, fu possibile **addestrare reti a più strati** (MLP), superando i limiti del percettrone singolo:

* I MLP possono rappresentare **funzioni non lineari complesse**,
* Riescono a **risolvere problemi come l’XOR**.

Questo segnò una **svolta fondamentale** nello sviluppo dell’intelligenza artificiale.

![schema](https://github.com/campionl/dl/blob/develop/assets/MLP.jpg)  

## Nuove limitazioni
Anche se il backpropagation aveva riacceso l’interesse negli anni ’80, negli anni ’90 e nei primi 2000 le reti neurali hanno incontrato nuovi ostacoli.

### Problemi di scalabilità
Le reti neurali di quel periodo erano spesso **piccole** (poche decine o centinaia di neuroni) perché
  - I computer erano **lenti**.
  - La memoria era **limitata**.
  - Gli algoritmi erano **troppo lenti** per le reti grandi.

### Overfitting e generalizzazione
Le reti imparavano i dati di addestramento "a memoria", quindi nei test con dati diversi facevano fatica.  

> In pratica: sembravano “intelligenti” in fase di test, ma “fallivano” con dati mai visti prima. Questo rendeva le reti **poco affidabili** in molti casi pratici.

## Il grande salto qualitativo
### RELU 

**Cos'è?**  
ReLU è una funzione matematica usata nelle reti neurali per decidere se un neurone deve "accendersi" o no.  

**Come funziona?**  
- Se l'input è **positivo**, lo lascia passare così com'è.  
  Esempio: ReLU(3) = **3**  
- Se l'input è **negativo**, lo blocca e lo trasforma in zero.  
  Esempio: ReLU(-2) = **0**  

**A cosa serve?**  
1. **Rende la rete più veloce e semplice** (rispetto a funzioni più complicate come sigmoid o tanh).  
2. **Aiuta a evitare il problema del "vanishing gradient"**, che rende difficile l'addestramento delle reti profonde.  
3. **Introduce non-linearità**, permettendo alla rete di imparare relazioni complesse.  

**Perché è importante?**  
Prima di ReLU, le reti neurali erano lente e difficili da addestrare in profondità. Con ReLU, le reti sono diventate più efficienti, aprendo la strada al deep learning moderno (come ChatGPT, riconoscimento immagini, ecc.).  

**Esempio pratico:**  
Immagina un filtro in una rete neurale che cerca bordi in un'immagine:  
- Se trova un bordo (valore positivo), lo fa passare.  
- Se non trova nulla (valore negativo), lo ignora.

![schema](https://github.com/campionl/dl/blob/develop/assets/relu_function.png)  


### RESNET - spiegazione
### **ResNet e Skip Connection - Spiegazione Super Semplice**

**Cos'è ResNet?**  
ResNet è un tipo speciale di rete neurale che può imparare anche con centinaia di strati, senza perdere efficacia. Il suo segreto? Le **skip connection** (scorciatoie intelligenti).

---

#### **Come funziona?**  
Immagina di dover imparare a riconoscere una foto di gatto:

1. **Nelle reti normali**:  
   - L'immagine passa attraverso tutti gli strati uno dopo l'altro  
   - Come un telefono senza fili: più strati ci sono, più il messaggio si distorce  

2. **In ResNet**:  
   - Ogni 2-3 strati c'è una **scorciatoia** che salta al livello successivo  
   - Funziona così:  
     ```  
     Output = Trasformazione(strati) + Input originale  
     ```  
   - Come se ogni tanto controllassi la foto originale per non perderti  

**Esempio numerico**:  
- Input (foto originale): `5`  
- Trasformazione dopo 3 strati: `+2`  
- Output finale: `5 (input) + 2 (modifiche) = 7`  

---

#### **Perché è geniale?**  
**Mantiene l'informazione originale**: Anche dopo 100 strati, la rete ricorda com'era la foto all'inizio  
**Risolve il problema dei gradienti che scompaiono**: Le correzioni arrivano fino ai primi strati  
**Permette reti super-profonde**: ResNet-152 ha 152 strati e funziona meglio di reti più corte  

---

#### **Skip Connection - Il Superpotere di ResNet**  
**Cos'è?**  
Una scorciatoia che permette all'informazione di:  
1. Passare normalmente attraverso gli strati  
2. **OPPURE** saltarli completamente e arrivare direttamente allo strato successivo  

**Come un atleta intelligente**:  
- Se il percorso è utile, lo fa tutto (impara nuove cose)  
- Se è inutile, salta gli ostacoli (risparmia energia)  

**Esempio pratico**:  
Riconoscere un gatto in una foto sfocata:  
- Gli strati profondi analizzano i dettagli (occhi, orecchie)  
- Se non trovano nulla, usano l'input originale (la foto grezza) tramite skip connection  

---

#### **Perché ha cambiato il Deep Learning?**  
Prima del 2015:  
- Le reti neurali diventavano **peggiori** oltre i 20 strati  
- Impossibile addestrare reti complesse  

Dopo ResNet:  
- Reti con **1000+ strati** addestrabili  
- Migliori prestazioni in:  
  - Riconoscimento immagini (Google Photos)  
  - Auto a guida autonoma  
  - Sistemi come ChatGPT (usano skip connection simili)  

---

#### **Esempio nella Vita Reale**  
Pensa a quando studi per un esame:  
- **Senza skip**: Rileggi tutto il libro 100 volte → alla fine non capisci più nulla  
- **Con skip**: Ogni 3 capitoli confronti con gli appunti originali → mantieni il filo logico  

![schema](https://github.com/campionl/dl/blob/develop/assets/RESNET.png)  


### GPU
Tutto iniziò con un problema semplice ma cruciale: le reti neurali, soprattutto quelle profonde, richiedevano un’enorme potenza di calcolo per essere addestrate.  

Le **CPU**, pur versatili, non erano ottimizzate per le operazioni massive e parallele richieste dal deep learning.  

Le **GPU**, invece, nate per il rendering grafico (dove devono gestire milioni di pixel simultaneamente), si rivelarono perfette. La loro architettura a **core multipli** permetteva di eseguire migliaia di operazioni in parallelo, accelerando di centinaia di volte operazioni come:  
- Le moltiplicazioni tra matrici (cuore del funzionamento di una rete neurale).  
- Le attivazioni di funzioni non lineari (come ReLU) su grandi batch di dati.  
- L’aggiornamento dei pesi durante la backpropagation.  
### **CPU vs GPU: la differenza principale** 
- Una **CPU** è come un **genio matematico** che risolve un problema alla volta, ma molto velocemente.  
- Una **GPU** è come una **squadra di 1000 studenti** che lavorano insieme su tanti piccoli calcoli contemporaneamente.  

Nelle reti neurali, dobbiamo fare **milioni di moltiplicazioni** (tra pesi e input) e somme in pochissimo tempo. Le CPU sono troppo lente perché fanno tutto in **sequenza**, mentre le GPU **parallelizzano** il lavoro, accelerando l'addestramento di **100x o più!**  

### **Perché questo è fondamentale nelle reti neurali?**  
Ogni strato di una rete neurale fa **milioni di operazioni** come queste.  
Senza GPU, addestrare un modello moderno (come ChatGPT o ResNet) richiederebbe **anni invece che giorni o ore**.  

### DROPOUT - spiegazione

## L'IA che cambia la nostra vita quotidiana  

Oggi le reti neurali sono ovunque e stanno trasformando il modo in cui viviamo e lavoriamo. Immaginate un assistente che:  

- **Vede** per noi: riconosce volti nelle foto, aiuta i medici a leggere radiografie e permette alle auto di guidare da sole.  
- **Ascolta** e parla: trascrive le nostre parole, traduce lingue straniere in tempo reale e risponde alle domande.  
- **Pensa** per noi:  
  - Nella finanza, prevede l'andamento dei mercati.  
  - Nello shopping, suggerisce prodotti che potrebbero piacerci.  
  - Al cinema, ci raccomanda film basati sui nostri gusti.  

**Dalla fabbrica all'ospedale**  
Nei laboratori simulano farmaci e malattie, nelle fabbriche controllano la qualità dei prodotti, mentre i robot imparano a muoversi in ambienti complessi. E con l'IA generativa (come ChatGPT), possiamo addirittura creare testi, immagini e musica originali!  

Una rivoluzione silenziosa che, passo dopo passo, sta rendendo le macchine sempre più "intelligenti" e utili nella vita di tutti i giorni. 

## Conclusioni
