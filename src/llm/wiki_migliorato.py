import numpy as np
from sentence_transformers import SentenceTransformer
import requests
import json
import re
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import sqlite3
import hashlib
import time
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    title: str
    content: str
    url: str
    source: str
    confidence: float
    metadata: Dict = None

class InMemoryVectorDB:
    """Database vettoriale in memoria per caching e ricerca semantica"""
    
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def add_document(self, doc_id: str, content: str, metadata: Dict = None):
        """Aggiunge un documento al database"""
        embedding = self.model.encode([content])[0]
        
        doc = {
            'id': doc_id,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.documents.append(doc)
        self.embeddings.append(embedding)
        
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Cerca documenti simili alla query"""
        if not self.documents:
            return []
            
        query_embedding = self.model.encode([query])[0]
        
        # Calcola similarità coseno
        similarities = []
        for embedding in self.embeddings:
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append(similarity)
        
        # Ordina per similarità
        indexed_similarities = list(enumerate(similarities))
        indexed_similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Restituisce top_k risultati
        results = []
        for idx, similarity in indexed_similarities[:top_k]:
            if similarity > 0.1:  # Soglia minima
                results.append((self.documents[idx], similarity))
                
        return results

class UniversalQASystem:
    """Sistema Q&A universale migliorato"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_db = InMemoryVectorDB()
        
        # Cache per evitare richieste duplicate
        self.cache = {}
        
        # Headers per richieste HTTP
        self.headers = {
            'User-Agent': 'UniversalQA/2.0 (Educational Purpose)',
            'Accept': 'application/json'
        }
        
        # Configurazione fonti multiple
        self.search_sources = [
            {'name': 'Wikipedia', 'priority': 1, 'enabled': True},
            {'name': 'Wikidata', 'priority': 2, 'enabled': True},
            {'name': 'DBpedia', 'priority': 3, 'enabled': True}
        ]
        
        print("🚀 Sistema Q&A Universale inizializzato!")
        
    def _get_cache_key(self, query: str) -> str:
        """Genera chiave cache per la query"""
        return hashlib.md5(query.lower().encode()).hexdigest()
    
    def _extract_key_terms(self, question: str) -> List[str]:
        """Estrae termini chiave dalla domanda"""
        # Rimuovi parole interrogative comuni
        stop_words = {
            'what', 'who', 'when', 'where', 'why', 'how', 'which', 'whose',
            'cosa', 'chi', 'quando', 'dove', 'perché', 'come', 'quale',
            'is', 'are', 'was', 'were', 'the', 'a', 'an', 'of', 'in', 'on', 'at',
            'è', 'sono', 'era', 'erano', 'il', 'la', 'lo', 'gli', 'le', 'di', 'da', 'in', 'con', 'su', 'per'
        }
        
        # Pulisci e tokenizza
        clean_question = re.sub(r'[^\w\s]', '', question.lower())
        words = clean_question.split()
        
        # Filtra stop words
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Se non ci sono termini chiave, usa tutta la domanda
        if not key_terms:
            key_terms = [question.strip()]
            
        return key_terms
    
    def _search_wikipedia(self, query: str, language: str = 'en') -> List[SearchResult]:
        """Cerca su Wikipedia con fallback multilingua"""
        results = []
        
        # Prova prima con ricerca diretta
        try:
            # API di ricerca Wikipedia
            search_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'extract' in data and data['extract']:
                    results.append(SearchResult(
                        title=data.get('title', query),
                        content=data['extract'],
                        url=data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        source=f'Wikipedia ({language.upper()})',
                        confidence=0.9,
                        metadata={'lang': language, 'type': 'direct'}
                    ))
        except Exception as e:
            logger.debug(f"Errore ricerca diretta Wikipedia: {e}")
        
        # Se non trova niente, prova con ricerca testuale
        if not results:
            try:
                search_api = f"https://{language}.wikipedia.org/w/api.php"
                params = {
                    'action': 'query',
                    'format': 'json',
                    'list': 'search',
                    'srsearch': query,
                    'srlimit': 3
                }
                
                response = requests.get(search_api, params=params, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('query', {}).get('search', []):
                        # Ottieni il contenuto della pagina
                        page_title = item['title']
                        summary_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}"
                        
                        try:
                            summary_response = requests.get(summary_url, headers=self.headers, timeout=5)
                            if summary_response.status_code == 200:
                                summary_data = summary_response.json()
                                if 'extract' in summary_data and summary_data['extract']:
                                    results.append(SearchResult(
                                        title=summary_data.get('title', page_title),
                                        content=summary_data['extract'],
                                        url=summary_data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                                        source=f'Wikipedia ({language.upper()})',
                                        confidence=0.8,
                                        metadata={'lang': language, 'type': 'search'}
                                    ))
                        except:
                            continue
                            
            except Exception as e:
                logger.debug(f"Errore ricerca testuale Wikipedia: {e}")
        
        return results
    
    def _search_wikidata(self, query: str) -> List[SearchResult]:
        """Cerca su Wikidata"""
        results = []
        
        try:
            url = "https://www.wikidata.org/w/api.php"
            params = {
                'action': 'wbsearchentities',
                'format': 'json',
                'language': 'en',
                'search': query,
                'limit': 5
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for entity in data.get('search', []):
                    if 'description' in entity and entity['description']:
                        results.append(SearchResult(
                            title=entity.get('label', ''),
                            content=entity['description'],
                            url=f"https://www.wikidata.org/wiki/{entity['id']}",
                            source='Wikidata',
                            confidence=0.7,
                            metadata={'entity_id': entity['id']}
                        ))
                        
        except Exception as e:
            logger.debug(f"Errore Wikidata: {e}")
            
        return results
    
    def _search_dbpedia(self, query: str) -> List[SearchResult]:
        """Cerca su DBpedia"""
        results = []
        
        try:
            # Prova con lookup service
            url = "http://lookup.dbpedia.org/api/search"
            params = {
                'query': query,
                'format': 'json',
                'maxResults': 3
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('docs', []):
                    if 'comment' in item and item['comment']:
                        results.append(SearchResult(
                            title=item.get('label', [''])[0] if item.get('label') else '',
                            content=item['comment'][0] if isinstance(item['comment'], list) else item['comment'],
                            url=item.get('resource', [''])[0] if item.get('resource') else '',
                            source='DBpedia',
                            confidence=0.6,
                            metadata={'resource': item.get('resource')}
                        ))
                        
        except Exception as e:
            logger.debug(f"Errore DBpedia: {e}")
            
        return results
    
    def _search_all_sources(self, query: str) -> List[SearchResult]:
        """Cerca in tutte le fonti disponibili"""
        all_results = []
        
        # Cerca in Wikipedia (inglese e italiano)
        for lang in ['en', 'it']:
            wiki_results = self._search_wikipedia(query, lang)
            all_results.extend(wiki_results)
            
            # Se trova buoni risultati in inglese, non cercare in italiano
            if lang == 'en' and any(r.confidence > 0.8 for r in wiki_results):
                break
        
        # Cerca in Wikidata
        wikidata_results = self._search_wikidata(query)
        all_results.extend(wikidata_results)
        
        # Cerca in DBpedia solo se non abbiamo abbastanza risultati
        if len(all_results) < 3:
            dbpedia_results = self._search_dbpedia(query)
            all_results.extend(dbpedia_results)
        
        return all_results
    
    def _rank_results(self, question: str, results: List[SearchResult]) -> List[SearchResult]:
        """Ordina i risultati per rilevanza alla domanda"""
        if not results:
            return []
        
        # Calcola embeddings
        question_embedding = self.model.encode([question])[0]
        
        scored_results = []
        for result in results:
            # Combina titolo e contenuto per il matching
            combined_text = f"{result.title} {result.content}"
            content_embedding = self.model.encode([combined_text])[0]
            
            # Calcola similarità semantica
            semantic_similarity = np.dot(question_embedding, content_embedding) / (
                np.linalg.norm(question_embedding) * np.linalg.norm(content_embedding)
            )
            
            # Combina con confidence della fonte
            final_score = (semantic_similarity * 0.7) + (result.confidence * 0.3)
            
            # Aggiorna il punteggio del risultato
            result.confidence = final_score
            scored_results.append(result)
        
        # Ordina per punteggio finale
        scored_results.sort(key=lambda x: x.confidence, reverse=True)
        
        return scored_results
    
    def _generate_answer(self, question: str, best_result: SearchResult) -> str:
        """Genera una risposta naturale basata sul miglior risultato"""
        if not best_result or not best_result.content:
            return "Mi dispiace, non sono riuscito a trovare una risposta alla tua domanda."
        
        content = best_result.content.strip()
        
        # Se il contenuto è troppo lungo, prendi la prima frase significativa
        sentences = content.split('.')
        if len(sentences) > 1 and len(sentences[0]) > 20:
            answer = sentences[0].strip() + '.'
        else:
            answer = content
        
        # Assicurati che la risposta non sia troppo corta o troppo lunga
        if len(answer) < 10:
            answer = content[:200] + '...' if len(content) > 200 else content
        elif len(answer) > 300:
            answer = answer[:300] + '...'
        
        return answer
    
    def ask(self, question: str) -> Dict:
        """Risponde a una domanda"""
        if not question.strip():
            return {"error": "Domanda vuota"}
        
        print(f"❓ Domanda: '{question}'")
        
        # Controlla cache
        cache_key = self._get_cache_key(question)
        if cache_key in self.cache:
            print("📋 Risposta dalla cache")
            return self.cache[cache_key]
        
        # Estrai termini chiave
        key_terms = self._extract_key_terms(question)
        print(f"🔑 Termini chiave: {key_terms}")
        
        # Cerca usando diversi approcci
        all_results = []
        
        # 1. Cerca con la domanda completa
        results = self._search_all_sources(question)
        all_results.extend(results)
        
        # 2. Cerca con i termini chiave combinati
        if len(key_terms) > 1:
            combined_terms = ' '.join(key_terms)
            results = self._search_all_sources(combined_terms)
            all_results.extend(results)
        
        # 3. Cerca con il termine più importante
        if key_terms:
            main_term = max(key_terms, key=len)  # Prende il termine più lungo
            results = self._search_all_sources(main_term)
            all_results.extend(results)
        
        print(f"📊 Trovati {len(all_results)} risultati totali")
        
        if not all_results:
            return {"error": "Nessun risultato trovato"}
        
        # Rimuovi duplicati basati sul contenuto
        unique_results = []
        seen_contents = set()
        for result in all_results:
            content_hash = hashlib.md5(result.content.encode()).hexdigest()
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)
        
        # Ordina per rilevanza
        ranked_results = self._rank_results(question, unique_results)
        
        if not ranked_results:
            return {"error": "Nessun risultato rilevante"}
        
        # Prendi il miglior risultato
        best_result = ranked_results[0]
        
        # Genera risposta
        answer = self._generate_answer(question, best_result)
        
        # Aggiungi alla cache
        response = {
            "question": question,
            "answer": answer,
            "best_result": {
                "title": best_result.title,
                "content": best_result.content,
                "source": best_result.source,
                "url": best_result.url,
                "confidence": best_result.confidence
            },
            "alternative_results": [
                {
                    "title": r.title,
                    "source": r.source,
                    "confidence": r.confidence,
                    "url": r.url
                }
                for r in ranked_results[1:3]
            ],
            "total_results_found": len(all_results),
            "timestamp": datetime.now().isoformat()
        }
        
        # Salva in cache
        self.cache[cache_key] = response
        
        # Aggiungi al database vettoriale per ricerche future
        self.vector_db.add_document(
            doc_id=cache_key,
            content=f"{question} {answer}",
            metadata={"type": "qa_pair", "source": best_result.source}
        )
        
        return response

def main():
    print("🌟 Sistema Q&A Universale - Versione Migliorata")
    print("=" * 60)
    print("Questo sistema può rispondere a qualsiasi tipo di domanda!")
    print("Esempi:")
    print("  • Qual è la capitale dell'Italia?")
    print("  • Who is the president of the United States?")
    print("  • What is quantum computing?")
    print("  • When was the Eiffel Tower built?")
    print("  • Come funziona l'intelligenza artificiale?")
    print("=" * 60)
    
    qa_system = UniversalQASystem()
    
    # Test rapido
    test_questions = [
        "Qual è la capitale dell'Italia?",
        "What is artificial intelligence?",
        "Who invented the telephone?",
        "When was Rome founded?"
    ]
    
    print("\n💡 Domande di esempio:")
    for i, q in enumerate(test_questions, 1):
        print(f"   {i}. {q}")
    
    while True:
        print("\n" + "="*50)
        print("❓ Fai una domanda (o 'exit' per uscire, 'test' per esempio):")
        user_input = input("> ").strip()
        
        if user_input.lower() == 'exit':
            print("👋 Arrivederci!")
            break
        
        if user_input.lower() == 'test':
            user_input = test_questions[0]
            print(f"🧪 Testando con: {user_input}")
        
        if not user_input:
            print("❌ Per favore inserisci una domanda.")
            continue
        
        try:
            start_time = time.time()
            result = qa_system.ask(user_input)
            end_time = time.time()
            
            if "error" in result:
                print(f"❌ {result['error']}")
                continue
            
            print(f"\n✅ RISPOSTA:")
            print(f"💬 {result['answer']}")
            
            print(f"\n📊 DETTAGLI:")
            print(f"🎯 Fonte principale: {result['best_result']['source']}")
            print(f"📄 Titolo: {result['best_result']['title']}")
            print(f"💯 Confidenza: {result['best_result']['confidence']:.3f}")
            print(f"⏱️ Tempo di risposta: {end_time - start_time:.2f}s")
            print(f"📈 Risultati totali trovati: {result['total_results_found']}")
            
            if result['best_result']['url']:
                print(f"🔗 Link: {result['best_result']['url']}")
            
            # Mostra fonti alternative
            if result['alternative_results']:
                print(f"\n🔍 FONTI ALTERNATIVE:")
                for i, alt in enumerate(result['alternative_results'], 1):
                    print(f"   {i}. {alt['title']} ({alt['source']}) - {alt['confidence']:.3f}")
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            logger.error(f"Errore durante la ricerca: {e}", exc_info=True)

if __name__ == "__main__":
    main()
