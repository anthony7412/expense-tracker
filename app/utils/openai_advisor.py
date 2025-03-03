from openai import OpenAI
from datetime import datetime, timedelta
from flask import current_app
from collections import defaultdict
import traceback
import json
import re

def get_openai_advice(expenses, categories, user_question=''):
    """Get personalized financial advice from OpenAI."""
    try:
        # Check if the message is a simple greeting
        if is_greeting(user_question):
            return [{
                'type': 'info',
                'message': get_greeting_response()
            }]
            
        api_key = current_app.config.get('OPENAI_API_KEY')
        print("Attempting to get OpenAI advice with API key:", api_key[:5] + "..." if api_key and len(api_key) > 5 else "Not set")
        
        if not api_key:
            print("No API key configured")
            return [{
                'type': 'danger',
                'message': 'OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.'
            }]
        
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Prepare expense data with enhanced analysis
        expense_summary = prepare_expense_summary(expenses, categories)
        if not expense_summary['valid']:
            return expense_summary['messages']
        
        # Build the prompt with more personalized context
        prompt = build_ai_prompt(expense_summary, user_question)
        print(f"Sending prompt to OpenAI (length: {len(prompt)})")

        try:
            response = client.chat.completions.create(
                model=current_app.config.get('OPENAI_MODEL', "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": """You are a knowledgeable financial advisor specializing in personal finance. 
                    Analyze the user's specific spending patterns and provide personalized, actionable advice.
                    
                    When giving recommendations:
                    - Reference specific categories where they spend money
                    - Mention actual amounts and percentages from their data
                    - Compare their spending to typical benchmarks
                    - Suggest specific actions based on their unique spending habits
                    - Provide category-specific optimization strategies
                    - Identify potential savings opportunities in their highest spending areas
                    
                    Be concise, practical, and data-driven in your recommendations.
                    Always tie your advice directly to their actual transaction history."""},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=current_app.config.get('OPENAI_MAX_TOKENS', 800),
                temperature=current_app.config.get('OPENAI_TEMPERATURE', 0.7)
            )
            
            if not response.choices:
                print("No choices in response")
                return [{
                    'type': 'danger',
                    'message': 'No response from AI. Please try again.'
                }]
                
            print("Successfully received response from OpenAI")
            return format_ai_response(response.choices[0].message.content)
            
        except Exception as api_error:
            print(f"OpenAI API error: {str(api_error)}")
            return handle_api_error(api_error)
            
    except Exception as e:
        print(f"General error in get_openai_advice: {str(e)}")
        print(traceback.format_exc())
        return [{
            'type': 'danger',
            'message': 'An unexpected error occurred. Please try again later.'
        }]

def is_greeting(text):
    """Check if the user message is a simple greeting."""
    if not text:
        return False
        
    text = text.lower().strip()
    greeting_patterns = [
        r'^hi$', r'^hello$', r'^hey$', r'^hi there$', r'^hello there$',
        r'^greetings$', r'^howdy$', r'^sup$', r'^what\'s up$', r'^hiya$',
        r'^good morning$', r'^good afternoon$', r'^good evening$',
        r'^how are you$', r'^how are you\?$', r'^how\'s it going$',
        r'^how\'s it going\?$', r'^how are things$', r'^how are things\?$'
    ]
    
    return any(re.match(pattern, text) for pattern in greeting_patterns)

def get_greeting_response():
    """Return a friendly greeting response."""
    import random
    
    greetings = [
        "Hello! How can I help you with your finances today?",
        "Hi there! I'm your financial assistant. What would you like to know about your expenses?",
        "Greetings! I'm here to help with your financial questions. What can I assist you with?",
        "Hello! I'm ready to provide financial insights. What would you like to know?",
        "Hi! I can help analyze your spending or provide financial advice. What are you interested in?"
    ]
    
    return random.choice(greetings)

def prepare_expense_summary(expenses, categories):
    """Prepare a summary of expense data for AI analysis."""
    if not expenses:
        return {
            'valid': False,
            'messages': [{
                'type': 'warning',
                'message': 'No expense data found. Please add some expenses to get personalized advice.'
            }]
        }
    
    # Get current date for reference
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Calculate total spending
    total_spending = sum(expense.amount for expense in expenses)
    
    # Group expenses by category
    category_spending = defaultdict(float)
    category_count = defaultdict(int)
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Uncategorized"
        category_spending[category_name] += expense.amount
        category_count[category_name] += 1
    
    # Calculate monthly trends (last 6 months)
    monthly_trends = {}
    for i in range(6):
        month_date = now - timedelta(days=30 * i)
        month_name = month_date.strftime("%B %Y")
        month_spending = sum(expense.amount for expense in expenses 
                           if expense.date.month == month_date.month 
                           and expense.date.year == month_date.year)
        if month_spending > 0:
            monthly_trends[month_name] = month_spending
    
    # Identify top spending categories
    top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
    
    # Calculate budget status for each category
    budget_status = {}
    for category in categories:
        if category.budget > 0:
            current_month_spending = sum(e.amount for e in expenses 
                                      if e.category_id == category.id 
                                      and e.date.month == current_month
                                      and e.date.year == current_year)
            budget_status[category.name] = {
                'budget': category.budget,
                'spent': current_month_spending,
                'remaining': category.budget - current_month_spending,
                'percentage': (current_month_spending / category.budget) * 100
            }
    
    # Identify recurring expenses
    recurring_expenses = []
    expense_dict = defaultdict(list)
    for expense in expenses:
        key = f"{expense.description.lower()}-{expense.amount}"
        expense_dict[key].append(expense)
    
    for key, exp_list in expense_dict.items():
        if len(exp_list) >= 2:
            recurring_expenses.append({
                'description': exp_list[0].description,
                'amount': exp_list[0].amount,
                'frequency': len(exp_list),
                'category': exp_list[0].category.name if exp_list[0].category else "Uncategorized"
            })
    
    # Identify unusual expenses (significantly higher than average for that category)
    unusual_expenses = []
    for expense in expenses:
        if expense.category:
            category_avg = category_spending[expense.category.name] / category_count[expense.category.name]
            if expense.amount > category_avg * 2 and expense.amount > 50:
                unusual_expenses.append({
                    'description': expense.description,
                    'amount': expense.amount,
                    'category': expense.category.name,
                    'date': expense.date.strftime("%Y-%m-%d")
                })
    
    return {
        'valid': True,
        'total_spending': total_spending,
        'category_spending': dict(category_spending),
        'monthly_trends': monthly_trends,
        'top_categories': top_categories[:5],
        'budget_status': budget_status,
        'recurring_expenses': recurring_expenses,
        'unusual_expenses': unusual_expenses,
        'expense_count': len(expenses),
        'category_count': len(category_spending)
    }

