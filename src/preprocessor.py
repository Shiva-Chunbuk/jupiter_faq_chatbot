import json
import re
import pandas as pd
from typing import List, Dict, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FAQPreprocessor:
    def __init__(self):
        self.processed_faqs = []
        self.categories = set()
        
    def load_raw_faqs(self, filename: str = "data/raw_faqs.json") -> List[Dict]:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                faqs = json.load(f)
            logger.info(f"Loaded {len(faqs)} raw FAQs")
            return faqs
        except FileNotFoundError:
            logger.error(f"File {filename} not found")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {filename}")
            return []
            
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
            
        text = re.sub(r'<[^>]+>', '', text)
        
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        
        text = re.sub(r'\s+', ' ', text)
        
        text = text.strip()
        
        return text
        
    def normalize_question(self, question: str) -> str:
        question = self.clean_text(question)
        
        question = question.lower()
        
        question = re.sub(r'[^\w\s?]', '', question)
        
        if not question.endswith('?'):
            question += '?'
            
        return question.strip()
        
    def categorize_faq(self, question: str, answer: str, existing_category: str = None) -> str:
        if existing_category and existing_category != 'General':
            return existing_category
            
        text = (question + " " + answer).lower()
        
        category_keywords = {
            'Payments': ['payment', 'pay', 'money', 'transfer', 'transaction', 'upi', 'neft', 'imps', 'send money'],
            'KYC': ['kyc', 'verification', 'document', 'identity', 'verify', 'aadhar', 'pan', 'passport'],
            'Rewards': ['reward', 'cashback', 'points', 'benefit', 'earn', 'redeem', 'offer'],
            'Cards': ['card', 'debit', 'credit', 'atm', 'pin', 'activate'],
            'Limits': ['limit', 'maximum', 'minimum', 'daily limit', 'monthly limit'],
            'Account': ['account', 'balance', 'statement', 'profile', 'settings'],
            'Security': ['security', 'password', 'otp', 'fraud', 'safe', 'secure']
        }
        
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
                
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return 'General'
            
    def find_similar_questions(self, faqs: List[Dict], threshold: float = 0.8) -> List[List[int]]:
        questions = [faq['question'] for faq in faqs]
        
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(questions)
        
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        similar_groups = []
        processed_indices = set()
        
        for i in range(len(questions)):
            if i in processed_indices:
                continue
                
            similar_indices = [i]
            for j in range(i + 1, len(questions)):
                if j not in processed_indices and similarity_matrix[i][j] >= threshold:
                    similar_indices.append(j)
                    processed_indices.add(j)
                    
            if len(similar_indices) > 1:
                similar_groups.append(similar_indices)
                processed_indices.update(similar_indices)
                
        return similar_groups
        
    def merge_similar_faqs(self, faqs: List[Dict], similar_groups: List[List[int]]) -> List[Dict]:
        merged_faqs = []
        merged_indices = set()
        
        for group in similar_groups:
            if not group:
                continue
                
            primary_faq = faqs[group[0]]
            
            all_questions = [faqs[i]['question'] for i in group]
            all_answers = [faqs[i]['answer'] for i in group]
            
            longest_answer = max(all_answers, key=len)
            
            merged_faq = {
                'question': primary_faq['question'],
                'answer': longest_answer,
                'category': primary_faq['category'],
                'alternative_questions': all_questions[1:] if len(all_questions) > 1 else []
            }
            
            merged_faqs.append(merged_faq)
            merged_indices.update(group)
            
        for i, faq in enumerate(faqs):
            if i not in merged_indices:
                faq['alternative_questions'] = []
                merged_faqs.append(faq)
                
        return merged_faqs
        
    def process_faqs(self, raw_faqs: List[Dict]) -> List[Dict]:
        logger.info("Starting FAQ preprocessing...")
        
        processed_faqs = []
        
        for faq in raw_faqs:
            if not faq.get('question') or not faq.get('answer'):
                continue
                
            processed_faq = {
                'question': self.clean_text(faq['question']),
                'answer': self.clean_text(faq['answer']),
                'category': self.categorize_faq(
                    faq['question'], 
                    faq['answer'], 
                    faq.get('category')
                )
            }
            
            if len(processed_faq['question']) > 10 and len(processed_faq['answer']) > 20:
                processed_faqs.append(processed_faq)
                self.categories.add(processed_faq['category'])
                
        logger.info(f"Cleaned {len(processed_faqs)} FAQs")
        
        similar_groups = self.find_similar_questions(processed_faqs)
        logger.info(f"Found {len(similar_groups)} groups of similar questions")
        
        merged_faqs = self.merge_similar_faqs(processed_faqs, similar_groups)
        logger.info(f"After merging: {len(merged_faqs)} unique FAQs")
        
        self.processed_faqs = merged_faqs
        
        return merged_faqs
        
    def get_category_stats(self) -> Dict[str, int]:
        category_counts = {}
        for faq in self.processed_faqs:
            category = faq['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts
        
    def save_processed_faqs(self, filename: str = "data/processed_faqs.json"):
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.processed_faqs, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Processed FAQs saved to {filename}")
        
        stats = self.get_category_stats()
        logger.info(f"Category distribution: {stats}")

if __name__ == "__main__":
    preprocessor = FAQPreprocessor()
    raw_faqs = preprocessor.load_raw_faqs()
    
    if raw_faqs:
        processed_faqs = preprocessor.process_faqs(raw_faqs)
        preprocessor.save_processed_faqs()
        print(f"Processed {len(processed_faqs)} FAQs")
        print(f"Categories: {preprocessor.get_category_stats()}")
    else:
        print("No FAQs to process")
