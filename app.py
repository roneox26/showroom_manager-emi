from flask import Flask, render_template, redirect, url_for
from config import config
from database import db, init_db
import os


def create_app(config_name='default'):
    """
    Application factory function
    
    Args:
        config_name: Configuration environment name
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    from routes.inventory import inventory_bp
    from routes.pos import pos_bp
    from routes.emi_manager import emi_bp
    
    app.register_blueprint(inventory_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(emi_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Home route
    @app.route('/')
    def index():
        """Home page - redirect to inventory"""
        return render_template('home.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app


if __name__ == '__main__':
    # Get environment from environment variable
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Create app
    app = create_app(env)
    
    # Run app
    print("=" * 50)
    print("🏪 Showroom Manager Application")
    print("=" * 50)
    print(f"Environment: {env}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 50)
    print("\nApplication is running on http://127.0.0.1:5000")
    print("\nAvailable routes:")
    print("  - Home: http://127.0.0.1:5000/")
    print("  - Inventory: http://127.0.0.1:5000/inventory/")
    print("  - POS/Sales: http://127.0.0.1:5000/pos/")
    print("  - EMI Dashboard: http://127.0.0.1:5000/emi/dashboard")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