def build_ai_prompt(data, user_question):
    """Build a detailed prompt for the AI with personalized expense data."""
    prompt = "Please analyze the following expense data and provide personalized financial advice:\n\n"
    
    # Add total spending information
    prompt += f"Total Spending: ${data['total_spending']:.2f}\n"
    prompt += f"Number of Transactions: {data['expense_count']}\n"
    prompt += f"Number of Spending Categories: {data['category_count']}\n\n"
    
    # Add category breakdown
    prompt += "Spending by Category:\n"
    for category, amount in data['category_spending'].items():
        percentage = (amount / data['total_spending']) * 100
        prompt += f"- {category}: ${amount:.2f} ({percentage:.1f}% of total)\n"
    
    # Add budget status
    if data['budget_status']:
        prompt += "\nBudget Status (Current Month):\n"
        for category, status in data['budget_status'].items():
            prompt += f"- {category}: ${status['spent']:.2f} spent of ${status['budget']:.2f} budget "
            prompt += f"({status['percentage']:.1f}% used, ${status['remaining']:.2f} remaining)\n"
    
    # Add top spending categories
    prompt += "\nTop Spending Categories:\n"
    for category, amount in data['top_categories']:
        percentage = (amount / data['total_spending']) * 100
        prompt += f"- {category}: ${amount:.2f} ({percentage:.1f}% of total)\n"
    
    # Add recurring expenses
    if data['recurring_expenses']:
        prompt += "\nRecurring Expenses:\n"
        for expense in data['recurring_expenses']:
            prompt += f"- {expense['description']} (${expense['amount']:.2f}, {expense['frequency']} occurrences, Category: {expense['category']})\n"
    
    # Add unusual expenses
    if data['unusual_expenses']:
        prompt += "\nUnusual Expenses (significantly higher than category average):\n"
        for expense in data['unusual_expenses']:
            prompt += f"- {expense['description']}: ${expense['amount']:.2f} ({expense['category']}, {expense['date']})\n"
    
    # Add monthly spending trends
    prompt += "\nMonthly Spending Trends:\n"
    for month, amount in data['monthly_trends'].items():
        prompt += f"- {month}: ${amount:.2f}\n"

    # Add user question with specific instructions
    if user_question:
        prompt += f"\nUser Question: {user_question}\n"
        prompt += "\nWhen answering, please:"
        prompt += "\n1. Directly reference the user's specific spending patterns"
        prompt += "\n2. Mention actual category names and amounts from their data"
        prompt += "\n3. Provide personalized recommendations based on their unique spending habits"
        prompt += "\n4. Suggest specific, actionable steps tailored to their financial situation"
    
    prompt += """\n\nPlease provide:
1. Key observations about the user's specific spending patterns
2. Personalized recommendations for improvement, mentioning specific categories
3. Actionable steps to optimize their budget based on their actual spending
4. Potential saving opportunities in their highest spending categories
5. Relevant financial advice based on their transaction history"""

    return prompt

def format_ai_response(response_text):
    """Format the AI response into structured advice."""
    try:
        # Split response into sections
        sections = response_text.split('\n')
        formatted_advice = []
        
        for section in sections:
            if not section.strip():
                continue
                
            # Determine message type based on content
            msg_type = 'info'
            if any(keyword in section.lower() for keyword in ['warning', 'caution', 'alert', 'budget', 'overspent']):
                msg_type = 'warning'
            elif any(keyword in section.lower() for keyword in ['saving', 'reduce', 'cut', 'opportunity', 'recommend', 'suggest']):
                msg_type = 'success'
            elif any(keyword in section.lower() for keyword in ['error', 'danger', 'critical', 'urgent']):
                msg_type = 'danger'
                
            formatted_advice.append({
                'type': msg_type,
                'message': section.strip()
            })
            
        return formatted_advice
        
    except Exception as e:
        print(f"Error formatting AI response: {str(e)}")
        return [{
            'type': 'danger',
            'message': 'Error formatting advice. Please try again.'
        }]

def handle_api_error(api_error):
    """Handle OpenAI API errors."""
    error_message = str(api_error)
    print(f"OpenAI API error: {error_message}")
    
    if 'rate limit' in error_message.lower():
        return [{
            'type': 'warning',
            'message': 'Service is busy. Please try again in a few minutes.'
        }]
    elif 'invalid api key' in error_message.lower():
        return [{
            'type': 'danger',
            'message': 'API configuration error. Please contact support.'
        }]
    else:
        return [{
            'type': 'danger',
            'message': 'Error getting advice. Please try again later.'
        }] 