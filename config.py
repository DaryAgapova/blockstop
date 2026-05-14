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
    COMPANY_NAME = 'ООО "Мир Пожарной Безопасности"'
    COMPANY_INN = '3460083690'
    COMPANY_KPP = '346001001'
    COMPANY_OGRN = '1233400000877'
    COMPANY_ADDRESS = '400074, Волгоградская область, г. Волгоград, ул. Рабоче-Крестьянская, вл.д. 44В, офис 10'
    COMPANY_PHONE = '8(8442)26-36-96; 8(8442)98-40-51; 8(8442)98-17-74'
    COMPANY_EMAIL = 'mpbv@yandex.ru'
    COMPANY_BANK = 'ФИЛИАЛ "ЦЕНТРАЛЬНЫЙ" БАНКА ВТБ (ПАО)'
    COMPANY_BANK_ACCOUNT = '40702810406720000090'
    COMPANY_CORR_ACCOUNT = '30101810145250000411'
    COMPANY_BIK = '044525411'
    COMPANY_OKVD = '46.69'
    COMPANY_OKPO = '83230772'
    COMPANY_DIRECTOR = 'Шадрина Юлия Юрьевна'
    COMPANY_ACCOUNTANT = 'Шадрина Юлия Юрьевна'
    COMPANY_DIRECTOR_TITLE = 'Директор'
