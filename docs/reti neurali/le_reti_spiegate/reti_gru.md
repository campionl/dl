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
