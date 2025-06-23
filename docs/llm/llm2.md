# LLM: Large Language Models

## Cosa sono gli LLM

I **Large Language Models (LLM)** sono programmi di intelligenza artificiale che "leggono" enormi quantità di testo (libri, articoli, siti web, ...) e imparano a generare risposte simili a quelle umane.  
- **Come funzionano?** Immagina un super-autocompletamento: dato un input (es. *"Come si fa la carbonara?"*), l'LLM prevede la risposta più probabile basandosi sui testi che ha visto.  
- **Perché "Large"?** Perché hanno miliardi di parametri (come neuroni digitali) e richiedono tantissimi dati per l'addestramento.  
- **A cosa servono?** Scrivere testi, tradurre lingue, rispondere a domande, generare codice, riassumere documenti e altre attività.

Alcuni esempi famosi sono **ChatGPT** (OpenAI), **Gemini** (Google), **Claude** (Anthropic) e **DeepSeek** (High-Flyer).

---

## Quando e come sono nati

L'idea di far "parlare" i computer esiste dagli anni '50, ma gli LLM moderni sono una rivoluzione recente:  

1. **Anni '60-2000**: primi chatbot come **ELIZA** (basato su regole fisse).  
2. **2000-2017**: modelli statistici e reti neurali ricorrenti (**RNN**), ancora limitati.  
3. **2017**: svolta con il **Transformer** (Google), un'architettura che usa l'**attenzione** per capire il contesto delle parole.  
4. **2018-oggi**: esplosione degli LLM:  
   - **GPT-3** (2020, OpenAI): 175 miliardi di parametri, capace di scrivere articoli e codice, addestrato su un testo equivalente a 20 milioni di libri.  
   - **GPT-4** (2023) e **Gemini** (Google): multimodali (testo + immagini).  
   - **LLaMA** (Meta): modelli open-source per la ricerca.  

---

## Da cosa sono composti e come funzionano

Gli LLM sono come cervelli digitali basati su:  

### 1. Architettura Transformer
L'architettura Transformer prevede tre fasi principali durante l'elaborazione dei dati:
- **Tokenizzazione**: il testo è diviso in pezzi (token), come parole o sillabe.  
- **Embedding**: ogni token è convertito in un numero (vettore) che ne rappresenta il significato.  
- **Attenzione**: la vera novità di questa architettura, introdotta nel 2017 da un team di Google nel *paper* "*Attention is all you need*", analizza le relazioni tra le parole (es. in *"Il gatto miagola"*, "miagola" è legato a "gatto").  

### 2. Fasi di apprendimento
- **Pre-training**: il modello impara da testi generici (es. Wikipedia) a prevedere la parola successiva.  
- **Fine-tuning**: viene specializzato (es. per chatbot o traduzioni).  
- **RLHF (Reinforcement Learning from Human Feedback)**: umani correggono le risposte per renderle più accurate e sicure.  

### 3. Generazione del testo
Quando chiedi qualcosa a un LLM:  
1. Suddivide la domanda in token.  
2. Analizza il contesto con l'attenzione.  
3. Genera la risposta parola per parola, calcolando la probabilità di ogni opzione.  

**Esempio:** se chiedi *"Chi ha scritto la Divina Commedia?"*, cerca nei suoi dati e risponde *"Dante Alighieri"*.  

---

## LLM Reasoning: capacità di ragionamento logico

Uno degli aspetti più avanzati degli LLM è il **reasoning**, ovvero la capacità di elaborare ragionamenti logici, dedurre informazioni e risolvere problemi complessi attraverso passaggi strutturati. A differenza delle semplici risposte basate sul riconoscimento di pattern, il reasoning implica:  
- **Analisi contestuale**: comprendere il problema in profondità.  
- **Scomposizione del problema**: dividere una domanda complessa in sotto-domande più semplici.  
- **Catene logiche**: collegare concetti in sequenza (es. *"Se A, allora B; dato che B è falso, A deve essere..."*).  
- **Gestione delle ambiguità**: distinguere tra significati multipli di una frase.  

