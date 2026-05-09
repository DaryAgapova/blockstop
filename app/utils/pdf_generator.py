import os
import urllib.request
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

FONT_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts')
FONT_REGULAR = os.path.join(FONT_DIR, 'DejaVuSans.ttf')
FONT_BOLD    = os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf')

FONT_URLS = {
    FONT_REGULAR: 'https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf',
    FONT_BOLD:    'https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf',
}

_fonts_registered = False

def _ensure_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    os.makedirs(FONT_DIR, exist_ok=True)
    for path, url in FONT_URLS.items():
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve(url, path)
            except Exception as e:
                print(f'[PDF] Cannot download font: {e}')
    try:
        pdfmetrics.registerFont(TTFont('DVR', FONT_REGULAR))
        pdfmetrics.registerFont(TTFont('DVB', FONT_BOLD))
        registerFontFamily('DV', normal='DVR', bold='DVB', italic='DVR', boldItalic='DVB')
    except Exception as e:
        print(f'[PDF] Font registration error: {e}')
    _fonts_registered = True

def _style(size=9, bold=False, color=colors.black, align='LEFT'):
    fn = 'DVB' if bold else 'DVR'
    al = {'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}.get(align, 0)
    return ParagraphStyle('s', fontName=fn, fontSize=size,
                          textColor=color, alignment=al, leading=size * 1.4)

def generate_invoice(order, invoice_path):
    _ensure_fonts()

    from flask import current_app
    cfg = current_app.config

    doc = SimpleDocTemplate(invoice_path, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    W = A4[0] - 30*mm

    RED   = colors.HexColor('#C0392B')
    NAVY  = colors.HexColor('#1a2744')
    LGREY = colors.HexColor('#F2F2F2')
    DGREY = colors.HexColor('#555555')

    story = []

    # ── Шапка ──────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(cfg['COMPANY_NAME'], _style(11, bold=True, color=RED)),
        Paragraph(
            f'ИНН {cfg["COMPANY_INN"]} / КПП {cfg["COMPANY_KPP"]}\n'
            f'ОГРН {cfg["COMPANY_OGRN"]}\n'
            f'{cfg["COMPANY_ADDRESS"]}\n'
            f'Тел.: {cfg["COMPANY_PHONE"]}\n'
            f'Email: {cfg["COMPANY_EMAIL"]}',
            _style(7.5, color=DGREY)
        )
    ]]
    t = Table(header_data, colWidths=[W*0.45, W*0.55])
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                            ('TOPPADDING',(0,0),(-1,-1),0),
                            ('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width=W, thickness=2, color=RED, spaceAfter=3*mm))

    # ── Банк ───────────────────────────────────────────────────────────────
    bank_data = [[
        Paragraph('Банк поставщика:', _style(7.5, color=DGREY)),
        Paragraph(
            f'{cfg["COMPANY_BANK"]}\n'
            f'р/с {cfg["COMPANY_BANK_ACCOUNT"]}\n'
            f'к/с {cfg["COMPANY_CORR_ACCOUNT"]}  БИК {cfg["COMPANY_BIK"]}',
            _style(7.5)
        )
    ]]
    bt = Table(bank_data, colWidths=[W*0.25, W*0.75])
    bt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                             ('TOPPADDING',(0,0),(-1,-1),1),
                             ('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    story.append(bt)
    story.append(HRFlowable(width=W, thickness=0.5, color=colors.grey, spaceAfter=5*mm))

    # ── Заголовок ──────────────────────────────────────────────────────────
    invoice_date = (order.updated_at or order.created_at).strftime('%d.%m.%Y')
    story.append(Paragraph(
        f'СЧЁТ НА ОПЛАТУ № {order.id} от {invoice_date} г.',
        _style(14, bold=True, align='CENTER', color=NAVY)
    ))
    story.append(Spacer(1, 4*mm))

    # ── Стороны ────────────────────────────────────────────────────────────
    def party_block(label, rows):
        data = [[Paragraph(label, _style(8, bold=True, color=NAVY))]]
        for k, v in rows:
            data.append([Paragraph(f'{k}: {v or "—"}', _style(7.5))])
        tbl = Table(data, colWidths=[W])
        tbl.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.5,colors.grey),
            ('BACKGROUND',(0,0),(-1,0),LGREY),
            ('TOPPADDING',(0,0),(-1,-1),3),
            ('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),6),
        ]))
        return tbl

    story.append(party_block('Поставщик', [
        ('Наименование', cfg['COMPANY_NAME']),
        ('ИНН/КПП', f'{cfg["COMPANY_INN"]} / {cfg["COMPANY_KPP"]}'),
        ('Адрес', cfg['COMPANY_ADDRESS']),
    ]))
    story.append(Spacer(1, 2*mm))
    story.append(party_block('Покупатель', [
        ('Наименование', order.client_company or order.client_full_name),
        ('ФИО', order.client_full_name),
        ('ИНН/КПП', f'{order.client_inn or "—"} / {order.client_kpp or "—"}'),
        ('Адрес', order.client_legal_address),
        ('Банк', order.client_bank_name),
        ('р/с', order.client_bank_account),
        ('к/с', order.client_corr_account),
        ('БИК', order.client_bik),
    ]))
    story.append(Spacer(1, 5*mm))

    # ── Таблица позиций ────────────────────────────────────────────────────
    col_w = [W*0.05, W*0.42, W*0.10, W*0.13, W*0.15, W*0.15]
    rows = [[
        Paragraph('№',            _style(8, bold=True, align='CENTER')),
        Paragraph('Наименование', _style(8, bold=True)),
        Paragraph('Ед.',          _style(8, bold=True, align='CENTER')),
        Paragraph('Кол-во',       _style(8, bold=True, align='CENTER')),
        Paragraph('Цена, руб.',   _style(8, bold=True, align='CENTER')),
        Paragraph('Сумма, руб.',  _style(8, bold=True, align='CENTER')),
    ]]

    grand_total = 0
    all_priced = True

    for i, item in enumerate(order.items, 1):
        if item.price_at_order:
            price_s = '{:,.2f}'.format(float(item.price_at_order)).replace(',', ' ')
            sub_s   = '{:,.2f}'.format(float(item.subtotal)).replace(',', ' ')
            grand_total += float(item.subtotal)
        else:
            price_s = 'По запросу'
            sub_s   = 'По запросу'
            all_priced = False

        rows.append([
            Paragraph(str(i),             _style(8, align='CENTER')),
            Paragraph(item.product_name,  _style(8)),
            Paragraph(item.product_unit,  _style(8, align='CENTER')),
            Paragraph(str(item.quantity), _style(8, align='CENTER')),
            Paragraph(price_s,            _style(8, align='CENTER')),
            Paragraph(sub_s,              _style(8, align='CENTER')),
        ])

    total_s = '{:,.2f} руб.'.format(grand_total).replace(',', ' ') if all_priced else 'По запросу'
    rows.append([
        Paragraph('', _style(8)),
        Paragraph('ИТОГО:', _style(9, bold=True, align='RIGHT')),
        Paragraph('', _style(8)),
        Paragraph('', _style(8)),
        Paragraph('', _style(8)),
        Paragraph(total_s, _style(9, bold=True, align='CENTER')),
    ])

    items_tbl = Table(rows, colWidths=col_w, repeatRows=1)
    items_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), NAVY),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('GRID',(0,0),(-1,-2), 0.4, colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-2), [colors.white, LGREY]),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),4),
        ('BACKGROUND',(0,-1),(-1,-1), colors.HexColor('#EEF2FF')),
        ('SPAN',(1,-1),(4,-1)),
        ('LINEABOVE',(0,-1),(-1,-1),1,NAVY),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Подвал ─────────────────────────────────────────────────────────────
    story.append(Paragraph(
        'Оплата данного счёта означает согласие с условиями поставки товара. '
        'Счёт действителен в течение 14 банковских дней.',
        _style(7.5, color=DGREY)
    ))
    story.append(Spacer(1, 6*mm))

    sig_data = [[
        Paragraph('Руководитель: ___________________________', _style(8)),
        Paragraph('М.П.', _style(8, align='CENTER')),
        Paragraph('Бухгалтер: ______________________________', _style(8, align='RIGHT')),
    ]]
    sig_tbl = Table(sig_data, colWidths=[W*0.45, W*0.10, W*0.45])
    sig_tbl.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(sig_tbl)

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        f'Сформировано {datetime.utcnow().strftime("%d.%m.%Y %H:%M")} UTC',
        _style(7, color=colors.lightgrey, align='RIGHT')
    ))

    doc.build(story)
    return invoice_path
