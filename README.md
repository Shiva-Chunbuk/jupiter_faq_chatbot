# Jupiter FAQ Bot

A conversational AI bot that answers questions about Jupiter banking services using web-scraped FAQs and large language models.

## Features

- **Web Scraping**: Automatically scrapes FAQs from Jupiter's help center
- **Smart Preprocessing**: Cleans, categorizes, and deduplicates FAQ content
- **Semantic Search**: Uses embeddings and FAISS for finding relevant answers
- **LLM Integration**: Leverages OpenAI GPT for natural, conversational responses
- **Interactive Demo**: Streamlit web interface for easy testing
- **Comprehensive Evaluation**: Jupyter notebook for performance analysis

## Project Structure

```
jupiter_faq_bot/
├── src/
│   ├── scraper.py          # Web scraping functionality
│   ├── preprocessor.py     # Data cleaning and processing
│   ├── embeddings.py       # Semantic search with FAISS
│   ├── bot.py             # Main bot logic with LLM integration
│   └── utils.py           # Helper functions
├── data/
│   ├── raw_faqs.json      # Scraped FAQ data
│   ├── processed_faqs.json # Cleaned and categorized data
│   ├── embeddings.pkl     # Precomputed embeddings
│   └── faiss_index.bin    # FAISS search index
├── demo/
│   └── streamlit_app.py   # Interactive web demo
├── notebooks/
│   └── evaluation.ipynb   # Performance evaluation
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

1. Clone or download the project:
```bash
cd jupiter_faq_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### 1. Scrape FAQs
```bash
python -m src.scraper
```

### 2. Process and Clean Data
```bash
python -m src.preprocessor
```

### 3. Create Embeddings
```bash
python -m src.embeddings
```

### 4. Test the Bot
```bash
python -m src.bot
```

### 5. Run Interactive Demo
```bash
streamlit run demo/streamlit_app.py
```

### 6. Evaluate Performance
```bash
jupyter notebook notebooks/evaluation.ipynb
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key for LLM responses
- `JUPITER_HELP_URL`: Jupiter help center URL (default: https://jupiter.money/help)

### Bot Settings
- `confidence_threshold`: Minimum confidence for showing results (default: 0.6)
- `model_name`: Sentence transformer model for embeddings (default: "all-MiniLM-L6-v2")

## Features in Detail

### Web Scraping
- Headless Chrome scraping with Selenium
- Fallback to BeautifulSoup for static content
- Automatic categorization of FAQs
- Sample data generation if scraping fails

### Data Processing
- HTML tag removal and text cleaning
- Duplicate question detection using TF-IDF similarity
- Smart categorization (Payments, KYC, Rewards, Cards, Limits, etc.)
- Alternative question mapping

### Semantic Search
- Sentence transformer embeddings for semantic understanding
- FAISS index for fast similarity search
- Category-based filtering
- Configurable similarity thresholds

### LLM Integration
- OpenAI GPT-3.5-turbo for natural responses
- Context-aware answer generation
- Confidence-based response strategies
- Graceful fallback when API unavailable

### Interactive Demo
- Clean Streamlit interface
- Real-time chat functionality
- Category browsing
- Conversation history
- Related question suggestions

## Evaluation Metrics

The evaluation notebook provides comprehensive analysis:

- **Confidence Score Distribution**: How confident the bot is in its answers
- **Semantic Similarity**: Consistency across paraphrased questions
- **Category Performance**: Accuracy by FAQ category
- **Response Quality**: Length, clarity, and appropriateness
- **Edge Case Handling**: Behavior with irrelevant or malformed queries

## Sample Queries

Try these questions with the bot:

- "How do I make a payment using Jupiter?"
- "What documents are required for KYC verification?"
- "How do Jupiter rewards work?"
- "What are the transaction limits?"
- "How do I activate my debit card?"
- "Can I use Jupiter internationally?"
- "How to check my account balance?"

## Limitations

- Depends on Jupiter's website structure for scraping
- Requires OpenAI API key for best performance
- Limited to FAQ content available on the website
- May need periodic updates as Jupiter's services evolve

## Future Enhancements

- **Multilingual Support**: Hindi and Hinglish language support
- **Query Suggestions**: Behavioral analysis for better recommendations
- **Retrieval vs LLM Comparison**: Performance analysis of different approaches
- **Real-time Updates**: Automatic FAQ refresh and reindexing
- **Advanced Analytics**: User interaction patterns and improvement insights

## Troubleshooting

### Common Issues

1. **Scraping Fails**: Check internet connection and Jupiter website availability
2. **OpenAI API Errors**: Verify API key and account credits
3. **Import Errors**: Ensure all dependencies are installed
4. **Empty Results**: Check if FAQ data exists in the data/ directory

### Debug Mode
Enable detailed logging by setting the log level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is for educational purposes as part of an AI internship assignment.
