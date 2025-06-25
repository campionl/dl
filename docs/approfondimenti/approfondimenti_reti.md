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



### Struttura della rete

![rete RNN](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Recurrent_neural_network_unfold.svg/1920px-Recurrent_neural_network_unfold.svg.png)



## Come lo spiegherei a un bambino?

Immagina di giocare al **telefono senza fili**, ma con una differenza: ogni volta che qualcuno passa il messaggio, **ricorda anche cosa è stato detto prima**. Così, ascoltando e memorizzando sempre di più, riesce a **indovinare meglio la parola successiva**. Le RNN funzionano proprio così: imparano a prevedere cosa verrà dopo, basandosi su ciò che è già successo.

---
---

# Rete Neurale Feedforward (FNN)

La **rete neurale feedforward** è uno dei modelli più semplici e fondamentali delle reti neurali artificiali. Le connessioni tra i nodi **non formano cicli**, a differenza delle reti neurali ricorrenti (RNN).

In una FNN, le informazioni **fluiscono in un'unica direzione**: dall'input verso l'output, attraversando eventualmente uno o più strati nascosti. Non esiste memoria degli input precedenti, quindi ogni output dipende solo dall'input attuale.

## Caratteristiche principali

- Nessun ciclo o retroazione.
- Ideale per classificazione e regressione.
- I neuroni non hanno memoria.
- Architettura semplice e veloce da addestrare.

## Tipi di FNN

## 1. Rete a singolo strato (Single-layer Perceptron)
- È la versione più semplice di FNN.
- Composta da uno **strato di input** collegato direttamente allo **strato di output**.
- Capacità limitate: può risolvere solo problemi **linearmente separabili**.

## 2. Rete a più strati (Multilayer Perceptron, MLP)
- Include uno o più **strati nascosti** tra input e output.
- Ogni strato è completamente connesso al successivo.
- Grazie a funzioni di attivazione non lineari (es. ReLU), può risolvere problemi **non linearmente separabili**.
- È la base per molte architetture più complesse.

---

## Struttura della rete

![rete FNN](https://upload.wikimedia.org/wikipedia/commons/7/7b/XOR_perceptron_net.png)

---

## Come lo spiegherei ad un bambino?

Immagina di dover indovinare che animale è partendo da alcune informazioni, tipo:

Ha le ali?

Fa "cip cip"?

Sa nuotare?

Ora immagina che ci siano delle scatole collegate in fila, come una catena:
- La prima scatola riceve queste informazioni.
- La seconda scatola le elabora un po’ (magari dice "se ha le ali, allora forse vola").
- L’ultima scatola decide che animale è: “È un uccellino!”

In questa **catena**, ogni scatola passa i dati alla **successiva**, ma mai indietro. **Non ricordano** le vecchie informazioni, fanno solo il loro lavoro e le passano avanti.
È un po’ come una catena di montaggio, dove ognuno aggiunge qualcosa per arrivare alla risposta finale.

---
---

# Rete Neurale GRU (Gated Recurrent Unit)

La **GRU (Gated Recurrent Unit)** è una variante più semplice e veloce della rete **LSTM**, progettata per sequenze temporali, testi o dati in serie.  
È una rete **ricorrente** con una struttura più leggera, ma simile, che riesce comunque a **mantenere la memoria nel tempo**.

---

## Come funziona una GRU?

Le GRU usano **2 porte** per controllare le informazioni che devono passare o essere dimenticate:

| Porta        | Funzione                                                         |
|--------------|------------------------------------------------------------------|
| Porta di aggiornamento (update gate) | Decide **quanto mantenere del vecchio stato** e **quanto aggiornare** |
| Porta di reset (reset gate)         | Decide **quanto del passato dimenticare** nel calcolo del nuovo stato |

> Meno componenti rispetto a una LSTM (che ne ha 3), ma stessa idea di base: **decidere cosa ricordare e cosa dimenticare**.

---

## Differenze principali tra LSTM e GRU

| LSTM                                | GRU                                       |
|-------------------------------------|-------------------------------------------|
| Più complessa (3 porte)             | Più semplice (2 porte)                    |
| Più potente su sequenze lunghe      | Più veloce e leggera                      |
| Usa una cella di memoria separata   | Tutto integrato nello **stato nascosto** |

---

## 💡 Quando usare una GRU?

- Quando hai **pochi dati** e vuoi un modello più leggero
- Quando il tempo di **allenamento** è importante
- Quando le **prestazioni della LSTM non migliorano molto**
- Per **traduzioni, chatbot, previsioni temporali**, ecc.

---

## Come spiegarla a un bambino?

Immagina che hai un **quaderno** dove scrivi cose importanti mentre ascolti una storia.  
Hai **due bottoni magici**:

- Uno ti dice: _"Aspetta! Questa parte è importante, non cancellarla!"_
- L'altro dice: _"Non serve ricordare questa parte, la puoi ignorare."_

Così puoi continuare ad ascoltare la storia e **ricordare solo le parti più utili**.
