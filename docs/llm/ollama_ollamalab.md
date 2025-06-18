# Ollama

## Cos’è Ollama

**Ollama** è un **framework open-source** che permette di **eseguire modelli linguistici (LLM) localmente senza dipendere dal cloud**.  

## A cosa serve

- **Eseguire modelli AI offline** con pieno controllo dei dati    
- **Garantire privacy**, poiché nulla viene inviato all’esterno
- **Sperimentare prompt, chatbot e assistenti** personalizzati
- **Integrare modelli in applicazioni** grazie alla CLI
- **Evitare costi e vincoli del cloud** sfruttando l’hardware locale

## Come funziona

1. **Installazione semplice**  
    Scaricabile da [ollama.com](https://ollama.com/), si installa con pochi comandi. Non servono ambienti complessi.
2. **Gestione modelli integrata**  
	`ollama list` elenca i modelli installati
	`ollama pull <modello>` scarica il modello (es. Llama 3, Mistral, Gemma…)
3. **Esecuzione locale**  
    Una volta scaricato, un modello può essere eseguito direttamente via terminale tramite il comando `ollama run <modello>`
4. **Ottimizzazione automatica**  
    I modelli vengono **quantizzati** automaticamente, riducendo il carico su CPU e GPU e rendendoli più veloci da avviare su hardware consumer.

# Ollama Lab

**Ollama Lab** è una **interfaccia grafica (GUI)** open-source pensata per semplificare l’uso di Ollama, soprattutto per chi preferisce evitare il terminale.

### Cosa permette di fare

- **Chat con i modelli Ollama** in un’interfaccia visuale intuitiva
- **Gestire modelli installati** (scarica, rimuovi, cambia modello)
- **Visualizzare la cronologia delle conversazioni**, tutta in locale
- **Configurare prompt iniziali e parametri**, senza scrivere codice

### Come si installa

- **Linux (Arch/Manjaro)**: disponibile via AUR con `yay -S ollama-lab`
- **Windows/macOS**: scaricabile come eseguibile desktop da GitHub

**Licenza**: open-source (MIT)

## Punti di forza

- **Semplice da usare**: bastano pochi comandi o clic
- **Privacy garantita**: nessun dato esce dal tuo computer
- **Estendibile**: compatibile con WebUI, LangChain, OpenDevin, AutoGen
- **Perfetto per sviluppatori e hobbisti**, ma usabile anche da utenti comuni
- **Gestione container interna**: ogni modello ha il suo ambiente isolato