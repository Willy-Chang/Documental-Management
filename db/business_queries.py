"""行政管理系統 — 資料查詢與操作模組

涵蓋：供應商、報價單、請購單、客戶訂單、發票、出口文件、生產管理、機器維修
"""
from datetime import datetime
from db.database import get_connection


# ==================== 通用工具 ====================

def generate_next_number(prefix, table, column):
    """產生下一個單據編號，格式：PREFIX-YYYYMM-NNNN"""
    now = datetime.now()
    year_month = now.strftime('%Y%m')
    pattern = f'{prefix}-{year_month}-%'
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT {column} FROM {table} WHERE {column} LIKE ? ORDER BY {column} DESC LIMIT 1",
            (pattern,)
        ).fetchone()
        if row:
            last_num = int(row[0].split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        return f'{prefix}-{year_month}-{next_num:04d}'
    finally:
        conn.close()


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _today():
    return datetime.now().strftime('%Y-%m-%d')


# ==================== 供應商 ====================

def get_all_suppliers():
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    finally:
        conn.close()


def get_supplier(supplier_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    finally:
        conn.close()


def add_supplier(name, code=None, contact=None, phone=None, email=None,
                 address=None, payment_terms=None, notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO suppliers (name, code, contact, phone, email, address, payment_terms, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, code, contact, phone, email, address, payment_terms, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_supplier(supplier_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), supplier_id]
        conn.execute(
            f"UPDATE suppliers SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_supplier(supplier_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== 報價單 ====================

def get_all_quotations(status=None, client_id=None):
    conn = get_connection()
    try:
        sql = """SELECT q.*, c.name as client_name
                 FROM quotations q
                 LEFT JOIN clients c ON q.client_id = c.id
                 WHERE 1=1"""
        params = []
        if status:
            sql += " AND q.status = ?"
            params.append(status)
        if client_id:
            sql += " AND q.client_id = ?"
            params.append(client_id)
        sql += " ORDER BY q.created_at DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_quotation(quotation_id):
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT q.*, c.name as client_name
               FROM quotations q
               LEFT JOIN clients c ON q.client_id = c.id
               WHERE q.id = ?""",
            (quotation_id,)
        ).fetchone()
    finally:
        conn.close()


def add_quotation(quotation_number, client_id=None, subject=None, currency='TWD',
                  exchange_rate=1.0, tax_rate=0.05, payment_terms=None,
                  delivery_terms=None, validity_days=30, notes=None,
                  status='草稿', created_by=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO quotations
               (quotation_number, client_id, subject, currency, exchange_rate,
                tax_rate, payment_terms, delivery_terms, validity_days, notes,
                status, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (quotation_number, client_id, subject, currency, exchange_rate,
             tax_rate, payment_terms, delivery_terms, validity_days, notes,
             status, created_by)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_quotation(quotation_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), quotation_id]
        conn.execute(
            f"UPDATE quotations SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_quotation(quotation_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM quotations WHERE id = ?", (quotation_id,))
        conn.commit()
    finally:
        conn.close()


def get_quotation_items(quotation_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM quotation_items WHERE quotation_id = ? ORDER BY item_no",
            (quotation_id,)
        ).fetchall()
    finally:
        conn.close()


def add_quotation_item(quotation_id, item_no, description, part_number=None,
                       specification=None, quantity=1, unit='PCS',
                       unit_price=0, notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO quotation_items
               (quotation_id, item_no, part_number, description, specification,
                quantity, unit, unit_price, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (quotation_id, item_no, part_number, description, specification,
             quantity, unit, unit_price, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_quotation_item(item_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [item_id]
        conn.execute(f"UPDATE quotation_items SET {fields} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_quotation_item(item_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM quotation_items WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def get_quotation_total(quotation_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity * unit_price), 0) as total FROM quotation_items WHERE quotation_id = ?",
            (quotation_id,)
        ).fetchone()
        return row['total'] if row else 0
    finally:
        conn.close()


# ==================== 請購單 ====================

def get_all_purchase_requisitions(status=None, department=None):
    conn = get_connection()
    try:
        sql = "SELECT * FROM purchase_requisitions WHERE 1=1"
        params = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if department:
            sql += " AND department = ?"
            params.append(department)
        sql += " ORDER BY created_at DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_purchase_requisition(pr_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM purchase_requisitions WHERE id = ?", (pr_id,)
        ).fetchone()
    finally:
        conn.close()


def add_purchase_requisition(pr_number, requester, department=None, purpose=None,
                             urgency='一般', status='草稿', notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO purchase_requisitions
               (pr_number, requester, department, purpose, urgency, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (pr_number, requester, department, purpose, urgency, status, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_purchase_requisition(pr_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), pr_id]
        conn.execute(
            f"UPDATE purchase_requisitions SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_purchase_requisition(pr_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM purchase_requisitions WHERE id = ?", (pr_id,))
        conn.commit()
    finally:
        conn.close()


def get_pr_items(pr_id):
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT pi.*, s.name as supplier_name
               FROM pr_items pi
               LEFT JOIN suppliers s ON pi.supplier_id = s.id
               WHERE pi.pr_id = ? ORDER BY pi.item_no""",
            (pr_id,)
        ).fetchall()
    finally:
        conn.close()


def add_pr_item(pr_id, item_no, description, category='零件', part_number=None,
                specification=None, quantity=1, unit='PCS', estimated_price=0,
                supplier_id=None, notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO pr_items
               (pr_id, item_no, category, part_number, description, specification,
                quantity, unit, estimated_price, supplier_id, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pr_id, item_no, category, part_number, description, specification,
             quantity, unit, estimated_price, supplier_id, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_pr_item(item_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [item_id]
        conn.execute(f"UPDATE pr_items SET {fields} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_pr_item(item_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM pr_items WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def get_pr_total(pr_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity * estimated_price), 0) as total FROM pr_items WHERE pr_id = ?",
            (pr_id,)
        ).fetchone()
        return row['total'] if row else 0
    finally:
        conn.close()


# ==================== 客戶訂單 ====================

def get_all_customer_orders(status=None, client_id=None):
    conn = get_connection()
    try:
        sql = """SELECT o.*, c.name as client_name
                 FROM customer_orders o
                 LEFT JOIN clients c ON o.client_id = c.id
                 WHERE 1=1"""
        params = []
        if status:
            sql += " AND o.status = ?"
            params.append(status)
        if client_id:
            sql += " AND o.client_id = ?"
            params.append(client_id)
        sql += " ORDER BY o.created_at DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_customer_order(order_id):
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT o.*, c.name as client_name
               FROM customer_orders o
               LEFT JOIN clients c ON o.client_id = c.id
               WHERE o.id = ?""",
            (order_id,)
        ).fetchone()
    finally:
        conn.close()


def add_customer_order(order_number, client_id, order_date, quotation_id=None,
                       po_number=None, delivery_date=None, currency='TWD',
                       payment_terms=None, delivery_terms=None, status='新訂單',
                       notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO customer_orders
               (order_number, client_id, quotation_id, po_number, order_date,
                delivery_date, currency, payment_terms, delivery_terms, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_number, client_id, quotation_id, po_number, order_date,
             delivery_date, currency, payment_terms, delivery_terms, status, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_customer_order(order_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), order_id]
        conn.execute(
            f"UPDATE customer_orders SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_customer_order(order_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM customer_orders WHERE id = ?", (order_id,))
        conn.commit()
    finally:
        conn.close()


def get_order_items(order_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY item_no",
            (order_id,)
        ).fetchall()
    finally:
        conn.close()


def add_order_item(order_id, item_no, description, part_number=None,
                   specification=None, quantity=1, unit='PCS',
                   unit_price=0, delivered_qty=0, notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO order_items
               (order_id, item_no, part_number, description, specification,
                quantity, unit, unit_price, delivered_qty, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, item_no, part_number, description, specification,
             quantity, unit, unit_price, delivered_qty, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_order_item(item_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [item_id]
        conn.execute(f"UPDATE order_items SET {fields} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_order_item(item_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM order_items WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def get_order_total(order_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity * unit_price), 0) as total FROM order_items WHERE order_id = ?",
            (order_id,)
        ).fetchone()
        return row['total'] if row else 0
    finally:
        conn.close()


def copy_quotation_to_order(quotation_id, order_number, order_date):
    """將報價單轉為客戶訂單（複製表頭與品項）"""
    q = get_quotation(quotation_id)
    if not q:
        return None
    order_id = add_customer_order(
        order_number=order_number,
        client_id=q['client_id'],
        order_date=order_date,
        quotation_id=quotation_id,
        currency=q['currency'],
        payment_terms=q['payment_terms'],
        delivery_terms=q['delivery_terms'],
    )
    items = get_quotation_items(quotation_id)
    for item in items:
        add_order_item(
            order_id=order_id,
            item_no=item['item_no'],
            part_number=item['part_number'],
            description=item['description'],
            specification=item['specification'],
            quantity=item['quantity'],
            unit=item['unit'],
            unit_price=item['unit_price'],
            notes=item['notes'],
        )
    update_quotation(quotation_id, status='已成交')
    return order_id


# ==================== 發票 ====================

def get_all_invoices(payment_status=None, client_id=None):
    conn = get_connection()
    try:
        sql = """SELECT inv.*, c.name as client_name, o.order_number
                 FROM invoices inv
                 LEFT JOIN clients c ON inv.client_id = c.id
                 LEFT JOIN customer_orders o ON inv.order_id = o.id
                 WHERE 1=1"""
        params = []
        if payment_status:
            sql += " AND inv.payment_status = ?"
            params.append(payment_status)
        if client_id:
            sql += " AND inv.client_id = ?"
            params.append(client_id)
        sql += " ORDER BY inv.created_at DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_invoice(invoice_id):
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT inv.*, c.name as client_name, o.order_number
               FROM invoices inv
               LEFT JOIN clients c ON inv.client_id = c.id
               LEFT JOIN customer_orders o ON inv.order_id = o.id
               WHERE inv.id = ?""",
            (invoice_id,)
        ).fetchone()
    finally:
        conn.close()


def add_invoice(invoice_number, client_id, invoice_date, order_id=None,
                due_date=None, currency='TWD', subtotal=0, tax_amount=0,
                total_amount=0, payment_status='未付', notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO invoices
               (invoice_number, order_id, client_id, invoice_date, due_date,
                currency, subtotal, tax_amount, total_amount, payment_status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (invoice_number, order_id, client_id, invoice_date, due_date,
             currency, subtotal, tax_amount, total_amount, payment_status, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_invoice(invoice_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), invoice_id]
        conn.execute(
            f"UPDATE invoices SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_invoice(invoice_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        conn.commit()
    finally:
        conn.close()


def get_invoice_items(invoice_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY item_no",
            (invoice_id,)
        ).fetchall()
    finally:
        conn.close()


def add_invoice_item(invoice_id, item_no, description, quantity=1, unit='PCS',
                     unit_price=0, notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO invoice_items
               (invoice_id, item_no, description, quantity, unit, unit_price, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (invoice_id, item_no, description, quantity, unit, unit_price, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_invoice_item(item_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [item_id]
        conn.execute(f"UPDATE invoice_items SET {fields} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_invoice_item(item_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM invoice_items WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def recalculate_invoice(invoice_id, tax_rate=0.05):
    """重算發票金額"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity * unit_price), 0) as subtotal FROM invoice_items WHERE invoice_id = ?",
            (invoice_id,)
        ).fetchone()
        subtotal = row['subtotal'] if row else 0
        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = subtotal + tax_amount
        conn.execute(
            "UPDATE invoices SET subtotal = ?, tax_amount = ?, total_amount = ?, updated_at = ? WHERE id = ?",
            (subtotal, tax_amount, total_amount, _now(), invoice_id)
        )
        conn.commit()
        return subtotal, tax_amount, total_amount
    finally:
        conn.close()


# ==================== 出口文件 ====================

def get_all_export_documents(status=None, order_id=None):
    conn = get_connection()
    try:
        sql = """SELECT ed.*, o.order_number, c.name as client_name
                 FROM export_documents ed
                 LEFT JOIN customer_orders o ON ed.order_id = o.id
                 LEFT JOIN clients c ON o.client_id = c.id
                 WHERE 1=1"""
        params = []
        if status:
            sql += " AND ed.status = ?"
            params.append(status)
        if order_id:
            sql += " AND ed.order_id = ?"
            params.append(order_id)
        sql += " ORDER BY ed.created_at DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_export_document(doc_id):
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT ed.*, o.order_number, c.name as client_name
               FROM export_documents ed
               LEFT JOIN customer_orders o ON ed.order_id = o.id
               LEFT JOIN clients c ON o.client_id = c.id
               WHERE ed.id = ?""",
            (doc_id,)
        ).fetchone()
    finally:
        conn.close()


def add_export_document(doc_type, order_id=None, invoice_id=None, doc_number=None,
                        issue_date=None, destination_country=None,
                        shipping_method=None, shipping_date=None, vessel_name=None,
                        bl_number=None, container_number=None, status='準備中',
                        file_path=None, notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO export_documents
               (order_id, invoice_id, doc_type, doc_number, issue_date,
                destination_country, shipping_method, shipping_date, vessel_name,
                bl_number, container_number, status, file_path, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, invoice_id, doc_type, doc_number, issue_date,
             destination_country, shipping_method, shipping_date, vessel_name,
             bl_number, container_number, status, file_path, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_export_document(doc_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), doc_id]
        conn.execute(
            f"UPDATE export_documents SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_export_document(doc_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM export_documents WHERE id = ?", (doc_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== 生產管理 ====================

def get_all_production_orders(status=None, order_id=None):
    conn = get_connection()
    try:
        sql = """SELECT po.*, o.order_number, c.name as client_name
                 FROM production_orders po
                 LEFT JOIN customer_orders o ON po.order_id = o.id
                 LEFT JOIN clients c ON o.client_id = c.id
                 WHERE 1=1"""
        params = []
        if status:
            sql += " AND po.status = ?"
            params.append(status)
        if order_id:
            sql += " AND po.order_id = ?"
            params.append(order_id)
        sql += " ORDER BY po.created_at DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_production_order(po_id):
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT po.*, o.order_number, c.name as client_name
               FROM production_orders po
               LEFT JOIN customer_orders o ON po.order_id = o.id
               LEFT JOIN clients c ON o.client_id = c.id
               WHERE po.id = ?""",
            (po_id,)
        ).fetchone()
    finally:
        conn.close()


def add_production_order(product_name, quantity=1, unit='PCS', order_id=None,
                         po_number=None, start_date=None, target_date=None,
                         status='待排程', priority='中', notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO production_orders
               (order_id, po_number, product_name, quantity, unit,
                start_date, target_date, status, priority, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, po_number, product_name, quantity, unit,
             start_date, target_date, status, priority, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_production_order(po_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), po_id]
        conn.execute(
            f"UPDATE production_orders SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_production_order(po_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM production_orders WHERE id = ?", (po_id,))
        conn.commit()
    finally:
        conn.close()


def get_production_tasks(po_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM production_tasks WHERE production_order_id = ? ORDER BY id",
            (po_id,)
        ).fetchall()
    finally:
        conn.close()


def get_all_production_tasks_for_gantt(status_filter=None):
    """取得所有生產任務（甘特圖用），包含生產單資訊"""
    conn = get_connection()
    try:
        sql = """SELECT pt.*, po.product_name, po.po_number, po.status as po_status
                 FROM production_tasks pt
                 JOIN production_orders po ON pt.production_order_id = po.id
                 WHERE 1=1"""
        params = []
        if status_filter:
            sql += " AND po.status = ?"
            params.append(status_filter)
        sql += " ORDER BY pt.start_date, pt.id"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def add_production_task(production_order_id, task_name, department=None,
                        assignee=None, start_date=None, end_date=None,
                        progress_pct=0, depends_on=None, status='待開始',
                        notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO production_tasks
               (production_order_id, task_name, department, assignee,
                start_date, end_date, progress_pct, depends_on, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (production_order_id, task_name, department, assignee,
             start_date, end_date, progress_pct, depends_on, status, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_production_task(task_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [task_id]
        conn.execute(f"UPDATE production_tasks SET {fields} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_production_task(task_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM production_tasks WHERE id = ?", (task_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== 機器 ====================

def get_all_machines(status=None, department=None):
    conn = get_connection()
    try:
        sql = "SELECT * FROM machines WHERE 1=1"
        params = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if department:
            sql += " AND department = ?"
            params.append(department)
        sql += " ORDER BY machine_code"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_machine(machine_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM machines WHERE id = ?", (machine_id,)).fetchone()
    finally:
        conn.close()


def add_machine(machine_code, machine_name, model=None, manufacturer=None,
                purchase_date=None, location=None, department=None,
                status='正常', notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO machines
               (machine_code, machine_name, model, manufacturer, purchase_date,
                location, department, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (machine_code, machine_name, model, manufacturer, purchase_date,
             location, department, status, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_machine(machine_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), machine_id]
        conn.execute(
            f"UPDATE machines SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_machine(machine_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM machines WHERE id = ?", (machine_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== 維修紀錄 ====================

def get_all_maintenance_records(status=None, machine_id=None, maintenance_type=None):
    conn = get_connection()
    try:
        sql = """SELECT mr.*, m.machine_code, m.machine_name
                 FROM maintenance_records mr
                 JOIN machines m ON mr.machine_id = m.id
                 WHERE 1=1"""
        params = []
        if status:
            sql += " AND mr.status = ?"
            params.append(status)
        if machine_id:
            sql += " AND mr.machine_id = ?"
            params.append(machine_id)
        if maintenance_type:
            sql += " AND mr.maintenance_type = ?"
            params.append(maintenance_type)
        sql += " ORDER BY mr.created_at DESC"
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def get_maintenance_record(record_id):
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT mr.*, m.machine_code, m.machine_name
               FROM maintenance_records mr
               JOIN machines m ON mr.machine_id = m.id
               WHERE mr.id = ?""",
            (record_id,)
        ).fetchone()
    finally:
        conn.close()


def add_maintenance_record(machine_id, description, reported_by,
                           maintenance_type='故障維修', assigned_to=None,
                           cause=None, solution=None, parts_used=None,
                           cost=0, downtime_hours=0, status='待處理',
                           next_maintenance_date=None, notes=None):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO maintenance_records
               (machine_id, maintenance_type, reported_by, assigned_to,
                description, cause, solution, parts_used, cost, downtime_hours,
                status, next_maintenance_date, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (machine_id, maintenance_type, reported_by, assigned_to,
             description, cause, solution, parts_used, cost, downtime_hours,
             status, next_maintenance_date, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_maintenance_record(record_id, **kwargs):
    conn = get_connection()
    try:
        fields = ', '.join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [_now(), record_id]
        conn.execute(
            f"UPDATE maintenance_records SET {fields}, updated_at = ? WHERE id = ?", values
        )
        conn.commit()
    finally:
        conn.close()


def delete_maintenance_record(record_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM maintenance_records WHERE id = ?", (record_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== 儀表板統計 ====================

def get_dashboard_stats():
    """取得儀表板統計資料"""
    conn = get_connection()
    try:
        stats = {}
        stats['quotation_count'] = conn.execute(
            "SELECT COUNT(*) as c FROM quotations").fetchone()['c']
        stats['quotation_pending'] = conn.execute(
            "SELECT COUNT(*) as c FROM quotations WHERE status = '已報價'").fetchone()['c']
        stats['order_count'] = conn.execute(
            "SELECT COUNT(*) as c FROM customer_orders").fetchone()['c']
        stats['order_active'] = conn.execute(
            "SELECT COUNT(*) as c FROM customer_orders WHERE status IN ('新訂單', '生產中')").fetchone()['c']
        stats['invoice_unpaid'] = conn.execute(
            "SELECT COUNT(*) as c FROM invoices WHERE payment_status IN ('未付', '逾期')").fetchone()['c']
        stats['invoice_unpaid_amount'] = conn.execute(
            "SELECT COALESCE(SUM(total_amount), 0) as t FROM invoices WHERE payment_status IN ('未付', '逾期')"
        ).fetchone()['t']
        stats['production_active'] = conn.execute(
            "SELECT COUNT(*) as c FROM production_orders WHERE status IN ('生產中', '待排程')").fetchone()['c']
        stats['maintenance_pending'] = conn.execute(
            "SELECT COUNT(*) as c FROM maintenance_records WHERE status IN ('待處理', '處理中')").fetchone()['c']
        stats['pr_pending'] = conn.execute(
            "SELECT COUNT(*) as c FROM purchase_requisitions WHERE status IN ('草稿', '待審核')").fetchone()['c']
        stats['client_count'] = conn.execute(
            "SELECT COUNT(*) as c FROM clients").fetchone()['c']
        stats['machine_count'] = conn.execute(
            "SELECT COUNT(*) as c FROM machines").fetchone()['c']
        stats['machine_down'] = conn.execute(
            "SELECT COUNT(*) as c FROM machines WHERE status IN ('維修中', '待維修')").fetchone()['c']
        return stats
    finally:
        conn.close()


# ==================== 客戶查詢（業務擴充） ====================

def get_all_clients_for_combo():
    """取得客戶清單供下拉選單使用"""
    conn = get_connection()
    try:
        return conn.execute("SELECT id, name, code FROM clients ORDER BY name").fetchall()
    finally:
        conn.close()


def get_all_orders_for_combo():
    """取得訂單清單供下拉選單使用"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, order_number FROM customer_orders ORDER BY order_number DESC"
        ).fetchall()
    finally:
        conn.close()


def get_all_quotations_for_combo():
    """取得報價單清單供下拉選單使用"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, quotation_number FROM quotations ORDER BY quotation_number DESC"
        ).fetchall()
    finally:
        conn.close()


def get_all_invoices_for_combo():
    """取得發票清單供下拉選單使用"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, invoice_number FROM invoices ORDER BY invoice_number DESC"
        ).fetchall()
    finally:
        conn.close()


def get_all_machines_for_combo():
    """取得機器清單供下拉選單使用"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, machine_code, machine_name FROM machines ORDER BY machine_code"
        ).fetchall()
    finally:
        conn.close()
