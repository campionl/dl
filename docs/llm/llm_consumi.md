# Rapporto sul Consumo Energetico e Idrico dell’Intelligenza Artificiale a Confronto con Altre Industrie Globali

## Introduzione

L’intelligenza artificiale (AI), e in particolare i grandi modelli linguistici (Large Language Models, LLM), stanno crescendo rapidamente in uso e complessità. Questo progresso tecnologico porta con sé un impatto significativo in termini di consumo energetico e risorse naturali, con implicazioni ambientali importanti.

Questo rapporto analizza il consumo di energia e acqua delle AI in ambito mondiale, confrontandolo con quello di altre industrie rilevanti, per inquadrare la reale dimensione del problema.

---

## 1. Consumo Energetico dell’Intelligenza Artificiale

### Allenamento dei Modelli

- L’addestramento di un singolo modello di grandi dimensioni, come GPT-3, ha richiesto circa **1.287 MWh** (megawattora) di energia. Per dare un’idea, questa quantità corrisponde al consumo energetico medio di circa 1.000 abitazioni statunitensi per un mese intero.
- Modelli successivi e più complessi (GPT-4, Gemini, Claude 3) richiedono ancora più risorse, spesso in multipli rispetto a GPT-3.
- L’allenamento è un’attività intensa, ma si svolge una tantum o con frequenza ridotta.

### Inferenza: L’uso Quotidiano

- La fase di inference (cioè il rispondere alle richieste degli utenti) è invece continua e rappresenta la parte più significativa del consumo energetico globale legato all’AI.
- Ad esempio, si stima che GPT-4 consumi fino a **500 MWh al giorno** solo per supportare le richieste in tempo reale.
- Complessivamente, secondo stime recenti, l’intero settore dell’AI generativa consuma oggi tra l’1% e il 2% dell’elettricità mondiale, con una crescita rapida e costante.

