from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()


def init_db(app):
    """
    Initialize the database with the Flask app
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    
    with app.app_context():
        # Import all models to ensure they're registered
        from models import product, customer, sales
        
        # Create all tables
        db.create_all()
        print("Database initialized successfully!")


def reset_db(app):
    """
    Drop all tables and recreate them (use with caution!)
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")
