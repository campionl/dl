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