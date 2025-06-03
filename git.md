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
