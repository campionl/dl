s# Consigli per la creazione di una rete neurale

Quando creiamo una rete neurale è importante riconoscere quando creare un nuovo livello e quando aggiungere un neurone ad un livello,
qui sotto c'è una guida per queste decisioni.

## Guida: Numero di Neuroni per Layer in una Rete Neurale

| Caso / Configurazione                         | Esempio (neuroni per layer) | Motivo                                                                                       | Quando usarla                                                                                 |
|----------------------------------------------|------------------------------|----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| - Input scarso, output ricco                 | 1 → 4                        | Estrazione di molte feature da pochi input. Serve espansione di rappresentazione.            | Quando hai un input semplice ma vuoi modellare fenomeni complessi (es. 1 valore → 4 categorie). |
| - Input ricco, output semplice               | 8 → 2                        | Compressione: i layer successivi imparano a sintetizzare le informazioni.                    | Es. immagini 28x28 → classificazione binaria.                                                   |
| - Struttura a clessidra (bottleneck)         | 16 → 4 → 16                  | Compressione e decompressione (tipo autoencoder). Il layer stretto forza l’apprendimento utile. | Compressione dati, denoising, feature extraction.                                               |
| - Architettura piramidale (decrescente)      | 64 → 32 → 16                 | Riduzione progressiva della dimensionalità → migliora generalizzazione.                      | Classificazione, regressione, riduzione del rumore.                                             |
| - Architettura piramide inversa (crescente)  | 8 → 16 → 32                  | Usata per generazione o upscaling (es. GAN, decoder, generazione testi o immagini).          | Decoder, generatori (es. VAE decoder, GAN generator).                                           |
| - Stesso numero di neuroni in ogni layer     | 16 → 16 → 16                 | Stessa capacità elaborativa a ogni livello. Rischia overfitting.                             | Quando non conosci bene i dati e vuoi una base uniforme.                                        |
| - Troppi neuroni nel primo layer             | 128 → 64 → 32                | Rischia overfitting: troppa capacità sin dall'inizio.                                        | Da evitare se l’input è semplice o rumoroso.                                                    |
| - Pochi neuroni nel primo layer              | 2 → 8 → 16                   | Primo layer perde informazione; il secondo tenta di ricostruirla → inefficienza.             | Evitare se l’input ha molte feature importanti.                                                 |
| - Layer centrale troppo piccolo              | 64 → 2 → 64                  | Bottleneck troppo stretto → perde troppe info.                                                | Utile solo se vuoi forzare un embedding molto compatto.                                         |
| - Tanti layer con pochi neuroni              | 8 → 8 → 8 → 8 → 8            | Approfondisci la rete senza aumentare la capacità troppo.                                    | NLP, RNN, transformers con deep attention.                                                      |

---

## Considerazioni Importanti

- **Primo layer**: dovrebbe avere almeno tanti neuroni quante feature in input.
- **Ultimo layer**: tanti neuroni quanti valori in output (es. 1 per regressione, N per classificazione).
- **Layer nascosti**: variano in base a:
  - Complessità del problema
  - Quantità di dati disponibili
  - Obiettivo del modello (classificazione, compressione, generazione…)

---

## Tip Tecnici

- Troppi neuroni/layers = **Overfitting**
- Troppo pochi = **Underfitting**
- Trova il giusto equilibrio con:
  - **Validazione cross**
  - **Early stopping**
  - **Regularizzazione**

## Quando Aggiungere Layer vs Neuroni in una Rete Neurale

| Cosa Modificare           | Quando Farlo                                                             | Effetto Principale                                                 | Esempio Applicativo                                               |
|---------------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------|-------------------------------------------------------------------|
| - Aggiungere un **neurone** in un layer | Quando il modello **underfitta leggermente** e hai ancora margine di capacità | Aumenta la **capacità locale** del layer                            | Un layer da 16 neuroni → 32 per migliorare accuratezza del training |
| - Aggiungere **molti neuroni**         | Quando il layer è **troppo piccolo** per catturare relazioni complesse          | Più potenza computazionale ma rischio overfitting                   | Classificatore con molti input ma scarsi risultati                |
| - Aggiungere **un nuovo layer**        | Quando la rete non riesce a catturare **relazioni gerarchiche o profonde**     | Aumenta la **profondità**, quindi astrazione progressiva             | Immagine: primo layer → bordi, secondo → forme, terzo → oggetti   |
| - Aggiungere **più layer**             | Se il problema è complesso e hai **tanti dati di addestramento**               | Profondità = più astrazione, ma più difficile da addestrare         | Riconoscimento facciale, NLP, visione profonda                    |
| - Aggiungere layer **solo in coda**    | Quando vuoi aumentare la **decodifica finale o raffinamento**                  | Rafforza la parte decisionale, utile per classificazione             | Rete che migliora output finale (es. 10 classi)                   |
| - Aggiungere layer **intermedi**       | Quando serve maggiore **trasformazione tra le feature**                        | Aumenta la trasformazione astratta tra input e output                | Modelli che imparano da dati multivariati complessi              |
| - Ridurre neuroni                      | Per ridurre overfitting o aumentare generalizzazione                            | Meno parametri = meno rischio overfitting                           | Da 128 a 64 se accuracy test > accuracy train                     |
| - Ridurre layer                        | Quando il modello è troppo lento o non migliora con più profondità              | Meno complessità, più generalizzazione, più veloce                   | Applicazioni embedded o mobile                                   |

