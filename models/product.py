from database import db
from datetime import datetime


class Product(db.Model):
    """Product model for inventory management"""
    
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with sales
    sales = db.relationship('Sale', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name} - {self.model}>'
    
    def update_stock(self, quantity, operation='add'):
        """
        Update stock quantity
        
        Args:
            quantity: Amount to add or subtract
            operation: 'add' to increase stock, 'subtract' to decrease
        
        Returns:
            bool: True if successful, False if insufficient stock
        """
        if operation == 'add':
            self.stock_quantity += quantity
            return True
        elif operation == 'subtract':
            if self.stock_quantity >= quantity:
                self.stock_quantity -= quantity
                return True
            return False
        return False
    
    def is_low_stock(self, threshold=5):
        """
        Check if product stock is below threshold
        
        Args:
            threshold: Minimum stock level
        
        Returns:
            bool: True if stock is low
        """
        return self.stock_quantity <= threshold
    
    def get_profit_margin(self):
        """Calculate profit margin percentage"""
        if self.buying_price > 0:
            return ((self.selling_price - self.buying_price) / self.buying_price) * 100
        return 0
    
    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'buying_price': self.buying_price,
            'selling_price': self.selling_price,
            'stock_quantity': self.stock_quantity,
            'is_low_stock': self.is_low_stock(),
            'profit_margin': round(self.get_profit_margin(), 2)
        }
