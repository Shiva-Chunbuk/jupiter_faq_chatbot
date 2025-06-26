import os
import json
import openai
from typing import List, Dict, Tuple, Optional
from .embeddings import FAQEmbeddings
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JupiterFAQBot:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.warning("No OpenAI API key provided. Bot will work in retrieval-only mode.")
        else:
            openai.api_key = self.openai_api_key
            
        self.embeddings = FAQEmbeddings()
        self.conversation_history = []
        self.confidence_threshold = 0.6
        
    def initialize(self):
        logger.info("Initializing FAQ bot...")
        
        if not self.embeddings.load_embeddings():
            logger.info("No pre-computed embeddings found. Creating new ones...")
            faqs = self.embeddings.load_faqs()
            if faqs:
                self.embeddings.create_embeddings()
                self.embeddings.build_faiss_index()
                self.embeddings.save_embeddings()
            else:
                logger.error("No FAQs found to initialize the bot")
                return False
                
        logger.info("FAQ bot initialized successfully")
        return True
        
    def search_faqs(self, query: str, k: int = 3) -> List[Tuple[Dict, float]]:
        return self.embeddings.search_similar(query, k=k, threshold=self.confidence_threshold)
        
    def generate_response_with_llm(self, query: str, relevant_faqs: List[Tuple[Dict, float]]) -> str:
        if not self.openai_api_key:
            return self._generate_simple_response(relevant_faqs)
            
        try:
            context = self._build_context(relevant_faqs)
            
            system_prompt = """You are a helpful customer service assistant for Jupiter, a digital banking app. 
            Your role is to provide friendly, accurate, and conversational answers to user questions about Jupiter's services.
            
            Guidelines:
            - Be conversational and friendly
            - Use the provided FAQ context to answer questions accurately
            - If you're not confident about an answer, say so politely
            - Keep responses concise but helpful
            - Use simple language that anyone can understand
            - If the question is not related to Jupiter banking services, politely redirect
            """
            
            user_prompt = f"""
            User Question: {query}
            
            Relevant FAQ Information:
            {context}
            
            Please provide a helpful and conversational response based on the FAQ information above.
            If the FAQs don't contain enough information to answer the question confidently, 
            let the user know and suggest they contact Jupiter support directly.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return self._generate_simple_response(relevant_faqs)
            
    def _build_context(self, relevant_faqs: List[Tuple[Dict, float]]) -> str:
        context_parts = []
        for i, (faq, score) in enumerate(relevant_faqs, 1):
            context_parts.append(f"""
            FAQ {i} (Relevance: {score:.2f}):
            Q: {faq['question']}
            A: {faq['answer']}
            Category: {faq['category']}
            """)
        return "\n".join(context_parts)
        
    def _generate_simple_response(self, relevant_faqs: List[Tuple[Dict, float]]) -> str:
        if not relevant_faqs:
            return "I'm sorry, I couldn't find any relevant information to answer your question. Please contact Jupiter support for assistance."
            
        best_faq, score = relevant_faqs[0]
        
        if score < 0.7:
            return f"I found some potentially relevant information, but I'm not entirely confident it answers your question:\n\n{best_faq['answer']}\n\nFor more specific help, please contact Jupiter support."
        else:
            return f"Based on our FAQ, here's what I found:\n\n{best_faq['answer']}"
            
    def get_response(self, query: str) -> Dict:
        logger.info(f"Processing query: {query}")
        
        if not query.strip():
            return {
                'response': "Please ask me a question about Jupiter banking services!",
                'confidence': 0.0,
                'source_faqs': [],
                'suggestions': self._get_popular_questions()
            }
            
        relevant_faqs = self.search_faqs(query, k=3)
        
        if not relevant_faqs:
            return {
                'response': "I couldn't find specific information about that. Could you try rephrasing your question or ask about payments, KYC, rewards, cards, or account limits?",
                'confidence': 0.0,
                'source_faqs': [],
                'suggestions': self._get_popular_questions()
            }
            
        response = self.generate_response_with_llm(query, relevant_faqs)
        confidence = relevant_faqs[0][1] if relevant_faqs else 0.0
        
        self.conversation_history.append({
            'query': query,
            'response': response,
            'confidence': confidence,
            'timestamp': self._get_timestamp()
        })
        
        return {
            'response': response,
            'confidence': confidence,
            'source_faqs': [faq for faq, _ in relevant_faqs],
            'suggestions': self._get_related_questions(relevant_faqs)
        }
        
    def _get_popular_questions(self) -> List[str]:
        popular = [
            "How do I make a payment?",
            "What documents are needed for KYC?",
            "How do Jupiter rewards work?",
            "What are the transaction limits?",
            "How do I activate my debit card?"
        ]
        return popular[:3]
        
    def _get_related_questions(self, relevant_faqs: List[Tuple[Dict, float]]) -> List[str]:
        suggestions = []
        
        for faq, _ in relevant_faqs:
            if 'alternative_questions' in faq:
                suggestions.extend(faq['alternative_questions'][:2])
                
        categories = list(set(faq['category'] for faq, _ in relevant_faqs))
        for category in categories[:2]:
            category_faqs = self.embeddings.get_category_faqs(category)
            for cat_faq in category_faqs[:2]:
                if cat_faq['question'] not in [faq['question'] for faq, _ in relevant_faqs]:
                    suggestions.append(cat_faq['question'])
                    
        return suggestions[:3]
        
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
        
    def get_categories(self) -> List[str]:
        if not self.embeddings.faqs:
            return []
        return list(set(faq.get('category', 'General') for faq in self.embeddings.faqs))
        
    def search_by_category(self, category: str, limit: int = 5) -> List[Dict]:
        return self.embeddings.get_category_faqs(category)[:limit]
        
    def get_conversation_history(self) -> List[Dict]:
        return self.conversation_history
        
    def clear_history(self):
        self.conversation_history = []
        logger.info("Conversation history cleared")

if __name__ == "__main__":
    bot = JupiterFAQBot()
    
    if bot.initialize():
        while True:
            query = input("\nAsk me about Jupiter banking services (or 'quit' to exit): ")
            if query.lower() in ['quit', 'exit', 'bye']:
                break
                
            result = bot.get_response(query)
            print(f"\nBot: {result['response']}")
            print(f"Confidence: {result['confidence']:.2f}")
            
            if result['suggestions']:
                print(f"\nRelated questions you might ask:")
                for suggestion in result['suggestions']:
                    print(f"- {suggestion}")
    else:
        print("Failed to initialize the bot")
