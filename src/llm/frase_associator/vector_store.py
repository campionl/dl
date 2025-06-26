import numpy as np
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FraseAssociator:
    """Sistema semplice per associare frasi e recuperarle tramite ricerca semantica"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Inizializza il sistema di associazione frasi
        
        Args:
            model_name: Nome del modello per gli embeddings
        """
        self.model_name = model_name
        
        # Inizializza il modello per gli embeddings
        try:
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Modello {model_name} caricato con successo")
        except Exception as e:
            logger.error(f"Errore nel caricamento del modello: {e}")
            self.embedding_model = None
            logger.warning("Usando embeddings casuali per demo")
        
        # Dizionario per le associazioni: frase_input -> frase_output
        self.associazioni = {}
        
        # Lista degli embeddings per le frasi input
        self.embeddings_input = []
        self.frasi_input = []
    
    def _genera_embedding(self, testo: str) -> np.ndarray:
        """Genera embedding per un testo"""
        if self.embedding_model:
            embedding = self.embedding_model.encode(testo, normalize_embeddings=True)
            return embedding
        else:
            # Embedding casuale per demo (sostituire con modello reale)
            # La dimensione deve corrispondere a quella del modello predefinito (384 per 'all-MiniLM-L6-v2')
            return np.random.normal(0, 1, 384)
    
    def aggiungi_associazione(self, frase_input: str, frase_output: str) -> str:
        """
        Associa una frase input a una frase output
        
        Args:
            frase_input: La frase che l'utente potrebbe dire/scrivere
            frase_output: La frase che deve essere restituita come risposta
            
        Returns:
            ID dell'associazione creata
        """
        # Genera un ID unico per l'associazione
        assoc_id = hashlib.md5(f"{frase_input}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        
        # Genera embedding per la frase input
        embedding = self._genera_embedding(frase_input)
        
        # Salva l'associazione
        self.associazioni[frase_input] = {
            'id': assoc_id,
            'input': frase_input,
            'output': frase_output,
            'embedding': embedding,
            'created_at': datetime.now().isoformat()
        }
        
        # Aggiorna le liste per la ricerca
        self.frasi_input.append(frase_input)
        self.embeddings_input.append(embedding)
        
        print(f"✓ Associazione creata (ID: {assoc_id})")
        print(f"  Input:  '{frase_input}'")
        print(f"  Output: '{frase_output}'")
        print()
        
        return assoc_id
    
    def trova_risposta(self, frase: str, soglia_similarita: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        Trova la risposta più simile alla frase data
        
        Args:
            frase: La frase per cui cercare una risposta
            soglia_similarita: Soglia minima di similarità (0-1)
            
        Returns:
            Dizionario con la risposta trovata e il punteggio, o None se non trovata
        """
        if not self.associazioni:
            print("❌ Nessuna associazione presente nel sistema")
            return None
        
        # Genera embedding per la frase di ricerca
        frase_embedding = self._genera_embedding(frase)
        
        # Calcola similarità con tutte le frasi input
        embeddings_array = np.array(self.embeddings_input)
        
        # Verifica se l'array degli embedding è vuoto
        if embeddings_array.size == 0:
            print("❌ Nessun embedding disponibile per il confronto.")
            return None
            
        # Aggiungi un controllo sulla dimensione dell'embedding per evitare errori
        if frase_embedding.shape[0] != embeddings_array.shape[1]:
            print(f"❌ Errore: la dimensione dell'embedding della frase ({frase_embedding.shape[0]}) non corrisponde alla dimensione degli embedding memorizzati ({embeddings_array.shape[1]}).")
            return None

        similarita = cosine_similarity([frase_embedding], embeddings_array)[0]
        
        # Trova la migliore corrispondenza
        idx_migliore = np.argmax(similarita)
        punteggio_migliore = similarita[idx_migliore]
        
        if punteggio_migliore >= soglia_similarita:
            frase_input_migliore = self.frasi_input[idx_migliore]
            associazione = self.associazioni[frase_input_migliore]
            
            risultato = {
                'id': associazione['id'],
                'input_originale': associazione['input'],
                'output': associazione['output'],
                'punteggio': float(punteggio_migliore),
                'frase_cercata': frase
            }
            
            print(f"✓ Risposta trovata (Punteggio: {punteggio_migliore:.3f})")
            print(f"  Tu hai scritto: '{frase}'")
            print(f"  Simile a: '{associazione['input']}'")
            print(f"  Risposta: '{associazione['output']}'")
            print()
            
            return risultato
        else:
            print(f"❌ Nessuna risposta trovata (miglior punteggio: {punteggio_migliore:.3f})")
            print(f"   Soglia richiesta: {soglia_similarita}")
            return None
    
    def elenca_associazioni(self) -> List[Dict[str, Any]]:
        """Elenca tutte le associazioni presenti"""
        risultati = []
        for frase_input, dati in self.associazioni.items():
            risultati.append({
                'id': dati['id'],
                'input': dati['input'],
                'output': dati['output'],
                'created_at': dati['created_at']
            })
        return risultati
    
    def rimuovi_associazione(self, frase_input: str = None, assoc_id: str = None) -> bool:
        """
        Rimuove un'associazione per frase input o ID
        
        Args:
            frase_input: La frase input dell'associazione da rimuovere
            assoc_id: L'ID dell'associazione da rimuovere
            
        Returns:
            True se rimossa con successo, False altrimenti
        """
        frase_da_rimuovere = None
        
        if frase_input and frase_input in self.associazioni:
            frase_da_rimuovere = frase_input
        elif assoc_id:
            for frase, dati in self.associazioni.items():
                if dati['id'] == assoc_id:
                    frase_da_rimuovere = frase
                    break
        
        if frase_da_rimuovere:
            # Trova l'indice nella lista
            try:
                idx = self.frasi_input.index(frase_da_rimuovere)
            except ValueError:
                print("❌ Associazione non trovata nelle liste interne (errore di sincronizzazione).")
                return False
            
            # Rimuovi da tutte le strutture dati
            del self.associazioni[frase_da_rimuovere]
            self.frasi_input.pop(idx)
            self.embeddings_input.pop(idx)
            
            print(f"✓ Associazione rimossa: '{frase_da_rimuovere}'")
            return True
        else:
            print("❌ Associazione non trovata")
            return False
    
    def salva_su_file(self, filepath: str) -> bool:
        """Salva tutte le associazioni su file"""
        try:
            dati_da_salvare = {}
            for frase_input, dati in self.associazioni.items():
                dati_da_salvare[frase_input] = {
                    'id': dati['id'],
                    'input': dati['input'],
                    'output': dati['output'],
                    'embedding': dati['embedding'].tolist(),  # Converti numpy array in lista per la serializzazione JSON
                    'created_at': dati['created_at']
                }
            
            export_data = {
                'associazioni': dati_da_salvare,
                'model_name': self.model_name,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Associazioni salvate in '{filepath}'")
            return True
        except Exception as e:
            print(f"❌ Errore nel salvataggio: {e}")
            return False
    
    def carica_da_file(self, filepath: str) -> bool:
        """Carica le associazioni da file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.associazioni = {}
            self.embeddings_input = []
            self.frasi_input = []
            
            for frase_input, dati in data['associazioni'].items():
                # Riconverti la lista in numpy array
                embedding = np.array(dati['embedding'])
                
                self.associazioni[frase_input] = {
                    'id': dati['id'],
                    'input': dati['input'],
                    'output': dati['output'],
                    'embedding': embedding,
                    'created_at': dati['created_at']
                }
                
                self.frasi_input.append(frase_input)
                self.embeddings_input.append(embedding)
            
            # Verifica se il modello caricato è diverso da quello attuale, e lo aggiorna
            if 'model_name' in data and data['model_name'] != self.model_name:
                logger.warning(f"Il file è stato salvato con un modello diverso ({data['model_name']}). Il sistema sta usando {self.model_name}. Potrebbe esserci una discrepanza negli embeddings.")
                # Opzionalmente, potresti ricaricare il modello qui o rigenerare gli embeddings
            
            print(f"✓ Caricate {len(self.associazioni)} associazioni da '{filepath}'")
            return True
        except FileNotFoundError:
            print(f"❌ Errore: Il file '{filepath}' non è stato trovato.")
            return False
        except json.JSONDecodeError:
            print(f"❌ Errore: Il file '{filepath}' non è un JSON valido.")
            return False
        except Exception as e:
            print(f"❌ Errore nel caricamento: {e}")
            return False
    
    def statistiche(self) -> Dict[str, Any]:
        """Restituisce statistiche del sistema"""
        return {
            'totale_associazioni': len(self.associazioni),
            'modello_utilizzato': self.model_name,
            'dimensione_embedding': len(self.embeddings_input[0]) if self.embeddings_input else 0
        }

def demo_interattiva():
    """Demo interattiva del sistema di associazione frasi"""
    print("=== SISTEMA DI ASSOCIAZIONE FRASI ===")
    print("Associa domande/frasi alle loro risposte!")
    print()
    
    # Inizializza il sistema
    associator = FraseAssociator()
    
    # Aggiungi un set di associazioni più ampio e vario
    print("📝 Aggiungendo un set di associazioni più ampio e diversificato...")

    # Categoria: Saluti e Presentazioni
    associator.aggiungi_associazione("Ciao", "Ciao! Come posso aiutarti oggi?")
    associator.aggiungi_associazione("Buongiorno", "Buongiorno a te! Cosa desideri?")
    associator.aggiungi_associazione("Buonasera", "Buonasera! Sono qui per assisterti.")
    associator.aggiungi_associazione("Salve", "Salve! Dimmi pure.")
    associator.aggiungi_associazione("Come stai?", "Sto bene, grazie per avermelo chiesto! E tu?")
    associator.aggiungi_associazione("Mi chiamo [nome]", "Piacere di conoscerti [nome]! Io sono un assistente virtuale.")
    associator.aggiungi_associazione("Come posso chiamarti?", "Non ho un nome, sono un'intelligenza artificiale.")

    # Categoria: Informazioni sul sistema
    associator.aggiungi_associazione("Chi sei?", "Sono un'intelligenza artificiale, un modello linguistico addestrato da Google.")
    associator.aggiungi_associazione("Cosa sai fare?", "Posso rispondere a domande, generare testi, tradurre lingue e molto altro!")
    associator.aggiungi_associazione("Qual è il tuo scopo?", "Il mio scopo è assistere gli utenti fornendo informazioni e svolgendo compiti.")
    associator.aggiungi_associazione("Quando sei stato creato?", "Sono stato sviluppato di recente, ma la mia conoscenza è in continua espansione.")

    # Categoria: Supporto Generale
    associator.aggiungi_associazione("Ho bisogno di aiuto", "Certo, sono qui per aiutarti. Descrivi il tuo problema.")
    associator.aggiungi_associazione("Non capisco", "Mi dispiace. Potresti riformulare la tua domanda?")
    associator.aggiungi_associazione("Puoi ripetere?", "Certamente, cosa vuoi che ripeta?")
    associator.aggiungi_associazione("Qual è il tuo orario di servizio?", "Sono disponibile 24 ore su 24, 7 giorni su 7.")
    associator.aggiungi_associazione("Parli altre lingue?", "Sì, posso comunicare in diverse lingue.")

    # Categoria: Domande Comuni (Esempio Meteo)
    associator.aggiungi_associazione("Che tempo fa oggi?", "Mi dispiace, non ho accesso a informazioni meteo in tempo reale.")
    associator.aggiungi_associazione("Previsioni del tempo", "Non posso fornire previsioni meteo.")
    associator.aggiungi_associazione("Piove?", "Non ho sensori per rilevare la pioggia.")

    # Categoria: Ringraziamenti e Congedo
    associator.aggiungi_associazione("Grazie", "Prego! Sono felice di aver potuto aiutare.")
    associator.aggiungi_associazione("Ti ringrazio", "Figurati! Se hai altro bisogno, chiedi pure.")
    associator.aggiungi_associazione("Grazie mille", "Di niente! È un piacere.")
    associator.aggiungi_associazione("Arrivederci", "Arrivederci! Spero di sentirti presto.")
    associator.aggiungi_associazione("Ci vediamo dopo", "A presto! Buona giornata.")
    associator.aggiungi_associazione("Buonanotte", "Buonanotte! Riposa bene.")

    # Categoria: Informazioni Specifiche (Esempio Prodotto/Servizio Immaginario)
    associator.aggiungi_associazione("Quanto costa X?", "Il costo di X è di 29.99 euro.")
    associator.aggiungi_associazione("Prezzo del prodotto X", "Il prezzo del prodotto X è di 29.99 euro.")
    associator.aggiungi_associazione("Dove posso comprare Y?", "Puoi acquistare Y sul nostro sito web o nei negozi autorizzati.")
    associator.aggiungi_associazione("Come funziona il servizio Z?", "Il servizio Z ti permette di [spiegazione breve].")
    associator.aggiungi_associazione("Dettagli servizio Z", "Per i dettagli sul servizio Z, consulta la sezione FAQ sul nostro sito.")

    # Categoria: Domande Generali
    associator.aggiungi_associazione("Cosa c'è di nuovo?", "Sono in continuo aggiornamento per migliorare le mie funzionalità.")
    associator.aggiungi_associazione("Raccontami una barzelletta", "Mi dispiace, non sono bravo a raccontare barzellette.")
    associator.aggiungi_associazione("Fammi ridere", "Posso cercare una barzelletta online per te se vuoi!")

    print("\nAssociazioni di esempio caricate. Ora puoi interagire con il sistema.")
    
    while True:
        print("\n" + "="*50)
        print("MENU:")
        print("1. Aggiungi nuova associazione")
        print("2. Cerca risposta")
        print("3. Elenca tutte le associazioni")
        print("4. Rimuovi associazione")
        print("5. Salva su file")
        print("6. Carica da file")
        print("7. Statistiche")
        print("8. Test con frasi simili")
        print("0. Esci")
        
        scelta = input("\nScegli un'opzione (0-8): ").strip()
        
        if scelta == "1":
            print("\n--- AGGIUNGI ASSOCIAZIONE ---")
            frase_input = input("Inserisci la frase/domanda (input): ").strip()
            frase_output = input("Inserisci la risposta (output): ").strip()
            if frase_input and frase_output:
                associator.aggiungi_associazione(frase_input, frase_output)
            else:
                print("❌ Entrambi i campi sono obbligatori!")
        
        elif scelta == "2":
            print("\n--- CERCA RISPOSTA ---")
            frase = input("Inserisci la frase da cercare: ").strip()
            if frase:
                risposta = associator.trova_risposta(frase)
                if not risposta:
                    print("💡 Suggerimento: Prova a riformulare la frase o abbassa la soglia di similarità (modifica il codice della demo).")
            else:
                print("❌ Inserisci una frase valida!")
        
        elif scelta == "3":
            print("\n--- TUTTE LE ASSOCIAZIONI ---")
            associazioni = associator.elenca_associazioni()
            if associazioni:
                for i, assoc in enumerate(associazioni, 1):
                    print(f"{i}. [{assoc['id']}] '{assoc['input']}' → '{assoc['output']}'")
            else:
                print("Nessuna associazione presente.")
        
        elif scelta == "4":
            print("\n--- RIMUOVI ASSOCIAZIONE ---")
            frase_input_o_id = input("Inserisci la frase input ESATTA o l'ID dell'associazione da rimuovere: ").strip()
            if frase_input_o_id:
                if len(frase_input_o_id) == 8: # Presumiamo sia un ID
                    associator.rimuovi_associazione(assoc_id=frase_input_o_id)
                else: # Presumiamo sia la frase input
                    associator.rimuovi_associazione(frase_input=frase_input_o_id)
            else:
                print("❌ Inserisci una frase o un ID valido!")
        
        elif scelta == "5":
            print("\n--- SALVA SU FILE ---")
            filepath = input("Nome del file (default: associazioni.json): ").strip()
            if not filepath:
                filepath = "associazioni.json"
            associator.salva_su_file(filepath)
        
        elif scelta == "6":
            print("\n--- CARICA DA FILE ---")
            filepath = input("Nome del file da caricare (default: associazioni.json): ").strip()
            if not filepath:
                filepath = "associazioni.json"
            associator.carica_da_file(filepath)
        
        elif scelta == "7":
            print("\n--- STATISTICHE ---")
            stats = associator.statistiche()
            for chiave, valore in stats.items():
                print(f"{chiave}: {valore}")
        
        elif scelta == "8":
            print("\n--- TEST FRASI SIMILI ---")
            test_frases = [
                "Salve a tutti",                  # Simile a "Ciao" / "Salve"
                "Come stai tu?",                  # Simile a "Come stai?"
                "Sai dirmi che ora è?",           # Simile a "Che ore sono?"
                "Molte grazie",                   # Simile a "Grazie" / "Ti ringrazio"
                "Ci si vede",                     # Simile a "Arrivederci"
                "Mi dici chi sei?",               # Simile a "Chi sei?"
                "A cosa servi?",                  # Simile a "Cosa sai fare?" / "Qual è il tuo scopo?"
                "Necessito di aiuto",             # Simile a "Ho bisogno di aiuto"
                "Non ho capito",                  # Simile a "Non capisco"
                "C'è il sole oggi?",              # Simile a "Che tempo fa oggi?" / "Piove?"
                "Qual è il prezzo di questo articolo?", # Simile a "Quanto costa X?" / "Prezzo del prodotto X"
                "Dov'è disponibile?",             # Simile a "Dove posso comprare Y?"
                "Come funziona Z?",               # Simile a "Come funziona il servizio Z?"
            ]
            
            print("Testando frasi simili a quelle memorizzate (soglia 0.5 per maggiore flessibilità):")
            for frase in test_frases:
                print(f"\n🔍 Test: '{frase}'")
                associator.trova_risposta(frase, soglia_similarita=0.5) # Soglia leggermente abbassata per i test
        
        elif scelta == "0":
            print("\n👋 Arrivederci!")
            break
        
        else:
            print("❌ Opzione non valida!")

if __name__ == "__main__":
    demo_interattiva()