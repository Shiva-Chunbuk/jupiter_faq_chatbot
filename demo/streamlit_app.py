import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bot import JupiterFAQBot
from src.utils import get_timestamp
import json

st.set_page_config(
    page_title="Jupiter FAQ Bot",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def initialize_bot():
    bot = JupiterFAQBot()
    if bot.initialize():
        return bot
    return None

def main():
    st.title("🏦 Jupiter FAQ Bot")
    st.markdown("Ask me anything about Jupiter banking services!")
    
    bot = initialize_bot()
    
    if bot is None:
        st.error("Failed to initialize the FAQ bot. Please check if the FAQ data is available.")
        return
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'bot_instance' not in st.session_state:
        st.session_state.bot_instance = bot
    
    with st.sidebar:
        st.header("📊 Bot Information")
        
        categories = bot.get_categories()
        st.subheader("Available Categories")
        for category in categories:
            st.write(f"• {category}")
        
        st.subheader("Quick Actions")
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            bot.clear_history()
            st.success("Conversation cleared!")
        
        if st.button("Show Popular Questions"):
            popular_questions = [
                "How do I make a payment?",
                "What documents are needed for KYC?",
                "How do Jupiter rewards work?",
                "What are the transaction limits?",
                "How do I activate my debit card?"
            ]
            st.subheader("Popular Questions")
            for q in popular_questions:
                if st.button(q, key=f"pop_{q}"):
                    st.session_state.current_query = q
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat with Jupiter Bot")
        
        query = st.text_input(
            "Ask your question:",
            placeholder="e.g., How do I transfer money using Jupiter?",
            key="query_input"
        )
        
        if hasattr(st.session_state, 'current_query'):
            query = st.session_state.current_query
            delattr(st.session_state, 'current_query')
        
        if st.button("Ask Question", type="primary") or query:
            if query.strip():
                with st.spinner("Thinking..."):
                    result = bot.get_response(query)
                
                st.session_state.conversation_history.append({
                    'query': query,
                    'result': result,
                    'timestamp': get_timestamp()
                })
                
                st.success("Response generated!")
        
        if st.session_state.conversation_history:
            st.subheader("💭 Conversation History")
            
            for i, conv in enumerate(reversed(st.session_state.conversation_history)):
                with st.expander(f"Q: {conv['query'][:50]}..." if len(conv['query']) > 50 else f"Q: {conv['query']}", expanded=(i==0)):
                    st.write(f"**You:** {conv['query']}")
                    st.write(f"**Jupiter Bot:** {conv['result']['response']}")
                    
                    confidence = conv['result']['confidence']
                    if confidence > 0.8:
                        confidence_color = "green"
                        confidence_text = "High"
                    elif confidence > 0.6:
                        confidence_color = "orange"
                        confidence_text = "Medium"
                    else:
                        confidence_color = "red"
                        confidence_text = "Low"
                    
                    st.markdown(f"**Confidence:** :{confidence_color}[{confidence_text} ({confidence:.2f})]")
                    
                    if conv['result']['suggestions']:
                        st.write("**Related Questions:**")
                        for suggestion in conv['result']['suggestions']:
                            if st.button(suggestion, key=f"suggest_{i}_{suggestion}"):
                                st.session_state.current_query = suggestion
                                st.rerun()
                    
                    st.write(f"*{conv['timestamp']}*")
    
    with col2:
        st.subheader("📋 FAQ Categories")
        
        selected_category = st.selectbox(
            "Browse by category:",
            ["All"] + categories
        )
        
        if selected_category != "All":
            category_faqs = bot.search_by_category(selected_category, limit=5)
            
            st.write(f"**{selected_category} FAQs:**")
            for faq in category_faqs:
                with st.expander(faq['question']):
                    st.write(faq['answer'])
                    if st.button(f"Ask about this", key=f"cat_{faq['question']}"):
                        st.session_state.current_query = faq['question']
                        st.rerun()
        
        st.subheader("🔍 Search Tips")
        st.info("""
        **For best results:**
        - Be specific in your questions
        - Use keywords like 'payment', 'KYC', 'rewards'
        - Ask one question at a time
        - Try rephrasing if you don't get the right answer
        """)
        
        st.subheader("📈 Session Stats")
        total_questions = len(st.session_state.conversation_history)
        st.metric("Questions Asked", total_questions)
        
        if total_questions > 0:
            avg_confidence = sum(conv['result']['confidence'] for conv in st.session_state.conversation_history) / total_questions
            st.metric("Average Confidence", f"{avg_confidence:.2f}")

if __name__ == "__main__":
    main()
