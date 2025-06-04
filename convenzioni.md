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

<<<<<<< HEAD
Nel campo **"ambito"** specifichiamo la parte del progetto coinvolta.  
Per la **descrizione breve** inseriamo un testo conciso (circa 50 caratteri), dove spieghiamo cosa abbiamo fatto. Solitamente si usa l'imperativo e non si mettono punti alla fine.  
Nel **corpo del commit** spieghiamo cosa abbiamo fatto e perchè e solitamente si usa un elenco puntato.  
Il **footer** è opzionale e si utilizza per riferimenti esterni.  
E' consigliato separare le modifiche, per esempio non eseguire un fix e un feat nello stesso commit.
=======
Nel campo **"ambito"** specifichiamo la parte del progetto coinvolta.
Per la **descrizione breve** inseriamo un testo conciso (circa 50 caratteri), dove spieghiamo cosa abbiamo fatto. Solitamente si usa l'imperativo e non si mettono punti alla fine.  
Nel **corpo del commit** spieghiamo cosa abbiamo fatto e perchè e solitamente si usa un elenco puntato.
Il **footer** è opzionale e si utilizza per riferimenti esterni.  
E' consigliato separare le modifiche, per esempio non eseguire un fix e un feat nello stesso commit.
>>>>>>> git
