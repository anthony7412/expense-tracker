from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sqlalchemy import extract

def analyze_spending_patterns(expenses, categories):
    """Analyze spending patterns and provide AI-powered insights."""
    insights = []
    
    # Group expenses by category
    category_spending = defaultdict(float)
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Uncategorized"
        category_spending[category_name] += expense.amount
    
    # Calculate total spending
    total_spending = sum(category_spending.values())
    
    # Analyze category distribution
    for category, amount in category_spending.items():
        if total_spending > 0:
            percentage = (amount / total_spending) * 100
            if percentage > 30:
                insights.append({
                    'type': 'warning',
                    'message': f'High spending in {category}: {percentage:.1f}% of total expenses. Consider setting a budget limit.'
                })
    
    # Analyze spending trends
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_expenses = defaultdict(float)
    for expense in expenses:
        if expense.date.year == current_year:
            monthly_expenses[expense.date.month] += expense.amount
    
    # Check for significant month-over-month changes
    if len(monthly_expenses) >= 2:
        current_month_spending = monthly_expenses.get(current_month, 0)
        prev_month_spending = monthly_expenses.get(current_month - 1, 0)
        if prev_month_spending > 0:
            change_percentage = ((current_month_spending - prev_month_spending) / prev_month_spending) * 100
            if change_percentage > 20:
                insights.append({
                    'type': 'info',
                    'message': f'Your spending increased by {change_percentage:.1f}% compared to last month.'
                })
            elif change_percentage < -20:
                insights.append({
                    'type': 'success',
                    'message': f'Great job! Your spending decreased by {abs(change_percentage):.1f}% compared to last month.'
                })
    
    # Provide budget-based insights
    for category in categories:
        monthly_spending = sum(e.amount for e in expenses 
                             if e.category_id == category.id 
                             and e.date.month == current_month
                             and e.date.year == current_year)
        
        if category.budget > 0:
            budget_percentage = (monthly_spending / category.budget) * 100
            if budget_percentage > 90:
                insights.append({
                    'type': 'danger',
                    'message': f'Alert: You\'ve used {budget_percentage:.1f}% of your {category.name} budget.'
                })
            elif budget_percentage > 75:
                insights.append({
                    'type': 'warning',
                    'message': f'Caution: You\'ve used {budget_percentage:.1f}% of your {category.name} budget.'
                })
    
    return insights

def get_ai_recommendations(expenses, categories):
    """Generate AI-powered recommendations based on spending patterns."""
    recommendations = []
    
    # Analyze frequent small expenses
    small_expenses = [e for e in expenses if e.amount < 20]
    if len(small_expenses) > 10:
        total_small = sum(e.amount for e in small_expenses)
        recommendations.append({
            'type': 'tip',
            'message': f'You have {len(small_expenses)} small expenses totaling ${total_small:.2f}. Consider tracking these closely as they can add up quickly.'
        })
    
    # Analyze category-specific patterns
    for category in categories:
        cat_expenses = [e for e in expenses if e.category_id == category.id]
        if len(cat_expenses) > 0:
            avg_amount = sum(e.amount for e in cat_expenses) / len(cat_expenses)
            if category.name == 'Dining' and avg_amount > 50:
                recommendations.append({
                    'type': 'saving',
                    'message': 'Your average dining expense is high. Consider meal prepping or looking for dining deals.'
                })
            elif category.name == 'Transportation' and len(cat_expenses) > 20:
                recommendations.append({
                    'type': 'saving',
                    'message': 'You have frequent transportation expenses. Consider getting a monthly pass or carpooling options.'
                })
    
    # Analyze recurring expenses
    recurring_expenses = defaultdict(list)
    for expense in expenses:
        key = f"{expense.description}-{expense.amount}"
        recurring_expenses[key].append(expense)
    
    for key, exp_list in recurring_expenses.items():
        if len(exp_list) > 2:
            recommendations.append({
                'type': 'subscription',
                'message': f'Recurring expense detected: {exp_list[0].description}. Review if this subscription is still needed.'
            })
    
    return recommendations 