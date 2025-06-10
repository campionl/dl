# Documentazione: Ottimizzatori, Callback, Data Augmentation e Transfer Learning

---

## 2. Ottimizzatori e loro impatto

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

## 3. Early stopping e Callback

I callback sono funzioni speciali che si eseguono durante il training per monitorare, modificare o interrompere il processo.

### EarlyStopping

- Interrompe il training se la metrica monitorata (es. validation loss) non migliora dopo un certo numero di epoche (`patience`).
- Aiuta a evitare overfitting e risparmia tempo.

```python
from keras.callbacks import EarlyStopping

early_stop = EarlyStopping(monitor='val_loss', patience=3)
model.fit(X_train, y_train, epochs=50, validation_split=0.2, callbacks=[early_stop])

