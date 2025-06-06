# Consigli per la creazione di una rete neurale

Quando creiamo una rete neurale è importante riconoscere quando creare un nuovo livello e quando aggiungere un neurone ad un livello,
qui sotto c'è una guida per queste decisioni.

## Guida: Numero di Neuroni per Layer in una Rete Neurale

| Caso / Configurazione                         | Esempio (neuroni per layer) | Motivo                                                                                       | Quando usarla                                                                                 |
|----------------------------------------------|------------------------------|----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| 🔹 Input scarso, output ricco                 | 1 → 4                        | Estrazione di molte feature da pochi input. Serve espansione di rappresentazione.            | Quando hai un input semplice ma vuoi modellare fenomeni complessi (es. 1 valore → 4 categorie). |
| 🔹 Input ricco, output semplice               | 8 → 2                        | Compressione: i layer successivi imparano a sintetizzare le informazioni.                    | Es. immagini 28x28 → classificazione binaria.                                                   |
| 🔹 Struttura a clessidra (bottleneck)         | 16 → 4 → 16                  | Compressione e decompressione (tipo autoencoder). Il layer stretto forza l’apprendimento utile. | Compressione dati, denoising, feature extraction.                                               |
| 🔹 Architettura piramidale (decrescente)      | 64 → 32 → 16                 | Riduzione progressiva della dimensionalità → migliora generalizzazione.                      | Classificazione, regressione, riduzione del rumore.                                             |
| 🔹 Architettura piramide inversa (crescente)  | 8 → 16 → 32                  | Usata per generazione o upscaling (es. GAN, decoder, generazione testi o immagini).          | Decoder, generatori (es. VAE decoder, GAN generator).                                           |
| 🔹 Stesso numero di neuroni in ogni layer     | 16 → 16 → 16                 | Stessa capacità elaborativa a ogni livello. Rischia overfitting.                             | Quando non conosci bene i dati e vuoi una base uniforme.                                        |
| 🔹 Troppi neuroni nel primo layer             | 128 → 64 → 32                | Rischia overfitting: troppa capacità sin dall'inizio.                                        | Da evitare se l’input è semplice o rumoroso.                                                    |
| 🔹 Pochi neuroni nel primo layer              | 2 → 8 → 16                   | Primo layer perde informazione; il secondo tenta di ricostruirla → inefficienza.             | Evitare se l’input ha molte feature importanti.                                                 |
| 🔹 Layer centrale troppo piccolo              | 64 → 2 → 64                  | Bottleneck troppo stretto → perde troppe info.                                                | Utile solo se vuoi forzare un embedding molto compatto.                                         |
| 🔹 Tanti layer con pochi neuroni              | 8 → 8 → 8 → 8 → 8            | Approfondisci la rete senza aumentare la capacità troppo.                                    | NLP, RNN, transformers con deep attention.                                                      |

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

- ✅ Troppi neuroni/layers = **Overfitting**
- ❌ Troppo pochi = **Underfitting**
- 🎯 Trova il giusto equilibrio con:
  - **Validazione cross**
  - **Early stopping**
  - **Regularizzazione**

## Quando Aggiungere Layer vs Neuroni in una Rete Neurale

| Cosa Modificare           | Quando Farlo                                                             | Effetto Principale                                                 | Esempio Applicativo                                               |
|---------------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------|-------------------------------------------------------------------|
| 🔹 Aggiungere un **neurone** in un layer | Quando il modello **underfitta leggermente** e hai ancora margine di capacità | Aumenta la **capacità locale** del layer                            | Un layer da 16 neuroni → 32 per migliorare accuratezza del training |
| 🔹 Aggiungere **molti neuroni**         | Quando il layer è **troppo piccolo** per catturare relazioni complesse          | Più potenza computazionale ma rischio overfitting                   | Classificatore con molti input ma scarsi risultati                |
| 🔹 Aggiungere **un nuovo layer**        | Quando la rete non riesce a catturare **relazioni gerarchiche o profonde**     | Aumenta la **profondità**, quindi astrazione progressiva             | Immagine: primo layer → bordi, secondo → forme, terzo → oggetti   |
| 🔹 Aggiungere **più layer**             | Se il problema è complesso e hai **tanti dati di addestramento**               | Profondità = più astrazione, ma più difficile da addestrare         | Riconoscimento facciale, NLP, visione profonda                    |
| 🔹 Aggiungere layer **solo in coda**    | Quando vuoi aumentare la **decodifica finale o raffinamento**                  | Rafforza la parte decisionale, utile per classificazione             | Rete che migliora output finale (es. 10 classi)                   |
| 🔹 Aggiungere layer **intermedi**       | Quando serve maggiore **trasformazione tra le feature**                        | Aumenta la trasformazione astratta tra input e output                | Modelli che imparano da dati multivariati complessi              |
| 🔹 Ridurre neuroni                      | Per ridurre overfitting o aumentare generalizzazione                            | Meno parametri = meno rischio overfitting                           | Da 128 a 64 se accuracy test > accuracy train                     |
| 🔹 Ridurre layer                        | Quando il modello è troppo lento o non migliora con più profondità              | Meno complessità, più generalizzazione, più veloce                   | Applicazioni embedded o mobile                                   |

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

