from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(30))
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user' | 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Client requisites (for invoice generation)
    company_name = db.Column(db.String(300))       # ФИО или название ООО/ИП
    inn = db.Column(db.String(20))
    kpp = db.Column(db.String(20))
    ogrn = db.Column(db.String(20))
    legal_address = db.Column(db.String(500))
    bank_name = db.Column(db.String(300))
    bank_account = db.Column(db.String(30))        # Расчётный счёт
    corr_account = db.Column(db.String(30))        # Корреспондентский счёт
    bik = db.Column(db.String(15))

    # Relations
    orders = db.relationship('Order', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100), default='fire')   # FontAwesome icon name
    image_filename = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2))            # None = цена по запросу
    unit = db.Column(db.String(30), default='шт.')
    image_filename = db.Column(db.String(255))
    in_stock = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')

    @property
    def price_display(self):
        if self.price is None:
            return 'По запросу'
        return f'{self.price:,.0f} ₽'.replace(',', ' ')

    def __repr__(self):
        return f'<Product {self.name}>'


# Order statuses
ORDER_STATUS = {
    'new': ('Новая', 'secondary'),
    'moderation': ('На модерации', 'warning'),
    'approved': ('Одобрена', 'info'),
    'invoice_sent': ('Счёт выставлен', 'primary'),
    'paid': ('Оплачено', 'success'),
    'completed': ('Выполнено', 'success'),
    'cancelled': ('Отменено', 'danger'),
}

ORDER_STATUS_FLOW = ['new', 'moderation', 'approved', 'invoice_sent', 'paid', 'completed']


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(30), default='new', nullable=False)

    # Client data snapshot at order time
    client_full_name = db.Column(db.String(200))
    client_phone = db.Column(db.String(30))
    client_email = db.Column(db.String(150))
    client_company = db.Column(db.String(300))
    client_inn = db.Column(db.String(20))
    client_kpp = db.Column(db.String(20))
    client_legal_address = db.Column(db.String(500))
    client_bank_name = db.Column(db.String(300))
    client_bank_account = db.Column(db.String(30))
    client_corr_account = db.Column(db.String(30))
    client_bik = db.Column(db.String(15))

    comment = db.Column(db.Text)                   # Комментарий клиента
    manager_comment = db.Column(db.Text)           # Комментарий менеджера
    total_amount = db.Column(db.Numeric(12, 2))
    invoice_pdf_filename = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy='select', cascade='all, delete-orphan')

    @property
    def status_label(self):
        return ORDER_STATUS.get(self.status, ('Неизвестно', 'secondary'))[0]

    @property
    def status_color(self):
        return ORDER_STATUS.get(self.status, ('Неизвестно', 'secondary'))[1]

    @property
    def total_display(self):
        if self.total_amount:
            return f'{self.total_amount:,.0f} ₽'.replace(',', ' ')
        return 'Не указана'

    def __repr__(self):
        return f'<Order #{self.id} {self.status}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)

    # Snapshot of product data at order time
    product_name = db.Column(db.String(300), nullable=False)
    product_unit = db.Column(db.String(30), default='шт.')
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_order = db.Column(db.Numeric(12, 2))   # None = по запросу

    @property
    def subtotal(self):
        if self.price_at_order and self.quantity:
            return self.price_at_order * self.quantity
        return None

    @property
    def subtotal_display(self):
        if self.subtotal:
            return f'{self.subtotal:,.0f} ₽'.replace(',', ' ')
        return 'По запросу'
