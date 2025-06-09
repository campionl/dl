# 🔥 Guida alle Funzioni di Attivazione nelle Reti Neurali

## ⚙️ Cos'è una funzione di attivazione?
Una funzione di attivazione è ciò che permette a un neurone artificiale di "decidere" se e quanto attivarsi.  
Serve a introdurre **non-linearità**, così che la rete possa risolvere problemi complessi (come classificazioni, immagini, ecc.).

---

## 📘 Funzioni di attivazione principali

### 1. ReLU (Rectified Linear Unit)
`f(x) = max(0, x)`

- Lascia passare solo i numeri positivi
- È molto veloce da calcolare
- Usata nei layer **nascosti**
- Problema: può "bloccare" neuroni se ricevono valori negativi per troppo tempo (problema dei neuroni morti)

---

### 2. Leaky ReLU
`f(x) = x se x > 0, altrimenti αx (tipicamente α = 0.01)`

- Variante della ReLU
- Permette un piccolo flusso anche quando x è negativa
- Previene i neuroni morti
- Ideale quando noti che la tua rete "smette di imparare"

---

### 3. Sigmoid
`f(x) = 1 / (1 + e^(-x))`

- Trasforma il valore in un numero tra 0 e 1
- Buona per classificazione **binaria**
- Interpretabile come **probabilità**
- Problema: non è centrata sullo 0 → può rallentare l’apprendimento (vanishing gradient)

---

### 4. Tanh (Tangente iperbolica)
`f(x) = (e^x - e^-x) / (e^x + e^-x)`

- Restituisce valori tra **-1 e 1**
- Simile alla sigmoid, ma **centrata**
- Migliore nei layer nascosti rispetto a sigmoid
- Anche lei può avere problemi di vanishing gradient

---

### 5. Softmax
`f(xᵢ) = e^(xᵢ) / Σ e^(xⱼ)`

- Usata solo nel **layer di output**
- Converte un vettore di valori in **probabilità**
- Ideale per classificazione **multiclasse** (3 o più classi)
- La somma di tutti i valori in output è sempre 1

---

## 📊 Tabella Riepilogativa

| Funzione     | Output       | Quando si usa                              |
|--------------|--------------|--------------------------------------------|
| ReLU         | [0, ∞)       | Nei layer nascosti                         |
| Leaky ReLU   | (-∞, ∞)      | Layer nascosti, se ReLU blocca i neuroni   |
| Sigmoid      | (0, 1)       | Output per classificazione binaria         |
| Tanh         | (-1, 1)      | Layer nascosti, alternativa più centrata   |
| Softmax      | [0, 1], somma = 1 | Output per classificazione multiclasse |

---

## ❓ Domande Frequenti

**➤ Quale usare nei layer nascosti?**  
→ ReLU (veloce e funziona bene) o Leaky ReLU (se ReLU blocca i neuroni negativi)

**➤ E nell’output per classificazione binaria (es. sì/no)?**  
→ Sigmoid con **1 solo neurone**

**➤ E per classificazione a 3 o più classi (es. tipo di fiore)?**  
→ Softmax con **tanti neuroni quanti le classi**

**➤ Cos’è il Vanishing Gradient?**  
→ Quando la rete smette di imparare perché i gradienti diventano troppo piccoli (succede spesso con sigmoid o tanh)

---

## 🧠 Consiglio pratico:

- ✅ **ReLU o Leaky ReLU** → nei layer nascosti
- ✅ **Sigmoid** → output per 0/1
- ✅ **Softmax** → output per classificazione 3+ classi
