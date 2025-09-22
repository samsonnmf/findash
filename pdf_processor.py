import pypdf as PyPDF2
import pdfplumber
import openai
from anthropic import Anthropic
import json
import re
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class PDFProcessor:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        if self.anthropic_api_key:
            self.anthropic = Anthropic(api_key=self.anthropic_api_key)
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from uploaded PDF file using pdfplumber (better for tables)"""
        try:
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            # Fallback to PyPDF2
            try:
                text = ""
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except Exception as e2:
                return f"Error extracting text: {str(e2)}"
    
    def process_with_llm(self, text, llm_provider="openai"):
        """Process extracted text with LLM to structure financial data"""
        
        prompt = f"""
        You are a financial data extraction expert. Extract transaction data from this bank statement or financial document text.

        Return ONLY a valid JSON array with this exact structure:
        [
            {{
                "date": "YYYY-MM-DD",
                "amount": -150.50,
                "category": "groceries",
                "type": "expense",
                "description": "Walmart purchase"
            }},
            {{
                "date": "YYYY-MM-DD", 
                "amount": 3000.00,
                "type": "income",
                "category": "salary",
                "description": "Monthly salary"
            }}
        ]

        Rules:
        - Use negative amounts for expenses, positive for income
        - Categories: groceries, dining, gas, utilities, rent, salary, freelance, investment, entertainment, healthcare, shopping, other
        - Types: expense, income, transfer
        - Format dates as YYYY-MM-DD
        - Keep descriptions concise
        - Only extract clear financial transactions
        - If no transactions found, return []

        Text to process:
        {text[:4000]}  # Limit text to avoid token limits
        """
        
        try:
            if llm_provider == "openai" and self.openai_api_key:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a precise financial data extraction tool. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                return response.choices[0].message.content.strip()
            
            elif llm_provider == "anthropic" and self.anthropic_api_key:
                response = self.anthropic.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text.strip()
            
            else:
                return "Error: No valid API key configured"
                
        except Exception as e:
            return f"Error processing with LLM: {str(e)}"
    
    def parse_llm_response(self, llm_response):
        """Parse LLM response and validate JSON structure"""
        try:
            # Clean response - remove markdown formatting if present
            cleaned_response = llm_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:-3].strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:-3].strip()
            
            # Parse JSON
            transactions = json.loads(cleaned_response)
            
            # Validate structure
            validated_transactions = []
            for transaction in transactions:
                if all(key in transaction for key in ['date', 'amount', 'category', 'type']):
                    # Validate date format
                    try:
                        datetime.strptime(transaction['date'], '%Y-%m-%d')
                        validated_transactions.append({
                            'date': transaction['date'],
                            'amount': float(transaction['amount']),
                            'category': transaction.get('category', 'other'),
                            'type': transaction.get('type', 'expense'),
                            'description': transaction.get('description', '')
                        })
                    except (ValueError, TypeError):
                        continue  # Skip invalid dates or amounts
            
            return validated_transactions
            
        except json.JSONDecodeError as e:
            return f"Error parsing JSON response: {str(e)}"
        except Exception as e:
            return f"Error validating transactions: {str(e)}"
    
    def process_pdf_file(self, pdf_file, llm_provider="openai"):
        """Complete pipeline: PDF → Text → LLM → Structured Data"""
        
        # Step 1: Extract text from PDF
        extracted_text = self.extract_text_from_pdf(pdf_file)
        
        if extracted_text.startswith("Error"):
            return {"error": extracted_text}
        
        if len(extracted_text.strip()) < 50:
            return {"error": "PDF appears to be empty or text extraction failed"}
        
        # Step 2: Process with LLM
        llm_response = self.process_with_llm(extracted_text, llm_provider)
        
        if llm_response.startswith("Error"):
            return {"error": llm_response}
        
        # Step 3: Parse and validate
        transactions = self.parse_llm_response(llm_response)
        
        if isinstance(transactions, str) and transactions.startswith("Error"):
            return {"error": transactions}
        
        return {
            "success": True,
            "transactions": transactions,
            "extracted_text_preview": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            "transaction_count": len(transactions)
        }
    
    def get_sample_transaction_format(self):
        """Return sample format for manual entry"""
        return {
            "date": "2024-01-15",
            "amount": -45.67,
            "category": "groceries",
            "type": "expense", 
            "description": "Weekly grocery shopping"
        }
