from database import db
from datetime import datetime
import re


class Customer(db.Model):
    """Customer model for storing customer information"""
    
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=True)
    nid_number = db.Column(db.String(50), nullable=True)  # National ID for EMI security
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with sales
    sales = db.relationship('Sale', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Customer {self.name} - {self.phone}>'
    
    @staticmethod
    def validate_phone(phone):
        """
        Validate phone number format (Bangladesh format)
        
        Args:
            phone: Phone number string
        
        Returns:
            bool: True if valid
        """
        # Bangladesh phone number pattern (11 digits starting with 01)
        pattern = r'^01[0-9]{9}$'
        return bool(re.match(pattern, phone))
    
    def get_total_purchases(self):
        """Get total purchase amount for this customer"""
        total = sum(sale.total_amount for sale in self.sales)
        return total
    
    def get_total_due(self):
        """Get total due amount (for EMI sales)"""
        total_due = 0
        for sale in self.sales:
            if sale.sale_type == 'EMI' and sale.emi_ledger:
                total_due += sale.emi_ledger.calculate_remaining_amount()
        return total_due
    
    def has_active_emi(self):
        """Check if customer has any active EMI"""
        for sale in self.sales:
            if sale.sale_type == 'EMI' and sale.emi_ledger and sale.emi_ledger.status == 'Active':
                return True
        return False
    
    def to_dict(self):
        """Convert customer to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'nid_number': self.nid_number,
            'total_purchases': self.get_total_purchases(),
            'total_due': self.get_total_due(),
            'has_active_emi': self.has_active_emi()
        }
