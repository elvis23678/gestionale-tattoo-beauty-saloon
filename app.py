import csv
import io
import os
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-this')
raw_url = os.environ.get('DATABASE_URL', 'sqlite:///gestionale.db')
if raw_url.startswith('postgres://'):
    raw_url = raw_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif raw_url.startswith('postgresql://'):
    raw_url = raw_url.replace('postgresql://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = raw_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    email = db.Column(db.String(160))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(120), unique=True, nullable=False, index=True)
    brand_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10,2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=1)
    active = db.Column(db.Boolean, nullable=False, default=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    supplier = db.relationship('Supplier', backref='products')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', backref='sales')
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10,2), nullable=False)
    total = db.Column(db.Numeric(10,2), nullable=False)
    note = db.Column(db.String(250))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', backref='movements')
    movement_type = db.Column(db.String(20), nullable=False)
    quantity_delta = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(250))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

ITEMS = [('TX51210G', 1, 'CHM-001', 24.9), ('TX51210W', 1, 'CHM-002', 24.9), ('TXV50314G-PPPK', 1, 'CHM-003', 34.9), ('TXV50314-PPPK', 1, 'CHM-004', 34.9), ('TJV5016-1608', 1, 'CUR-001', 34.9), ('TL62-AQ1608', 1, 'TOP-001', 19.9), ('TCS30505-AQ1416', 1, 'EAR-001', 24.9), ('TA40701-1608LD', 1, 'CLK-001', 99.9), ('TA40701-1610LD', 1, 'CLK-002', 109.9), ('TA40701G-1610LD', 1, 'CLK-003', 114.9), ('TE01-163.5LD', 1, 'TOP-002', 79.9), ('HTL00-16104', 10, 'LAB-001', 14.9), ('HTM00-16083', 3, 'LAB-002', 9.9), ('TCS02-AB14125', 1, 'NIP-001', 19.9), ('TD08-140858', 5, 'BEL-001', 19.9), ('TD08-141058', 5, 'BEL-002', 19.9), ('TD08-AQ141046', 1, 'BEL-003', 24.9), ('TD08-PP141058', 1, 'BEL-004', 24.9), ('TD08-VM141058', 1, 'BEL-005', 24.9), ('TE01-162.5', 10, 'TOP-003', 9.9), ('TE01-163.5', 2, 'TOP-004', 12.9), ('TE01-1404', 2, 'TOP-005', 14.9), ('TG01-16', 10, 'TOOL-001', 7.9), ('TL08-16083', 10, 'LAB-003', 19.9), ('TL08G-16082.5', 2, 'LAB-004', 24.9), ('TL08G-16083', 2, 'LAB-005', 24.9), ('TA35-1608', 1, 'CLK-004', 39.9), ('TA35-1610', 1, 'CLK-005', 44.9), ('TA134G-1610', 1, 'CLK-006', 29.9), ('TA33-1605', 1, 'CLK-007', 24.9), ('TA33-1606', 1, 'CLK-008', 24.9), ('TA33-1607', 1, 'CLK-009', 24.9), ('TA33-1609', 1, 'CLK-010', 29.9), ('TA33-1612', 1, 'CLK-011', 29.9), ('TA33G-1605', 1, 'CLK-012', 29.9), ('TA33G-1608', 1, 'CLK-013', 29.9), ('TA33G-1612', 1, 'CLK-014', 34.9), ('TA39-1606', 1, 'CLK-015', 24.9), ('TA228G-1610', 1, 'CLK-016', 39.9), ('TA236-CL1610', 1, 'CLK-017', 34.9), ('TA3046G-1610', 1, 'CLK-018', 39.9), ('TA41205G-AQ1608', 1, 'CLK-019', 44.9), ('TA50709-AQCL1608', 1, 'CLK-020', 44.9), ('TAV40414G-1610', 1, 'CLK-021', 39.9), ('TAV40525G-1610', 1, 'CLK-022', 44.9), ('TAV50523G-GN1610', 1, 'CLK-023', 44.9), ('TD00-1410', 1, 'BEL-006', 29.9), ('TD00-AQ1410', 1, 'BEL-007', 34.9), ('TD00G-1410', 1, 'BEL-008', 34.9), ('TD00-SB1410', 1, 'BEL-009', 34.9), ('TD00-TAN1410', 1, 'BEL-010', 34.9), ('TD05-1412', 1, 'BEL-011', 24.9), ('TD15-AB1410', 1, 'BEL-012', 24.9), ('TDV5012G-PP1410', 1, 'BEL-013', 44.9), ('TDV5012-PP1410', 1, 'BEL-014', 39.9), ('TDV40424-1410', 1, 'BEL-015', 39.9)]

def category_from_code(code):
    return {'CHM':'Charm','CUR':'Curved','TOP':'Top','EAR':'Ear','CLK':'Clicker','LAB':'Labret','NIP':'Nipple','BEL':'Belly','TOOL':'Tool'}.get(code.split('-')[0], 'Altro')

def seed_if_empty():
    db.create_all()
    if Supplier.query.count() == 0:
        db.session.add(Supplier(name='Jutique', currency='USD'))
        db.session.commit()
    if Product.query.count() == 0:
        supplier = Supplier.query.filter_by(name='Jutique').first()
        for supplier_code, qty, brand_code, price in ITEMS:
            product = Product(supplier_code=supplier_code, brand_code=brand_code, category=category_from_code(brand_code), price=price, quantity=qty, supplier=supplier)
            db.session.add(product)
            db.session.flush()
            db.session.add(StockMovement(product_id=product.id, movement_type='CARICO_INIZIALE', quantity_delta=qty, note='Importazione primo ordine'))
        db.session.commit()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.before_request
