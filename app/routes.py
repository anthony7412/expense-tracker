from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models import User, Expense, Category, Statement, Reminder, FinancialGoal
from app.forms import RegistrationForm, LoginForm, ExpenseForm, StatementUploadForm, DateRangeForm, CategoryForm, ReminderForm, FinancialGoalForm
from app.utils.pdf_extractor import extract_transactions_from_pdf
from app.utils.expense_categorizer import categorize_expense
from sqlalchemy import extract
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import json
from app.utils.expense_analyzer import analyze_spending_patterns, get_ai_recommendations
from app.utils.openai_advisor import get_openai_advice
from collections import defaultdict
from .utils.receipt_scanner import scan_receipt
from .utils.financial_health import calculate_financial_health

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
expense_bp = Blueprint('expense', __name__)

# Main routes
@main_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('expense.dashboard'))
    return render_template('home.html')

# Auth routes
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('expense.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            # Add default categories for the new user
            default_categories = [
                ('Groceries', 500.0),
                ('Transportation', 200.0),
                ('Entertainment', 150.0),
                ('Utilities', 300.0),
                ('Dining', 250.0),
                ('Shopping', 200.0),
                ('Healthcare', 150.0),
                ('Other', 200.0)
            ]
            
            for name, budget in default_categories:
                category = Category(
                    name=name,
                    budget=budget,
                    user_id=user.id
                )
                db.session.add(category)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed. Please try again. Error: {str(e)}', 'danger')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# Expense routes
@expense_bp.route('/dashboard')
@login_required
def dashboard():
    # Get existing dashboard data
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get all expenses and categories for the current user
    all_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Get insights and recommendations
    insights = analyze_spending_patterns(all_expenses, categories)
    recommendations = get_ai_recommendations(all_expenses, categories)
    
    # Calculate monthly trends (last 6 months)
    monthly_trends = {}
    for i in range(6):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
        
        month_expenses = sum(e.amount for e in all_expenses 
                           if e.date.month == month and e.date.year == year)
        monthly_trends[f"{year}-{month:02d}"] = month_expenses
    
    # Calculate category-wise spending
    category_spending = {}
    category_budget_usage = {}
    for category in categories:
        total = sum(e.amount for e in all_expenses if e.category_id == category.id)
        category_spending[category.name] = total
        if category.budget > 0:
            category_budget_usage[category.name] = (total / category.budget) * 100
    
    # Calculate daily spending pattern
    daily_spending = defaultdict(float)
    for expense in all_expenses:
        if expense.date.month == current_month and expense.date.year == current_year:
            daily_spending[expense.date.day] += expense.amount
    
    return render_template('dashboard.html',
                         categories=list(category_spending.keys()),
                         amounts=list(category_spending.values()),
                         monthly_trends=monthly_trends,
                         category_budget_usage=category_budget_usage,
                         daily_spending=dict(daily_spending),
                         insights=insights,
                         recommendations=recommendations)

@expense_bp.route('/expenses')
@login_required
def list_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc()).all()
    return render_template('expenses/list.html', expenses=expenses)

@expense_bp.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    
    # Ensure user owns this expense
    if expense.user_id != current_user.id:
        flash('You do not have permission to edit this expense.', 'danger')
        return redirect(url_for('expense.list_expenses'))
    
    form = ExpenseForm()
    # Populate category choices
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.description = form.description.data
        expense.date = form.date.data
        expense.category_id = form.category_id.data
        
        db.session.commit()
        flash('Expense has been updated!', 'success')
        return redirect(url_for('expense.list_expenses'))
    
    # Pre-populate form with current values
    elif request.method == 'GET':
        form.amount.data = expense.amount
        form.description.data = expense.description
        form.date.data = expense.date
        form.category_id.data = expense.category_id
    
    return render_template('expenses/form.html', 
                         title='Edit Expense',
                         form=form,
                         expense=expense)

