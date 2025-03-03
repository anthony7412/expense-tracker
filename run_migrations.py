from app import create_app, db
from app.models import FinancialGoal
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    # Create the financial_goals table if it doesn't exist
    inspector = inspect(db.engine)
    if not inspector.has_table('financial_goals'):
        db.create_all()
        print("Created missing tables")
    else:
        print("All tables already exist") 