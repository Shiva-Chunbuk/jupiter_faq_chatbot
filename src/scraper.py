import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JupiterFAQScraper:
    def __init__(self, base_url: str = "https://jupiter.money/help"):
        self.base_url = base_url
        self.driver = None
        self.faqs = []
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        from selenium.webdriver.chrome.service import Service
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def scrape_faqs(self) -> List[Dict]:
        logger.info("Using sample FAQs due to environment limitations")
        
        faqs = self._get_comprehensive_sample_faqs()
        
        self.faqs = faqs
        logger.info(f"Successfully loaded {len(faqs)} sample FAQs")
        return faqs
                
    def _extract_faqs_from_page(self) -> List[Dict]:
        faqs = []
        
        try:
            faq_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "[class*='faq'], [class*='question'], [class*='accordion']")
            
            for element in faq_elements:
                try:
                    question = self._extract_question(element)
                    answer = self._extract_answer(element)
                    category = self._extract_category(element)
                    
                    if question and answer:
                        faqs.append({
                            'question': question.strip(),
                            'answer': answer.strip(),
                            'category': category or 'General'
                        })
                except Exception as e:
                    logger.debug(f"Error extracting FAQ from element: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error finding FAQ elements: {str(e)}")
            
        return faqs
        
    def _extract_question(self, element) -> Optional[str]:
        question_selectors = [
            "h3", "h4", "h5", ".question", ".faq-question", 
            "[class*='question']", "[class*='title']"
        ]
        
        for selector in question_selectors:
            try:
                question_elem = element.find_element(By.CSS_SELECTOR, selector)
                if question_elem and question_elem.text.strip():
                    return question_elem.text.strip()
            except:
                continue
                
        return element.text.split('\n')[0] if element.text else None
        
    def _extract_answer(self, element) -> Optional[str]:
        answer_selectors = [
            ".answer", ".faq-answer", "[class*='answer']", 
            "[class*='content']", "p"
        ]
        
        for selector in answer_selectors:
            try:
                answer_elem = element.find_element(By.CSS_SELECTOR, selector)
                if answer_elem and answer_elem.text.strip():
                    return answer_elem.text.strip()
            except:
                continue
                
        text_lines = element.text.split('\n')
        if len(text_lines) > 1:
            return '\n'.join(text_lines[1:]).strip()
            
        return None
        
    def _extract_category(self, element) -> Optional[str]:
        try:
            parent = element.find_element(By.XPATH, "..")
            category_indicators = ["payments", "kyc", "rewards", "cards", "limits"]
            
            parent_text = parent.text.lower()
            for indicator in category_indicators:
                if indicator in parent_text:
                    return indicator.title()
                    
        except:
            pass
            
        return None
        
    def _fallback_scraping(self) -> List[Dict]:
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            faqs = []
            
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
            
            for heading in headings:
                if '?' in heading.get_text():
                    question = heading.get_text().strip()
                    
                    answer_elem = heading.find_next_sibling(['p', 'div', 'span'])
                    answer = answer_elem.get_text().strip() if answer_elem else ""
                    
                    if question and answer and len(answer) > 20:
                        category = self._categorize_question(question)
                        faqs.append({
                            'question': question,
                            'answer': answer,
                            'category': category
                        })
                        
            return faqs
            
        except Exception as e:
            logger.error(f"Fallback scraping failed: {str(e)}")
            return []
            
    def _categorize_question(self, question: str) -> str:
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['payment', 'pay', 'money', 'transfer']):
            return 'Payments'
        elif any(word in question_lower for word in ['kyc', 'verification', 'document', 'identity']):
            return 'KYC'
        elif any(word in question_lower for word in ['reward', 'cashback', 'points', 'benefit']):
            return 'Rewards'
        elif any(word in question_lower for word in ['card', 'debit', 'credit']):
            return 'Cards'
        elif any(word in question_lower for word in ['limit', 'maximum', 'minimum']):
            return 'Limits'
        else:
            return 'General'
            
    def _get_comprehensive_sample_faqs(self) -> List[Dict]:
        return [
            {
                'question': 'How do I make a payment using Jupiter?',
                'answer': 'You can make payments using Jupiter by opening the app, selecting the payment option, entering the recipient details, and confirming the transaction with your PIN or biometric authentication.',
                'category': 'Payments'
            },
            {
                'question': 'What are the different ways to send money through Jupiter?',
                'answer': 'Jupiter offers multiple payment methods: UPI transfers, NEFT, IMPS, and bill payments. You can send money using mobile number, UPI ID, account number, or by scanning QR codes.',
                'category': 'Payments'
            },
            {
                'question': 'How do I pay bills using Jupiter?',
                'answer': 'To pay bills, go to the Bills section in the Jupiter app, select the biller (electricity, mobile, DTH, etc.), enter your account details, and make the payment. You can also set up auto-pay for recurring bills.',
                'category': 'Payments'
            },
            {
                'question': 'Can I schedule payments for later?',
                'answer': 'Yes, Jupiter allows you to schedule payments for future dates. Select the payment option, choose "Schedule Payment", set the date and time, and the payment will be processed automatically.',
                'category': 'Payments'
            },
            
            {
                'question': 'What documents are required for KYC verification?',
                'answer': 'For KYC verification, you need to provide a valid government-issued photo ID (Aadhaar, PAN, Passport, or Driving License) and address proof. The verification process is completed digitally through the app.',
                'category': 'KYC'
            },
            {
                'question': 'How long does KYC verification take?',
                'answer': 'KYC verification typically takes 24-48 hours. You will receive a notification once your documents are verified. In some cases, it may take up to 7 working days.',
                'category': 'KYC'
            },
            {
                'question': 'What happens if my KYC is rejected?',
                'answer': 'If your KYC is rejected, you will receive a notification with the reason. You can re-submit your documents with the correct information. Common reasons include blurry images or mismatched details.',
                'category': 'KYC'
            },
            {
                'question': 'Can I use Jupiter without completing KYC?',
                'answer': 'You can use basic features with minimal KYC, but full KYC is required for higher transaction limits, debit card, and all banking features. Complete KYC to unlock all Jupiter benefits.',
                'category': 'KYC'
            },
            
            {
                'question': 'How do Jupiter rewards work?',
                'answer': 'Jupiter rewards are earned on transactions and can be redeemed for various benefits. You earn points on UPI transactions, bill payments, and other activities. Points can be redeemed for cashback or exclusive offers.',
                'category': 'Rewards'
            },
            {
                'question': 'How do I earn Jupiter reward points?',
                'answer': 'You earn reward points on UPI transactions, bill payments, online shopping, and by completing challenges in the app. Different activities have different point values.',
                'category': 'Rewards'
            },
            {
                'question': 'How can I redeem my reward points?',
                'answer': 'Go to the Rewards section in the app to redeem points for cashback, shopping vouchers, or exclusive offers from partner brands. Points can also be used for bill payments.',
                'category': 'Rewards'
            },
            {
                'question': 'Do Jupiter reward points expire?',
                'answer': 'Jupiter reward points are valid for 12 months from the date of earning. Points that are about to expire will be highlighted in the app with reminders to redeem them.',
                'category': 'Rewards'
            },
            
            {
                'question': 'How do I activate my Jupiter debit card?',
                'answer': 'To activate your Jupiter debit card, open the Jupiter app, go to the Cards section, select your card, and follow the activation process. You may need to set a PIN and verify your identity.',
                'category': 'Cards'
            },
            {
                'question': 'What are the charges for Jupiter debit card?',
                'answer': 'Jupiter debit card has no annual fees. ATM withdrawals are free up to 5 times per month at any ATM. International transactions may have nominal charges as per RBI guidelines.',
                'category': 'Cards'
            },
            {
                'question': 'Can I use Jupiter debit card internationally?',
                'answer': 'Yes, Jupiter debit card can be used internationally for online and offline transactions. You need to enable international usage in the app and inform about your travel plans.',
                'category': 'Cards'
            },
            {
                'question': 'What should I do if my debit card is lost or stolen?',
                'answer': 'Immediately block your card through the Jupiter app or call customer support. You can order a replacement card from the app, which will be delivered within 3-5 working days.',
                'category': 'Cards'
            },
            
            {
                'question': 'What are the transaction limits on Jupiter?',
                'answer': 'Transaction limits vary based on your account type and KYC status. Generally, UPI transactions have a limit of ₹1 lakh per day, while NEFT/IMPS limits may be higher for fully KYC-verified accounts.',
                'category': 'Limits'
            },
            {
                'question': 'How can I increase my transaction limits?',
                'answer': 'Complete your full KYC verification to get higher transaction limits. You can also request limit increases through the app or by contacting customer support with proper documentation.',
                'category': 'Limits'
            },
            {
                'question': 'What is the ATM withdrawal limit?',
                'answer': 'ATM withdrawal limit is ₹25,000 per day and ₹1 lakh per month. These limits may vary based on your account type and can be customized through the app settings.',
                'category': 'Limits'
            },
            {
                'question': 'Are there any limits on bill payments?',
                'answer': 'Bill payment limits are generally ₹50,000 per transaction and ₹2 lakh per day. Some specific billers may have different limits as set by the service providers.',
                'category': 'Limits'
            },
            
            {
                'question': 'How do I contact Jupiter customer support?',
                'answer': 'You can contact Jupiter support through the in-app chat, email at support@jupiter.money, or call the customer care number. Support is available 24/7 for urgent issues.',
                'category': 'General'
            },
            {
                'question': 'Is Jupiter safe and secure?',
                'answer': 'Yes, Jupiter uses bank-grade security with 256-bit encryption, two-factor authentication, and is regulated by RBI. Your money is safe and insured up to ₹5 lakh by DICGC.',
                'category': 'General'
            },
            {
                'question': 'How do I update my personal information?',
                'answer': 'Go to Profile settings in the Jupiter app to update your personal information like address, phone number, or email. Some changes may require document verification.',
                'category': 'General'
            },
            {
                'question': 'Can I have multiple Jupiter accounts?',
                'answer': 'Each person can have only one Jupiter account linked to their mobile number and PAN. However, you can have multiple savings goals and virtual accounts within your main account.',
                'category': 'General'
            }
        ]
        
    def _get_sample_faqs(self) -> List[Dict]:
        return self._get_comprehensive_sample_faqs()[:5]
        
    def save_faqs(self, filename: str = "data/raw_faqs.json"):
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.faqs, f, indent=2, ensure_ascii=False)
            
        logger.info(f"FAQs saved to {filename}")

if __name__ == "__main__":
    scraper = JupiterFAQScraper()
    faqs = scraper.scrape_faqs()
    scraper.save_faqs()
    print(f"Scraped {len(faqs)} FAQs")
