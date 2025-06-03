# Markdown

Markdown è un linguaggio di markup leggero implementato in vari software come Github, word, Notion, etc…

L’output può essere poi convertito in PDF o HTML

Markdown permette tramite l’uso di caratteri specifici di applicare una formattazione e una modifica della struttura del testo.

Con Markdown quindi possiamo dare design e struttura al testo per personalizzarlo come ci è più comodo.

I principali caratteri per formattazione del testo markdown sono:

( * ) ( # ) ( _ ) ( - )


## Intestazioni
Le intestazioni sono molto utili per strutturare una documentazione.  

Per le intestazioni usiamo il carattere `#`.  
In base al numero di `#` il titolo è più o meno grande, fino ad un massimo di sei `#`.    

*Alcuni esempi:*
- `#` Titolo molto grande
- `#######` Titolo molto piccolo

## Formattazione  
La formattazione serve modificare il testo inserendo per esempio testo in grassetto o in corsivo.  
- **Testo normale**  
  Per il testo senza formattazione non c'è bisogno di alcun simbolo  
  
  *Esempio:*  
  `Testo normale`  
  Testo normale
- **Testo in grassetto**  
  Per il grassetto bisogna inserire due asterischi all'inizio e alla fine della frase interessata

  *Esempio:*  
  `**grassetto**`  
  **grassetto**
- **Testo corsivo**
  Per il corsivo si inserisce un asterisco all'inizio e alla fine della frase interessata

  *Esempio:*  
  `*corsivo*`    
  *corsivo*  
- **Testo corsivo e grassetto**
  Per inserire un testo sia in corsivo e in grassetto si utilizzano tre asterischi all'inizio e alla fine della frase interessata

  *Esempio:*  
  `***grassetto e corsivo***`  
  ***grassetto e corsivo***  
- **Testo con la barra**
  Per inserire un testo con la barra sopra si utilizzano due tilde `~` all'inizio e alla fine della frase interessata

  *Esempio:*  
  `~~barrato~~`  
  ~~barrato~~

## Citazioni
Le citazioni evidenziano blocchi di testo o di codice.  
Esistono quindi **due** tipi di citazioni.

---
Le **Citazioni di testo** sono usate per evidenziare un passaggio importante che non è codice.  
+ Sono ideali per citazioni verbali, estratti da documenti, o per mettere in risalto avvisi o note.<br>
+ Per scrivere una citazione usiamo `>`.<br>
**Esempio di citazione di testo**
> Il file Markdown.md serve da introduzione per scrivere una documentazione in modo professionale. <br>

---
Le **Citazioni di codice** sono usate specificamente per mostrare frammenti di codice sorgente, comandi o sintassi che non devono essere interpretati come testo normale.<br>

 + Esistono due distinzioni:
   + Il **Codice Inline** è usato per evidenziare piccoli frammenti di codice: 
   Per creare un codice inline si racchiude il testo tra due apici inversi.
`esempio di codice inline`
    + Il **Blocco di codice** è usato per evidenziare diverse righe di codice.
     Si usano tre apici inversi all'inizio e alla fine del blocco di codice.
     ```python
	     for(i in range(10)):
				print(i)
	 ```
## Fare un elenco

Per gli elenchi puntati si inserisce un trattino `-` all'inizio della riga  

*Sintassi:*  

`-elemento 1`  
`-elemento 2`  

*Esempio:*
- elemento 1
- elemento 2    

Per l’elenco numerato si inserisce il numero dell’elemento seguito da un punto all’inizio della riga.

*Sintassi:*

`1. elemento 1`  
`2. elemento 2`  
`3. elemento 3`  

*Esempio:*

1. elemento 1
2. elemento 2
3. elemento 3


## Fare un collegamento esterno

Per inserire un collegamento ad un sito esterno.  

*Sintassi:*  

`<indirizzo del sito web>.`  

*Esempio:*  

<https://www.wikipedia.org>

Collegamento con nome personalizzato.  

*Sintassi:*  

`[nome personalizzato]\(<link>).`  

*Esempio:*  

[Visita Wikipedia](https://www.wikipedia.org)  

## Inserire immagini

Per inserire le immagini  

*Sintassi:*  

__`![Testo alternativo](URL o percorso “Titolo opzionale")`__

`!` : indica che inserisci l’immagine.  
`[Testo alternativo]` : testo che viene mostrato in caso non si carica l’immagine.  
`(URL o percorso)` : link all’immagine (percorso locale o URL).  
`”Titolo”` : opzionale, compare quando passi il mouse sopra l’immagine.  


*Esempio:*  

`![Logo di GitHub](https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png "Vai su GitHub")`  

![Logo di GitHub](https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png "Vai su GitHub")


## Collegare un’immagine a un link

Per rendere cliccabile un immagine in Markdown (cioè che porta a un link)  

*Sintassi:*  

__`[![Testo alternativo](URL o percorso “Titolo”)](Link di destinazione)`__

`[ … ]` : le parentesi indicano che si sta creando un link.  
`!` : Dice che dentro ci sarà un immagine.  
`![Testo alternativo]` : È l’immagine vera e propria.  
`(URL o percorso)` : È il percorso o il link dell’immagine da mostrare.  
`”Titolo”` : Facoltativo, appare quando passi il mouse sull’immagine.  
`(Link di destinazione)` : Dopo l’immagine, tra parentesi tonde va l’URL dove porterà il clic.  


  *Esempio:*  

`[![GitHub Logo](https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png "Vai su GitHub")](https://github.com)`  

  [![GitHub Logo](https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png "Vai su GitHub")](https://github.com)