![Consumo Energetico dell'AI vs Altre Industrie](https://cdn.statcdn.com/Infographic/images/normal/34295.jpeg)

*Fonte: [Statista](https://www.statista.com/chart/34295/data-centers-electricity-generation-source/)*

Il grafico mostra la crescita dell’energia consumata dai data center e l’incidenza crescente dell’AI.

---

## 2. Confronto con Altre Industrie

| Settore                        | Consumo Energetico Annuale Stimato (TWh) | Consumo Idrico Annuale Stimato            | Note Principali                                    |
|-------------------------------|------------------------------------------|--------------------------------------------|--------------------------------------------------|
| AI (LLM + Data Center)         | 250–300                                  | Circa 700 milioni litri al giorno (USA)    | In forte crescita, con tendenza ad accelerare    |
| Aviazione civile globale       | ~900                                     | N/A                                        | Settore energeticamente rilevante, AI vicino a questi valori |
| Industria del cemento          | ~2.500                                   | Basso                                       | Elevate emissioni di CO₂, settore altamente energivoro  |
| Cloud computing (generale)     | ~600                                     | Alto                                        | AI è una componente crescente all’interno di questo settore |
| Agricoltura globale            | ~4.000                                   | Oltre il 70% del consumo idrico mondiale    | Dominante per l’uso idrico                        |
| Criptovalute (Bitcoin)         | 110–140                                  | Molto basso                                 | Settore ad alta controversia per consumo energetico|

**Nota**: 1 TWh (terawattora) equivale a 1 miliardo di kilowattora.

---

## 3. Confronto con il Settore dei Trasporti

Il settore dei trasporti è uno dei maggiori consumatori di energia a livello globale, in particolare per il trasporto su strada, aereo e marittimo.

- Il consumo energetico globale dei trasporti si aggira intorno ai **3.000 TWh** all’anno, quindi è di gran lunga superiore a quello attuale dell’AI.
- Tuttavia, la rapida crescita dell’AI potrebbe avvicinarsi a questi numeri in un futuro non troppo lontano.
- È importante considerare anche le emissioni di CO₂, dove il settore trasporti è tra i principali responsabili globali.

![Consumo Energetico Settore Trasporti vs AI](https://static.digitalworlditalia.it/wp-content/uploads/2024/06/1719312517-dataev1.jpg)

*Fonte: DigitalWorldItalia*

---

## 4. Impatto Idrico dell’Intelligenza Artificiale

- I data center utilizzano enormi quantità di acqua per il raffreddamento dei server, particolarmente nei sistemi che impiegano raffreddamento a liquido o a immersione.
- Ogni singola richiesta a un modello come GPT-4 può implicare l’uso indiretto di circa 0,5 litri d’acqua per il raffreddamento necessario.
- Per esempio, Google ha dichiarato nel 2022 un consumo di circa **5,6 miliardi di litri d’acqua** per il raffreddamento dei propri data center.
- L’uso idrico è un problema serio soprattutto in aree geografiche già stressate da siccità o carenza d’acqua.

![Confronto Consumo Idrico](https://cdn.lifegate.it/b2SoytIbvqYh3i6kOxIKT-kMeQI=/1536x/smart/https://www.lifegate.it/app/uploads/2025/05/grafico-consumo-acqua-ai.png)

*Fonte: [Life Gate]([https://bryantresearch.co.uk/insight-items/comparing-water-footprint-ai/](https://www.lifegate.it/impatto-ambientale-intelligenza-artificiale))*

Confronto tra consumo idrico dell’AI e di industrie come agricoltura e produzione alimentare.

---

## 5. Tendenze di Crescita e Proiezioni

- Secondo analisi condotte dall’International Energy Agency (IEA) e dal Massachusetts Institute of Technology (MIT), se la crescita del settore AI non sarà frenata, entro il 2030 il consumo energetico globale dell’AI potrebbe superare quello dell’intera Germania, che oggi si attesta intorno ai 500 TWh/anno.
- Le grandi aziende tecnologiche stanno costruendo nuovi data center su scala globale, con infrastrutture sempre più potenti e complesse.
- L’hardware più avanzato, come le GPU NVIDIA H100 o le TPU di ultima generazione, consentono prestazioni elevate ma richiedono anche un maggiore fabbisogno energetico.

![Proiezioni Consumo Energetico Data Center](https://cdn.statcdn.com/Infographic/images/normal/34292.jpeg)

*Fonte: [Statista](https://es.statista.com/grafico/34292/generacion-de-electricidad-para-abastecer-los-centros-de-datos-por-fuente-de-energia/)*

Proiezioni del fabbisogno energetico dei data center, con incidenza delle fonti rinnovabili.

---

## 6. Tecnologie e Strategie per Mitigare l’Impatto

- Quantizzazione e distillazione: metodi che riducono la dimensione dei modelli e di conseguenza il consumo computazionale.
- Modelli più piccoli e ottimizzati: ad esempio LLaMA 3 8B offre un buon compromesso tra performance e consumo.
- Raffreddamento efficiente: utilizzo di sistemi avanzati come il raffreddamento a immersione e il riciclo dell’acqua.
- Energia rinnovabile: crescente impiego di fonti pulite per alimentare i data center, anche se la dipendenza energetica rimane elevata.
- Nonostante i miglioramenti tecnologici, la domanda globale di capacità computazionale continua a crescere più velocemente dei guadagni in efficienza.

![Consumo Energetico per Query AI vs Altri Servizi](https://news.engin.umich.edu/wp-content/uploads/2023/04/EfficientML-feature.jpg)

*Fonte: [Kanoppi](https://news.engin.umich.edu/2023/04/optimization-could-cut-the-carbon-footprint-of-ai-training-by-up-to-75/)*

Confronto del consumo energetico per singola richiesta tra AI e altri servizi digitali.

# Impatto Ambientale dei Modelli Linguistici: Ottimizzazione e Futuro Sostenibile

## 1. Introduzione

I grandi modelli linguistici (LLM) rappresentano uno dei maggiori progressi nell’intelligenza artificiale, ma il loro impatto ambientale è un problema crescente. Addestrare e usare questi modelli richiede enormi risorse computazionali, traducendosi in un significativo consumo di energia e risorse naturali.

Questo documento approfondisce le tecniche di ottimizzazione e le innovazioni hardware volte a ridurre questo impatto, delineando il percorso verso un’AI più sostenibile.

---

## 2. Ottimizzazione Energetica degli LLM

### 2.1 Tecniche di Ottimizzazione

- **Quantizzazione**  
  La quantizzazione trasforma i parametri del modello da formati a precisione elevata (es. 32-bit float) a formati più leggeri (8-bit, 4-bit o addirittura binari).  
  Questo riduce drasticamente il volume di dati da elaborare e la memoria necessaria, abbassando i consumi energetici senza un calo sostanziale delle prestazioni, soprattutto in fase di inferenza.  
  Tecniche moderne, come la quantizzazione post-addestramento (PTQ) o quantizzazione quantistica-aware training (QAT), migliorano la precisione mantenendo alta efficienza.

  ![Quantizzazione dei modelli](https://cdn.prod.website-files.com/680a070c3b99253410dd3df5/680a070c3b99253410dd46d9_67ed557668ef26d8645abad1_6737388c606474b3fdf8d5dd_6737384f8442eff592e5e2f9_Guide_fig4.png)  
  *Fonte: Ultralytics*

- **Distillazione**  
  Con la distillazione si addestra un modello più piccolo (“studente”) a imitare il comportamento di uno più grande e complesso (“insegnante”).  
  Il modello distillato richiede meno parametri e risorse computazionali, rendendo più sostenibile l’uso su larga scala, specie per applicazioni commerciali o su dispositivi con risorse limitate.

  ![Distillazione di un modello](https://img.ai4business.it/wp-content/uploads/2025/03/20120334/immagine-che-contiene-testo-diagramma-mappa-il.jpg.webp)  
  *Fonte: Ai4Business*

- **Pruning (Potatura)**  
  Consiste nell’eliminare pesi, neuroni o intere connessioni non essenziali o con impatto trascurabile sulle prestazioni.  
  Può essere strutturato (rimuovendo intere unità) o non strutturato (rimuovendo singoli pesi).  
  Il pruning permette di alleggerire il modello e ridurre la complessità computazionale, diminuendo il consumo di energia durante addestramento e inferenza.

  ![Pruning in una rete neurale](https://cdn.prod.website-files.com/680a070c3b99253410dd3df5/680a070c3b99253410dd46da_67ed557668ef26d8645abad4_6737388d606474b3fdf8d602_67373828717bb6efa6851dfb_Guide_fig3.png)  
  *Fonte: Ultralytics*

- **Sparse Training e Sparse Inference**  
  L’idea è sfruttare la sparseness, cioè la predominanza di valori zero nelle matrici di pesi, per evitare calcoli inutili.  
  Questo approccio richiede hardware e software specifici, ma promette una riduzione drastica del costo computazionale, specialmente per modelli molto grandi.

- **Mixed Precision Training**  
  Combina calcoli a bassa precisione (16-bit floating point) con quelli a precisione più alta (32-bit) durante l’addestramento, riducendo consumo e memoria senza compromettere la qualità finale del modello.

  ![Mixed Precision Training](https://developer-blogs.nvidia.com/wp-content/uploads/2019/01/pasted-image-0-21.png)  
  *Fonte: Nvidia Developer*

- **AutoML e Neural Architecture Search (NAS)**  
  Automatizzano la ricerca di architetture più efficienti, ottimizzando la struttura del modello per un bilanciamento ottimale tra prestazioni e risorse richieste.  
  Questi metodi aiutano a progettare modelli più leggeri senza sacrificare qualità.

- **Caching e Riutilizzo delle Risposte**  
  Per ridurre il carico di calcolo, è possibile memorizzare risposte a domande frequenti o simili, evitando di ricalcolare risultati già disponibili, diminuendo così l’energia consumata.

---

### 2.2 Hardware e Infrastrutture

- **GPU (Graphics Processing Units)**  
  Sono il principale hardware per training e inferenza di LLM grazie alla loro capacità di eseguire calcoli paralleli massivi.  
  Modelli come NVIDIA A100 e H100 offrono supporto nativo a tecniche come mixed precision e quantizzazione, migliorando l’efficienza energetica.  
  Limite: le GPU consumano comunque molta energia, e per grandi modelli sono necessari cluster enormi.

  ![GPU NVIDIA H100](https://www.nvidia.com/content/nvidiaGDC/it/it_IT/data-center/h100/_jcr_content/root/responsivegrid/nv_container_177275295/nv_image.coreimg.100.1290.jpeg/1738320689973/hopper-h100-grace-hopper-2c50-d-2x.jpeg)  
  *Fonte: NVIDIA*

- **TPU (Tensor Processing Units)**  
  Progettate da Google esclusivamente per il machine learning, sono ottimizzate per operazioni tensoriali e accelerano molto l’addestramento di reti neurali.  
  Consumo energetico per operazione inferiore rispetto alle GPU, ma meno flessibili.  
  Usate principalmente nei data center di Google e in alcune piattaforme cloud.

  ![Google TPU](https://static.tecnichenuove.it/01net/2016/05/google-tpu.png)  
  *Fonte: Google Cloud*

- **ASIC (Application-Specific Integrated Circuits)**  
  Chip custom progettati per specifici compiti AI, massimizzano efficienza energetica riducendo sprechi.  
  Ideali per inferenza in produzione, ma poco flessibili per training o modelli diversi.  
  Sono la scelta d’avanguardia per ridurre consumi energetici negli ambienti edge e data center.

- **FPGA (Field Programmable Gate Arrays)**  
  Circuiti programmabili che possono essere adattati per eseguire modelli AI con efficienza superiore alle GPU in certi scenari.  
  Usati per prototipi o applicazioni specifiche con bisogno di bassa latenza e risparmio energetico.

- **Data Center ad Alta Efficienza Energetica**  
  Innovazioni nell’infrastruttura dei data center riducono il consumo complessivo:  
  - Raffreddamento a liquido o a immersione, che è più efficiente del raffreddamento ad aria.  
  - Microgrid energetiche che integrano fonti rinnovabili locali.  
  - Progettazione “free cooling” che sfrutta il clima freddo naturale per il raffreddamento passivo.

  ![Data Center a immersione](https://qz.com/cdn-cgi/image/width=1920,quality=85,format=auto/https://assets.qz.com/media/7b2f79385bb9b77b26bda9125fe3aabc.jpg)  
  *Fonte: Quartz*

- **Localizzazione e Design**  
  Posizionare data center in regioni con clima freddo (es. Scandinavia, Canada) per minimizzare l’energia spesa nel raffreddamento.  
  Progettare layout che massimizzino la densità di calcolo riducendo i costi energetici.

- **Virtualizzazione e Containerizzazione**  
  Software che massimizzano l’uso delle risorse hardware disponibili, riducendo la necessità di sovra-allocazione e spreco energetico.

---

## 3. Strategie per un Futuro Sostenibile

- **Incremento di Fonti Rinnovabili**  
  Data center e infrastrutture AI devono passare a energia solare, eolica, idroelettrica o altre rinnovabili per abbattere l’impronta carbonica.

- **Recupero e Riciclo del Calore**  
  Il calore generato dalle CPU/GPU può essere recuperato per riscaldare edifici o per processi industriali, diminuendo sprechi.

- **Regolamentazione e Trasparenza**  
  Richiedere alle aziende tech report obbligatori su consumi energetici e impatti ambientali, per rendere pubblico il costo ecologico dei servizi AI.

- **Promozione di Modelli Efficienti e Open Source**  
  Incentivare la diffusione di modelli leggeri, ottimizzati e condivisi, evitando sprechi dovuti a molteplici modelli simili sviluppati separatamente.

- **Ricerca e Innovazione Continua**  
  Supportare la ricerca su nuovi algoritmi e hardware che migliorino il rapporto prestazioni/energia.

---

## 4. Conclusioni

L’intelligenza artificiale è oggi una tecnologia che sta entrando in una fase di impatto ambientale significativo, destinata a crescere rapidamente se non si adottano misure adeguate.

Sebbene non sia ancora tra i settori più energivori o idro-esigenti, la traiettoria di crescita indica che rischia di superare molti settori tradizionali entro pochi anni.

Per garantire uno sviluppo sostenibile è necessario:

- Richiedere maggiore trasparenza da parte delle aziende tech riguardo al consumo energetico e idrico dei loro servizi.
- Investire nella ricerca e sviluppo di modelli più efficienti dal punto di vista energetico.
- Promuovere politiche pubbliche che regolino e incentivino l’uso di energie rinnovabili e la gestione responsabile delle risorse nei data center.
- Sensibilizzare la comunità tecnica e il pubblico sull’impatto ambientale delle tecnologie AI.

La sostenibilità degli LLM non è più un’opzione, ma una necessità.  
Le tecniche di ottimizzazione e l’hardware evoluto sono la chiave per mantenere la crescita tecnologica senza distruggere l’ambiente.  
Servono impegno e trasparenza da parte di tutta l’industria.

---

## 5. Risorse e Approfondimenti

- [Green AI: A Research Agenda](https://arxiv.org/abs/1907.10597)  
- [Efficient Large-Scale Language Model Training on GPUs](https://arxiv.org/abs/2104.04473)  
- [Energy and Policy Considerations for Deep Learning in NLP](https://www.aclweb.org/anthology/P18-1041/)  
- [Sparse Transformers](https://arxiv.org/abs/1904.10509)  
- [Neural Architecture Search: A Survey](https://arxiv.org/abs/1808.05377)  
