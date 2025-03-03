# Modified receipt scanner with lazy imports
import os
from datetime import datetime
from flask import current_app
import re

# Define flags but don't import modules yet
TESSERACT_AVAILABLE = None
CV2_AVAILABLE = None

def _check_dependencies():
    """Check if required dependencies are available (lazy loading)"""
    global TESSERACT_AVAILABLE, CV2_AVAILABLE
    
    # Only check once
    if TESSERACT_AVAILABLE is None:
        try:
            import pytesseract
            from PIL import Image
            
            # Set tesseract path from config if available
            if hasattr(current_app.config, 'TESSERACT_CMD'):
                pytesseract.pytesseract.tesseract_cmd = current_app.config['TESSERACT_CMD']
                
            TESSERACT_AVAILABLE = True
        except ImportError:
            TESSERACT_AVAILABLE = False
    
    if CV2_AVAILABLE is None:
        try:
            import cv2
            import numpy as np
            CV2_AVAILABLE = True
        except ImportError:
            CV2_AVAILABLE = False
    
    return TESSERACT_AVAILABLE, CV2_AVAILABLE

def preprocess_image(image_path):
    """Preprocess the image to improve OCR accuracy."""
    _check_dependencies()
    
    if not CV2_AVAILABLE:
        return image_path
        
    try:
        # Import here to avoid module-level import errors
        import cv2
        import numpy as np
        
        # Read the image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Save preprocessed image
        preprocessed_path = image_path.replace('.', '_processed.')
        cv2.imwrite(preprocessed_path, opening)
        
        return preprocessed_path
    except Exception as e:
        current_app.logger.error(f"Error preprocessing image: {str(e)}")
        return image_path

def extract_text_from_receipt(image_path):
    """Extract text from receipt image using OCR."""
    _check_dependencies()
    
    if not TESSERACT_AVAILABLE:
        return "OCR functionality not available. Please install pytesseract and Pillow."
        
    try:
        # Import here to avoid module-level import errors
        import pytesseract
        from PIL import Image
        
        # Preprocess the image
        processed_image_path = preprocess_image(image_path)
        
        # Open the processed image
        image = Image.open(processed_image_path)
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(image)
        
        # Clean up temporary file
        if os.path.exists(processed_image_path) and processed_image_path != image_path:
            os.remove(processed_image_path)
            
        return text
    except Exception as e:
        current_app.logger.error(f"Error extracting text from receipt: {str(e)}")
        return None

def parse_receipt_data(text):
    """Parse receipt text to extract expense information."""
    if not text:
        return None
    
    # Initialize data dictionary
    receipt_data = {
        'total_amount': None,
        'date': None,
        'merchant': None,
        'items': []
    }
    
    # Extract total amount
    total_patterns = [
        r'TOTAL\s*[\$]?\s*(\d+\.\d{2})',
        r'Total\s*[\$]?\s*(\d+\.\d{2})',
        r'AMOUNT\s*[\$]?\s*(\d+\.\d{2})',
        r'Amount\s*[\$]?\s*(\d+\.\d{2})',
        r'GRAND TOTAL\s*[\$]?\s*(\d+\.\d{2})',
        r'Grand Total\s*[\$]?\s*(\d+\.\d{2})',
        r'[\$]?\s*(\d+\.\d{2})\s*$'
    ]
    
    for pattern in total_patterns:
        match = re.search(pattern, text)
        if match:
            receipt_data['total_amount'] = float(match.group(1))
            break
    
    # Extract date
    date_patterns = [
        r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})',
        r'(\d{2,4}[/.-]\d{1,2}[/.-]\d{1,2})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{2,4}'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1)
            try:
                # Try different date formats
                for fmt in ['%m/%d/%Y', '%m/%d/%y', '%Y/%m/%d', '%d/%m/%Y', '%m-%d-%Y', '%Y-%m-%d']:
                    try:
                        receipt_data['date'] = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            except:
                pass
            break
    
    # Extract merchant name (usually at the top of receipt)
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    
    if non_empty_lines:
        # First line is often the merchant name
        receipt_data['merchant'] = non_empty_lines[0].strip()
    
    return receipt_data

def suggest_category(merchant, description, categories):
    """Suggest a category based on merchant name and description."""
    merchant = merchant.lower() if merchant else ""
    description = description.lower() if description else ""
    
    # Define keyword mappings
    category_keywords = {
        'grocery': ['grocery', 'supermarket', 'food', 'market', 'walmart', 'target', 'kroger', 'safeway'],
        'dining': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonald', 'burger', 'pizza', 'taco'],
        'transportation': ['gas', 'uber', 'lyft', 'taxi', 'transit', 'train', 'bus', 'metro', 'fuel'],
        'shopping': ['amazon', 'store', 'mall', 'shop', 'retail', 'clothing', 'electronics'],
        'utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'bill', 'utility'],
        'entertainment': ['movie', 'theater', 'netflix', 'spotify', 'hulu', 'disney', 'game'],
        'health': ['doctor', 'pharmacy', 'medical', 'health', 'fitness', 'gym', 'hospital']
    }
    
    # Check for category matches
    for category_name, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in merchant or keyword in description:
                # Find matching category in user's categories
                for category in categories:
                    if category_name.lower() in category.name.lower():
                        return category.id
    
    # Default to first category or None
    return categories[0].id if categories else None

def scan_receipt(image_path, categories):
    """Process receipt image and extract expense data."""
    _check_dependencies()
    
    if not TESSERACT_AVAILABLE:
        return {
            'success': False,
            'message': 'Receipt scanning requires pytesseract and Pillow. Please install these packages or enter expenses manually.'
        }
    
    text = extract_text_from_receipt(image_path)
    if not text:
        return {
            'success': False,
            'message': 'Failed to extract text from receipt'
        }
    
    receipt_data = parse_receipt_data(text)
    if not receipt_data or not receipt_data['total_amount']:
        return {
            'success': False,
            'message': 'Could not identify expense amount from receipt'
        }
    
    # Create expense data
    expense_data = {
        'amount': receipt_data['total_amount'],
        'description': receipt_data['merchant'] or 'Receipt Scan',
        'date': receipt_data['date'] or datetime.now(),
        'category_id': suggest_category(receipt_data['merchant'], '', categories),
        'source': 'receipt_scan',
        'success': True
    }
    
    return expense_data 