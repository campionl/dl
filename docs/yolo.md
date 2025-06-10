# YOLO
***You Only Look Once*** è un **sistema di rilevamento oggetti** in tempo reale, basato su **reti neurali convoluzionali**, che ha rivoluzionato il campo dell'elaborazione delle immagini.
## Cos'è YOLO?
YOLO è un **algoritmo di rilevamento oggetti** che esegue la classificazione e la localizzazione degli oggetti in un'unica passata attraverso l'immagine, da cui il nome "*You Only Look Once*". 
YOLO analizza l'intera immagine contemporaneamente per rilevare gli oggetti e determinarne la posizione.
## Come funziona YOLO?
YOLO divide l'immagine in una griglia e, per ogni cella della griglia, **predice le probabilità** di classificazione degli oggetti e le coordinate dei bordi dei rettangoli di delimitazione. In questo modo, l'algoritmo riesce a **rilevare simultaneamente più oggetti** in un'unica immagine, con una velocità e precisione significative.
In una frazione di secondo è in grado di:
- Trovare tutti gli oggetti (gatti, auto, biciclette...)
- Disegnare un riquadro intorno a ognuno
- Stabilire cos'è ogni oggetto.

### 1 - Suddivisione in Griglia (Grid Cells)
YOLO divide l'immagine in una **griglia** (es. 13x13 celle), ogni cella è come un "piccolo investigatore" che cerca oggetti al suo interno.

### 2 - Ogni Cella Predice *Bounding Boxes*
La ***bounding box*** (o "riquadro di delimitazione") è il cuore di YOLO: è il rettangolo che disegna intorno agli oggetti che rileva.
Ogni cella della griglia dice: 
- **"Qui potrebbe esserci un oggetto"** → **bounding box**. 
	- Per ogni *bounding box*, YOLO usa coordinate **relative** (normalizzate tra 0 e 1) per essere indipendente dalla dimensione dell'immagine:
		-  `x` e `y` indicano la posizione del centro **rispetto alla cella della griglia**.
		-  `w` e `h` indicano la larghezza e l'altezza del box **rispetto all'intera immagine**.
	- Ogni *bounding box* ha un **punteggio di confidenza** (tra 0 e 1) che dice:
		- **Quanto è sicuro** che ci sia davvero un oggetto lì dentro.
		- **Quanto è accurato** il riquadro.
---
#### **Non-Maximum Suppression (NMS)**
**Elimina i riquadri sovrapposti** tenendo solo i migliori:
1. Ordina le bounding box per **confidence score**.
2. Tieni quella con il punteggio più alto.
3. Elimina tutte le altre che si sovrappongono troppo (**IOU > soglia**).

**Cos'è IOU (Intersection over Union)?**
-  Misura **quanto si sovrappongono** due riquadri.
-  Se `IOU > 0.5` (esempio), YOLO considera che siano lo stesso oggetto.
---

## L'Architettura di YOLO
YOLO è diviso in 3 parti principali: 
### 1 - Backbone
È una **CNN (Convolutional Neural Network)** che estrae features (es. Darknet-53 in YOLOv3, CSPNet in YOLOv4). 
Guarda l'immagine e cerca **linee, colori, forme** (livelli iniziali), poi riconosce **zampe, ruote, occhi** (livelli profondi). 
*(Come quando impari a disegnare: prima fai le linee generali, poi i dettagli!)* 
### 2 - Neck
**FPN (Feature Pyramid Network) o PANet**: Prende features a diversi livelli e le combina. 
Per rilevare **oggetti piccoli e grandi**! 
- Le features a **bassa risoluzione** vedono oggetti grandi. 
- Le features ad **alta risoluzione** vedono oggetti piccoli. 
*(Come se usassi una lente d'ingrandimento per i dettagli e un drone per la vista dall'alto!)* 
### 3 - Head
Prende le features e **predice bounding box e classi** (le categorie degli oggetti che YOLO può riconoscere, come "cane", "gatto", "auto"). 
Usa **anchor boxes** (forme predefinite di riquadri) per aiutare a stimare meglio. 
*(Come se avessi degli "stampini" per disegnare meglio i riquadri intorno agli oggetti!)* 

## Come impara YOLO? (Training)
**Input**: Immagini + Bounding box già annotate (es. "Gatto a x=100, y=50, w=30, h=40"). 
**Loss Function**: Una formula che misura l'errore tra: 
- Predizioni di YOLO vs. Bounding box veri. 
- Penalizza errori su: 
	- Coordinate (x,y,w,h). 
	- Confidence score. 
	- Classi sbagliate. 
**Ottimizzazione**: la rete **aggiusta i suoi pesi** (backpropagation) per ridurre l'errore. 

