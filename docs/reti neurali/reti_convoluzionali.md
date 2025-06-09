# 🧠 Reti Convoluzionali (CNN)

Le **reti convoluzionali** (o CNN, dall’inglese *Convolutional Neural Networks*) sono un tipo speciale di rete neurale ispirata al modo in cui funziona il **cervello degli animali**, in particolare la **corteccia visiva**, che è la parte del cervello che ci fa vedere e riconoscere le cose.

Immagina che il cervello “guardi” un’immagine a pezzetti, capendo prima i contorni, poi le forme, e infine tutto l’oggetto. Le CNN fanno esattamente questo!

---

## 🧬 Perché sono speciali?

Le reti convoluzionali sono una specie di evoluzione dei classici **percettroni multistrato** (MLP), ma sono molto più intelligenti nel trattare immagini. Infatti:

- Usano **pochi passaggi di pre-elaborazione**.
- Trovano **da sole** le parti importanti dell’immagine, come occhi, orecchie, o linee, grazie ai **filtri**.

---

## 🔍 Come funzionano?

1. **Convoluzione**  
   Pensa a una lente d’ingrandimento che guarda piccoli pezzi dell’immagine, uno alla volta. Questo passaggio si chiama **convoluzione** e serve per trovare cose come bordi, linee e colori.

2. **Attivazione**  
   Dopo aver guardato un pezzettino, la rete decide: "È importante o no?" Usa una formula per rispondere, chiamata **funzione di attivazione** (di solito ReLU).

3. **Pooling (o sottocampionamento)**  
   Poi la rete fa una specie di riassunto, prendendo solo i pezzi più importanti. Questo si chiama **pooling**, e aiuta a ridurre il peso del lavoro senza perdere dettagli importanti.

4. **Strato finale (fully connected)**  
   Quando la rete ha “guardato” tutta l’immagine e capito le parti più importanti, passa queste informazioni agli **strati finali**, che prendono una decisione, come: “Questo è un gatto!”

---

## 🚀 Evoluzione delle CNN e uso delle GPU

Nel **2011**, gli scienziati hanno avuto un’idea:  
> “E se usassimo le **GPU** (quelle dei videogiochi) per far funzionare le reti più velocemente?”

💥 Boom! I risultati sono stati incredibili:  
le CNN sono diventate **molto più veloci** e **molto più precise** nel riconoscere immagini.

---

## 🖼️ I Dataset Famosi

Per allenare queste reti servono **tante immagini**. Alcuni dei dataset più famosi sono:

- **MNIST** – numeri scritti a mano.
- **CIFAR-10** – immagini di oggetti come auto, animali, navi, ecc.
- **ImageNet** – milioni di immagini di ogni tipo.
- **NORB** e **HWDB1.0** – per oggetti 3D e scrittura cinese.

---

## 🤖 Dove si usano le CNN?

Le reti convoluzionali oggi si usano ovunque:

- Nei **cellulari** per riconoscere volti e sbloccare lo schermo.
- Nei **robot** per “vedere” l’ambiente.
- Nei **videogiochi** per creare intelligenza visiva.
- E perfino nelle **auto a guida autonoma**!

---

## 🧠 In sintesi

Le CNN sono come un piccolo cervello che impara a **vedere**, **capire** e **riconoscere** le immagini.  
Sono intelligenti, veloci e sempre più usate nel mondo dell’intelligenza artificiale.