# 🧠 Tutti i Layer delle Reti Neurali - Spiegati in modo semplice

> Ogni layer è come una fase della lavorazione di un'informazione. Vediamo cosa fanno.

---

## 🔷 Funzioni di Attivazione (usate nei neuroni)

### 1. ReLU (Rectified Linear Unit)
- Formula: `f(x) = max(0, x)`
- Fa passare solo i valori positivi, azzera i negativi.
- ✅ Veloce e usatissima nelle CNN e MLP.

### 2. Sigmoid
- Formula: `f(x) = 1 / (1 + e^(-x))`
- Trasforma l'input in un numero tra 0 e 1.
- ✅ Ottima per classificazione binaria.
- ⚠️ Tende a saturare (i gradienti diventano piccoli).

### 3. Tanh (Tangente iperbolica)
- Formula: `f(x) = (e^x - e^-x)/(e^x + e^-x)`
- Output tra -1 e 1.
- ⚠️ Simile a sigmoid, ma centrata su 0.

### 4. Softmax
- Converte una lista di numeri in **probabilità** che sommano a 1.
- Usata nell'**ultimo layer per classificazione multi-classe**.

---

## 🔷 Layer di Costruzione

### 5. Dense / Fully Connected
- Ogni neurone è connesso a tutti quelli del layer precedente.
- Usato in classificatori e MLP.

### 6. Conv2D (Convolutional Layer)
- Applica un **filtro** per trovare pattern in immagini.
- Usato nelle CNN per riconoscere bordi, texture, ecc.

### 7. MaxPooling2D
- Riduce la dimensione dell’immagine, mantenendo le info più importanti.
- Esempio: da 4x4 a 2x2 prendendo il valore massimo.

### 8. Dropout
- Spegne casualmente alcuni neuroni durante l’allenamento.
- Aiuta a prevenire l’**overfitting**.

### 9. Flatten
- Appiattisce un'immagine 2D in un vettore 1D.
- Utile prima di passare da CNN a Dense.

### 10. Batch Normalization
- Normalizza i valori nel layer per stabilizzare e velocizzare l’allenamento.

### 11. Residual / Skip Connection
- Permette di **saltare** uno o più layer e sommare direttamente l'input.
- Usato nelle **ResNet** per reti molto profonde.

---

## 🔷 Layer per Sequenze o Testi

### 12. RNN (Recurrent Neural Network)
- Tiene memoria di ciò che è successo prima.
- Usato per testi e audio.
- ⚠️ Dimentica con sequenze troppo lunghe.

### 13. LSTM (Long Short-Term Memory)
- Variante avanzata dell'RNN.
- Ha una “memoria lunga” ed è più resistente alla dimenticanza.

### 14. GRU (Gated Recurrent Unit)
- Simile all’LSTM, ma più veloce e semplice.

### 15. Embedding Layer
- Trasforma parole o simboli in vettori numerici.
- Es: "gatto" → [0.1, 0.8, -0.5...]

---

## 🔷 Layer Moderni (Transformers)

### 16. Transformer / Self-Attention
- Ogni parola guarda tutte le altre e decide a chi dare peso.
- Cuore di GPT, BERT, ChatGPT.
- Gestisce bene sequenze lunghe.

---

## 🔷 Layer per Scopi Specifici

| Layer                | Scopo                                                |
|----------------------|------------------------------------------------------|
| Conv1D / Conv3D      | Dati 1D (audio) o 3D (video, immagini volumetriche)  |
| GlobalAveragePooling | Riduce ogni mappa a un solo valore medio            |
| Upsampling2D         | Aumenta la dimensione di un'immagine (opposto del pooling) |
| TransposedConv2D     | Generazione immagini (es. nei generatori GAN)       |

---

## 🎯 In Sintesi

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

---

## ✅ Vuoi un esempio pratico in codice?
Posso scriverti un esempio in PyTorch o Keras con questi layer, basta chiedere.