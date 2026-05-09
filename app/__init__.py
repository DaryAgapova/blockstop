import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class is None:
        from config import Config
        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)

    # Ensure upload folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['FONTS_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'invoices'), exist_ok=True)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Войдите в аккаунт для доступа к этой странице.'
    login_manager.login_message_category = 'warning'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.cabinet import cabinet_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cabinet_bp, url_prefix='/cabinet')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Jinja2 global helpers
    @app.template_filter('money')
    def money_filter(value):
        if value is None:
            return 'По запросу'
        return '{:,.0f}'.format(float(value)).replace(',', ' ') + ' ₽'

    @app.context_processor
    def inject_globals():
        from app.models import Category
        categories = Category.query.order_by(Category.sort_order).all()
        cart = {}
        from flask import session
        cart_items = session.get('cart', {})
        cart_count = sum(v for v in cart_items.values())
        return {
            'nav_categories': categories,
            'cart_count': cart_count,
        }

    return app
