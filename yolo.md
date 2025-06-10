# YOLO
You Only Look Once è un sistema di rilevamento oggetti in tempo reale, basato su reti neurali convoluzionali, che ha rivoluzionato il campo dell'elaborazione delle immagini.
## Cos'è YOLO?
YOLO è un algoritmo di rilevamento oggetti che esegue la classificazione e la localizzazione degli oggetti in un'unica passata attraverso l'immagine, da cui il nome "You Only Look Once".  
YOLO analizza l'intera immagine contemporaneamente per rilevare gli oggetti e determinarne la posizione.  
## Come funziona YOLO?
YOLO divide l'immagine in una griglia e, per ogni cella della griglia, predice le probabilità di classificazione degli oggetti e le coordinate dei bordi dei rettangoli di delimitazione. In questo modo, l'algoritmo riesce a rilevare simultaneamente più oggetti in un'unica immagine, con una velocità e precisione significative. 
## Perché YOLO è importante?
YOLO è diventato uno dei modelli più popolari per il rilevamento oggetti grazie alla sua velocità e accuratezza, permettendo applicazioni in vari campi come l'automazione, la sicurezza e la guida autonoma. 
In sintesi:
YOLO è un sistema di rilevamento oggetti in tempo reale, basato su reti neurali convoluzionali, che esegue la classificazione e la localizzazione degli oggetti in un'unica passata attraverso l'immagine. Questa tecnologia ha rivoluzionato il campo dell'elaborazione delle immagini, permettendo applicazioni in vari settori.
# Come Funziona YOLO?
Immagina di essere un **super-poliziotto robot** che guarda una foto e in **meno di un secondo** deve:
1. **Trovare tutti gli oggetti** (gatti, auto, biciclette...).  
2. **Disegnare un riquadro** intorno a ognuno.  
3. **Dire cos'è** ogni oggetto.  

YOLO fa tutto questo **in un solo colpo d'occhio** (da qui il nome *You Only Look Once*).  

---

## **1. Suddivisione in Griglia (Grid Cells)**
- **Passo 1**: YOLO divide l'immagine in una **griglia** (es. 13x13 celle).  
  - Ogni cella è come un **"piccolo investigatore"** che cerca oggetti al suo interno.
---

## **2. Ogni Cella Predice Bounding Boxes**
La **bounding box** (o "riquadro di delimitazione") è il cuore di YOLO: è il rettangolo che disegna intorno agli oggetti che rileva.
Ogni cella della griglia dice:  
- **"Ehi, qui potrebbe esserci un oggetto!"** → **bounding box**.  
  - Per ogni bounding box, YOLO usa coordinate  **relative**  (normalizzate tra 0 e 1) per essere indipendente dalla dimensione dell'immagine:
-   `x`  e  `y`  = posizione del centro  **rispetto alla cella della griglia**.  
-   `w`  e  `h`  = larghezza/altezza  **rispetto all'intera immagine**.
  -Ogni bounding box ha un  **punteggio di confidenza**  (tra 0 e 1) che dice:
-   **Quanto è sicuro**  che ci sia davvero un oggetto lì dentro.
-   **Quanto è accurato**  il riquadro.
---
#### **Non-Maximum Suppression (NMS)**
-   **Elimina i riquadri sovrapposti**  tenendo solo i migliori.
-   Passaggi:
    1.  Ordina le bounding box per  **confidence score**.
    2.  Tieni quella con il punteggio più alto.
    3.  Elimina tutte le altre che si sovrappongono troppo (**IOU > soglia**).
**Cos'è IOU (Intersection over Union)?**
-   Misura  **quanto si sovrappongono**  due riquadri.
-   Se  `IOU > 0.5`  (esempio), YOLO considera che siano lo stesso oggetto.
---

## **4. L'Architettura di YOLO**
YOLO è diviso in 3 parti principali:  

### **Backbone**
- È una **CNN (Convolutional Neural Network)** che estrae features (es. Darknet-53 in YOLOv3, CSPNet in YOLOv4).  
- **Cosa fa?**  
  - Guarda l'immagine e cerca **linee, colori, forme** (livelli iniziali).  
  - Poi riconosce **zampe, ruote, occhi** (livelli profondi).  
*(Come quando impari a disegnare: prima fai le linee generali, poi i dettagli!)*  
### **Neck**
- **FPN (Feature Pyramid Network) o PANet**: Prende features a diversi livelli e le combina.  
- **Perché?** Per rilevare **oggetti piccoli e grandi**!  
  - Le features a **bassa risoluzione** vedono oggetti grandi.  
  - Le features ad **alta risoluzione** vedono oggetti piccoli.  
*(Come se usassi una lente d'ingrandimento per i dettagli e un drone per la vista dall'alto!)*  
### **Head**
- Prende le features e **predice bounding box + classi**(Le categorie degli oggetti che YOLO può riconoscere (es. "cane", "gatto", "auto").  
- Usa **anchor boxes** (forme predefinite di riquadri) per aiutare a stimare meglio.  
*(Come se avessi degli "stampini" per disegnare meglio i riquadri intorno agli oggetti!)*  

---

## **5. Come YOLO impara? (Training)**
- **Input**: Immagini + Bounding box già annotate (es. "Gatto a x=100, y=50, w=30, h=40").  
- **Loss Function**: Una formula che misura l'errore tra:  
  - Predizioni di YOLO vs. Bounding box veri.  
  - Penalizza errori su:  
    - Coordinate (x,y,w,h).  
    - Confidence score.  
    - Classi sbagliate.  
- **Ottimizzazione**: La rete **aggiusta i suoi pesi** (backpropagation) per ridurre l'errore. 
---
## **8. Problemi di YOLO (Limiti)**
- **Oggetti piccoli**: Se sono troppo piccoli, YOLO potrebbe perderli.  
- **Oggetti sovrapposti**: Se due cani sono troppo vicini, potrebbe vederli come uno solo.  
- **Luci/ombre**: Condizioni di luce difficili possono confonderlo.  

**Soluzioni**:  
- Usare **YOLOv7/v8** (migliorati sui piccoli oggetti).  
- Aggiungere più dati di addestramento.  
