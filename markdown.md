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

## Inserire immagini

Per inserire le immagini si usa la sintassi  
__![Testo alternativo](URL o percorso “Titolo opzionale)__

`!`indica che inserisci l’immagine.  
`[Testo alternativo]`è il testo che viene mostrato in caso non si carica l’immagine.  
`(URL o percorso)`il link all’immagine (percorso locale o URL).  
`”Titolo”`opzionale, compare quando passi il mouse sopra l’immagine.  

## Collegare un’immagine a un link

Per rendere cliccabile un immagine in Markdown (cioè che porta a un link), si usa la sintassi:  

__`[![Testo alternativo](URL o percorso “Titolo”)](Link di destinazione)__

`[ … ]`le parentesi indicano che si sta creando un link.
`!`Dice che dentro ci sarà un immagine.  
`![Testo alternativo]`È l’immagine vera e propria.  
`(URL o percorso)`È il percorso o il link dell’immagine da mostrare.  
`”Titolo”`Facoltativo, appare quando passi il mouse sull’immagine.  
`(Link di destinazione)`Dopo l’immagine, tra parentesi tonde va l’URL dove porterà il clic.  
  
