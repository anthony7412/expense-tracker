from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

def calculate_financial_health(expenses, categories, goals, reminders, income=0):
    """Calculate overall financial health score and metrics."""
    today = datetime.now()
    
    # Initialize health metrics
    health = {
        'score': 0,  # 0-100 score
        'metrics': {
            'budget_adherence': 0,
            'savings_ratio': 0,
            'debt_management': 0,
            'expense_stability': 0,
            'goal_progress': 0
        },
        'insights': [],
        'recommendations': []
    }
    
    # Calculate total spending for current month
    current_month_expenses = [e for e in expenses 
                             if e.date.month == today.month and e.date.year == today.year]
    total_spending = sum(e.amount for e in current_month_expenses)
    
    # Calculate budget adherence
    categories_with_budget = [c for c in categories if c.budget > 0]
    if categories_with_budget:
        budget_scores = []
        for category in categories_with_budget:
            cat_expenses = [e.amount for e in current_month_expenses if e.category_id == category.id]
            cat_total = sum(cat_expenses)
            
            # Calculate adherence score (100 = at or under budget, 0 = 2x budget or more)
            if cat_total <= category.budget:
                adherence = 100
            else:
                overspend_ratio = cat_total / category.budget
                adherence = max(0, 100 - (overspend_ratio - 1) * 100)
            
            budget_scores.append(adherence)
        
        health['metrics']['budget_adherence'] = sum(budget_scores) / len(budget_scores)
    else:
        health['metrics']['budget_adherence'] = 50  # Neutral if no budgets set
        health['insights'].append({
            'type': 'warning',
            'message': 'Set category budgets to improve your financial health score'
        })
    
    # Calculate savings ratio (if income provided)
    if income > 0:
        savings = income - total_spending
        savings_ratio = (savings / income) * 100
        
        # Score: 0 = negative savings, 100 = saving 30% or more
        if savings <= 0:
            health['metrics']['savings_ratio'] = 0
        else:
            health['metrics']['savings_ratio'] = min(100, (savings_ratio / 30) * 100)
    else:
        health['metrics']['savings_ratio'] = 50  # Neutral if no income data
        health['insights'].append({
            'type': 'info',
            'message': 'Add income information to get a more accurate financial health score'
        })
    
    # Calculate expense stability
    if len(expenses) > 10:
        # Get monthly totals for past 6 months
        monthly_totals = defaultdict(float)
        for expense in expenses:
            if (today - expense.date).days <= 180:
                month_key = f"{expense.date.year}-{expense.date.month}"
                monthly_totals[month_key] += expense.amount
        
        if monthly_totals:
            # Calculate coefficient of variation (lower is more stable)
            values = list(monthly_totals.values())
            std_dev = np.std(values)
            mean = np.mean(values)
            
            if mean > 0:
                cv = std_dev / mean
                # Score: 100 = very stable (cv < 0.1), 0 = very unstable (cv > 0.5)
                stability_score = max(0, 100 - (cv * 200))
                health['metrics']['expense_stability'] = stability_score
    else:
        health['metrics']['expense_stability'] = 50  # Neutral if not enough data
    
    # Calculate goal progress
    active_goals = [g for g in goals if not g.is_completed]
    if active_goals:
        goal_scores = []
        for goal in active_goals:
            # Calculate expected progress based on time elapsed
            total_days = (goal.target_date - goal.start_date).days
            days_passed = (today - goal.start_date).days
            
            if total_days > 0 and days_passed > 0:
                expected_progress = min(100, (days_passed / total_days) * 100)
                actual_progress = goal.progress_percentage
                
                # Score how well the actual progress matches or exceeds expected progress
                if actual_progress >= expected_progress:
                    goal_score = 100
                else:
                    goal_score = (actual_progress / expected_progress) * 100
                
                goal_scores.append(goal_score)
        
        if goal_scores:
            health['metrics']['goal_progress'] = sum(goal_scores) / len(goal_scores)
    else:
        health['metrics']['goal_progress'] = 50  # Neutral if no goals
        health['insights'].append({
            'type': 'info',
            'message': 'Set financial goals to track your progress and improve your score'
        })
    
    # Calculate debt management (based on upcoming payment reminders)
    upcoming_payments = [r for r in reminders if not r.is_completed and (r.due_date - today).days <= 30]
    if upcoming_payments:
        total_upcoming = sum(r.amount for r in upcoming_payments)
        
        # Check for overdue payments
        overdue_payments = [r for r in upcoming_payments if r.due_date < today]
        
        if overdue_payments:
            # Penalize for overdue payments
            health['metrics']['debt_management'] = max(0, 50 - (len(overdue_payments) * 10))
            health['insights'].append({
                'type': 'danger',
                'message': f'You have {len(overdue_payments)} overdue payments. Pay these as soon as possible.'
            })
        else:
            # Good debt management if no overdue payments
            health['metrics']['debt_management'] = 80
            
            # Check if upcoming payments are high relative to spending
            if total_spending > 0 and total_upcoming > total_spending * 0.5:
                health['metrics']['debt_management'] = 60
                health['insights'].append({
                    'type': 'warning',
                    'message': 'Your upcoming payments are high relative to your monthly spending.'
                })
    else:
        health['metrics']['debt_management'] = 90  # Very good if no upcoming payments
    
    # Calculate overall health score (weighted average of metrics)
    weights = {
        'budget_adherence': 0.3,
        'savings_ratio': 0.25,
        'debt_management': 0.2,
        'expense_stability': 0.15,
        'goal_progress': 0.1
    }
    
    health['score'] = sum(metric_score * weights[metric_name] 
                         for metric_name, metric_score in health['metrics'].items())
    
    # Generate recommendations based on lowest scores
    sorted_metrics = sorted(health['metrics'].items(), key=lambda x: x[1])
    lowest_metrics = sorted_metrics[:2]
    
    for metric_name, score in lowest_metrics:
        if metric_name == 'budget_adherence' and score < 70:
            health['recommendations'].append({
                'type': 'action',
                'message': 'Review categories where you\'re exceeding budget and adjust your spending or increase budgets.'
            })
        elif metric_name == 'savings_ratio' and score < 70:
            health['recommendations'].append({
                'type': 'action',
                'message': 'Try to increase your savings rate by reducing non-essential expenses.'
            })
        elif metric_name == 'debt_management' and score < 70:
            health['recommendations'].append({
                'type': 'action',
                'message': 'Focus on paying off overdue payments and managing upcoming expenses.'
            })
        elif metric_name == 'expense_stability' and score < 70:
            health['recommendations'].append({
                'type': 'action',
                'message': 'Your spending varies significantly month to month. Try to establish more consistent spending habits.'
            })
        elif metric_name == 'goal_progress' and score < 70:
            health['recommendations'].append({
                'type': 'action',
                'message': 'You\'re falling behind on your financial goals. Consider adjusting your goals or increasing contributions.'
            })
    
    return health 