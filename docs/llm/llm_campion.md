I modelli di intelligenza artificiale come gli LLM sono **reti neurali** che lavorano con **vettori numerici** (detti *vettori di embedding*).
Quindi prima di tutto devono **"tradurre" il testo** (sequenze di caratteri o parole) in una **forma numerica**. Questo processo si chiama ***preprocessing*** e il passo principale è la ***tokenizzazione***.

## Tokenizzazione
### Cos'è

La ***tokenizzazione*** è il processo che **divide** il testo in “pezzi” chiamati **token**.  

> **Token**
> **Unità minime** utili al modello per **comprendere** e **calcolare**

Un **token** può essere:
- una parola intera (`"ciao"`)
- una parte di parola (`"inform"` in `"informatica"`)
- un simbolo (`"."`, `"?"`)
- uno spazio (`" "`)

### Come funziona

Ogni modello ha un **tokenizer** integrato, cioè un **algoritmo** che divide l'input in token consultando un **vocabolario di token**.
Ecco cosa fa il tokenizer:

**Input**
Testo: `"Ciao, come stai?"`

**Step 1: suddivide il testo in token**
```python
["Ciao", ",", "come", "stai", "?"]
```
oppure
```python
["C", "iao", ",", "come", "st", "ai", "?"]
```

**Step 2: converte ogni token in un numero (indice)**

| Token  | ID   |
| ------ | ---- |
| "Ciao" | 5012 |
| ","    | 13   |
| "come" | 998  |
| "stai" | 2074 |
| "?"    | 30   |

Il modello **lavora su questi ID numerici**, che poi vengono **convertiti in vettori** tramite **embedding** (ne parliamo dopo).

---

## Embedding

Gli **ID dei token** vengono successivamente convertiti in **vettori di embedding** (tramite un processo anch'esso chiamato *embedding*).

Esempio (semplificato):

```python
Token "ciao" → ID 5012 → Embedding: [0.12, -0.07, ..., 0.93]
```

I **vettori di embedding** (lunghi ad esempio 768 o 2048 elementi) codificano **informazioni complesse e astratte** su ogni token, tra cui il significato semantico, il ruolo sintattico (sostantivo, verbo, …), il contesto d’uso (es. “banca” come edificio o istituto finanziario) e le relazioni tra parole (es. “regina” - “re” ≈ “donna” - “uomo”)

Questi vettori vengono poi **elaborati** nei vari **strati del modello** (Transformer, Attention, ecc.).