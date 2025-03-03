from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    expenses = db.relationship('Expense', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Define relationship without backref or back_populates
    expenses = db.relationship('Expense', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Expense(db.Model):
    __tablename__ = 'expenses'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source = db.Column(db.String(50), default='manual')
    
    # Define relationship with foreign_keys to avoid ambiguity
    category = db.relationship('Category', foreign_keys=[category_id])
    
    def __repr__(self):
        return f'<Expense {self.description} ${self.amount}>'

class Statement(db.Model):
    __tablename__ = 'statements'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    processed = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('statements', lazy=True))
    
    def __repr__(self):
        return f'<Statement {self.filename}>'

class Reminder(db.Model):
    __tablename__ = 'reminders'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_type = db.Column(db.String(20), nullable=True)  # 'weekly', 'monthly', 'yearly'
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('reminders', lazy=True))
    category = db.relationship('Category', backref=db.backref('reminders', lazy=True))

class FinancialGoal(db.Model):
    __tablename__ = 'financial_goals'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    target_date = db.Column(db.DateTime, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('goals', lazy=True))
    category = db.relationship('Category', backref=db.backref('goals', lazy=True))
    
    @property
    def progress_percentage(self):
        if self.target_amount == 0:
            return 100
        return min(100, (self.current_amount / self.target_amount) * 100)
    
    @property
    def days_remaining(self):
        if self.is_completed:
            return 0
        today = datetime.utcnow().date()
        return (self.target_date.date() - today).days 