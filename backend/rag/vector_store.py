"""
RAG Vector Store — keyword-based search with optional embedding upgrade.
Stores document chunks and enables location-based authority retrieval.
Uses TF-IDF for keyword matching (works out of the box with no extra dependencies).
"""
import os
import json
import re
import math
from collections import defaultdict, Counter
from typing import Optional

STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vector_store.json")


class VectorStore:
    """
    Simple but effective keyword-based vector store for RAG retrieval.
    Uses TF-IDF scoring for document retrieval.
    """
    
    def __init__(self):
        self.documents: list = []  # [{text, source, metadata}]
        self.index: dict = {}     # word -> [doc_indices]
        self.idf: dict = {}       # word -> IDF score
        self._loaded = False
        self._load()
    
    def _load(self):
        """Load stored index from disk."""
        try:
            if os.path.exists(STORE_PATH):
                with open(STORE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.documents = data.get("documents", [])
                self._build_index()
                self._loaded = True
                print(f"[VectorStore] Loaded {len(self.documents)} document chunks")
        except Exception as e:
            print(f"[VectorStore] Load error: {e}")
    
    def _save(self):
        """Persist store to disk."""
        os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump({"documents": self.documents}, f, ensure_ascii=False, indent=2)
    
    def add_documents(self, chunks: list):
        """
        Add document chunks to the store.
        chunks: list of {text, source, chunk_index, ...}
        """
        for chunk in chunks:
            self.documents.append({
                "text": chunk["text"],
                "source": chunk.get("source", ""),
                "metadata": {
                    k: v for k, v in chunk.items() 
                    if k not in ("text",)
                }
            })
        
        self._build_index()
        self._save()
        print(f"[VectorStore] Added {len(chunks)} chunks. Total: {len(self.documents)}")
    
    def _tokenize(self, text: str) -> list:
        """Simple tokenization: lowercase, split on non-alphanumeric."""
        return re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    
    def _build_index(self):
        """Build inverted index and compute IDF scores."""
        self.index = defaultdict(list)
        doc_freq = Counter()
        
        for i, doc in enumerate(self.documents):
            tokens = set(self._tokenize(doc["text"]))
            for token in tokens:
                self.index[token].append(i)
                doc_freq[token] += 1
        
        # Compute IDF
        n = len(self.documents) or 1
        self.idf = {
            word: math.log(n / (1 + freq))
            for word, freq in doc_freq.items()
        }
    
    def search(self, query: str, top_k: int = 5) -> list:
        """
        Search for documents matching the query using TF-IDF scoring.
        Returns list of {text, source, score, metadata}.
        """
        if not self.documents:
            return []
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        # Score each document
        scores = defaultdict(float)
        
        for token in query_tokens:
            if token in self.index:
                idf = self.idf.get(token, 0)
                for doc_idx in self.index[token]:
                    # TF: frequency of token in document
                    doc_tokens = self._tokenize(self.documents[doc_idx]["text"])
                    tf = doc_tokens.count(token) / max(len(doc_tokens), 1)
                    scores[doc_idx] += tf * idf
        
        # Sort by score and return top_k
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for idx, score in ranked:
            doc = self.documents[idx]
            results.append({
                "text": doc["text"],
                "source": doc.get("source", ""),
                "score": round(score, 4),
                "metadata": doc.get("metadata", {})
            })
        
        return results
    
    def clear(self):
        """Clear the entire store."""
        self.documents = []
        self.index = {}
        self.idf = {}
        self._save()
    
    def get_stats(self) -> dict:
        """Get store statistics."""
        sources = set(d.get("source", "") for d in self.documents)
        return {
            "total_chunks": len(self.documents),
            "total_sources": len(sources),
            "sources": list(sources),
            "vocabulary_size": len(self.index)
        }


# Singleton
vector_store = VectorStore()
