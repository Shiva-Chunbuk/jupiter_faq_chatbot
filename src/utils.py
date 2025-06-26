import json
import logging
import os
from typing import Dict, List, Any
import time
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_file: str = None):
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if log_file:
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format
        )

def load_json(filename: str) -> Dict:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File {filename} not found")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in {filename}")
        return {}

def save_json(data: Any, filename: str):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_directories(paths: List[str]):
    for path in paths:
        os.makedirs(path, exist_ok=True)
        logging.info(f"Created directory: {path}")

def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def measure_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

def validate_environment():
    required_dirs = ['data', 'logs']
    create_directories(required_dirs)
    
    if not os.getenv('OPENAI_API_KEY'):
        logging.warning("OPENAI_API_KEY not found in environment variables")
        return False
    return True

def format_faq_for_display(faq: Dict) -> str:
    return f"""
    Question: {faq.get('question', 'N/A')}
    Answer: {faq.get('answer', 'N/A')}
    Category: {faq.get('category', 'General')}
    """

def calculate_similarity_score(text1: str, text2: str) -> float:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return float(similarity[0][0])

def clean_filename(filename: str) -> str:
    import re
    return re.sub(r'[^\w\-_\.]', '_', filename)

def get_file_size(filename: str) -> str:
    try:
        size = os.path.getsize(filename)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except OSError:
        return "Unknown"

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        
    def start_timer(self, operation: str):
        self.metrics[operation] = {'start': time.time()}
        
    def end_timer(self, operation: str):
        if operation in self.metrics:
            self.metrics[operation]['end'] = time.time()
            self.metrics[operation]['duration'] = (
                self.metrics[operation]['end'] - self.metrics[operation]['start']
            )
            
    def get_metrics(self) -> Dict:
        return self.metrics
        
    def log_metrics(self):
        for operation, data in self.metrics.items():
            if 'duration' in data:
                logging.info(f"{operation}: {data['duration']:.2f} seconds")
