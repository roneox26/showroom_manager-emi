from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import db
from models.product import Product
from models.customer import Customer
from models.sales import Sale, EMI_Ledger
from datetime import datetime, timedelta
from config import Config

pos_bp = Blueprint('pos', __name__, url_prefix='/pos')


@pos_bp.route('/')
def index():
    """POS interface for making sales"""
    products = Product.query.filter(Product.stock_quantity > 0).all()
    customers = Customer.query.all()
    emi_periods = Config.DEFAULT_EMI_PERIODS
    
    return render_template('sell_product.html', 
                         products=products, 
                         customers=customers,
                         emi_periods=emi_periods)


@pos_bp.route('/cash-sale', methods=['POST'])
def cash_sale():
    """Process a cash sale (full payment)"""
    try:
        product_id = int(request.form.get('product_id'))
        customer_id = request.form.get('customer_id')
        customer_name = request.form.get('customer_name')
        customer_phone = request.form.get('customer_phone')
        
        # Get or create customer
        if customer_id:
            customer = Customer.query.get(int(customer_id))
        else:
            # Create new customer
            if not customer_name or not customer_phone:
                flash('ক্রেতার নাম এবং ফোন নম্বর আবশ্যক!', 'danger')
                return redirect(url_for('pos.index'))
            
            # Check if phone already exists
            existing_customer = Customer.query.filter_by(phone=customer_phone).first()
            if existing_customer:
                customer = existing_customer
            else:
                customer = Customer(
                    name=customer_name,
                    phone=customer_phone,
                    address=request.form.get('customer_address', '')
                )
                db.session.add(customer)
                db.session.flush()  # Get customer ID
        
        # Get product
        product = Product.query.get_or_404(product_id)
        
        # Check stock
        if product.stock_quantity < 1:
            flash(f'পণ্য "{product.name}" স্টকে নেই!', 'danger')
            return redirect(url_for('pos.index'))
        
        # Create sale
        sale = Sale(
            customer_id=customer.id,
            product_id=product.id,
            sale_type='Cash',
            total_amount=product.selling_price,
            paid_amount=product.selling_price
        )
        
        # Update stock
        product.update_stock(1, 'subtract')
        
        db.session.add(sale)
        db.session.commit()
        
        flash(f'নগদ বিক্রয় সফল! বিল নম্বর: {sale.id}', 'success')
        return redirect(url_for('pos.invoice', sale_id=sale.id))
        
    except ValueError:
        flash('অবৈধ ডেটা!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'ত্রুটি: {str(e)}', 'danger')
    
    return redirect(url_for('pos.index'))


@pos_bp.route('/emi-sale', methods=['POST'])
def emi_sale():
    """Process an EMI sale with down payment"""
    try:
        product_id = int(request.form.get('product_id'))
        customer_id = request.form.get('customer_id')
        customer_name = request.form.get('customer_name')
        customer_phone = request.form.get('customer_phone')
        customer_address = request.form.get('customer_address', '')
        customer_nid = request.form.get('customer_nid', '')
        
        down_payment = float(request.form.get('down_payment', 0))
        emi_period = int(request.form.get('emi_period'))  # Number of months
        interest_rate = float(request.form.get('interest_rate', 0))  # Interest rate percentage
        
        # Get or create customer
        if customer_id:
            customer = Customer.query.get(int(customer_id))
        else:
            # Create new customer (NID required for EMI)
            if not customer_name or not customer_phone:
                flash('ক্রেতার নাম এবং ফোন নম্বর আবশ্যক!', 'danger')
                return redirect(url_for('pos.index'))
            
            if not customer_nid:
                flash('EMI বিক্রয়ের জন্য NID নম্বর আবশ্যক!', 'danger')
                return redirect(url_for('pos.index'))
            
            # Check if phone already exists
            existing_customer = Customer.query.filter_by(phone=customer_phone).first()
            if existing_customer:
                customer = existing_customer
                # Update NID if not set
                if not customer.nid_number:
                    customer.nid_number = customer_nid
            else:
                customer = Customer(
                    name=customer_name,
                    phone=customer_phone,
                    address=customer_address,
                    nid_number=customer_nid
                )
                db.session.add(customer)
                db.session.flush()
        
        # Get product
        product = Product.query.get_or_404(product_id)
        
        # Check stock
        if product.stock_quantity < 1:
            flash(f'পণ্য "{product.name}" স্টকে নেই!', 'danger')
            return redirect(url_for('pos.index'))
        
        # Validate down payment
        if down_payment < 0 or down_payment >= product.selling_price:
            flash('ডাউন পেমেন্ট অবৈধ!', 'danger')
            return redirect(url_for('pos.index'))
        
        # Calculate EMI with interest (Flat Rate Method)
        principal_amount = product.selling_price - down_payment
        
        # Calculate total interest
        total_interest = (principal_amount * interest_rate * emi_period) / (100 * 12)
        
        # Total amount to be paid in installments
        total_emi_amount = principal_amount + total_interest
        
        # Monthly installment
        monthly_amount = total_emi_amount / emi_period
        
        # Create sale
        sale = Sale(
            customer_id=customer.id,
            product_id=product.id,
            sale_type='EMI',
            total_amount=product.selling_price,
            paid_amount=down_payment
        )
        
        db.session.add(sale)
        db.session.flush()  # Get sale ID
        
        # Create EMI ledger
        next_payment_date = datetime.now().date() + timedelta(days=30)
        emi_ledger = EMI_Ledger(
            sale_id=sale.id,
            total_installments=emi_period,
            monthly_amount=monthly_amount,
            interest_rate=interest_rate,
            installments_paid=0,
            next_payment_date=next_payment_date,
            status='Active'
        )
        
        # Update stock
        product.update_stock(1, 'subtract')
        
        db.session.add(emi_ledger)
        db.session.commit()
        
        flash(f'EMI বিক্রয় সফল! বিল নম্বর: {sale.id}', 'success')
        return redirect(url_for('pos.invoice', sale_id=sale.id))
        
    except ValueError:
        flash('অবৈধ ডেটা!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'ত্রুটি: {str(e)}', 'danger')
    
    return redirect(url_for('pos.index'))


@pos_bp.route('/invoice/<int:sale_id>')
def invoice(sale_id):
    """Display invoice for a sale"""
    sale = Sale.query.get_or_404(sale_id)
    return render_template('invoice.html', sale=sale)


@pos_bp.route('/calculate-emi', methods=['POST'])
def calculate_emi():
    """API endpoint to calculate EMI details"""
    try:
        total_price = float(request.json.get('total_price'))
        down_payment = float(request.json.get('down_payment', 0))
        emi_period = int(request.json.get('emi_period'))
        interest_rate = float(request.json.get('interest_rate', 0))
        
        principal_amount = total_price - down_payment
        
        # Calculate interest (Flat Rate Method)
        total_interest = (principal_amount * interest_rate * emi_period) / (100 * 12)
        
        # Total EMI amount
        total_emi_amount = principal_amount + total_interest
        
        # Monthly installment
        monthly_amount = total_emi_amount / emi_period
        
        return jsonify({
            'success': True,
            'total_price': total_price,
            'down_payment': down_payment,
            'principal_amount': principal_amount,
            'interest_rate': interest_rate,
            'total_interest': round(total_interest, 2),
            'total_emi_amount': round(total_emi_amount, 2),
            'emi_period': emi_period,
            'monthly_amount': round(monthly_amount, 2)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
