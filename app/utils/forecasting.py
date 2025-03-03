from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sqlalchemy import extract
from ..models import Expense, Category, Reminder

def generate_expense_forecast(expenses, categories, reminders):
    """Generate a 6-month expense forecast based on historical data and upcoming reminders."""
    today = datetime.now()
    forecast_months = 6
    
    # Initialize forecast data structure
    forecast = {
        'monthly_totals': [],
        'category_forecasts': [],
        'upcoming_payments': [],
        'savings_potential': 0,
        'expected_total': 0
    }
    
    # Calculate average monthly spending by category
    category_spending = defaultdict(list)
    monthly_totals = defaultdict(float)
    
    # Group expenses by month and category for the past 6 months
    for expense in expenses:
        # Only consider expenses from the past 6 months
        if (today - expense.date).days <= 180:
            month_key = f"{expense.date.year}-{expense.date.month}"
            monthly_totals[month_key] += expense.amount
            
            category_name = expense.category.name if expense.category else "Uncategorized"
            category_spending[category_name].append(expense.amount)
    
    # Calculate average monthly spending for each category
    category_averages = {}
    for category, amounts in category_spending.items():
        if amounts:
            category_averages[category] = sum(amounts) / len(amounts)
    
    # Calculate overall monthly average
    if monthly_totals:
        overall_monthly_avg = sum(monthly_totals.values()) / len(monthly_totals)
    else:
        overall_monthly_avg = 0
    
    # Generate monthly forecasts
    for i in range(1, forecast_months + 1):
        forecast_date = today + timedelta(days=30 * i)
        month_name = forecast_date.strftime("%B %Y")
        
        # Start with the average monthly total
        forecast_total = overall_monthly_avg
        
        # Add any upcoming reminders for this month
        for reminder in reminders:
            reminder_date = reminder.due_date
            if reminder_date.year == forecast_date.year and reminder_date.month == forecast_date.month:
                forecast_total += reminder.amount
        
        forecast['monthly_totals'].append({
            'month': month_name,
            'amount': round(forecast_total, 2)
        })
        
        forecast['expected_total'] += forecast_total
    
    # Generate category-specific forecasts
    for category, avg_amount in category_averages.items():
        forecast['category_forecasts'].append({
            'category': category,
            'monthly_avg': round(avg_amount, 2),
            'six_month_total': round(avg_amount * forecast_months, 2)
        })
    
    # Add upcoming payments from reminders
    for reminder in reminders:
        if not reminder.is_completed:
            forecast['upcoming_payments'].append({
                'title': reminder.title,
                'amount': reminder.amount,
                'due_date': reminder.due_date.strftime("%Y-%m-%d"),
                'days_away': (reminder.due_date - today).days,
                'is_recurring': reminder.is_recurring,
                'recurrence_type': reminder.recurrence_type
            })
    
    # Calculate potential savings
    # Identify categories with above-average spending
    if category_averages:
        avg_category_spending = sum(category_averages.values()) / len(category_averages)
        for category, avg in category_averages.items():
            if avg > avg_category_spending * 1.2:  # 20% above average
                # Estimate savings if reduced to average
                potential_savings = (avg - avg_category_spending) * forecast_months
                forecast['savings_potential'] += potential_savings
    
    forecast['savings_potential'] = round(forecast['savings_potential'], 2)
    forecast['expected_total'] = round(forecast['expected_total'], 2)
    
    return forecast 