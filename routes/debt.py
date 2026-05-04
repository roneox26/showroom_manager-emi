from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.debt import DebtRecord
from database import db
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename

debt_bp = Blueprint('debt', __name__, url_prefix='/debt')

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/debt_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@debt_bp.route('/')
def index():
    """Display all debt records"""
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = DebtRecord.query
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search:
        query = query.filter(
            (DebtRecord.name.ilike(f'%{search}%')) |
            (DebtRecord.phone.ilike(f'%{search}%'))
        )
    
    records = query.order_by(DebtRecord.due_date.asc()).all()
    
    # Calculate statistics
    total_amount = sum(r.amount for r in DebtRecord.query.all())
    total_paid = sum(r.paid_amount for r in DebtRecord.query.all())
    total_pending = total_amount - total_paid
    overdue_count = len([r for r in records if r.is_overdue])
    
    stats = {
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'overdue_count': overdue_count
    }
    
    return render_template('debt/index.html', records=records, stats=stats, 
                         status_filter=status_filter, search=search)


@debt_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Add new debt record"""
    if request.method == 'POST':
        try:
            # Handle file upload
            photo_filename = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add timestamp to filename to make it unique
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    photo_filename = f"{timestamp}_{filename}"
                    
                    # Create upload directory if it doesn't exist
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, photo_filename))
            
            # Create new record
            record = DebtRecord(
                name=request.form['name'],
                phone=request.form['phone'],
                address=request.form.get('address', ''),
                amount=float(request.form['amount']),
                due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d').date(),
                photo=photo_filename,
                notes=request.form.get('notes', '')
            )
            
            db.session.add(record)
            db.session.commit()
            
            flash(f'লেনদেন রেকর্ড যোগ করা হয়েছে: {record.name}', 'success')
            return redirect(url_for('debt.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('debt/add.html')


@debt_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Edit existing debt record"""
    record = DebtRecord.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            record.name = request.form['name']
            record.phone = request.form['phone']
            record.address = request.form.get('address', '')
            record.amount = float(request.form['amount'])
            record.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
            record.notes = request.form.get('notes', '')
            
            # Handle photo update
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old photo if exists
                    if record.photo:
                        old_photo_path = os.path.join(UPLOAD_FOLDER, record.photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    photo_filename = f"{timestamp}_{filename}"
                    
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, photo_filename))
                    record.photo = photo_filename
            
            db.session.commit()
            flash('রেকর্ড আপডেট করা হয়েছে', 'success')
            return redirect(url_for('debt.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('debt/edit.html', record=record)


@debt_bp.route('/payment/<int:id>', methods=['GET', 'POST'])
def payment(id):
    """Record payment for a debt"""
    record = DebtRecord.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            payment_amount = float(request.form['payment_amount'])
            
            if payment_amount <= 0:
                flash('পেমেন্ট পরিমাণ ০ এর বেশি হতে হবে', 'error')
                return redirect(url_for('debt.payment', id=id))
            
            if payment_amount > record.remaining_amount:
                flash('পেমেন্ট পরিমাণ বাকি টাকার চেয়ে বেশি হতে পারবে না', 'error')
                return redirect(url_for('debt.payment', id=id))
            
            record.paid_amount += payment_amount
            
            # Update status
            if record.paid_amount >= record.amount:
                record.status = 'paid'
            elif record.paid_amount > 0:
                record.status = 'partial'
            
            db.session.commit()
            flash(f'পেমেন্ট রেকর্ড করা হয়েছে: ৳{payment_amount}', 'success')
            return redirect(url_for('debt.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('debt/payment.html', record=record)


@debt_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Delete debt record"""
    record = DebtRecord.query.get_or_404(id)
    
    try:
        # Delete photo if exists
        if record.photo:
            photo_path = os.path.join(UPLOAD_FOLDER, record.photo)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        db.session.delete(record)
        db.session.commit()
        flash('রেকর্ড মুছে ফেলা হয়েছে', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('debt.index'))


@debt_bp.route('/view/<int:id>')
def view(id):
    """View detailed debt record"""
    record = DebtRecord.query.get_or_404(id)
    return render_template('debt/view.html', record=record)


@debt_bp.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    records = DebtRecord.query.all()
    
    stats = {
        'total_records': len(records),
        'total_amount': sum(r.amount for r in records),
        'total_paid': sum(r.paid_amount for r in records),
        'total_pending': sum(r.remaining_amount for r in records),
        'overdue_count': len([r for r in records if r.is_overdue]),
        'paid_count': len([r for r in records if r.status == 'paid']),
        'pending_count': len([r for r in records if r.status == 'pending'])
    }
    
    return jsonify(stats)
