# Git

## Cos’è Git

Git è un sistema di controllo di versione che permette di gestire e tenere traccia delle modifiche al codice di un progetto. Ogni sviluppatore ha una copia completa del repository, compresa la cronologia delle modifiche, e può lavorare sia offline che online. Questo rende il lavoro di squadra più sicuro, organizzato ed efficiente.

## Concetti chiave

-  **Repository (repo)**: Pensa a un repository (repo) come una cartella speciale per il tuo progetto. Questa cartella non contiene solo i tuoi file, ma anche tutta la storia delle modifiche che hai fatto. Ne esistono due tipi:
	- **Locale**: La copia del progetto che hai sul tuo computer.
	- **Remota**: La copia del progetto che si trova su un server online (come GitHub), utile per collaborare con altri o per avere un backup.
-  **Commit**: Ogni volta che "salvi" il tuo lavoro in Git con un commit, è come se scattassi una "fotografia" (snapshot) del tuo progetto in quel preciso momento. Questa foto cattura lo stato di tutti i tuoi file così come sono in quel commit.

## Aree di lavoro

-  **Working directory**: dove si modificano i file
-  **Staging area**: dove si preparano le modifiche da includere nel commit
-  **Repository locale**: dove Git salva definitivamente i commit

## Flusso di lavoro base

1.  **Modificare i file** nella working directory
2.  **Aggiungere i file modificati** all’area di staging con `git add`
3.  **Salvare le modifiche** con `git commit` con una descrizione appropriata
4.  **Sincronizzare con il repository** remoto usando `git push` (invia) e `git pull` (riceve)

## Configurazione iniziale

I comandi che seguono vanno eseguiti subito dopo la configurazione di Git.
Questi comandi servono per "firmare" i commit su git.
Questo **NON** è un login.

```
git config --global user.name "<nome>"

git config --global user.email "<email>"
```

## Login GitHub

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
3. Quando GitHub chiede **username e password**:
	- Username: *il tuo nome utente GitHub*
	- Password: *Token generato*

### SSH
La chiave SSH fornisce numerosi vantaggi:
- Non devi ricordare token o password
- Accesso automatico a ogni operazione
- Sicuro come una cassaforte bancaria

Per funzionare viene creato un **lucchetto** (detto chiave pubblica) e una **chiave** (detta chiave privata).
- La chiave **PUBBLICA** viene data a GitHub.
- La chiave **PRIVATA** resta sul computer.
#### Configurazione passo-passo
1. **Generazione chiavi**
	```
	ssh-keygen -t ed25519 -C "tua_email@esempio.com"
	```
	Premendo invio tre volte, le chiavi verranno salvate nella cartella di default `C:\\Users\\nomeutente\\.ssh`
2. **Avvia il portachiavi digitale**
	```
	eval "$(ssh-agent -s)"
	```
	Con Windows è necessario abilitare il servizio ssh-agent

	```
	sc config ssh-agent start=auto
	sc start ssh-agent
	```
3. **Aggiungiamo la chiave privata**
	```
	ssh-add ~/.ssh/id_ed25519
	```
4. **Copiare la chiave pubblica**
		Eseguire questo comando e copiare la chiave.
	```
	type ~/.ssh/id_ed25519.pub
	```
