
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

## Risoluzione dei conflitti

### Scenario:

- Entrambi gli utenti, nominati A e B, eseguono un git pull correttamente.
- Entrambi modificano **lo stesso file**.
- L'**utente A** esegue git add e git push correttamente.
- L'**utente B** prova a fare git push, ma riceve un errore in quanto è presente un conflitto fra la versione locale e quella nel repository remoto.

```
! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to 'origin'
hint: Updates were rejected because the tip of your current branch is behind
```

#### Passi da seguire:
- Eseguire una pull dal main (o dal branch in cui si sta lavorando)

```
git pull origin main
```

- Si verifica un conflitto: durante il git pull, Git cercherà di unire i cambiamenti dell’utente A con quelli dell’utente B. Se entrambi hanno modificato la stessa parte dello stesso file, Git non può risolverlo automaticamente e mostrerà un messaggio tipo:
```
Auto-merging esempio.txt
CONFLICT (content): Merge conflict in esempio.txt
Automatic merge failed; fix conflicts and then commit the result.
```

- Aprire il file di testo
Vedrai qualcosa del genere: 
```
<<<<<<< HEAD  
Contenuto modificato da Utente B  
=======
Contenuto modificato da Utente A  
\>>>>>>> origin/main  
```
- Risolvi il conflitto manualmente.  
Decidi come vuoi unire i due contenuti. Puoi:
	- Tenere la versione dell’utente B
	- Tenere la versione dell’utente A
	- Fondere le modifiche manualmente

Esempio di fusione manuale:
Contenuto modificato da Utente A
Contenuto modificato da Utente B
Poi rimuovi i segni speciali (<<<<<<<, =======, >>>>>>>).

- Concludi con le istruzioni di add, commit e push