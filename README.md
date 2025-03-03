# AI Expense Tracker

An intelligent expense tracking application with receipt scanning, financial health analysis, and AI-powered insights.
![image](https://github.com/user-attachments/assets/80c46f5a-4dd5-487c-8cf3-9abf0957997d)


![image](https://github.com/user-attachments/assets/fcd6dc69-5587-440e-be8d-6847ec779a4f)


## Features

- **Expense Management**: Track and categorize your expenses
- **Receipt Scanning**: Automatically extract expense details from receipt photos
- **Financial Health Dashboard**: Get insights into your financial well-being
- **Budget Tracking**: Set budgets for different categories and monitor adherence
- **Financial Goals**: Set and track progress towards savings goals
- **Payment Reminders**: Never miss a bill payment
- **AI-Powered Insights**: Get personalized recommendations to improve your finances
- **Statement Upload**: Import expenses from bank statements
- **Spending Analysis**: Visualize your spending patterns

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **AI/ML**: OpenAI GPT for financial advice, Tesseract OCR for receipt scanning

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/expense-tracker.git
   cd expense-tracker
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python init_db.py
   ```

5. Run the application:
   ```
   python run.py
   ```

6. Access the application at http://localhost:5000

## Optional Dependencies

### Receipt Scanning

To enable receipt scanning functionality:

1. Install additional Python packages:
   ```
   pip install pytesseract pillow opencv-python
   ```

2. Install Tesseract OCR:
   - Windows: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`

3. Update the Tesseract path in `config.py` if necessary.

## Configuration

Edit `config.py` to customize:

- Database connection
- OpenAI API key (for AI recommendations)
- File upload settings
- Session lifetime
- Tesseract OCR path

## Usage

1. Register a new account
2. Add expense categories with budgets
3. Start tracking expenses
4. Set up financial goals
5. Check your financial health dashboard for insights

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
