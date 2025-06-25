graph TD
    A[Input Utente: “Quanto fa 3 + 5?”] --> B[Pre-elaborazione]
    subgraph “Flusso di Elaborazione”
    B --> C[Tokenizzazione]
    C --> D[Embedding]
    D --> E[Trasformatori: 3 + 5]
    E --> F[Generazione Output]
    end
    F --> G[Output: “8”]

    %% Dettaglio Tokenizzazione
    C --> C1[“Quanto” → ID: 2456]
    C --> C2[“fa” → ID: 102]
    C --> C3[“3” → ID: 128]
    C --> C4[“+” → ID: 42]
    C --> C5[“5” → ID: 129]
    C --> C6[“?” → ID: 27]

    %% Dettaglio Embedding
    D --> D1[Vettore 256D per “3”]
    D --> D2[Vettore 256D per “+”]
    D --> D3[Vettore 256D per “5”]
    style D1 fill:#f9f,stroke:#333
    style D2 fill:#f9f,stroke:#333
    style D3 fill:#f9f,stroke:#333

    %% Meccanismo Trasformatori
    E --> E1[Self-Attention:<br/>Collega “3”, “+” e “5”]
    E --> E2[Feedforward:<br/>Attiva pattern matematici]
    E --> E3[Calcolo contestuale:<br/>Simula “3+5”]
    style E1 fill:#ffe,stroke:#333

    %% Generazione Output
    F --> F1[Probabilità token:<br/>“8”: 85%<br/>“7”: 10%<br/>“10”: 5%]
    F --> F2[Decodifica: “8” → ID: 130]
    style F1 fill:#e6f7ff,stroke:#333

    %% Spiegazione Matematica
    H[“Come funziona il calcolo?”] --> I[Pattern Recognition]
    H --> J[Correlazione statistica]
    H --> K[Assenza di calcolo reale]
    style H fill:#f96,stroke:#333,stroke-width:2px