import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models import Order

cabinet_bp = Blueprint('cabinet', __name__)


@cabinet_bp.route('/')
@login_required
def index():
    return redirect(url_for('cabinet.orders'))


@cabinet_bp.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    user_orders = Order.query.filter_by(user_id=current_user.id)\
        .order_by(Order.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    return render_template('cabinet/orders.html', orders=user_orders)


@cabinet_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    return render_template('cabinet/order_detail.html', order=order)


@cabinet_bp.route('/orders/<int:order_id>/invoice')
@login_required
def download_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    if not order.invoice_pdf_filename:
        flash('Счёт ещё не сформирован.', 'warning')
        return redirect(url_for('cabinet.order_detail', order_id=order_id))
    invoices_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'invoices')
    return send_from_directory(invoices_dir, order.invoice_pdf_filename, as_attachment=True)


@cabinet_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name     = request.form.get('full_name', '').strip()
        current_user.phone         = request.form.get('phone', '').strip()
        current_user.company_name  = request.form.get('company_name', '').strip() or None
        current_user.inn           = request.form.get('inn', '').strip() or None
        current_user.kpp           = request.form.get('kpp', '').strip() or None
        current_user.ogrn          = request.form.get('ogrn', '').strip() or None
        current_user.legal_address = request.form.get('legal_address', '').strip() or None
        current_user.bank_name     = request.form.get('bank_name', '').strip() or None
        current_user.bank_account  = request.form.get('bank_account', '').strip() or None
        current_user.corr_account  = request.form.get('corr_account', '').strip() or None
        current_user.bik           = request.form.get('bik', '').strip() or None

        # Password change (optional)
        new_pass  = request.form.get('new_password', '')
        new_pass2 = request.form.get('new_password2', '')
        if new_pass:
            if len(new_pass) < 6:
                flash('Новый пароль должен быть не менее 6 символов.', 'danger')
                return redirect(url_for('cabinet.profile'))
            if new_pass != new_pass2:
                flash('Пароли не совпадают.', 'danger')
                return redirect(url_for('cabinet.profile'))
            current_user.set_password(new_pass)

        db.session.commit()
        flash('Профиль обновлён.', 'success')
        return redirect(url_for('cabinet.profile'))

    return render_template('cabinet/profile.html')