## Perché YOLO è importante?
YOLO è diventato uno dei modelli più popolari per il rilevamento oggetti grazie alla sua **velocità e accuratezza**, permettendo applicazioni in vari campi come l'automazione, la sicurezza e la guida autonoma. 

## Problemi di YOLO
- **Oggetti piccoli**: se sono troppo piccoli, YOLO potrebbe perderli. 
- **Oggetti sovrapposti**: se due cani sono troppo vicini, potrebbe vederli come uno solo. 
- **Luci / Ombre**: condizioni di luce difficili possono confonderlo. 

### Soluzioni
- Usare **YOLOv7/v8** (migliorati sui piccoli oggetti). 
- Aggiungere **più dati** di addestramento. 

# Storia di YOLO

## Pre-YOLO: il contesto storico
Prima di YOLO, i modelli di *object detection* si basavano su approcci complessi e lenti:  
- **R-CNN (2014)**: utilizzava una pipeline a più stadi (selezione di parti dell'immagine dove potrebbero esserci oggetti + classificazione).  
- **Fast R-CNN (2015)**: migliorava l'efficienza ma manteneva la complessità.  
- **Faster R-CNN (2015)**: introduceva le "Region Proposal Networks" (RPN), ma era ancora troppo lento per applicazioni real-time.  

## 2015 – Nascita di YOLO
- Creato da **Joseph Redmon** e il suo team (incluso Ali Farhadi).  
- Pubblicato per la prima volta in un **articolo scientifico** (arXiv:1506.02640).
- Idea rivoluzionaria: **analizzare l’immagine una sola volta** invece di usare metodi lenti come R-CNN.  

## 2016 – YOLOv2 (o YOLO9000)
- Miglioramenti nella **precisione** e **velocità**.  
- Introdotto il concetto di **"anchor boxes"** (template o forma predefinita che la rete usa come punto di partenza) per gestire meglio le dimensioni degli oggetti.  
- Poteva riconoscere oltre **9000 classi** di oggetti (da qui il nome YOLO9000).  

## 2018 – YOLOv3
- Ancora più **preciso**, grazie a una rete neurale più profonda ([**Darknet-53**](https://www.geeksforgeeks.org/darknet-53/)).  
- Miglior gestione degli **oggetti piccoli**.  
- Rimase lo **standard** per anni.  

## 2020 – YOLOv4 e YOLOv5 (dopo l'abbandono di Redmon)
- **YOLOv4** (Aprile 2020): Sviluppato da **Alexey Bochkovskiy**, con ottimizzazioni per **velocità** e **precisione**.  
- **YOLOv5** (Giugno 2020): Creato da **Ultralytics**, più facile da usare e con prestazioni simili a v4.  
- Redmon si era **ritirato per preoccupazioni etiche** sull'uso militare dell'AI.  

## 2022-2023 – YOLOv6, v7, v8, v9…
- La community ha continuato a migliorare YOLO con nuove versioni (spesso sviluppate da team diversi).  
- **YOLOv8** (2023) è oggi molto popolare per applicazioni in tempo reale.  

# L'inventore di YOLO: Joseph Redmon

Il principale ideatore del sistema YOLO (*You Only Look Once*) è **Joseph Redmon**.

![Joseph Redmon](./assets/joseph_redmon.jpeg)

## Formazione
Joseph Redmon è un **informatico** e **matematico** statunitense, ha conseguito un **dottorato** di ricerca in *Computer Science* presso l'Università di Washington.

## I lavori
Nell'arco della sua vita ha contribuito alla realizzazione di YOLO e Darknet.
**YOLO** è un algoritmo di ***object-detection*** che analizza le immagini con un approccio unificato che applica una **singola rete neurale** all'intera immagine, dividendola in regioni e prevedendo le *bounding box* (caselle di delimitazione) e le probabilità per ogni regione, questo ha permesso di raggiungere velocità di rilevamento degli oggetti in tempo reale senza precedenti.
**Darknet** è un framework open-source per il deep learning, scritto in C e CUDA, utilizzato per implementare YOLO.

## Il suo ritiro
Nel 2020 si ritirò dal campo della ricerca sui modelli di intelligenza artificiale per motivi etici, su Twitter dichiarò:

> *Ho smesso di lavorare nel campo dell'AI perché non mi sentivo a mio agio con l'uso militare e la sorveglianza di massa della tecnologia che ho contribuito a creare.*

Ha infatti criticato progetti come **Google Maven** (AI per droni militari) e le collaborazioni tra università e dipartimenti di difesa.

Attualmente mantiene il suo progetti open-source come *Darknet Neural Network Framework* (ma non li aggiorna), partecipa occasionalmente a discussioni su AI etica e open-source e lavora come programmatore freelance e scienziato informatico.