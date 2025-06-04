# Conflitti 
___


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
