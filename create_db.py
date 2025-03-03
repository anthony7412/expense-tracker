from app import create_app, db
from app.models import User, Category, Expense, Statement
import os

def create_database():
    app = create_app()
    
    # Make sure the uploads directory exists
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    with app.app_context():
        # Drop existing database file if it exists
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expense_tracker.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database file: {db_path}")
        
        # Create all database tables
        db.create_all()
        print("Created new database tables")
        
        # Create a default user
        default_user = User(username='default', email='default@example.com')
        default_user.set_password('password123')
        db.session.add(default_user)
        db.session.commit()
        print("Created default user")
        
        # Add default categories with budgets for the default user
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
                user_id=default_user.id
            )
            db.session.add(category)
        
        try:
            db.session.commit()
            print("Added default categories")
            print("Database created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating database: {e}")

if __name__ == "__main__":
    create_database() 