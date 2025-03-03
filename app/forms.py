from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, TextAreaField, DateField, EmailField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp, NumberRange, Optional
from app.models import User
from datetime import datetime

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                       validators=[DataRequired(), 
                                 Regexp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                                      message='Invalid email address')])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=50)])
    budget = FloatField('Monthly Budget', validators=[DataRequired()])
    submit = SubmitField('Save Category')

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired(), Length(max=200)])
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Expense')

class StatementUploadForm(FlaskForm):
    statement = FileField('Bank Statement (PDF)', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    submit = SubmitField('Upload Statement')

class DateRangeForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Generate Report')

class ReminderForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    due_date = DateField('Due Date', validators=[DataRequired()], format='%Y-%m-%d')
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    is_recurring = BooleanField('Recurring Payment')
    recurrence_type = SelectField('Recurrence', choices=[
        ('', 'Not Recurring'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], validators=[Optional()])
    submit = SubmitField('Save Reminder')

class FinancialGoalForm(FlaskForm):
    title = StringField('Goal Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    target_amount = FloatField('Target Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    current_amount = FloatField('Current Progress', validators=[NumberRange(min=0)], default=0)
    category_id = SelectField('Category (Optional)', coerce=int, validators=[Optional()])
    target_date = DateField('Target Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Save Goal') 