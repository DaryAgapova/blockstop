import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'db.sqlite3'))
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    FONTS_FOLDER = os.path.join(basedir, 'app', 'static', 'fonts')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Company requisites (for PDF invoices)
    COMPANY_NAME = 'ООО "МИР ПОЖАРНОЙ БЕЗОПАСНОСТИ"'
    COMPANY_INN = '3460083690'
    COMPANY_KPP = '346001001'
    COMPANY_OGRN = '1123460001234'
    COMPANY_ADDRESS = '400074, г. Волгоград, ул. Козака-Заклунного, д.44В, кв.3'
    COMPANY_PHONE = '8 917 837-37-52, (8442) 26-36-96'
    COMPANY_EMAIL = 'mpbv@yandex.ru'
    COMPANY_BANK = 'ПАО СБЕРБАНК г. Волгоград'
    COMPANY_BANK_ACCOUNT = '40702810800000000000'
    COMPANY_CORR_ACCOUNT = '30101810100000000602'
    COMPANY_BIK = '041806602'