---

## Regole Generali

| Situazione del Modello                  | Azione Consigliata                  |
|----------------------------------------|-------------------------------------|
| Overfitting (molta accuratezza train, bassa test) | ➖ Neuroni o ➖ layer / + regularizzazione |
| Underfitting (bassa accuratezza ovunque)         | ➕ Neuroni o ➕ layer                |
| Accuracy stabile ma bassa              | ➕ Layer per astrazione maggiore    |
| Accuracy altalenante                   | Controlla learning rate o batch size |
| Training troppo lento                  | ➖ Layer o ➖ Neuroni                 |

---

## Best Practice

- Aumenta **neuroni** quando vuoi migliorare una fase specifica.
- Aggiungi **layer** quando il problema richiede più passi astratti o logici.
- Evita di farlo a caso: valuta con **validazione e curve di apprendimento**.

---

# Tutti i Layer delle Reti Neurali - Spiegati in modo semplice

> Ogni layer è come una fase della lavorazione di un'informazione. Vediamo cosa fanno.

---

# Keras Layers – Guida Completa

## 1. Core Layers

| Layer                 | Descrizione                                                    | Uso                         |
|-----------------------|----------------------------------------------------------------|-----------------------------|
| `Dense(units)`        | Layer completamente connesso (fully connected).               | Classificatori, MLP         |
| `Activation('relu')`  | Applica una funzione di attivazione.                          | Attivazioni standalone      |
| `Dropout(rate)`       | Spegne neuroni casualmente durante il training.               | Regularizzazione            |
| `Flatten()`           | Appiattisce un tensore multidimensionale in 1D.               | Da CNN a Dense              |
| `Reshape(target_shape)`| Cambia la forma del tensore.                                 | Manipolazione della forma   |
| `Input(shape)`        | Definisce un tensore di input (solo in Functional API).       | Inizio rete funzionale      |

---

## 2. Convolutional Layers

| Layer                  | Descrizione                                             | Uso                     |
|------------------------|---------------------------------------------------------|--------------------------|
| `Conv2D(filters, kernel_size)` | Applica convoluzioni su immagini 2D.        | Visione artificiale      |
| `Conv1D` / `Conv3D`     | Convoluzioni su dati 1D o 3D.                         | Audio, video             |
| `SeparableConv2D`       | Convoluzione più leggera e veloce.                   | MobileNet, reti leggere  |
| `DepthwiseConv2D`       | Convoluzione per canale.                             | Architetture avanzate    |

---

## 3. Pooling Layers

| Layer                      | Descrizione                                          | Uso                           |
|----------------------------|------------------------------------------------------|-------------------------------|
| `MaxPooling2D(pool_size)`  | Seleziona il valore massimo da ogni finestra.       | Riduce dimensioni spaziali    |
| `AveragePooling2D`         | Calcola la media in ogni regione.                   | Alternativa più stabile       |
| `GlobalMaxPooling2D()`     | Ritorna il max di ogni feature map.                 | Classificatore compatto       |
| `GlobalAveragePooling2D()` | Media globale per ogni feature map.                 | Molto usato in MobileNet      |

---

## 4. Normalizzazione e Rumore

| Layer                     | Descrizione                                            | Uso                        |
|---------------------------|--------------------------------------------------------|-----------------------------|
| `BatchNormalization()`    | Normalizza attivazioni batch per batch.               | Stabilizzazione e velocità  |
| `LayerNormalization()`    | Normalizza per ogni campione.                         | NLP, RNN                    |
| `GaussianNoise(stddev)`   | Aggiunge rumore casuale.                              | Regularizzazione            |
| `GaussianDropout(rate)`   | Versione rumorosa di Dropout.                         | Alternativa avanzata        |

---

## 5. Reti Ricorrenti (RNN)

| Layer                 | Descrizione                                  | Uso                |
|-----------------------|----------------------------------------------|---------------------|
| `SimpleRNN(units)`    | RNN base.                                    | Sequenze brevi      |
| `LSTM(units)`         | Long Short-Term Memory.                      | Testi, serie temporali |
| `GRU(units)`          | Variante efficiente di LSTM.                 | NLP, serie temporali |

