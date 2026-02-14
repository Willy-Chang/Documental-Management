"""PDF 文件生成引擎 — 使用 reportlab 生成報價單 / 發票 / 請購單等業務文件"""
import os
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm, cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from config import COMPANY_NAME


def _register_font():
    """嘗試註冊中文字型"""
    font_paths = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        'C:/Windows/Fonts/msjh.ttc',
        'C:/Windows/Fonts/mingliu.ttc',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', fp))
                return 'ChineseFont'
            except Exception:
                continue
    return 'Helvetica'


def _get_styles(font_name):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ChTitle', fontName=font_name, fontSize=16,
        leading=20, alignment=1, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='ChSubTitle', fontName=font_name, fontSize=10,
        leading=14, alignment=1, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name='ChNormal', fontName=font_name, fontSize=9,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name='ChSmall', fontName=font_name, fontSize=8,
        leading=10
    ))
    return styles


def generate_quotation_pdf(filepath, quotation, items, client_name=''):
    """生成報價單 PDF"""
    if not HAS_REPORTLAB:
        raise RuntimeError("需要安裝 reportlab 套件才能生成 PDF")

    font_name = _register_font()
    styles = _get_styles(font_name)
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=1.5*cm, rightMargin=1.5*cm)
    elements = []

    # 表頭
    elements.append(Paragraph(COMPANY_NAME, styles['ChTitle']))
    elements.append(Paragraph('報 價 單', styles['ChSubTitle']))
    elements.append(Spacer(1, 4*mm))

    # 基本資訊表格
    info_data = [
        [f'報價單號：{quotation["quotation_number"]}',
         f'日期：{quotation["created_at"][:10] if quotation["created_at"] else ""}'],
        [f'客戶名稱：{client_name}',
         f'幣別：{quotation.get("currency", "TWD")}'],
        [f'主旨：{quotation.get("subject", "") or ""}',
         f'有效天數：{quotation.get("validity_days", 30)} 天'],
        [f'付款條件：{quotation.get("payment_terms", "") or ""}',
         f'交貨條件：{quotation.get("delivery_terms", "") or ""}'],
    ]
    info_table = Table(info_data, colWidths=[doc.width/2]*2)
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4*mm))

    # 品項表格
    header = ['項次', '料號', '品名規格', '數量', '單位', '單價', '小計']
    item_data = [header]
    total = 0
    for item in items:
        qty = float(item['quantity'] or 0)
        price = float(item['unit_price'] or 0)
        amount = qty * price
        total += amount
        desc = item['description'] or ''
        if item.get('specification'):
            desc += f"\n{item['specification']}"
        item_data.append([
            str(item['item_no']),
            item.get('part_number', '') or '',
            desc,
            f'{qty:,.2f}',
            item.get('unit', 'PCS'),
            f'{price:,.2f}',
            f'{amount:,.2f}',
        ])

    tax_rate = float(quotation.get('tax_rate', 0.05) or 0)
    tax = round(total * tax_rate, 2)
    grand_total = total + tax

    item_data.append(['', '', '', '', '', '小計', f'{total:,.2f}'])
    item_data.append(['', '', '', '', '', f'稅金 ({tax_rate*100:.0f}%)', f'{tax:,.2f}'])
    item_data.append(['', '', '', '', '', '合計', f'{grand_total:,.2f}'])

    col_widths = [30, 60, 180, 50, 35, 60, 70]
    item_table = Table(item_data, colWidths=col_widths, repeatRows=1)
    item_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B9BD5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('ALIGN', (5, 1), (6, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('LINEABOVE', (5, -3), (6, -3), 1, colors.black),
        ('LINEABOVE', (5, -1), (6, -1), 1.5, colors.black),
        ('FONTSIZE', (5, -3), (6, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(item_table)

    # 備註
    if quotation.get('notes'):
        elements.append(Spacer(1, 6*mm))
        elements.append(Paragraph(f'備註：{quotation["notes"]}', styles['ChNormal']))

    doc.build(elements)
    return filepath


def generate_invoice_pdf(filepath, invoice, items, client_name=''):
    """生成發票 PDF"""
    if not HAS_REPORTLAB:
        raise RuntimeError("需要安裝 reportlab 套件才能生成 PDF")

    font_name = _register_font()
    styles = _get_styles(font_name)
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=1.5*cm, rightMargin=1.5*cm)
    elements = []

    elements.append(Paragraph(COMPANY_NAME, styles['ChTitle']))
    elements.append(Paragraph('發 票', styles['ChSubTitle']))
    elements.append(Spacer(1, 4*mm))

    info_data = [
        [f'發票號碼：{invoice["invoice_number"]}',
         f'開票日期：{invoice.get("invoice_date", "")}'],
        [f'客戶名稱：{client_name}',
         f'幣別：{invoice.get("currency", "TWD")}'],
        [f'到期日：{invoice.get("due_date", "") or ""}',
         f'付款狀態：{invoice.get("payment_status", "未付")}'],
    ]
    info_table = Table(info_data, colWidths=[doc.width/2]*2)
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4*mm))

    header = ['項次', '品名規格', '數量', '單位', '單價', '小計']
    item_data = [header]
    for item in items:
        qty = float(item['quantity'] or 0)
        price = float(item['unit_price'] or 0)
        amount = qty * price
        item_data.append([
            str(item['item_no']),
            item['description'] or '',
            f'{qty:,.2f}',
            item.get('unit', 'PCS'),
            f'{price:,.2f}',
            f'{amount:,.2f}',
        ])

    subtotal = float(invoice.get('subtotal', 0) or 0)
    tax = float(invoice.get('tax_amount', 0) or 0)
    total = float(invoice.get('total_amount', 0) or 0)

    item_data.append(['', '', '', '', '小計', f'{subtotal:,.2f}'])
    item_data.append(['', '', '', '', '稅金', f'{tax:,.2f}'])
    item_data.append(['', '', '', '', '合計', f'{total:,.2f}'])

    col_widths = [35, 210, 55, 40, 65, 75]
    item_table = Table(item_data, colWidths=col_widths, repeatRows=1)
    item_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B9BD5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('ALIGN', (4, 1), (5, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('LINEABOVE', (4, -3), (5, -3), 1, colors.black),
        ('LINEABOVE', (4, -1), (5, -1), 1.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(item_table)

    if invoice.get('notes'):
        elements.append(Spacer(1, 6*mm))
        elements.append(Paragraph(f'備註：{invoice["notes"]}', styles['ChNormal']))

    doc.build(elements)
    return filepath