@expense_bp.route('/expenses/delete/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    
    # Ensure user owns this expense
    if expense.user_id != current_user.id:
        flash('You do not have permission to delete this expense.', 'danger')
        return redirect(url_for('expense.list_expenses'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense has been deleted!', 'success')
    return redirect(url_for('expense.list_expenses'))

@expense_bp.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    # Populate category choices
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            date=form.date.data,
            category_id=form.category_id.data,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expense.list_expenses'))
    
    return render_template('expenses/form.html', 
                         title='Add Expense',
                         form=form)

@expense_bp.route('/categories')
@login_required
def list_categories():
    categories = Category.query.all()
    return render_template('categories/list.html', categories=categories)

@expense_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, budget=form.budget.data)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('expense.list_categories'))
    return render_template('categories/form.html', form=form, title='Add Category')

@expense_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm()
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.budget = form.budget.data
        db.session.commit()
        flash('Category has been updated!', 'success')
        return redirect(url_for('expense.list_categories'))
    
    elif request.method == 'GET':
        form.name.data = category.name
        form.budget.data = category.budget
    
    return render_template('categories/form.html', 
                         title='Edit Category',
                         form=form,
                         category=category)

@expense_bp.route('/categories/delete/<int:id>')
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    if category.expenses:
        flash('Cannot delete category with existing expenses. Please reassign or delete the expenses first.', 'danger')
        return redirect(url_for('expense.list_categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category has been deleted!', 'success')
    return redirect(url_for('expense.list_categories'))

@expense_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_statement():
    form = StatementUploadForm()
    if form.validate_on_submit():
        try:
            # Save and process file
            statement_file = form.statement.data
            filename = secure_filename(statement_file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            statement_file.save(filepath)
            
            # Delete all existing expenses for the current user
            try:
                Expense.query.filter_by(user_id=current_user.id).delete()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash('Error clearing previous expenses.', 'danger')
                return redirect(url_for('expense.dashboard'))
            
            # Process new transactions
            transactions = extract_transactions_from_pdf(filepath)
            successful_imports = 0
            
            for transaction in transactions:
                # Skip zero amount transactions
                if transaction['amount'] == 0:
                    continue
                
                # Determine final amount based on transaction type
                final_amount = transaction['amount']
                if transaction['type'] == 'payment':
                    final_amount = -final_amount
                
                # Categorize the transaction
                category_name = categorize_expense(transaction['description'])
                category = Category.query.filter_by(name=category_name).first()
                if not category:
                    category = Category.query.filter_by(name='Miscellaneous').first()
                
                # Create new expense
                expense = Expense(
                    amount=final_amount,
                    description=transaction['description'],
                    date=transaction['date'],
                    category_id=category.id,
                    user_id=current_user.id,
                    source='Bank Statement'
                )
                db.session.add(expense)
                successful_imports += 1
            
            db.session.commit()
            os.remove(filepath)
            
            if successful_imports > 0:
                flash(f'Successfully cleared previous transactions and imported {successful_imports} new transactions!', 'success')
            else:
                flash('No new transactions found in the statement.', 'info')
            
            return redirect(url_for('expense.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing statement: {str(e)}', 'danger')
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return render_template('upload.html', form=form)

@expense_bp.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    form = DateRangeForm()
    
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        
        # Get expenses in date range
        expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).all()
        
        # Get expense summary by category
        expenses_by_category = db.session.query(
            Category.name, db.func.sum(Expense.amount)
        ).join(Expense).filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).group_by(Category.name).all()
        
        categories = [cat[0] for cat in expenses_by_category]
        amounts = [float(cat[1]) for cat in expenses_by_category]
        
        # Get daily expenses for line chart
        daily_expenses = db.session.query(
            db.func.date(Expense.date), db.func.sum(Expense.amount)
        ).filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).group_by(db.func.date(Expense.date)).all()
        
        dates = [str(day[0]) for day in daily_expenses]
        daily_amounts = [float(day[1]) for day in daily_expenses]
        
        return render_template(
            'reports.html',
            form=form,
            expenses=expenses,
            categories=json.dumps(categories),
            amounts=json.dumps(amounts),
            dates=json.dumps(dates),
            daily_amounts=json.dumps(daily_amounts),
            start_date=start_date,
            end_date=end_date
        )
    
    # Default to current month
    today = datetime.today()
    form.start_date.data = datetime(today.year, today.month, 1)
    form.end_date.data = today
    
    return render_template('reports.html', form=form)

@expense_bp.route('/get-ai-advice', methods=['POST'])
@login_required
def get_ai_advice():
    try:
        print("AI advice route accessed")
        
        # Get user question from request
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
            
        user_question = data['question']
        if not user_question.strip():
            return jsonify({
                'success': False,
                'error': 'Please enter a question'
            }), 400
            
        print(f"User question: {user_question}")
        
        # Get all expenses and categories for the current user
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
        categories = Category.query.filter_by(user_id=current_user.id).all()
        
        print(f"Found {len(expenses)} expenses and {len(categories)} categories")
        
        # Get OpenAI advice directly
        ai_advice = get_openai_advice(expenses, categories, user_question)
        
        if not ai_advice:
            print("No advice was generated")
            return jsonify({
                'success': False,
                'error': 'No advice generated'
            }), 400
            
        print(f"Successfully generated advice")
        return jsonify({
            'success': True,
            'advice': ai_advice
        })
        
    except Exception as e:
        print(f"Error in get_ai_advice route: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@expense_bp.route('/process-statement', methods=['POST'])
@login_required
def process_statement():
    try:
        form = StatementUploadForm()
        if form.validate_on_submit():
            file = form.statement.data
            if file:
                # Save the file
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Extract transactions
                transactions = extract_transactions_from_pdf(filepath)
                successful_imports = 0
                
                # Ensure "Other" category exists
                other_category = Category.query.filter_by(
                    name='Other',
                    user_id=current_user.id
                ).first()
                
                if not other_category:
                    other_category = Category(
                        name='Other',
                        budget=200.0,
                        user_id=current_user.id
                    )
                    db.session.add(other_category)
                    db.session.commit()
                    print("Created 'Other' category")
                
                # Process each transaction
                for transaction in transactions:
                    try:
                        # Get category
                        category_name = categorize_expense(transaction['description'])
                        category = Category.query.filter_by(
                            name=category_name,
                            user_id=current_user.id
                        ).first()
                        
                        # If category doesn't exist, use "Other"
                        if not category:
                            print(f"Category {category_name} not found, using Other")
                            category = other_category
                        
                        if not category or not category.id:
                            print("Error: Invalid category")
                            continue
                        
                        # Create expense
                        final_amount = transaction['amount']
                        if transaction.get('type', '').lower() == 'payment':
                            final_amount = -final_amount
                        
                        expense = Expense(
                            amount=final_amount,
                            description=transaction['description'],
                            date=transaction['date'],
                            category_id=category.id,
                            user_id=current_user.id,
                            source='statement'
                        )
                        db.session.add(expense)
                        db.session.commit()
                        successful_imports += 1
                        print(f"Successfully imported transaction: {transaction['description']}")
                            
                    except Exception as e:
                        print(f"Error processing transaction: {str(e)}")
                        db.session.rollback()
                        continue
                
                # Clean up the uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                if successful_imports > 0:
                    flash(f'Successfully imported {successful_imports} transactions!', 'success')
                else:
                    flash('No transactions were imported. Please check the statement format.', 'warning')
                
                return redirect(url_for('expense.list_expenses'))
                
        flash('Error processing statement. Please try again.', 'danger')
        return redirect(url_for('expense.upload_statement'))
        
    except Exception as e:
        print(f"Error processing statement: {str(e)}")
        flash('Error processing statement. Please try again.', 'danger')
        return redirect(url_for('expense.upload_statement'))

# Reminder routes
@expense_bp.route('/reminders')
@login_required
def reminders():
    upcoming_reminders = Reminder.query.filter_by(
        user_id=current_user.id, 
        is_completed=False
    ).order_by(Reminder.due_date).all()
    
    completed_reminders = Reminder.query.filter_by(
        user_id=current_user.id, 
        is_completed=True
    ).order_by(Reminder.due_date.desc()).limit(5).all()
    
    return render_template(
        'expenses/reminders.html', 
        upcoming_reminders=upcoming_reminders,
        completed_reminders=completed_reminders,
        title="Payment Reminders"
    )

@expense_bp.route('/reminders/add', methods=['GET', 'POST'])
@login_required
def add_reminder():
    form = ReminderForm()
    form.category_id.choices = [(0, 'None')] + [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()
    ]
    
    if form.validate_on_submit():
        category_id = form.category_id.data if form.category_id.data != 0 else None
        reminder = Reminder(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            amount=form.amount.data,
            category_id=category_id,
            is_recurring=form.is_recurring.data,
            recurrence_type=form.recurrence_type.data if form.is_recurring.data else None
        )
        db.session.add(reminder)
        db.session.commit()
        flash('Reminder added successfully!', 'success')
        return redirect(url_for('expense.reminders'))
    
    return render_template('expenses/reminder_form.html', form=form, title="Add Reminder")

@expense_bp.route('/reminders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    if reminder.user_id != current_user.id:
        abort(403)
        
    form = ReminderForm(obj=reminder)
    form.category_id.choices = [(0, 'None')] + [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()
    ]
    
    if form.validate_on_submit():
        category_id = form.category_id.data if form.category_id.data != 0 else None
        reminder.title = form.title.data
        reminder.description = form.description.data
        reminder.due_date = form.due_date.data
        reminder.amount = form.amount.data
        reminder.category_id = category_id
        reminder.is_recurring = form.is_recurring.data
        reminder.recurrence_type = form.recurrence_type.data if form.is_recurring.data else None
        
        db.session.commit()
        flash('Reminder updated successfully!', 'success')
        return redirect(url_for('expense.reminders'))
    
    return render_template('expenses/reminder_form.html', form=form, title="Edit Reminder")

@expense_bp.route('/reminders/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    if reminder.user_id != current_user.id:
        abort(403)
        
    reminder.is_completed = not reminder.is_completed
    
    # If completing a recurring reminder, create the next one
    if reminder.is_completed and reminder.is_recurring:
        next_due_date = None
        if reminder.recurrence_type == 'weekly':
            next_due_date = reminder.due_date + timedelta(days=7)
        elif reminder.recurrence_type == 'monthly':
            # Add a month to the current date
            next_month = reminder.due_date.month + 1
            next_year = reminder.due_date.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            next_due_date = reminder.due_date.replace(year=next_year, month=next_month)
        elif reminder.recurrence_type == 'yearly':
            next_due_date = reminder.due_date.replace(year=reminder.due_date.year + 1)
            
        if next_due_date:
            new_reminder = Reminder(
                user_id=current_user.id,
                title=reminder.title,
                description=reminder.description,
                due_date=next_due_date,
                amount=reminder.amount,
                category_id=reminder.category_id,
                is_recurring=True,
                recurrence_type=reminder.recurrence_type
            )
            db.session.add(new_reminder)
    
    db.session.commit()
    return jsonify({'success': True, 'completed': reminder.is_completed})

@expense_bp.route('/reminders/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    if reminder.user_id != current_user.id:
        abort(403)
        
    db.session.delete(reminder)
    db.session.commit()
    flash('Reminder deleted successfully!', 'success')
    return redirect(url_for('expense.reminders'))

# Financial Goals routes
@expense_bp.route('/goals')
@login_required
def goals():
    active_goals = FinancialGoal.query.filter_by(
        user_id=current_user.id, 
        is_completed=False
    ).order_by(FinancialGoal.target_date).all()
    
    completed_goals = FinancialGoal.query.filter_by(
        user_id=current_user.id, 
        is_completed=True
    ).order_by(FinancialGoal.target_date.desc()).all()
    
    return render_template(
        'expenses/goals.html', 
        active_goals=active_goals,
        completed_goals=completed_goals,
        title="Financial Goals"
    )

@expense_bp.route('/goals/add', methods=['GET', 'POST'])
@login_required
def add_goal():
    form = FinancialGoalForm()
    form.category_id.choices = [(0, 'None')] + [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()
    ]
    
    if form.validate_on_submit():
        category_id = form.category_id.data if form.category_id.data != 0 else None
        goal = FinancialGoal(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            target_amount=form.target_amount.data,
            current_amount=form.current_amount.data,
            category_id=category_id,
            target_date=form.target_date.data
        )
        
        # Check if goal is already completed
        if goal.current_amount >= goal.target_amount:
            goal.is_completed = True
            
        db.session.add(goal)
        db.session.commit()
        flash('Financial goal added successfully!', 'success')
        return redirect(url_for('expense.goals'))
    
    return render_template('expenses/goal_form.html', form=form, title="Add Financial Goal")

@expense_bp.route('/goals/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_goal(id):
    goal = FinancialGoal.query.get_or_404(id)
    if goal.user_id != current_user.id:
        abort(403)
        
    form = FinancialGoalForm(obj=goal)
    form.category_id.choices = [(0, 'None')] + [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()
    ]
    
    if form.validate_on_submit():
        category_id = form.category_id.data if form.category_id.data != 0 else None
        goal.title = form.title.data
        goal.description = form.description.data
        goal.target_amount = form.target_amount.data
        goal.current_amount = form.current_amount.data
        goal.category_id = category_id
        goal.target_date = form.target_date.data
        
        # Check if goal is now completed
        if goal.current_amount >= goal.target_amount:
            goal.is_completed = True
        else:
            goal.is_completed = False
            
        db.session.commit()
        flash('Financial goal updated successfully!', 'success')
        return redirect(url_for('expense.goals'))
    
    return render_template('expenses/goal_form.html', form=form, title="Edit Financial Goal")

@expense_bp.route('/goals/<int:id>/update-progress', methods=['POST'])
@login_required
def update_goal_progress(id):
    goal = FinancialGoal.query.get_or_404(id)
    if goal.user_id != current_user.id:
        abort(403)
        
    data = request.get_json()
    if 'amount' in data:
        try:
            amount = float(data['amount'])
            goal.current_amount += amount
            
            if goal.current_amount >= goal.target_amount:
                goal.is_completed = True
                
            db.session.commit()
            return jsonify({
                'success': True, 
                'current_amount': goal.current_amount,
                'progress': goal.progress_percentage,
                'is_completed': goal.is_completed
            })
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid amount'})
    
    return jsonify({'success': False, 'error': 'No amount provided'})

@expense_bp.route('/goals/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_goal(id):
    goal = FinancialGoal.query.get_or_404(id)
    if goal.user_id != current_user.id:
        abort(403)
        
    db.session.delete(goal)
    db.session.commit()
    flash('Financial goal deleted successfully!', 'success')
    return redirect(url_for('expense.goals'))

# Expense Forecasting
@expense_bp.route('/forecast')
@login_required
def forecast():
    # Get all expenses for the current user
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Get upcoming reminders
    upcoming_reminders = Reminder.query.filter_by(
        user_id=current_user.id, 
        is_completed=False
    ).order_by(Reminder.due_date).all()
    
    # Generate forecast data
    forecast_data = generate_expense_forecast(expenses, categories, upcoming_reminders)
    
    return render_template(
        'expenses/forecast.html',
        forecast=forecast_data,
        title="Expense Forecast"
    )

# Receipt scanning routes
@expense_bp.route('/scan-receipt', methods=['GET', 'POST'])
@login_required
def scan_receipt():
    # Check if OCR is available
    from .utils.receipt_scanner import TESSERACT_AVAILABLE
    
    if not TESSERACT_AVAILABLE:
        flash('Receipt scanning requires additional packages. Please install pytesseract and Pillow, or enter expenses manually.', 'warning')
        return render_template('expenses/scan_receipt.html', 
                             title='Scan Receipt',
                             ocr_available=False)
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'receipt' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['receipt']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file:
            # Get user categories
            categories = Category.query.filter_by(user_id=current_user.id).all()
            
            # Create uploads directory if it doesn't exist
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # Process the receipt
            result = scan_receipt(file_path, categories)
            
            if result['success']:
                # Pre-fill the expense form with extracted data
                return redirect(url_for('expense.add_expense_from_receipt', 
                                      amount=result['amount'],
                                      description=result['description'],
                                      date=result['date'].strftime('%Y-%m-%d'),
                                      category_id=result['category_id'] or '',
                                      source='receipt_scan'))
            else:
                flash(result['message'], 'warning')
                # Clean up the file
                if os.path.exists(file_path):
                    os.remove(file_path)
                return redirect(url_for('expense.scan_receipt'))
    
    return render_template('expenses/scan_receipt.html', 
                         title='Scan Receipt',
                         ocr_available=True)

@expense_bp.route('/expenses/add-from-receipt')
@login_required
def add_expense_from_receipt():
    form = ExpenseForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    
    # Pre-fill form with data from receipt scan
    form.amount.data = request.args.get('amount', type=float)
    form.description.data = request.args.get('description', '')
    form.date.data = datetime.strptime(request.args.get('date', ''), '%Y-%m-%d') if request.args.get('date') else datetime.today()
    form.category_id.data = request.args.get('category_id', type=int) if request.args.get('category_id') else None
    
    return render_template('expenses/form.html', 
                         title='Add Expense from Receipt',
                         form=form,
                         receipt_scan=True)

@expense_bp.route('/financial-health')
@login_required
def financial_health():
    # Get user data
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    goals = FinancialGoal.query.filter_by(user_id=current_user.id).all()
    reminders = Reminder.query.filter_by(user_id=current_user.id).all()
    
    # Calculate financial health
    health = calculate_financial_health(expenses, categories, goals, reminders)
    
    # Get recent expenses
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()
    
    # Get upcoming reminders
    upcoming_reminders = Reminder.query.filter_by(user_id=current_user.id, is_completed=False).order_by(Reminder.due_date).limit(5).all()
    
    # Get active goals
    active_goals = FinancialGoal.query.filter_by(user_id=current_user.id, is_completed=False).all()
    
    return render_template(
        'expenses/financial_health.html',
        health=health,
        recent_expenses=recent_expenses,
        upcoming_reminders=upcoming_reminders,
        active_goals=active_goals,
        title="Financial Health Dashboard"
    ) 