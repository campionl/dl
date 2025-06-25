# Documentazione: Ottimizzatori, Callback, Data Augmentation e Transfer Learning

---

## 1. Ottimizzatori e loro impatto

Gli ottimizzatori sono algoritmi che aggiornano i pesi del modello durante il training per minimizzare la funzione di perdita.

### Ottimizzatori comuni in Keras

- **Adam**  
  Combina i vantaggi di AdaGrad e RMSprop. Adatto alla maggior parte dei casi, convergenza rapida e stabile.  
  Parametri importanti: learning rate (default 0.001), beta1, beta2.

- **SGD (Stochastic Gradient Descent)**  
  Aggiorna i pesi usando una singola o mini-batch di dati. Può includere momentum per accelerare la convergenza.  
  Utile se si vuole più controllo o per modelli semplici.

- **RMSprop**  
  Adatta il learning rate per ogni peso individualmente, ottimo per problemi con dati rumorosi o sequenziali.

### Parametri chiave

- **Learning rate**: velocità con cui il modello aggiorna i pesi; troppo alto può far divergere, troppo basso rallenta il training.
- **Momentum**: aiuta a evitare oscillazioni durante la discesa del gradiente.

---

## 2. Callback

I callback sono funzioni speciali che si eseguono durante il training per monitorare, modificare o interrompere il processo.

### EarlyStopping

- Interrompe il training se la metrica monitorata (es. validation loss) non migliora dopo un certo numero di epoche (`patience`).
- Aiuta a evitare overfitting e risparmia tempo.

```
from keras.callbacks import EarlyStopping

early_stop = EarlyStopping(monitor='val_loss', patience=3)
model.fit(X_train, y_train, epochs=50, validation_split=0.2, callbacks=[early_stop])
```
---

## Altri callback utili

### ModelCheckpoint
Salva il modello automaticamente durante l’allenamento ogni volta che migliora una metrica.

```
from keras.callbacks import ModelCheckpoint

checkpoint = ModelCheckpoint('best_model.h5', monitor='val_loss', save_best_only=True)
model.fit(X_train, y_train, validation_split=0.2, epochs=50, callbacks=[checkpoint])
```

### ReduceLROnPlateau
Riduce il learning rate quando una metrica smette di migliorare.

```
from keras.callbacks import ReduceLROnPlateau

reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2)
model.fit(X_train, y_train, validation_split=0.2, epochs=50, callbacks=[reduce_lr])
```

### TensorBoard
Permette di monitorare l’allenamento in tempo reale tramite interfaccia grafica.

```
from keras.callbacks import TensorBoard

tensorboard = TensorBoard(log_dir='./logs')
model.fit(X_train, y_train, validation_split=0.2, epochs=50, callbacks=[tensorboard])
```

### CSVLogger
Registra i risultati dell’allenamento in un file ".csv" .

```
from keras.callbacks import CSVLogger

logger = CSVLogger('training_log.csv')
model.fit(X_train, y_train, validation_split=0.2, epochs=50, callbacks=[logger])
```
