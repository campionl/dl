# Rete Neurale Ricorrente (RNN)

La **rete neurale ricorrente (RNN)** è un tipo di rete neurale in cui i neuroni possono formare **cicli**, cioè l'output di un nodo può essere **riutilizzato come input in un momento successivo**.

Questo rende le RNN particolarmente adatte a elaborare **sequenze temporali di dati**, dove è importante tenere traccia di ciò che è successo in passato per interpretare correttamente il presente.

## Caratteristiche principali

- Ha una **memoria interna** che trattiene informazioni sulle iterazioni precedenti.
- Adatta a dati sequenziali o temporali: testo, audio, serie temporali.
- Supporta l’**analisi predittiva** e la generazione sequenziale.

## Applicazioni tipiche

- Riconoscimento vocale.
- Traduzione automatica.
- Generazione di testo.
- Riconoscimento della scrittura.
- Previsioni di borsa o dati temporali.

---

### Struttura della rete

![rete RNN](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Recurrent_neural_network_unfold.svg/1920px-Recurrent_neural_network_unfold.svg.png)

---

## Come lo spiegherei a un bambino?

Immagina di giocare al **telefono senza fili**, ma con una differenza: ogni volta che qualcuno passa il messaggio, **ricorda anche cosa è stato detto prima**. Così, ascoltando e memorizzando sempre di più, riesce a **indovinare meglio la parola successiva**. Le RNN funzionano proprio così: imparano a prevedere cosa verrà dopo, basandosi su ciò che è già successo.