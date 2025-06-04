# Git
---
## Cos’è Git
Git è un sistema di controllo di versione che permette di gestire e tenere traccia delle modifiche al codice di un progetto. Ogni sviluppatore ha una copia completa del repository, compresa la cronologia delle modifiche, e può lavorare sia offline che online. Questo rende il lavoro di squadra più sicuro, organizzato ed efficiente.

## Concetti chiave
- **Repository (repo)**: Pensa a un repository (repo) come una cartella speciale per il tuo progetto. Questa cartella non contiene solo i tuoi file, ma anche tutta la storia delle modifiche che hai fatto. Ne esistono due tipi:
    - Locale: La copia del progetto che hai sul tuo computer.
    - Remota: La copia del progetto che si trova su un server online (come GitHub), utile per collaborare con altri o per avere un backup.
- **Commit**: Ogni volta che "salvi" il tuo lavoro in Git con un commit, è come se scattassi una "fotografia" (snapshot) del tuo progetto in quel preciso momento. Questa foto cattura lo stato di tutti i tuoi file così come sono in quel commit.

## Aree di lavoro
- **Working directory**: dove si modificano i file
- **Staging area**: dove si preparano le modifiche da includere nel commit
- **Repository locale**: dove Git salva definitivamente i commit

## Flusso di lavoro base
1. **Modificare i file** nella working directory
2. **Aggiungere i file modificati** all’area di staging con ```git add```
3. **Salvare le modifiche** con ```git commit``` con una descrizione appropriata
4. **Sincronizzare con il repository** remoto usando ```git push``` (invia) e ```git pull``` (riceve)

## Configurazione iniziale
I comandi che seguono vanno eseguiti subito dopo la configurazione di Git.
Questi comandi servono per "firmare" i commit su git.  
**Non** è un login.
```
git config --global user.name "<nome>"
git config --global user.email "<email>"
```
## Login su Git
Per fare il login su Github esistono due modi.
### HTTPS e Token Personale
Per accedere a repository GitHub tramite HTTPS:  
GitHub richiede un *Token di Accesso Personale (PAT)* per motivi di sicurezza:  
- Maggiore protezione contro attacchi brute-force  
- Controllo granulare sui permessi (es. accesso solo ai repository)  
- Integrazione con sistemi di autenticazione a due fattori  

