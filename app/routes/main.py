import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, abort, send_from_directory, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Category, Product, Order, OrderItem

main_bp = Blueprint('main', __name__)


# ── Home ───────────────────────────────────────────────────────────────────────

@main_bp.route('/')
def index():
    categories = Category.query.order_by(Category.sort_order).all()
    featured = Product.query.filter_by(featured=True, in_stock=True).limit(8).all()
    return render_template('index.html', categories=categories, featured=featured)


# ── Catalog ────────────────────────────────────────────────────────────────────

@main_bp.route('/catalog')
def catalog():
    cat_slug = request.args.get('cat')
    search   = request.args.get('q', '').strip()
    page     = request.args.get('page', 1, type=int)

    query = Product.query
    active_category = None

    if cat_slug:
        active_category = Category.query.filter_by(slug=cat_slug).first_or_404()
        query = query.filter_by(category_id=active_category.id)

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.order_by(Product.featured.desc(), Product.id.desc()).paginate(
        page=page, per_page=12, error_out=False
    )

    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('catalog.html',
                           products=products,
                           categories=categories,
                           active_category=active_category,
                           search=search)


# ── Product detail ─────────────────────────────────────────────────────────────

@main_bp.route('/product/<int:product_id>')
def product(product_id):
    p = Product.query.get_or_404(product_id)
    related = Product.query.filter(
        Product.category_id == p.category_id,
        Product.id != p.id
    ).limit(4).all()
    return render_template('product.html', product=p, related=related)


# ── Cart ────────────────────────────────────────────────────────────────────────

@main_bp.route('/cart')
def cart():
    cart_data = session.get('cart', {})
    items = []
    total = 0
    all_priced = True
    for prod_id_str, qty in cart_data.items():
        p = Product.query.get(int(prod_id_str))
        if p:
            subtotal = float(p.price) * qty if p.price else None
            if subtotal:
                total += subtotal
            else:
                all_priced = False
            items.append({'product': p, 'qty': qty, 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total if all_priced else None)


@main_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def cart_add(product_id):
    p = Product.query.get_or_404(product_id)
    qty = int(request.form.get('qty', 1))
    cart = session.get('cart', {})
    key = str(product_id)
    cart[key] = cart.get(key, 0) + qty
    session['cart'] = cart
    flash(f'«{p.name}» добавлен в корзину.', 'success')
    next_url = request.form.get('next') or request.referrer or url_for('main.catalog')
    return redirect(next_url)


@main_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
def cart_remove(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('main.cart'))


@main_bp.route('/cart/update', methods=['POST'])
def cart_update():
    cart = session.get('cart', {})
    for key in list(cart.keys()):
        qty = request.form.get(f'qty_{key}', type=int)
        if qty and qty > 0:
            cart[key] = qty
        elif qty == 0:
            cart.pop(key, None)
    session['cart'] = cart
    return redirect(url_for('main.cart'))


# ── Checkout / order placement ─────────────────────────────────────────────────

@main_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_data = session.get('cart', {})
    if not cart_data:
        flash('Корзина пуста.', 'warning')
        return redirect(url_for('main.catalog'))

    if request.method == 'POST':
        comment = request.form.get('comment', '').strip()

        order = Order(
            user_id=current_user.id,
            status='new',
            comment=comment,
            # Snapshot client data
            client_full_name=current_user.full_name,
            client_phone=current_user.phone,
            client_email=current_user.email,
            client_company=current_user.company_name,
            client_inn=current_user.inn,
            client_kpp=current_user.kpp,
            client_legal_address=current_user.legal_address,
            client_bank_name=current_user.bank_name,
            client_bank_account=current_user.bank_account,
            client_corr_account=current_user.corr_account,
            client_bik=current_user.bik,
        )
        db.session.add(order)
        db.session.flush()  # get order.id

        total = 0
        has_prices = True
        for prod_id_str, qty in cart_data.items():
            p = Product.query.get(int(prod_id_str))
            if not p:
                continue
            item = OrderItem(
                order_id=order.id,
                product_id=p.id,
                product_name=p.name,
                product_unit=p.unit,
                quantity=qty,
                price_at_order=p.price,
            )
            db.session.add(item)
            if p.price:
                total += float(p.price) * qty
            else:
                has_prices = False

        order.total_amount = total if has_prices else None
        db.session.commit()

        session.pop('cart', None)
        flash('Заявка успешно оформлена! Менеджер свяжется с вами после проверки.', 'success')
        return redirect(url_for('cabinet.order_detail', order_id=order.id))

    # Prefill form with user data
    return render_template('checkout.html', user=current_user, cart=cart_data)


# ── Static uploads ─────────────────────────────────────────────────────────────

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


# ── About / contacts ───────────────────────────────────────────────────────────

@main_bp.route('/contacts')
def contacts():
    return render_template('contacts.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')
