# Git flow

### Cos'è git flow?  

Git flow è un modello per la gestione del flusso di lavoro sui branch,  
questo inoltre a differenza di modelli più moderni utilizza due branch principali,  
ovvero `main` e `develop` 
  
- il `main` o `master` è il branch stabile dove inseriamo solo la versione finale che ha superato tutti i test necessari per assicurarsi che sia funzionante.  
- il `develop` è il branch dove lavoriamo attivamente allo sviluppo di nuove funzionalità, il fix dei bugs, ottimizzazione e altri miglioramenti, in poche parole è la base dove si costruisce tutto prima di andare sul main.

### Come lavoriamo usando git flow?  
  
Quando lavoriamo sulla repository usando la libreria git-flow,  
il comando git flow init creera su una repository esistente il branch `develop`.  

mentre lavoriamo sul develop se vogliamo testare una nuova funzione per vedere come si applica nel contesto del programma su qui stiamo lavorando e per evitare che il branch develop venga corrotto creiamo un nuovo branch `feature`,  

- il branch `feature` agisce per il branch **develop** nella stessa maniera in qui **develop** agisce per il **main** o **mastes** in modo tale da non rallentare il progresso sul branch principale  
  
***In parole povere noi utilizziamo feature per testare funzioni da poi aggiungere a develop***

Se vogliamo creare un branch feature possiamo usare un comando sempre dalla libreria git-flow:  
`git flow feature start feature_branch`  
oppure senza la libreria:  
`git checkout develop`  
`git checkout -b feature_branch`  

### Cosa fare al completamento e approvazione di una feature?  

Quando abbiamo finito di lavorare ad una feature **e** abbiamo ottenuto l'approvazione perchè venga implementata, possiamo fondere il branch `feature`con il branch `develop` usando il la libreria di git-flow:  
`git flow feature finish feature_branch`  
oppure senza:  
`git checkout develop`  
[`git merge feature_branch`](https://github.com/campionl/dl/blob/4edf30cc6e715a677dc493fe65a291c02501e2b1/git.md?plain=1#L42)  

### Quando devo rilasciare il programma come mi preparo?  

A questo punto se abbiamo finito il programma o ci stiamo avvicinando alla data di rilascio del software creeremo un nuovo branch a partire da `develop`, questo sarà il branch `release`.  

- il branch `release` serve a prepararsi al rilascio del software, arrivati a questo punto non potremo più applicare modifiche o aggiungere nuove feature, in questo branch potremo solo fare bug fix e aggiungere la documentazione relativa al programma.

Per creare il branch `release` come sempre abbiamo due modi:  
- Con libreria git-flow:
  `git flow release start 0.1.0`
  l'ultimo numero è correlato alla versione del software
- Senza libreria:
  `git checkout develop`
  `git checkout -b release/0.1.0`
  
Ovviamente quando saremo arrivati al giorno del rilascio dovremo unire il branch `release` al `main` per poi cancellare `release` quindi:  
- Con lib:
  `git flow release finish '0.1.0'`
- Senza lib:
  `git checkout main`
  `git merge release/0.1.0`

### Se ho fatto un breve errore è voglio correggerlo rapidamente?  

Ci sono ovviamente casi in qui il software potrebbe riscontrare degli errori, per sistemare tali errori abbiamo a disposizione il branch `hotfix`.  
- `hotfix` serve per manutenzioni rapide, ha differenza di `release` e `feature` questo viene creato sotto il `main` o `master`.

Avere una linea di sviluppo separata permette di gestire i ticket senza intaccare il resto del flusso di lavoro  

Per creare un branch hotfix:  
- Con lib:
  `git flow hotfix start hotfix_branch`
- Senza lib:
  `git checkout main`
  `git checkout -b hotfix_branch`
