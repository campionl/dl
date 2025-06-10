# Convoluzione e Reti Neurali Convoluzionali (CNN)  

## La Convoluzione in matematica

La **convoluzione** è un'operazione matematica che combina due funzioni per produrne una terza e descrive come la forma di una funzione viene modicata da un'altra.  

La formula è:

$$(f * g)(t) = \int_{-\infty}^{\infty} f(\tau) g(t - \tau) d\tau$$

## Cos'è la Convoluzione?  

Immagina di avere un'immagine, come una foto del tuo gatto, e vuoi insegnare a una rete neurale a riconoscere se c'è un gatto nella foto. La **convoluzione** è uno degli strumenti più potenti per farlo.  

Pensa alla convoluzione come a un piccolo "filtro" (chiamato **kernel** o **maschera**) che scorre sopra l'immagine e ne estrae informazioni locali, come bordi, linee, colori o texture.  

### Come funziona?  
1. **Hai un'immagine**: una griglia di pixel, come un disegno a quadretti.  
2. **Hai un kernel**: una griglia piccola (es. 3x3) di numeri, come questa:  
   ```  
   [ -1, 0, 1 ]  
   [ -1, 0, 1 ]  
   [ -1, 0, 1 ]  
   ```  
3. **Scorri il kernel sull'immagine**:  
   - Metti il kernel sopra un pezzetto dell'immagine (es. 3x3 pixel).  
   - Moltiplica ogni pixel del kernel con il corrispondente pixel dell'immagine.  
   - Somma tutti i risultati: questo valore diventa un nuovo pixel in una nuova "mappa delle caratteristiche" (*feature map*).  
   - Ripeti per ogni zona dell'immagine, spostandoti come una finestra scorrevole.  

### A cosa serve?  
- **Riduce la complessità**: Analizza piccole aree alla volta invece di tutta l'immagine in una volta.  
- **Preserva le relazioni spaziali**: I pixel vicini vengono analizzati insieme, mantenendo la struttura dell'immagine.  
- **Estrae caratteristiche gerarchiche**: I primi livelli catturano bordi e colori, mentre livelli più profondi riconoscono forme complesse come zampe o orecchie.  

### Esempio pratico:  
Se l'immagine ha un bordo verticale (da sinistra scuro a destra chiaro), il kernel darà un valore alto in quella zona, segnalando "qui c'è un bordo!". Strati successivi della rete useranno queste informazioni per capire se c'è un gatto.  

---  

## Cosa sono le Reti Convoluzionali (CNN)?  

Le **reti convoluzionali** (o CNN, *Convolutional Neural Networks*) sono un tipo speciale di rete neurale ispirato al modo in cui funziona il **cervello degli animali**, in particolare la **corteccia visiva**, che ci permette di riconoscere le cose.  

### Perché sono speciali?  
Le CNN sono un'evoluzione delle reti neurali tradizionali (MLP) e sono particolarmente adatte per lavorare con le immagini perché:  
- Usano pochi passaggi di pre-elaborazione.  
- Trovano autonomamente le parti importanti dell'immagine, come bordi, linee e forme, grazie ai **filtri convoluzionali**.  

### Come funzionano?  
1. **Convoluzione**: Una "lente d'ingrandimento" (kernel) scorre sull'immagine per estrarre caratteristiche locali.  
2. **Attivazione**: Una funzione (come ReLU) decide se le caratteristiche trovate sono importanti.  
3. **Pooling**: Riduce le dimensioni dell'immagine mantenendo solo le informazioni più rilevanti (es. prendendo il valore massimo in ogni zona).  
4. **Strato finale (fully connected)**: Combina tutte le caratteristiche estratte per prendere una decisione, come "questo è un gatto!".  

### Dove si usano?  
Le CNN sono ovunque:  
- **Cellulari**: per sbloccare lo schermo con il riconoscimento facciale.  
- **Robot**: per interpretare l'ambiente circostante.  
- **Auto a guida autonoma**: per riconoscere segnali stradali e pedoni.

## Come funziona il layer di Pooling nelle CNN?

Il **pooling** (o sottocampionamento) è uno strato fondamentale nelle Reti Neurali Convoluzionali (CNN) che aiuta a ridurre le dimensioni delle *feature maps* mantenendo le informazioni più importanti.

### A cosa serve il Pooling?

1. **Riduce la complessità computazionale:** Diminuisce il numero di parametri da elaborare, rendendo la rete più veloce.
2. **Mantiene le caratteristiche principali:** Conserva i dettagli più rilevanti (come bordi o forme) scartando informazioni ridondanti.
3. **Rende la rete più robusta:** Aiuta a evitare l'overfitting (memorizzazione dei dati di training invece che apprendimento).

### Perché non usare solo la Convoluzione?

- Senza pooling, le feature maps diventerebbero troppo grandi, rendendo la rete lenta e difficile da addestrare.
- Il pooling preserva l’invariante alla traslazione: se un oggetto si sposta leggermente nell’immagine, la CNN lo riconosce comunque.
