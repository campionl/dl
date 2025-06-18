# Rete Neurale LSTM (Long Short-Term Memory)

Una **rete LSTM** è un tipo speciale di rete neurale **ricorrente (RNN)** progettata per **ricordare informazioni a lungo termine**.

Le LSTM sono molto usate per elaborare sequenze temporali o testi, come:

- Traduzione automatica
- Previsione di serie temporali
- Generazione di testo
- Riconoscimento vocale

---

## Come funziona una LSTM?

Le LSTM sono costituite da **celle di memoria** che possono:

- **Memorizzare informazioni**
- **Cancellare ciò che non serve**
- **Uscire con nuove informazioni utili**

Per fare questo usano **3 porte** principali:

| Porta        | Funzione                                                                 |
|--------------|--------------------------------------------------------------------------|
| Porta di input    | Decide **quali informazioni nuove** salvare                         |
| Porta di forget   | Decide **quali vecchie informazioni** dimenticare                   |
| Porta di output   | Decide **quale parte della memoria** usare come output              |

---

## Differenza tra LSTM e RNN classiche

| RNN Classica                   | LSTM                                       |
|-------------------------------|--------------------------------------------|
| Ricorda solo **poche informazioni recenti** | Ricorda **informazioni anche lontane** |
| Tende a dimenticare col tempo  | Ha **memoria a lungo termine**             |
| Più semplice                   | Più complessa ma molto più potente         |

---

## Struttura della rete

![rete LSTM](https://it.mathworks.com/discovery/lstm/_jcr_content/mainParsys/band/mainParsys/lockedsubnav/mainParsys/columns_1332042868/09887e7d-81a1-4a53-b298-eb7bd9d6ac8c/image.adapt.full.medium.jpg/1747387222672.jpg)

---

## Come spiegarlo a un bambino?

Immagina una **lavagna magica** che può **ricordare cose importanti** e **cancellare quelle inutili** mentre ascolta una storia.  
Ogni volta che sente qualcosa di importante, lo scrive. Se sente qualcosa che non serve, lo cancella. Così alla fine può **indovinare come continua la storia!**