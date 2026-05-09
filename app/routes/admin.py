import os
import uuid
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, abort, send_from_directory)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Category, Product, Order, ORDER_STATUS, ORDER_STATUS_FLOW

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return login_required(decorated)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file, subfolder='products'):
    if not file or not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'{uuid.uuid4().hex}.{ext}'
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return f'{subfolder}/{filename}'


# ── Dashboard ──────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_required
def dashboard():
    from app.models import User
    stats = {
        'orders_new':      Order.query.filter_by(status='new').count(),
        'orders_total':    Order.query.count(),
        'products_total':  Product.query.count(),
        'users_total':     User.query.filter_by(role='user').count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)


# ── Orders ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/orders')
@admin_required
def orders():
    status = request.args.get('status', '')
    page   = request.args.get('page', 1, type=int)
    query  = Order.query
    if status:
        query = query.filter_by(status=status)
    orders_pag = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/orders.html',
                           orders=orders_pag,
                           statuses=ORDER_STATUS,
                           active_status=status)


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html',
                           order=order,
                           statuses=ORDER_STATUS,
                           status_flow=ORDER_STATUS_FLOW)


@admin_bp.route('/orders/<int:order_id>/set-status', methods=['POST'])
@admin_required
def order_set_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status not in ORDER_STATUS:
        flash('Неверный статус.', 'danger')
        return redirect(url_for('admin.order_detail', order_id=order_id))
    order.status = new_status
    order.manager_comment = request.form.get('manager_comment', order.manager_comment)
    order.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Статус заказа #{order.id} изменён на «{ORDER_STATUS[new_status][0]}».', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/orders/<int:order_id>/generate-invoice', methods=['POST'])
@admin_required
def generate_invoice(order_id):
    order = Order.query.get_or_404(order_id)

    # Update prices if manager filled them in
    for item in order.items:
        field = f'price_{item.id}'
        price_val = request.form.get(field)
        if price_val:
            try:
                item.price_at_order = float(price_val.replace(',', '.').replace(' ', ''))
            except ValueError:
                pass

    # Recalculate total
    total = 0
    all_priced = True
    for item in order.items:
        if item.price_at_order:
            total += float(item.price_at_order) * item.quantity
        else:
            all_priced = False
    order.total_amount = total if all_priced else None

    # Manager comment
    order.manager_comment = request.form.get('manager_comment', order.manager_comment)
    order.updated_at = datetime.utcnow()
    db.session.flush()

    # Generate PDF
    from app.utils.pdf_generator import generate_invoice as gen_pdf
    invoices_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'invoices')
    os.makedirs(invoices_dir, exist_ok=True)
    filename = f'invoice_{order.id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.pdf'
    filepath = os.path.join(invoices_dir, filename)

    try:
        gen_pdf(order, filepath)
        order.invoice_pdf_filename = filename
        order.status = 'invoice_sent'
        db.session.commit()
        flash(f'Счёт для заказа #{order.id} сформирован и доступен клиенту в личном кабинете.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при генерации PDF: {e}', 'danger')

    return redirect(url_for('admin.order_detail', order_id=order_id))


# ── Products ───────────────────────────────────────────────────────────────────

@admin_bp.route('/products')
@admin_required
def products():
    cat_id = request.args.get('cat', type=int)
    page   = request.args.get('page', 1, type=int)
    query  = Product.query
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    prods = query.order_by(Product.id.desc()).paginate(page=page, per_page=20, error_out=False)
    cats  = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/products.html', products=prods, categories=cats, active_cat=cat_id)


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def product_new():
    cats = Category.query.order_by(Category.sort_order).all()
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()
        price_str   = request.form.get('price', '').strip()
        unit        = request.form.get('unit', 'шт.').strip()
        in_stock    = bool(request.form.get('in_stock'))
        featured    = bool(request.form.get('featured'))

        if not name or not category_id:
            flash('Название и категория обязательны.', 'danger')
            return render_template('admin/product_form.html', categories=cats, product=None)

        price = None
        if price_str:
            try:
                price = float(price_str.replace(',', '.').replace(' ', ''))
            except ValueError:
                flash('Неверный формат цены.', 'danger')
                return render_template('admin/product_form.html', categories=cats, product=None)

        image_filename = None
        if 'image' in request.files:
            image_filename = save_image(request.files['image'])

        product = Product(
            name=name, category_id=category_id, description=description,
            price=price, unit=unit, in_stock=in_stock, featured=featured,
            image_filename=image_filename,
        )
        db.session.add(product)
        db.session.commit()
        flash('Товар добавлен.', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', categories=cats, product=None)


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    cats = Category.query.order_by(Category.sort_order).all()

    if request.method == 'POST':
        product.name        = request.form.get('name', '').strip()
        product.category_id = request.form.get('category_id', type=int)
        product.description = request.form.get('description', '').strip()
        price_str           = request.form.get('price', '').strip()
        product.unit        = request.form.get('unit', 'шт.').strip()
        product.in_stock    = bool(request.form.get('in_stock'))
        product.featured    = bool(request.form.get('featured'))

        product.price = None
        if price_str:
            try:
                product.price = float(price_str.replace(',', '.').replace(' ', ''))
            except ValueError:
                flash('Неверный формат цены.', 'danger')
                return render_template('admin/product_form.html', categories=cats, product=product)

        if 'image' in request.files and request.files['image'].filename:
            new_img = save_image(request.files['image'])
            if new_img:
                product.image_filename = new_img

        db.session.commit()
        flash('Товар обновлён.', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', categories=cats, product=product)


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Товар удалён.', 'success')
    return redirect(url_for('admin.products'))


# ── Categories ─────────────────────────────────────────────────────────────────

@admin_bp.route('/categories')
@admin_required
def categories():
    cats = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@admin_required
def category_new():
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        slug       = request.form.get('slug', '').strip()
        desc       = request.form.get('description', '').strip()
        icon       = request.form.get('icon', 'fire').strip()
        sort_order = request.form.get('sort_order', 0, type=int)

        if not name or not slug:
            flash('Название и slug обязательны.', 'danger')
        elif Category.query.filter_by(slug=slug).first():
            flash('Slug уже занят.', 'danger')
        else:
            cat = Category(name=name, slug=slug, description=desc, icon=icon, sort_order=sort_order)
            db.session.add(cat)
            db.session.commit()
            flash('Категория добавлена.', 'success')
            return redirect(url_for('admin.categories'))

    return render_template('admin/category_form.html', category=None)


@admin_bp.route('/categories/<int:cat_id>/edit', methods=['GET', 'POST'])
@admin_required
def category_edit(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if request.method == 'POST':
        cat.name        = request.form.get('name', '').strip()
        cat.slug        = request.form.get('slug', '').strip()
        cat.description = request.form.get('description', '').strip()
        cat.icon        = request.form.get('icon', 'fire').strip()
        cat.sort_order  = request.form.get('sort_order', 0, type=int)
        db.session.commit()
        flash('Категория обновлена.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=cat)


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@admin_required
def category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.products.count() > 0:
        flash('Нельзя удалить категорию с товарами.', 'danger')
        return redirect(url_for('admin.categories'))
    db.session.delete(cat)
    db.session.commit()
    flash('Категория удалена.', 'success')
    return redirect(url_for('admin.categories'))
