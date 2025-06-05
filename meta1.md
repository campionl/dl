# Reti neurali

## Introduzione
Le reti neurali artificiali (**ANN**, Artificial Neural Networks) sono modelli matematici ispirati al cervello umano. Sono una parte fondamentale dell’intelligenza artificiale e vengono utilizzate per riconoscere schemi, prendere decisioni e risolvere problemi complessi in modo automatico.

## Definizione
Una rete neurale è composta da neuroni artificiali, organizzati in strati:
- uno strato di **input** (*dati in ingresso*),
- uno o più strati **nascosti** (*elaborazione*),
- uno strato di **output** (*risultato*).

Ogni connessione ha un peso, che regola quanto un'informazione è importante. Durante l’addestramento, la rete impara modificando questi pesi per migliorare i risultati.

## Ispirazione biologica
Questo modello si ispira al cervello umano, dove i neuroni comunicano tra loro tramite sinapsi. Infatti anche nelle reti neurali i neuroni artificiali ricevono segnali, li elaborano e trasmettono il risultato. Sebbene molto semplificata, questa struttura consente di simulare meccanismi di apprendimento simili a quelli biologici.

## Perché studiare le reti neurali?
Le reti neurali sono oggi molto usate perché possono apprendere direttamente dai dati. Le loro applicazioni sono ovunque:
- **Medicina**: diagnosi da immagini (radiografie, TAC)
- **Tecnologia**: assistenti vocali, riconoscimento facciale
- **Industria**: manutenzione predittiva, controllo qualità
- **Finanza**: analisi di mercato, prevenzione frodi
- **Automobili**: guida autonoma

Studiare le reti neurali significa capire come rendere i computer più intelligenti e capaci di imparare, contribuendo all’innovazione in molti settori.

## Nascita delle reti neurali
Le reti neurali artificiali nascono tra gli anni '40 e '60, grazie ai primi studi che cercavano di imitare il cervello umano usando modelli matematici. Tra i primi studiosi troviamo:
- **Warren McCulloch e Walter Pitts**: nel 1943 propongono il primo modello di neurone artificiale. Questo modello era molto semplice:
    - riceveva segnali in **ingresso**,
    - li **sommava**,
    - e se superavano una certa soglia, generava un **output** (come un “sì” o “no”).

    È il primo tentativo di rappresentare il funzionamento di un neurone biologico in modo matematico.
- **Frank Rosenblatt**: Nel 1958 sviluppa il perceptron, un modello un pò più avanzato.
Il perceptron è una rete neurale molto semplice, con:
    - uno strato di **input**,
    - uno strato di **output**,
    - un **algoritmo** per apprendere dai dati modificando i pesi.

È il primo vero modello di rete neurale in grado di imparare.

## Limitazioni iniziali
Nonostante l'entusiasmo iniziale, il perceptron aveva un grosso limite: non riusciva a risolvere problemi non linearmente separabili, come il famoso problema **XOR** (dove non basta tracciare una linea per separare le due classi).  
Questo portò a una fase di stallo (chiamato AI winter) nella ricerca sulle reti neurali, fino agli anni ’80, quando vennero introdotti modelli più complessi con strati nascosti e nuovi algoritmi di apprendimento.

## Il periodo di stallo
Uno dei motivi principali di questa crisi fu la pubblicazione del libro **"Perceptrons"** di Marvin Minsky e Seymour Papert nel 1969.  
Nel libro, gli autori dimostrarono matematicamente i limiti del perceptron, spiegando che:
- non può risolvere problemi non linearmente separabili (come il già citato problema XOR),
- e che non era possibile superare questi limiti con la struttura semplice del perceptron a uno strato.

Anche se le loro critiche erano corrette solo per i modelli più semplici, molti interpretarono il messaggio come: **le reti neurali non funzionano** e quindi molti ricercatori e agenzie di finanziamento persero fiducia nelle reti neurali spostando l'attenzione su altri approcci (come la logica simbolica e i sistemi esperti). Questo provocò una vera e propria pausa nello sviluppo pratico delle reti neurali per quasi due decenni.