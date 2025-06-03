# Git
---
## Cos’è Git
Git è un sistema di controllo di versione distribuito che permette di gestire e tracciare le modifiche al codice sorgente di un progetto in modo efficiente e sicuro. Ogni sviluppatore ha una copia completa del repository, inclusa la storia delle modifiche, e può lavorare sia offline sia online.

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

## Concetti chiave
- **Repository (repo)**: cartella che contiene i file del progetto e la cronologia delle modifiche, può essere locale o remoto
- **Snapshot/Commit**: ogni volta che si salva il lavoro con un commit, Git crea uno snapshot dello stato attuale dei file
- **Checksum SHA-1**: Git usa un codice univoco per identificare ogni commit e file, garantendo l’integrità dei dati

## Aree di lavoro
- **Working directory**: dove si modificano i file
- **Staging area**: dove si preparano le modifiche da includere nel commit
- **Repository locale**: dove Git salva definitivamente i commit

## Flusso di lavoro base
1. **Modificare i file** nella working directory
2. **Aggiungere le modifiche** all’area di staging con ```git add```
3. **Salvare le modifiche** con ```git commit```
4. **Sincronizzare con il repository** remoto usando ```git push``` (invia) e ```git pull``` (riceve)

## Configurazione iniziale
I comandi che seguono vanno eseguiti subito dopo la configurazione di Git per assicurare che ogni commit sia correttamente attribuito.
```
git config --global user.name "<nome>"
git config --global user.email "<email>"
```
