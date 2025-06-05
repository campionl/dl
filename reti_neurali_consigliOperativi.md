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