def initialize_once():
    if not getattr(app, '_db_initialized', False):
        with app.app_context():
            seed_if_empty()
        app._db_initialized = True

@app.route('/health')
def health():
    return {'status':'ok'}, 200

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username','').strip()
        password = request.form.get('password','')
        expected_user = os.environ.get('ADMIN_USER', 'admin')
        password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        plain_password = os.environ.get('ADMIN_PASSWORD', 'cambia-subito')
        valid = user == expected_user and (check_password_hash(password_hash, password) if password_hash else password == plain_password)
        if valid:
            session.clear(); session['logged_in'] = True; session['username'] = user
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Credenziali non valide.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    products = Product.query.filter_by(active=True).count()
    pieces = db.session.query(func.coalesce(func.sum(Product.quantity),0)).scalar()
    low_stock = Product.query.filter(Product.active.is_(True), Product.quantity <= Product.reorder_level).count()
    revenue = db.session.query(func.coalesce(func.sum(Sale.total),0)).scalar()
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(8).all()
    return render_template('dashboard.html', products=products, pieces=pieces, low_stock=low_stock, revenue=revenue, recent_sales=recent_sales)

@app.route('/products')
@login_required
def products():
    q = request.args.get('q','').strip()
    query = Product.query
    if q:
        like = f'%{q}%'
        query = query.filter(or_(Product.brand_code.ilike(like), Product.supplier_code.ilike(like), Product.category.ilike(like)))
    rows = query.order_by(Product.brand_code).all()
    return render_template('products.html', rows=rows, q=q)

@app.route('/products/<int:product_id>/stock', methods=['POST'])
@login_required
def adjust_stock(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        delta = int(request.form.get('delta','0'))
    except ValueError:
        flash('Quantità non valida.', 'danger'); return redirect(url_for('products'))
    if delta == 0 or product.quantity + delta < 0:
        flash('Movimento non valido o giacenza insufficiente.', 'danger'); return redirect(url_for('products'))
    product.quantity += delta
    movement_type = 'CARICO' if delta > 0 else 'SCARICO'
    db.session.add(StockMovement(product_id=product.id, movement_type=movement_type, quantity_delta=delta, note=request.form.get('note','').strip()))
    db.session.commit(); flash('Giacenza aggiornata.', 'success')
    return redirect(url_for('products', q=request.args.get('q','')))

@app.route('/sales', methods=['GET','POST'])
@login_required
def sales():
    if request.method == 'POST':
        product = Product.query.get_or_404(int(request.form['product_id']))
        try:
            qty = int(request.form['quantity'])
        except ValueError:
            qty = 0
        if qty <= 0 or qty > product.quantity:
            flash('Quantità non valida o giacenza insufficiente.', 'danger'); return redirect(url_for('sales'))
        unit_price = product.price
        total = unit_price * qty
        sale = Sale(product=product, quantity=qty, unit_price=unit_price, total=total, note=request.form.get('note','').strip())
        product.quantity -= qty
        db.session.add(sale); db.session.flush()
        db.session.add(StockMovement(product_id=product.id, movement_type='VENDITA', quantity_delta=-qty, note=f'Vendita #{sale.id}'))
        db.session.commit(); flash('Vendita registrata e magazzino aggiornato.', 'success')
        return redirect(url_for('sales'))
    rows = Sale.query.order_by(Sale.created_at.desc()).limit(100).all()
    products = Product.query.filter(Product.active.is_(True), Product.quantity > 0).order_by(Product.brand_code).all()
    return render_template('sales.html', rows=rows, products=products)

@app.route('/suppliers', methods=['GET','POST'])
@login_required
def suppliers():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if name and not Supplier.query.filter_by(name=name).first():
            db.session.add(Supplier(name=name, currency=request.form.get('currency','EUR')[:3].upper(), email=request.form.get('email','').strip(), notes=request.form.get('notes','').strip()))
            db.session.commit(); flash('Fornitore aggiunto.', 'success')
        else:
            flash('Nome mancante o fornitore già presente.', 'danger')
        return redirect(url_for('suppliers'))
    return render_template('suppliers.html', rows=Supplier.query.order_by(Supplier.name).all())

@app.route('/movements')
@login_required
def movements():
    rows = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(200).all()
    return render_template('movements.html', rows=rows)

@app.route('/export/products.csv')
@login_required
def export_products():
    output = io.StringIO(); writer = csv.writer(output, delimiter=';')
    writer.writerow(['Codice fornitore','Quantità','Codice brand','Categoria','Prezzo','Fornitore'])
    for p in Product.query.order_by(Product.brand_code):
        writer.writerow([p.supplier_code,p.quantity,p.brand_code,p.category,f'{p.price:.2f}',p.supplier.name])
    return Response('\ufeff'+output.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=prodotti.csv'})

@app.template_filter('eur')
def eur(value):
    return ('€ {:,.2f}'.format(float(value))).replace(',', 'X').replace('.', ',').replace('X','.')

if __name__ == '__main__':
    with app.app_context(): seed_if_empty()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=os.environ.get('FLASK_DEBUG') == '1')
