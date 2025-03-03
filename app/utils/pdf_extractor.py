import pdfplumber
import re
from datetime import datetime

def clean_amount(amount_str):
    """Clean and convert amount string to float."""
    # Remove $ and , from amount
    amount_str = amount_str.replace('$', '').replace(',', '')
    # Handle negative amounts (both -$X.XX and $-X.XX formats)
    if amount_str.startswith('-'):
        return -float(amount_str[1:])
    elif '-' in amount_str:
        return -float(amount_str.replace('-', ''))
    return float(amount_str)

def extract_transactions_from_pdf(pdf_path):
    """
    Extract transactions from bank statement PDF.
    Returns a list of dictionaries containing transaction details.
    """
    transactions = []
    current_section = None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')
                
                for line in lines:
                    # Identify section headers
                    if 'Payments' in line:
                        current_section = 'payments'
                        continue
                    elif 'Transactions' in line:
                        current_section = 'transactions'
                        continue
                    
                    # Skip header lines and empty lines
                    if not line.strip() or 'Date' in line or 'Description' in line or 'Amount' in line:
                        continue

                    # Try to parse the line based on the current section
                    try:
                        # Match date pattern MM/DD/YYYY
                        date_match = re.search(r'\d{2}/\d{2}/\d{4}', line)
                        if not date_match:
                            continue
                            
                        date_str = date_match.group()
                        transaction_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                        
                        # Extract amount (looking for dollar amounts)
                        amount_matches = re.findall(r'-?\$?\d+,?\d*\.\d{2}', line)
                        if not amount_matches:
                            continue
                            
                        # Get the last amount in the line (transaction amount)
                        amount_str = amount_matches[-1]
                        amount = clean_amount(amount_str)
                        
                        # Extract description
                        # Remove date, amounts, and any "Daily Cash" related text
                        description = line.replace(date_str, '')
                        for amt in amount_matches:
                            description = description.replace(amt, '')
                        description = re.sub(r'\d+%', '', description)  # Remove percentage
                        description = re.sub(r'\s+', ' ', description).strip()
                        
                        # Skip Daily Cash redemption entries
                        if 'Daily Cash redemption' in description:
                            continue
                            
                        # Clean up description
                        description = re.sub(r'\s+', ' ', description)
                        description = description.strip()
                        
                        # Skip if no meaningful description
                        if not description:
                            continue
                            
                        # Add transaction type based on section
                        transaction_type = 'payment' if current_section == 'payments' else 'purchase'
                        
                        transactions.append({
                            'date': transaction_date,
                            'description': description,
                            'amount': abs(amount),  # Store positive amount
                            'type': transaction_type
                        })
                        
                    except Exception as e:
                        print(f"Error processing line: {line}")
                        print(f"Error details: {str(e)}")
                        continue
    
    except Exception as e:
        print(f"Error extracting transactions: {e}")
        return []
    
    return transactions 