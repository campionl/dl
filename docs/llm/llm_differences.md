# Confronto tra i Principali LLM

| Modello        | Anno | Parametri  | Multimodale | Open Source | Contesto Max     | Note Principali                                 |
|----------------|------|------------|-------------|--------------|------------------|--------------------------------------------------|
| ***GPT-3***      | 2020 | 175B       | [ ]          | [ ]           | ~2K token         | Primo LLM mainstream, base di ChatGPT v1        |
| ***GPT-4***      | 2023 | ? (stimato ~1T) | [x]      | [ ]           | 32K token         | Migliorato nel reasoning, non open              |
| ***GPT-4 Turbo***| 2024 | ?          | [x]          | [ ]           | 128K token        | Più economico e veloce, usato in ChatGPT Plus   |
| ***Claude 3 Opus*** | 2024 | ?       | [x]          | [ ]           | 200K+ token       | Ottimo nel reasoning e sicurezza                |
| ***Claude 3.5*** | 2025 | ?          | [x]          | [ ]           | 200K+ token       | Forte in coding, rilasciato giugno 2025         |
| ***Gemini 1.5 Pro***| 2024 | ?       | [x]          | [ ]           | 1M token          | Lunghissimo contesto, eccellente analisi        |
| ***Mistral 7B*** | 2023 | 7B         | [x]          | [x]           | ~32K token        | Efficiente, ottimo per uso locale               |
| ***Mixtral 8x7B*** | 2023 | 12.9B attivi (MoE) | [ ] | [x]           | ~32K token        | Architettura Mixture of Experts                 |
| ***LLaMA 2***    | 2023 | 7B / 13B / 70B | [ ]       | [x] (con licenza) | ~4K–32K token | Base per tanti modelli open                     |
| ***BERT***       | 2019 | 110M (base), 340M (large) | [ ] | [x]       | Fisso (no contesto esteso) | Ottimo per NLP classico, non generativo         |
| ***BLOOM***      | 2022 | 176B       | [ ]          | [x]           | ~2K token         | Multilingua, comunitario                        |
| ***Grok (xAI)*** | 2023 | ?          | [ ]          | [ ]           | ?                 | Creato da Elon Musk, integrato in X             |

---

## *Legenda*
- **Multimodale**: può gestire testo + immagini (e in futuro audio/video)
- **Contesto Max**: quanti token può ricordare in un singolo prompt
- **MoE**: *Mixture of Experts* (attiva solo una parte dei neuroni → efficienza)

---

## *Note finali*
- I modelli **GPT-4 Turbo, Claude 3.5, Gemini 1.5 Pro** sono i più avanzati al momento.
- I modelli **Mistral e LLaMA** sono perfetti per chi vuole **modelli open-source**.
- **BERT** resta fondamentale per analisi testuale classica, ma non genera testo.