### Approcci diversi nei vari LLM
- **GPT-4, Claude e Gemini**: spesso **nascondono il ragionamento**, mostrando solo la risposta finale, a meno che non venga esplicitamente richiesto (es. *"Spiega passo per passo"*). Questo può limitare la trasparenza.  
- **MiMo-7B**: si distingue perché **mostra automaticamente il processo logico**, come un tutor che:  
	- Definisce il contesto.  
	- Elenca i passaggi intermedi.  
	- Giustifica la risposta finale.
Questo approccio lo rende ideale per **applicazioni educative**, debugging tecnico o situazioni in cui la spiegabilità è cruciale.  

### Perché il reasoning è una sfida  
Nonostante i progressi, gli LLM **non ragionano come esseri umani**:  
- **Sono probabilistici**: scelgono la risposta più "plausibile", non sempre corretta.  
- **Sensibili alla formulazione**: una domanda rielaborata può cambiare la risposta.  
- **Limitazioni in astrazione**: faticano con problemi che richiedono creatività o conoscenze non presenti nei dati di addestramento.  

### Futuro del reasoning negli LLM  
Le ricerche più recenti puntano a:  
- **Modelli "a pensiero visibile"** (come MiMo-7B), che migliorano la fiducia degli utenti.  
- **Integrazione con strumenti esterni** (calcolatrici, database) per compensare i limiti logici.  
- **Allenamento su problemi strutturati** (matematica, codice) per affinare la precisione.  

Il reasoning è un confine critico tra LLM "utili" e sistemi veramente intelligenti, ma la strada è ancora lunga.  

---

## In quale contesto si collocano

Gli LLM fanno parte di:  
- **Intelligenza Artificiale (IA)**: campo generale per macchine "intelligenti".  
- **Machine Learning**: apprendono dai dati senza essere programmati esplicitamente.  
- **NLP (Natural Language Processing)**: settore che studia l'interazione tra computer e linguaggio umano.  

Rispetto ai vecchi sistemi di NLP basati su regole rigide (es. *"Se la domanda contiene 'Divina Commedia', rispondi 'Dante'""*), gli LLM imparano da soli, sono flessibili e adattabili.

---

## Stato dell'arte (2024-2025)
Oggi gli LLM sono più potenti che mai:  

### Modelli più avanzati
- **GPT-4o** (OpenAI): multimodale (gestisce testo, immagini e audio).  
- **Claude 3** (Anthropic): focus su sicurezza e risposte affidabili.  
- **Gemini 1.5** (Google): integra ricerche web in tempo reale.  
- **LLaMA 3** (Meta): open-source, usato per ricerca e sviluppo.  

### Capacità principali  
- Scrivere testi complessi (articoli, poesie, codice).  
- Tradurre in modo fluido tra lingue.  
- Rispondere a domande tecniche (anche se a volte sbagliano).  
- Creare contenuti multimediali (testo + immagini).  

### Limiti Attuali  
- **Allucinazioni**: Inventano risposte plausibili ma false.  
- **Bias**: Riproducono pregiudizi presenti nei dati di addestramento.  
- **Costi**: Consumano molta energia per l'addestramento.  

---

## Futuro e Sfide  
- **Efficienza**: Modelli più piccoli ma potenti (es. Mistral 7B).  
- **Multimodalità**: Integrazione con video, suoni e sensori.  
- **Etica**: Come evitare disinformazione e garantire privacy.  
- **Lavoro**: Automazione di alcuni compiti (es. scrittura, customer service).  

**Domande Aperte:**  
- Riusciranno mai a "ragionare" come gli umani?  
- Come regolarne l'uso per evitare abusi?  

---

## Conclusione  
Gli LLM sono strumenti straordinari, ma non "capiscono" davvero ciò che dicono: sono come pappagalli super-intelligenti. Il loro futuro dipenderà da come li useremo, bilanciando innovazione ed etica.