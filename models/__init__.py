# Import all models for easy access
from models.product import Product
from models.customer import Customer
from models.sales import Sale, EMI_Ledger

__all__ = ['Product', 'Customer', 'Sale', 'EMI_Ledger']
