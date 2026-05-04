from database import db
from datetime import datetime


class DebtRecord(db.Model):
    """Model for tracking money lending/borrowing records"""
    __tablename__ = 'debt_records'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    photo = db.Column(db.String(255))  # Store photo filename
    status = db.Column(db.String(20), default='pending')  # pending, paid, partial
    paid_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DebtRecord {self.name} - {self.amount}>'
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to be paid"""
        return self.amount - self.paid_amount
    
    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        from datetime import date
        return self.due_date < date.today() and self.status != 'paid'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'amount': self.amount,
            'due_date': self.due_date.strftime('%Y-%m-%d'),
            'photo': self.photo,
            'status': self.status,
            'paid_amount': self.paid_amount,
            'remaining_amount': self.remaining_amount,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