Il token funge da "super password temporanea" e va generato manualmente.  
Ecco come procedere:
1. Crea il tuo token cliccando [qui](https://github.com/settings/tokens) *(è necessario essere loggati con il proprio account GitHub)*.
2. Clicca su **Generate new token (classic)**, dopo:
	- Scegliere una scadenza per il token (30 o 90 giorni).
	- Selezionare i permessi del token in base a cosa bisogna fare (per lavorare con repository spuntare **repo**).
3.  Quando GitHub chiede **username e password**:
	- Username: *il tuo nome utente GitHub*
    - Password: *Token generato*
### SSH
La chiave SSH fornisce numerosi vantaggi:
- Non devi ricordare token o password
- Accesso automatico a ogni operazione      
- Sicuro come una cassaforte bancaria

Per funzionare viene creato un **lucchetto** (detto chiave pubblica) e una **chiave** (detta chiave privata).
- La chiave **PUBBLICA**  viene data a GitHub.
- La chiave **PRIVATA** resta sul computer.

1. Genera una chiave SSH
```
ssh-keygen -t ed25519 -C "<email>"
```

2. Avvia l'agente
```
eval "$(ssh-agent -s)"
```

3. Aggiungi la chiave all'agente
```
ssh-add ~/.ssh/id_ed25519
```

4. Copia la chiave pubblica
```
cat ~/.ssh/id_ed25519.pub
```

5. Aggiungi la chiave al tuo account GitHub
    1. Vai sulle impostazioni di github e clicca su "SSH and GPG keys"
    2. Clicca su "New SSH key"
    3. Incolla la chiave
    4. Dagli un nome e salvala

6. Testa la connessione
```
ssh -T git@github.com
```

## Gestione dei branch (rami)

Immaginiamo il nostro progetto (repo) come un albero: 

- Il branch *main* è il tronco, ossia la versione stabile del progetto
- I diversi branch (in italiano *rami*) sono copie indipendenti del progetto, dove è possibile implementare nuove funzionalità e testarle senza corrompere la versione stabile

Creazione di un branch
```
git branch <nome-branch>
```

Spostarsi in un branch
```
git checkout <nome-branch>
```

Crea e si sposta in un nuovo branch
```
git checkout -b <nome-branch>
```

Caricare il nuovo branch su GitHub
```
git push -u origin <nome-branch>
```

Vedere i branch presenti
```
git branch -a
```

Fare il merge di un branch
```
git merge <nome-branch>
```

Eliminare un branch in locale
```
git branch -D <nome-branch>
```

Eliminare un branch in remoto
```
git push origin --delete <nome-branch>
```

## Comandi base
Creare un repository
```
git init 
```

Clonare localmente un repository 
```
git clone <url-repo>
```

Mostrare lo stato dei file
```
git status
```

Preparare un file per il commit
```
git add <file>
```

Salvare le modifiche
```
git commit -m <messaggio>
```

Inviare le modifiche
```
git push
```

Aggiornare le modifiche
```
git pull
```

Visualizzare la cronologia
```
git log
```

mostra le differenze tra due versioni (file non aggiunti o tra commit)
```
git diff
```

Per abbreviare i comandi (alias)
```
git config --global alias.<comando-abbreviato> '<comando-da-abbreviare>'
```

Esempio:
```
git config --global alias.del-branch 'branch -d'
git del-branch nome-branch
```  

Unisce i branch ma si ottiene una cronologia più pulita rispetto al merge come se fosse sempre stato sullo stesso branch
```
git rebase
```

Annullare le modifiche introdotte da un commit, creando un nuovo commit  
```
git revert
```

Annullare le modifiche tornando indietro a un commit specifico  
```
git reset
```   

Mette da parte temporaneamente tutte le modifiche non committate  

```  
git stash  
```  

Sinconizza i cambiamenti remoti senza modificare i file  
```
git fetch
```

Configura le impostazioni di Git  
```
git config
```

Cancella i file non tracciati in locale  
```
git clean
```

## Git Reflog – Registro delle Attività

Immagina il `reflog` come il **registro delle attività** del tuo progetto Git.  
È come un diario che tiene traccia di tutto quello che fai con i tuoi branch e commit.

---

##  Cosa registra il reflog?

Tutte le tue **azioni importanti**, tra cui:

- Quando cambi branch (`git checkout`)
- Quando fai nuovi commit (`git commit`)
- Quando unisci branch (`git merge`)
- Quando cancelli o modifichi commit (`git reset`, `git rebase`)
---

##  A cosa serve?

- È come il **"Ctrl+Z"** di Git: se fai un errore, puoi tornare indietro
- Ti mostra la **storia completa** di tutto quello che hai fatto
- Ti aiuta a **ritrovare commit** che pensavi di aver perso

---

## Sintassi base

```bash
git reflog
git reflog show <branch>  # Mostra il reflog per un branch specifico
```

---

## Output tipico

L'output mostra righe nel formato:

```
<checksum> HEAD@{<n>}: <azione>: <messaggio>
```

**Esempio:**

```
a1b2c3d HEAD@{0}: commit: Aggiorna documentazione
e4f5g6h HEAD@{1}: checkout: moving from main to feature-branch
```

---

## Casi d'uso principali

### Recupero di commit persi

- Hai eliminato un branch per sbaglio
- Hai fatto un `reset --hard` e vuoi tornare indietro

### Analisi della cronologia

- Vedere tutte le operazioni eseguite nel repository

###  Debug

- Capire quando e come è stato introdotto un bug

---

##  Esempi pratici

### Per vedere tutte le modifiche a HEAD:

```bash
git reflog
```

### Per vedere le modifiche a un branch specifico:

```bash
git reflog show feature-branch
```

### Per tornare a uno stato precedente:

```bash
git reset --hard HEAD@{5}
```

---

##  Importanti note

- Il reflog è **locale** al tuo repository
- Le voci **scadono dopo 90 giorni** (configurabile)
- Il reflog **non viene pushato** sul repository remoto
- È un **meccanismo di sicurezza**, non un sostituto per i commit

---

##  Dettagli aggiuntivi

### Dove eri e dove vai:

- Ricorda qual era il tuo commit precedente
- Registra a quale nuovo commit sei arrivato

> Esempio:  
> "Sei passato dal commit `ABC123` al commit `DEF456`"

### Cosa hai fatto esattamente:

- Scrive se hai fatto un commit, un merge, un reset, ecc.
- Aggiunge il messaggio del commit (se applicabile)

---
##  Esempio pratico

Hai cancellato per sbaglio un branch? Con `git reflog` puoi:

- Vedere quando quel branch esisteva
- Trovare l'ultimo commit che era su quel branch
- **Recuperarlo!**