5. **Registrare la chiave su GitHub**
	1. Andare su [github.com/settings/keys](https://github.com/settings/keys)  (bisogna essere loggato)
	2. Clicca  **"New SSH key"**
	3. Compila i campi:
	    - **Title**: Un nome riconoscibile (es. "PC Ufficio Windows")
	    - **Key type**: Lascia "Authentication Key"
	    - **Key**: Incolla (`Ctrl+V`) il testo copiato al punto 4
	4. Clicca  **"Add SSH key"**
6. **Tentativo di connessione**
	```
	ssh -T git@github.com
	```
	Se il comando non dà errori, tutto è stato fatto correttamente.  
7. **Conclusioni**
Da adesso, quando si aprirà una repository bisognerà seguire questa sintassi.
	```
	git clone git@github.com:tuousername/nomerepo.git
	```

## Gestione dei branch (rami)

Immaginiamo il nostro progetto (repo) come un albero:
- Il branch *main* è il tronco, ossia la versione stabile del progetto
- I diversi branch (in italiano *rami*) sono copie indipendenti del progetto, dove è possibile implementare nuove funzionalità e testarle senza corrompere la versione stabile.

Creazione di un branch
```
git branch <nome-branch>
```

Spostamento in un branch
```
git checkout <nome-branch>
```

Creazione e spostamento in un nuovo branch
```
git checkout -b <nome-branch>
```

Caricamento il nuovo branch su GitHub
```
git push -u origin <nome-branch>
```

Visualizzazione dei branch presenti
```
git branch -a
```

Merge di un branch
```
git merge <nome-branch>
```

Eliminazione un branch in locale
```
git branch -D <nome-branch>
```

Eliminazione un branch in remoto
```
git push origin --delete <nome-branch>
```

## Comandi base

Creazione di un repository
```
git init
```

Clonazione locale di un repository
```
git clone <url-repo>
```

Visualizzazione dello stato dei file
```
git status
```

Preparazione di un file per il commit
```
git add <file>
```

Salvataggio delle modifiche
```
git commit -m <messaggio>
```

Invio delle modifiche al repo remoto
```
git push
```

Aggiornamento delle modifiche
```
git pull
```

Visualizzazione della cronologia
```
git log
```

Visualizzazione delle differenze tra due versioni (file non aggiunti o tra commit)
```  
git diff
```

Salvataggio temporaneo locale di tutte le modifiche non committate  
```  
git stash  
```  

Ripristino delle modifiche e cancella lo stash
```   
git stash pop
```  

Ripristino delle modifiche mantenute nello stash
```  
git stash apply
```

Visualizzazione di tutti gli stash salvati
```  
git stash list
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

Ricerca del commit che ha introdotto un bug
```
git bisect start
git bisect good [nome di un commit senza bug]
git bad [nome del commit con bug]
# per ogni commit indicare:
git bisect good		# se il bug non è presente
git bisect bad		# se il bug è presente
```

Unione dei branch ma ottenendo una cronologia più pulita rispetto al merge come se fosse sempre stato sullo stesso branch
```
git rebase
```

Annullamento delle modifiche introdotte da un commit, creando un nuovo commit  
```
git revert
```

Annullamento delle modifiche tornando indietro a un commit specifico  
```
git reset
```

Sinconizzazione dei cambiamenti remoti senza modificare i file  
```
git fetch
```

Configurazione delle impostazioni di Git  
```
git config
```

Cancellazione dei file non tracciati in locale  
```
git clean
```

VIsualizzazione delle informazioni dettagliate sul lavoro eseguito nel repo
```
git reflog
git reflog show <branch>  # Mostra il reflog per un branch specifico
git reset --hard HEAD@{5}  # Per tornare a uno stato precedente:
```

Elenca i nomi dei repository remoti configurati
```
git remote
```

Elenca i remoti con gli URL di fetch e push
```
git remote -v
```

Aggiunge un nuovo repository remoto
```
git remote add <nome> <url>	
```

Rimuove un repository remoto
```
git remote remove <nome>	
```

Cambia il nome di un repository remoto
```
git remote rename <nome-vecchio> <nome-nuovo>	
```

## Gestione file e cartelle nei progetti Git 

Un repository Git dovrebbe sempre contenere:  
- `README.md`: documento introduttivo del progetto contenente i riferimenti agli altri documenti
- `src/` oppure `app/`: cartella contenente il codice sorgente del progetto
- `docs/`: cartella contenente i file di documentazione del progetto
- `assets/`: cartella contenente file grafici come immagini, icone e font
- `tests/`: cartella contenente i file di test automatici
- `config/`: cartella contenente i file di configurazione del progetto
- `build/` oppure `dist/`: cartella contenente i file compilati o distribuiti (di solito ignorati)
- `license.txt`: file contenente il testo legale della licenza del tuo progetto
- `.gitignore`: file che indica quali file o cartelle non devono essere tracciate da Git
- `.git/`: cartella nascosta creata da Git per tracciare il repository

## Convenzioni per le descrizioni dei commit
Quando si esegue un commit bisogna descrivere accuratamente cosa è stato modificato così da non creare confusione nei collaboratori quando vanno a leggere le modifiche.  
Un **buon commit** segue questo schema:
```
<tipo>(<ambito>): <descrizione breve>
<corpo del commit (opzionale)>
<footer (opzionale)>
```
Nel campo **"tipo"** possiamo avere:
- `feat` (nuova funzionalità);
- `fix` (correzione bug);
- `docs` (modifiche alla documentazione);
- `style` (modifiche alla formattazione);
- `refactor` (modifiche al codice che non correggono bug nè aggiungono funzionalità);
- `perf` (miglioramento delle prestazioni);
- `test` (aggiunta o modifica di test);
- `chore` (task di manutenzione);
- `ci` (cambiamenti di CI/CD);
- `build` (modifiche a script di build);
- `revert` (rollback di un commit precedente);

E' consigliato separare le modifiche, per esempio non eseguire un fix e un feat nello stesso commit.
Nel campo **"ambito"** specifichiamo la parte del progetto coinvolta.
Per la **descrizione breve** inseriamo un testo conciso (circa 50 caratteri), dove spieghiamo cosa abbiamo fatto. Solitamente si usa l'imperativo e non si mettono punti alla fine.  
Nel **corpo del commit** spieghiamo cosa abbiamo fatto e perchè e solitamente si usa un elenco puntato.
Il **footer** è opzionale e si utilizza per riferimenti esterni.  

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

Poi rimuovi i segni speciali (`<<<<<<<`, `=======`, `>>>>>>>`).

- Concludi con le istruzioni di add, commit e push
