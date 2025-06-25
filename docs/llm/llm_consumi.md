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

![Consumo Energetico per Query AI vs Altri Servizi](https://kanoppi.co/wp-content/uploads/2025/06/AI-Energy-Comparison.png)

*Fonte: [Kanoppi](https://kanoppi.co/search-engines-vs-ai-energy-consumption-compared/)*

Confronto del consumo energetico per singola richiesta tra AI e altri servizi digitali.

---

## 7. Conclusioni

L’intelligenza artificiale è oggi una tecnologia che sta entrando in una fase di impatto ambientale significativo, destinata a crescere rapidamente se non si adottano misure adeguate.

Sebbene non sia ancora tra i settori più energivori o idro-esigenti, la traiettoria di crescita indica che rischia di superare molti settori tradizionali entro pochi anni.

Per garantire uno sviluppo sostenibile è necessario:

- Richiedere maggiore trasparenza da parte delle aziende tech riguardo al consumo energetico e idrico dei loro servizi.
- Investire nella ricerca e sviluppo di modelli più efficienti dal punto di vista energetico.
- Promuovere politiche pubbliche che regolino e incentivino l’uso di energie rinnovabili e la gestione responsabile delle risorse nei data center.
- Sensibilizzare la comunità tecnica e il pubblico sull’impatto ambientale delle tecnologie AI.
