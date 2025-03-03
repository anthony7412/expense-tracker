"""Create financial goals table

This script creates the financial_goals table in the database.
"""

from app import db
from app.models import FinancialGoal
from flask import current_app
import os

def run_migration():
    """Run the migration to create the financial_goals table"""
    with current_app.app_context():
        # Create the table
        db.create_all()
        print("Created financial_goals table")

if __name__ == "__main__":
    run_migration() 