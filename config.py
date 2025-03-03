import os
from datetime import timedelta

class Config:
    # Add a strong secret key - this should be a random string in production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///expense_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # OpenAI configuration
    OPENAI_API_KEY = "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"  # Replace with your actual API key
    OPENAI_MODEL = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS = 800  # Increased for more detailed responses
    OPENAI_TEMPERATURE = 0.7
    
    # Security settings
    WTF_CSRF_ENABLED = False  # Disable CSRF protection globally
    
    # CSRF secret key
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf-key-change-this')
    
    # Optional dependencies
    # To enable receipt scanning, install: pip install pytesseract pillow opencv-python
    # You'll also need to install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki 
    
    # Tesseract OCR configuration
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path for your system 