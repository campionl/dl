## Gestione File e Cartelle nei progetti Git  


### Struttura di base di un Repository  

Un repository Git contiene tipicamente:  
- `README.md`: documento introduttivo del progetto
- `.gitignore`: file che indica quali file/cartelle non devono essere tracciate
- `src/`: cartella con il codice sorgente
- `docs/`: documentazione
- `tests/`: file per i test
- `build/ o dist/`: file compilati o distribuiti (di solito ignorati)
- `.git/`: cartella nascosta creata da Git per tracciare il repository

### Aggiunta File e Cartelle   

```
git add nomefile.estensione
```
```
git add nomecartella/
```

### Rimuovere File e Cartelle
```
git rm nomefile  
```  
```  
git rm -r nomecartella  
```   

### Rinominare o Spostare  
```
git mv vecchio_nome nuovo_nome
```  


### Organizzazione Consigliata del Progetto  
progetto/
│
├── README.md  
├── .gitignore  
├── src/  
│   ├── main/  
│   └── utils/  
├── tests/  
├── docs/  
└── build/   ← da ignorare   

#### Best Practice  
- Mantenere nomi **descrittivi** e **minuscoli** con trattini (`-`) o underscore (`_`).
- Evitare spazi nei nomi.
- Commit frequenti aiutano a tracciare bene le modifiche.
