from app import create_app, db
from app.models import Category

def init_db():
    app = create_app()
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Add default categories if they don't exist
        default_categories = [
            'Groceries',
            'Dining',
            'Transportation',
            'Entertainment',
            'Shopping',
            'Utilities',
            'Housing',
            'Healthcare',
            'Education',
            'Personal',
            'Travel',
            'Subscription',
            'Miscellaneous'
        ]
        
        for category_name in default_categories:
            if not Category.query.filter_by(name=category_name).first():
                category = Category(name=category_name)
                db.session.add(category)
        
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db() 