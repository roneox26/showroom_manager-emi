from database import db
from datetime import datetime, timedelta


class Sale(db.Model):
    """Sale model for recording sales transactions"""
    
    __tablename__ = 'sale'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    sale_type = db.Column(db.String(20), nullable=False)  # 'Cash' or 'EMI'
    total_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, nullable=False)  # Down payment for EMI, full amount for Cash
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with EMI ledger (one-to-one)
    emi_ledger = db.relationship('EMI_Ledger', backref='sale', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Sale {self.id} - {self.sale_type} - ৳{self.total_amount}>'
    
    def calculate_due_amount(self):
        """Calculate remaining due amount"""
        return self.total_amount - self.paid_amount
    
    def is_emi_sale(self):
        """Check if this is an EMI sale"""
        return self.sale_type == 'EMI'
    
    def is_fully_paid(self):
        """Check if sale is fully paid"""
        return self.paid_amount >= self.total_amount
    
    def to_dict(self):
        """Convert sale to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'sale_type': self.sale_type,
            'total_amount': self.total_amount,
            'paid_amount': self.paid_amount,
            'due_amount': self.calculate_due_amount(),
            'sale_date': self.sale_date.strftime('%Y-%m-%d %H:%M:%S')
        }


class EMI_Ledger(db.Model):
    """EMI Ledger model for tracking installment payments"""
    
    __tablename__ = 'emi_ledger'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False, unique=True)
    total_installments = db.Column(db.Integer, nullable=False)  # Total number of months
    monthly_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=0.0)  # Interest rate percentage (e.g., 5.0 for 5%)
    installments_paid = db.Column(db.Integer, default=0)
    next_payment_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Active')  # 'Active', 'Completed', 'Defaulted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EMI_Ledger {self.id} - {self.installments_paid}/{self.total_installments}>'
    
    def pay_installment(self):
        """
        Record an installment payment
        
        Returns:
            bool: True if payment recorded successfully
        """
        if self.installments_paid < self.total_installments:
            self.installments_paid += 1
            
            # Update next payment date (add 30 days)
            self.next_payment_date = self.next_payment_date + timedelta(days=30)
            
            # Update status if completed
            if self.installments_paid >= self.total_installments:
                self.status = 'Completed'
            
            # Update sale paid amount
            self.sale.paid_amount += self.monthly_amount
            
            return True
        return False
    
    def calculate_remaining_amount(self):
        """Calculate total remaining amount to be paid"""
        remaining_installments = self.total_installments - self.installments_paid
        return remaining_installments * self.monthly_amount
    
    def calculate_total_emi_amount(self):
        """Calculate total EMI amount (all installments including interest)"""
        return self.total_installments * self.monthly_amount
    
    def is_overdue(self):
        """Check if payment is overdue"""
        if self.status == 'Active':
            return datetime.now().date() > self.next_payment_date
        return False
    
    def get_days_overdue(self):
        """Get number of days overdue"""
        if self.is_overdue():
            delta = datetime.now().date() - self.next_payment_date
            return delta.days
        return 0
    
    def mark_as_defaulted(self):
        """Mark EMI as defaulted"""
        self.status = 'Defaulted'
    
    def to_dict(self):
        """Convert EMI ledger to dictionary"""
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'customer_name': self.sale.customer.name if self.sale and self.sale.customer else None,
            'customer_phone': self.sale.customer.phone if self.sale and self.sale.customer else None,
            'product_name': self.sale.product.name if self.sale and self.sale.product else None,
            'total_installments': self.total_installments,
            'monthly_amount': self.monthly_amount,
            'interest_rate': self.interest_rate,
            'installments_paid': self.installments_paid,
            'installments_remaining': self.total_installments - self.installments_paid,
            'remaining_amount': self.calculate_remaining_amount(),
            'next_payment_date': self.next_payment_date.strftime('%Y-%m-%d'),
            'status': self.status,
            'is_overdue': self.is_overdue(),
            'days_overdue': self.get_days_overdue()
        }
