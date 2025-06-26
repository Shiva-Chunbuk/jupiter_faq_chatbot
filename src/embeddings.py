import json
import numpy as np
from typing import List, Dict, Tuple, Optional
import faiss
from sentence_transformers import SentenceTransformer
import pickle
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FAQEmbeddings:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.faqs = []
        self.embeddings = None
        self.index = None
        self.dimension = 384  # Default dimension for all-MiniLM-L6-v2
        
    def load_faqs(self, filename: str = "data/processed_faqs.json") -> List[Dict]:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.faqs = json.load(f)
            logger.info(f"Loaded {len(self.faqs)} processed FAQs")
            return self.faqs
        except FileNotFoundError:
            logger.error(f"File {filename} not found")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {filename}")
            return []
            
    def create_embeddings(self) -> np.ndarray:
        if not self.faqs:
            logger.error("No FAQs loaded. Call load_faqs() first.")
            return np.array([])
            
        logger.info("Creating embeddings for FAQs...")
        
        texts = []
        for faq in self.faqs:
            combined_text = f"{faq['question']} {faq['answer']}"
            texts.append(combined_text)
            
        self.embeddings = self.model.encode(texts, show_progress_bar=True)
        self.dimension = self.embeddings.shape[1]
        
        logger.info(f"Created embeddings with shape: {self.embeddings.shape}")
        return self.embeddings
        
    def build_faiss_index(self) -> faiss.Index:
        if self.embeddings is None:
            logger.error("No embeddings found. Call create_embeddings() first.")
            return None
            
        logger.info("Building FAISS index...")
        
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        
        normalized_embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.index.add(normalized_embeddings.astype('float32'))
        
        logger.info(f"Built FAISS index with {self.index.ntotal} vectors")
        return self.index
        
    def search_similar(self, query: str, k: int = 5, threshold: float = 0.5) -> List[Tuple[Dict, float]]:
        if self.index is None:
            logger.error("No FAISS index found. Call build_faiss_index() first.")
            return []
            
        query_embedding = self.model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if score >= threshold and idx < len(self.faqs):
                results.append((self.faqs[idx], float(score)))
                
        return results
        
    def save_embeddings(self, embeddings_file: str = "data/embeddings.pkl", 
                       index_file: str = "data/faiss_index.bin"):
        os.makedirs(os.path.dirname(embeddings_file), exist_ok=True)
        
        with open(embeddings_file, 'wb') as f:
            pickle.dump({
                'embeddings': self.embeddings,
                'faqs': self.faqs,
                'dimension': self.dimension
            }, f)
            
        if self.index is not None:
            faiss.write_index(self.index, index_file)
            
        logger.info(f"Embeddings saved to {embeddings_file}")
        logger.info(f"FAISS index saved to {index_file}")
        
    def load_embeddings(self, embeddings_file: str = "data/embeddings.pkl", 
                       index_file: str = "data/faiss_index.bin"):
        try:
            with open(embeddings_file, 'rb') as f:
                data = pickle.load(f)
                self.embeddings = data['embeddings']
                self.faqs = data['faqs']
                self.dimension = data['dimension']
                
            if os.path.exists(index_file):
                self.index = faiss.read_index(index_file)
                
            logger.info(f"Loaded embeddings and index successfully")
            return True
            
        except FileNotFoundError:
            logger.warning("Embeddings or index file not found")
            return False
        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}")
            return False
            
    def get_category_faqs(self, category: str) -> List[Dict]:
        return [faq for faq in self.faqs if faq.get('category', '').lower() == category.lower()]
        
    def search_by_category(self, query: str, category: str, k: int = 3) -> List[Tuple[Dict, float]]:
        category_faqs = self.get_category_faqs(category)
        if not category_faqs:
            return []
            
        all_results = self.search_similar(query, k=len(self.faqs))
        
        category_results = []
        for faq, score in all_results:
            if faq.get('category', '').lower() == category.lower():
                category_results.append((faq, score))
                if len(category_results) >= k:
                    break
                    
        return category_results

if __name__ == "__main__":
    embeddings = FAQEmbeddings()
    
    faqs = embeddings.load_faqs()
    if faqs:
        embeddings.create_embeddings()
        embeddings.build_faiss_index()
        embeddings.save_embeddings()
        
        test_query = "How do I make a payment?"
        results = embeddings.search_similar(test_query, k=3)
        
        print(f"Query: {test_query}")
        print(f"Found {len(results)} similar FAQs:")
        for faq, score in results:
            print(f"Score: {score:.3f} - {faq['question']}")
    else:
        print("No FAQs found to process")
