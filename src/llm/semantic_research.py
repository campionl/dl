"""
Script per ricerca semantica all'interno di file di testo.
Utilizza sentence-transformers per creare embeddings semantici.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import re

class SemanticSearcher:
    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Inizializza il ricercatore semantico.
        
        Args:
            model_name: Nome del modello sentence-transformer da utilizzare
        """
        print(f"Caricamento del modello: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = None
        self.file_paths = []
        
    def load_documents(self, directory: str, extensions: List[str] = ['.txt', '.md', '.py', '.js', '.html', '.css']):
        """
        Carica tutti i documenti dalla directory specificata.
        
        Args:
            directory: Path della directory da scannerizzare
            extensions: Lista delle estensioni di file da considerare
        """
        print(f"Scansione della directory: {directory}")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if content.strip():  # Solo file non vuoti
                                self.documents.append(content)
                                self.file_paths.append(file_path)
                                print(f"Caricato: {file_path}")
                    except Exception as e:
                        print(f"Errore nel caricamento di {file_path}: {e}")
        
        print(f"Caricati {len(self.documents)} documenti")
    
    def chunk_text(self, text: str, max_length: int = 512, overlap: int = 50) -> List[str]:
        """
        Divide il testo in chunk più piccoli per migliorare la ricerca.
        
        Args:
            text: Testo da dividere
            max_length: Lunghezza massima di ogni chunk (in caratteri)
            overlap: Sovrapposizione tra chunk consecutivi
            
        Returns:
            Lista di chunk di testo
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_length
            
            # Cerca l'ultimo punto, punto e virgola o a capo prima del limite
            if end < len(text):
                last_sentence = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end),
                    text.rfind('\n', start, end)
                )
                
                if last_sentence > start:
                    end = last_sentence + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
        return chunks
    
    def create_embeddings(self, use_chunks: bool = True):
        """
        Crea gli embeddings per tutti i documenti caricati.
        
        Args:
            use_chunks: Se True, divide i documenti in chunk più piccoli
        """
        if not self.documents:
            raise ValueError("Nessun documento caricato")
        
        print("Creazione degli embeddings...")
        
        if use_chunks:
            # Crea chunk per ogni documento
            all_chunks = []
            self.chunk_to_file = []  # Mappa chunk -> file originale
            
            for i, doc in enumerate(self.documents):
                chunks = self.chunk_text(doc)
                all_chunks.extend(chunks)
                self.chunk_to_file.extend([i] * len(chunks))
            
            self.text_segments = all_chunks
            print(f"Creati {len(all_chunks)} chunk da {len(self.documents)} documenti")
        else:
            self.text_segments = self.documents
            self.chunk_to_file = list(range(len(self.documents)))
        
        # Crea embeddings
        self.embeddings = self.model.encode(self.text_segments, show_progress_bar=True)
        print(f"Embeddings creati: {self.embeddings.shape}")
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[Tuple[str, str, float]]:
        """
        Effettua una ricerca semantica.
        
        Args:
            query: Query di ricerca
            top_k: Numero massimo di risultati da restituire
            threshold: Soglia minima di similarità
            
        Returns:
            Lista di tuple (file_path, content, similarity_score)
        """
        if self.embeddings is None:
            raise ValueError("Gli embeddings non sono stati creati. Esegui prima create_embeddings()")
        
        print(f"Ricerca per: '{query}'")
        
        # Crea embedding per la query
        query_embedding = self.model.encode([query])
        
        # Calcola similarità
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Ottieni i risultati migliori
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity = similarities[idx]
            if similarity >= threshold:
                file_idx = self.chunk_to_file[idx]
                file_path = self.file_paths[file_idx]
                content = self.text_segments[idx]
                results.append((file_path, content, similarity))
        
        return results
    
    def save_index(self, filepath: str):
        """Salva l'indice per riutilizzo futuro."""
        index_data = {
            'embeddings': self.embeddings,
            'text_segments': self.text_segments,
            'file_paths': self.file_paths,
            'chunk_to_file': self.chunk_to_file
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(index_data, f)
        print(f"Indice salvato in: {filepath}")
    
    def load_index(self, filepath: str):
        """Carica un indice precedentemente salvato."""
        with open(filepath, 'rb') as f:
            index_data = pickle.load(f)
        
        self.embeddings = index_data['embeddings']
        self.text_segments = index_data['text_segments']
        self.file_paths = index_data['file_paths']
        self.chunk_to_file = index_data['chunk_to_file']
        print(f"Indice caricato da: {filepath}")

def main():
    parser = argparse.ArgumentParser(description='Ricerca semantica nei file')
    parser.add_argument('directory', help='Directory da scannerizzare')
    parser.add_argument('query', help='Query di ricerca')
    parser.add_argument('--top-k', type=int, default=5, help='Numero di risultati (default: 5)')
    parser.add_argument('--threshold', type=float, default=0.3, help='Soglia di similarità (default: 0.3)')
    parser.add_argument('--extensions', nargs='+', default=['.txt', '.md', '.py', '.js', '.html', '.css'],
                       help='Estensioni di file da considerare')
    parser.add_argument('--save-index', help='Salva l\'indice in questo file')
    parser.add_argument('--load-index', help='Carica l\'indice da questo file')
    parser.add_argument('--model', default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                       help='Modello sentence-transformer da usare')
    
    args = parser.parse_args()
    
    # Inizializza il ricercatore
    searcher = SemanticSearcher(args.model)
    
    # Carica o crea l'indice
    if args.load_index and os.path.exists(args.load_index):
        searcher.load_index(args.load_index)
    else:
        if not os.path.exists(args.directory):
            print(f"Errore: Directory '{args.directory}' non trovata")
            sys.exit(1)
        
        searcher.load_documents(args.directory, args.extensions)
        if not searcher.documents:
            print("Nessun documento trovato nella directory specificata")
            sys.exit(1)
        
        searcher.create_embeddings()
        
        if args.save_index:
            searcher.save_index(args.save_index)
    
    # Effettua la ricerca
    results = searcher.search(args.query, args.top_k, args.threshold)
    
    # Mostra i risultati
    if not results:
        print("Nessun risultato trovato con la soglia specificata")
    else:
        print(f"\n=== Risultati per '{args.query}' ===")
        for i, (file_path, content, similarity) in enumerate(results, 1):
            print(f"\n{i}. File: {file_path}")
            print(f"   Similarità: {similarity:.3f}")
            print(f"   Contenuto: {content[:200]}{'...' if len(content) > 200 else ''}")
            print("-" * 80)

if __name__ == "__main__":
    # Esempio di utilizzo interattivo se eseguito senza argomenti
    if len(sys.argv) == 1:
        print("=== Ricerca Semantica Interattiva ===")
        
        directory = input("Inserisci il path della directory da scannerizzare: ").strip()
        if not os.path.exists(directory):
            print("Directory non trovata!")
            sys.exit(1)
        
        searcher = SemanticSearcher()
        searcher.load_documents(directory)
        
        if not searcher.documents:
            print("Nessun documento trovato!")
            sys.exit(1)
        
        searcher.create_embeddings()
        
        while True:
            query = input("\nInserisci la query di ricerca (o 'quit' per uscire): ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if query:
                results = searcher.search(query)
                
                if not results:
                    print("Nessun risultato trovato")
                else:
                    print(f"\n=== Risultati per '{query}' ===")
                    for i, (file_path, content, similarity) in enumerate(results, 1):
                        print(f"\n{i}. File: {os.path.basename(file_path)}")
                        print(f"   Percorso: {file_path}")
                        print(f"   Similarità: {similarity:.3f}")
                        print(f"   Estratto: {content[:150]}{'...' if len(content) > 150 else ''}")
    else:
        main()