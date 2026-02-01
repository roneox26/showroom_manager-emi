from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import db
from models.sales import Sale, EMI_Ledger
from models.customer import Customer
from datetime import datetime, timedelta

emi_bp = Blueprint('emi', __name__, url_prefix='/emi')


@emi_bp.route('/dashboard')
def dashboard():
    """EMI dashboard showing all active EMIs and due list"""
    # Get filter parameters
    status_filter = request.args.get('status', 'Active')
    search_query = request.args.get('search', '')
    
    # Base query
    query = EMI_Ledger.query
    
    # Apply status filter
    if status_filter and status_filter != 'All':
        query = query.filter(EMI_Ledger.status == status_filter)
    
    # Apply search filter (customer name or phone)
    if search_query:
        query = query.join(Sale).join(Customer).filter(
            db.or_(
                Customer.name.ilike(f'%{search_query}%'),
                Customer.phone.ilike(f'%{search_query}%')
            )
        )
    
    emi_ledgers = query.all()
    
    # Separate overdue EMIs
    overdue_emis = [emi for emi in emi_ledgers if emi.is_overdue()]
    
    # Calculate statistics
    total_active = EMI_Ledger.query.filter_by(status='Active').count()
    total_completed = EMI_Ledger.query.filter_by(status='Completed').count()
    total_defaulted = EMI_Ledger.query.filter_by(status='Defaulted').count()
    total_overdue = len([emi for emi in EMI_Ledger.query.filter_by(status='Active').all() if emi.is_overdue()])
    
    # Calculate total receivable amount
    active_emis = EMI_Ledger.query.filter_by(status='Active').all()
    total_receivable = sum(emi.calculate_remaining_amount() for emi in active_emis)
    
    return render_template('emi_dashboard.html',
                         emi_ledgers=emi_ledgers,
                         overdue_emis=overdue_emis,
                         status_filter=status_filter,
                         search_query=search_query,
                         total_active=total_active,
                         total_completed=total_completed,
                         total_defaulted=total_defaulted,
                         total_overdue=total_overdue,
                         total_receivable=total_receivable)


@emi_bp.route('/due-list')
def due_list():
    """Filter EMIs by due date"""
    # Get EMIs due this month
    today = datetime.now().date()
    end_of_month = today.replace(day=28) + timedelta(days=4)
    end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
    
    due_emis = EMI_Ledger.query.filter(
        EMI_Ledger.status == 'Active',
        EMI_Ledger.next_payment_date <= end_of_month
    ).all()
    
    return render_template('emi_due_list.html', due_emis=due_emis)


@emi_bp.route('/pay/<int:emi_id>', methods=['POST'])
def pay_installment(emi_id):
    """Record an installment payment"""
    try:
        emi_ledger = EMI_Ledger.query.get_or_404(emi_id)
        
        # Check if EMI is active
        if emi_ledger.status != 'Active':
            flash(f'এই EMI {emi_ledger.status} অবস্থায় আছে!', 'warning')
            return redirect(url_for('emi.dashboard'))
        
        # Check if already completed
        if emi_ledger.installments_paid >= emi_ledger.total_installments:
            flash('সমস্ত কিস্তি ইতিমধ্যে পরিশোধ করা হয়েছে!', 'info')
            return redirect(url_for('emi.dashboard'))
        
        # Record payment
        success = emi_ledger.pay_installment()
        
        if success:
            db.session.commit()
            
            customer_name = emi_ledger.sale.customer.name
            remaining = emi_ledger.total_installments - emi_ledger.installments_paid
            
            if emi_ledger.status == 'Completed':
                flash(f'{customer_name} এর সমস্ত কিস্তি সম্পন্ন হয়েছে! 🎉', 'success')
            else:
                flash(f'কিস্তি পরিশোধ সফল! অবশিষ্ট: {remaining} টি', 'success')
            
            return redirect(url_for('emi.receipt', emi_id=emi_id))
        else:
            flash('কিস্তি পরিশোধ ব্যর্থ!', 'danger')
        
    except Exception as e:
        db.session.rollback()
        flash(f'ত্রুটি: {str(e)}', 'danger')
    
    return redirect(url_for('emi.dashboard'))


@emi_bp.route('/receipt/<int:emi_id>')
def receipt(emi_id):
    """Generate payment receipt"""
    emi_ledger = EMI_Ledger.query.get_or_404(emi_id)
    return render_template('emi_receipt.html', emi_ledger=emi_ledger)


@emi_bp.route('/customer/<int:customer_id>')
def customer_emi_history(customer_id):
    """View customer's EMI history"""
    customer = Customer.query.get_or_404(customer_id)
    
    # Get all EMI sales for this customer
    emi_sales = Sale.query.filter_by(
        customer_id=customer_id,
        sale_type='EMI'
    ).all()
    
    return render_template('customer_emi_history.html', 
                         customer=customer, 
                         emi_sales=emi_sales)


@emi_bp.route('/mark-defaulted/<int:emi_id>', methods=['POST'])
def mark_defaulted(emi_id):
    """Mark an EMI as defaulted"""
    try:
        emi_ledger = EMI_Ledger.query.get_or_404(emi_id)
        
        if emi_ledger.status == 'Active':
            emi_ledger.mark_as_defaulted()
            db.session.commit()
            flash('EMI ডিফল্টেড হিসেবে চিহ্নিত করা হয়েছে!', 'warning')
        else:
            flash('শুধুমাত্র সক্রিয় EMI ডিফল্টেড করা যাবে!', 'danger')
        
    except Exception as e:
        db.session.rollback()
        flash(f'ত্রুটি: {str(e)}', 'danger')
    
    return redirect(url_for('emi.dashboard'))


@emi_bp.route('/api/emi/<int:emi_id>')
def get_emi_details(emi_id):
    """API endpoint to get EMI details"""
    emi_ledger = EMI_Ledger.query.get_or_404(emi_id)
    return jsonify(emi_ledger.to_dict())


@emi_bp.route('/api/stats')
def get_stats():
    """API endpoint for EMI statistics"""
    total_active = EMI_Ledger.query.filter_by(status='Active').count()
    total_completed = EMI_Ledger.query.filter_by(status='Completed').count()
    total_defaulted = EMI_Ledger.query.filter_by(status='Defaulted').count()
    
    active_emis = EMI_Ledger.query.filter_by(status='Active').all()
    total_receivable = sum(emi.calculate_remaining_amount() for emi in active_emis)
    total_overdue = len([emi for emi in active_emis if emi.is_overdue()])
    
    return jsonify({
        'total_active': total_active,
        'total_completed': total_completed,
        'total_defaulted': total_defaulted,
        'total_receivable': round(total_receivable, 2),
        'total_overdue': total_overdue
    })