---

## 6. Altri Layer Utili

| Layer                       | Descrizione                                  | Uso                     |
|-----------------------------|----------------------------------------------|--------------------------|
| `Embedding(input_dim, output_dim)` | Codifica parole in vettori.        | NLP, testi               |
| `RepeatVector(n)`           | Ripete un vettore n volte.                  | Encoder-Decoder          |
| `TimeDistributed(layer)`    | Applica un layer nel tempo (frame per frame).| Insieme a RNN            |
| `LeakyReLU(alpha)`          | Variante di ReLU con parte negativa.         | CNN avanzate             |
| `PReLU()`                   | ReLU con pendenza appresa.                   | Ottimizzazioni           |
| `ReLU(max_value, threshold, ...)` | Controllo dettagliato su ReLU.      | Versione configurabile   |

---

## 7. Functional API

| Elemento                  | Descrizione                                 |
|---------------------------|---------------------------------------------|
| `Input(shape)`            | Crea l'input per una rete non-sequenziale.  |
| `Model(inputs, outputs)`  | Definisce un modello da input a output.     |

---

## Consigli d'Uso

- Usa `Sequential()` per modelli semplici: `input_shape` va nel primo layer.
- Usa `Input()` solo se lavori con la **Functional API**.
- In molti layer come `Conv2D` e `Dense`, puoi mettere direttamente l’attivazione con `activation='relu'`.

---

## Overfitting e Underfitting
- **Overfitting**: Il modello impara troppo bene i dati di training, includendo anche rumore e dettagli irrilevanti.  
  - Sintomi: alta accuratezza su training, bassa su test/validazione.  
  - Soluzioni: Dropout, regolarizzazione, aumentare dati, ridurre complessità.

- **Underfitting**: Il modello è troppo semplice per catturare i pattern nei dati.  
  - Sintomi: bassa accuratezza su training e test.  
  - Soluzioni: aumentare neuroni/layer, addestrare più a lungo, usare modelli più complessi.

---

## Funzione di attivazione
- Trasforma l’output di un neurone per introdurre non-linearità.  
- Tipi comuni:
  - **ReLU** (Rectified Linear Unit): `max(0, x)`, semplice e efficace, problema del "morto" solo neuroni.  
  - **Leaky ReLU**: variante che evita neuroni morti con piccola pendenza per x < 0.  
  - **Sigmoid**: utile per output binari, problema saturazione.  
  - **Softmax**: per classificazione multi-classe, trasforma output in probabilità.

---

## Ottimizzatori
- Aggiornano i pesi della rete per minimizzare la funzione di perdita.  
- Esempi:
  - **SGD** (Stochastic Gradient Descent): base, semplice.  
  - **Adam**: combina momentum e adattamento del learning rate, più usato e performante.  
  - **RMSprop**: adatta learning rate per ogni parametro.

---

## Regularizzazione
- Tecniche per ridurre overfitting e migliorare generalizzazione.  
- Tipi:
  - **Dropout**: spegne casualmente neuroni durante il training.  
  - **L1 e L2** (weight decay): penalizzano pesi grandi aggiungendo termine di regolarizzazione alla loss.  
  - **Early stopping**: ferma il training quando la loss di validazione peggiora.

---

## Batch size e Epochs
- **Batch size**: numero di esempi usati per calcolare un aggiornamento del modello.  
  - Batch piccoli = aggiornamenti più rumorosi, possono aiutare ad evitare minimi locali ma rallentano il training.  
  - Batch grandi = più stabili ma più costosi in memoria.

- **Epoch**: un’epoca è il passaggio completo su tutto il dataset.  
  - Troppe epoche = rischio overfitting.  
  - Poche epoche = rischio underfitting.

---

## In Sintesi

| Tipo di Layer       | Cosa Fa                                                |
|---------------------|--------------------------------------------------------|
| Dense               | Connessione completa tra neuroni                       |
| Conv2D              | Estrae pattern da immagini                             |
| MaxPooling2D        | Riduce dimensione prendendo il massimo                 |
| ReLU / Sigmoid / Tanh | Funzioni di attivazione                              |
| Softmax             | Converte in probabilità                                |
| Dropout             | Evita overfitting spegnendo neuroni a caso            |
| BatchNorm           | Stabilizza e accelera l’allenamento                    |
| Flatten             | Appiattisce per passare a layer densi                  |
| Embedding           | Codifica parole in numeri                              |
| Transformer         | "Attenzione" tra elementi in una sequenza              |
| LSTM / GRU          | Gestione memoria nel tempo per dati sequenziali        |
