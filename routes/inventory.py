from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import db
from models.product import Product
from config import Config

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


@inventory_bp.route('/')
def index():
    """Display all products with stock levels"""
    # Get search query if any
    search_query = request.args.get('search', '')
    
    if search_query:
        products = Product.query.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.model.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        products = Product.query.all()
    
    # Separate low stock products
    low_stock_products = [p for p in products if p.is_low_stock(Config.LOW_STOCK_THRESHOLD)]
    
    return render_template('inventory.html', 
                         products=products, 
                         low_stock_products=low_stock_products,
                         low_stock_threshold=Config.LOW_STOCK_THRESHOLD)


@inventory_bp.route('/add', methods=['POST'])
def add_product():
    """Add a new product to inventory"""
    try:
        name = request.form.get('name')
        model = request.form.get('model')
        buying_price = float(request.form.get('buying_price'))
        selling_price = float(request.form.get('selling_price'))
        stock_quantity = int(request.form.get('stock_quantity', 0))
        
        # Validation
        if not name or not model:
            flash('পণ্যের নাম এবং মডেল আবশ্যক!', 'danger')
            return redirect(url_for('inventory.index'))
        
        if buying_price <= 0 or selling_price <= 0:
            flash('মূল্য অবশ্যই শূন্যের চেয়ে বেশি হতে হবে!', 'danger')
            return redirect(url_for('inventory.index'))
        
        if selling_price < buying_price:
            flash('বিক্রয় মূল্য ক্রয় মূল্যের চেয়ে কম হতে পারে না!', 'warning')
        
        # Create new product
        product = Product(
            name=name,
            model=model,
            buying_price=buying_price,
            selling_price=selling_price,
            stock_quantity=stock_quantity
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash(f'পণ্য "{name}" সফলভাবে যোগ করা হয়েছে!', 'success')
        
    except ValueError:
        flash('অবৈধ মূল্য বা স্টক সংখ্যা!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'ত্রুটি: {str(e)}', 'danger')
    
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/update/<int:product_id>', methods=['POST'])
def update_product(product_id):
    """Update product details and stock"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Update fields if provided
        if 'name' in request.form:
            product.name = request.form.get('name')
        if 'model' in request.form:
            product.model = request.form.get('model')
        if 'buying_price' in request.form:
            product.buying_price = float(request.form.get('buying_price'))
        if 'selling_price' in request.form:
            product.selling_price = float(request.form.get('selling_price'))
        if 'stock_quantity' in request.form:
            product.stock_quantity = int(request.form.get('stock_quantity'))
        
        db.session.commit()
        flash(f'পণ্য "{product.name}" আপডেট করা হয়েছে!', 'success')
        
    except ValueError:
        flash('অবৈধ মূল্য বা স্টক সংখ্যা!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'ত্রুটি: {str(e)}', 'danger')
    
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    """Delete a product"""
    try:
        product = Product.query.get_or_404(product_id)
        product_name = product.name
        
        # Check if product has sales
        if product.sales:
            flash(f'পণ্য "{product_name}" মুছে ফেলা যাবে না কারণ এটির বিক্রয় রেকর্ড রয়েছে!', 'danger')
            return redirect(url_for('inventory.index'))
        
        db.session.delete(product)
        db.session.commit()
        
        flash(f'পণ্য "{product_name}" মুছে ফেলা হয়েছে!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'ত্রুটি: {str(e)}', 'danger')
    
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/low-stock')
def low_stock():
    """View products with low stock"""
    products = Product.query.all()
    low_stock_products = [p for p in products if p.is_low_stock(Config.LOW_STOCK_THRESHOLD)]
    
    return render_template('inventory.html', 
                         products=low_stock_products, 
                         low_stock_products=low_stock_products,
                         low_stock_threshold=Config.LOW_STOCK_THRESHOLD,
                         show_low_stock_only=True)


@inventory_bp.route('/api/product/<int:product_id>')
def get_product_api(product_id):
    """API endpoint to get product details"""
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())
