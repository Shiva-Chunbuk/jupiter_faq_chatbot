#!/usr/bin/env python3

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scraper import JupiterFAQScraper
from src.preprocessor import FAQPreprocessor
from src.embeddings import FAQEmbeddings
from src.bot import JupiterFAQBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_complete_pipeline():
    logger.info("Starting Jupiter FAQ Bot Pipeline")
    
    try:
        logger.info("Step 1: Scraping FAQs...")
        scraper = JupiterFAQScraper()
        faqs = scraper.scrape_faqs()
        scraper.save_faqs()
        logger.info(f"Scraped {len(faqs)} FAQs")
        
        logger.info("Step 2: Processing FAQs...")
        preprocessor = FAQPreprocessor()
        raw_faqs = preprocessor.load_raw_faqs()
        processed_faqs = preprocessor.process_faqs(raw_faqs)
        preprocessor.save_processed_faqs()
        logger.info(f"Processed {len(processed_faqs)} FAQs")
        
        logger.info("Step 3: Creating embeddings...")
        embeddings = FAQEmbeddings()
        embeddings.load_faqs()
        embeddings.create_embeddings()
        embeddings.build_faiss_index()
        embeddings.save_embeddings()
        logger.info("Embeddings created and saved")
        
        logger.info("Step 4: Testing bot...")
        bot = JupiterFAQBot()
        if bot.initialize():
            test_queries = [
                "How do I make a payment?",
                "What documents are needed for KYC?",
                "How do Jupiter rewards work?"
            ]
            
            for query in test_queries:
                result = bot.get_response(query)
                logger.info(f"Query: {query}")
                logger.info(f"Confidence: {result['confidence']:.2f}")
                logger.info(f"Response: {result['response'][:100]}...")
                logger.info("-" * 50)
        
        logger.info("Pipeline completed successfully!")
        logger.info("You can now run: streamlit run demo/streamlit_app.py")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    success = run_complete_pipeline()
    if success:
        print("\n✅ Pipeline completed successfully!")
        print("Next steps:")
        print("1. Run the demo: streamlit run demo/streamlit_app.py")
        print("2. Evaluate performance: jupyter notebook notebooks/evaluation.ipynb")
    else:
        print("\n❌ Pipeline failed. Check the logs for details.")
