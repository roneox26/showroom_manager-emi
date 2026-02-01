# Import all route blueprints
from routes.inventory import inventory_bp
from routes.pos import pos_bp
from routes.emi_manager import emi_bp

__all__ = ['inventory_bp', 'pos_bp', 'emi_bp']
