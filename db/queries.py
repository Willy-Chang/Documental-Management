import sqlite3
from datetime import datetime
from db.database import get_connection


# ===== 客戶 =====

def add_client(name, code='', contact='', phone='', notes=''):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO clients (name, code, contact, phone, notes) VALUES (?, ?, ?, ?, ?)",
            (name, code or None, contact, phone, notes)
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()

def update_client(client_id, name, code='', contact='', phone='', notes=''):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE clients SET name=?, code=?, contact=?, phone=?, notes=?,
               updated_at=datetime('now','localtime') WHERE id=?""",
            (name, code or None, contact, phone, notes, client_id)
        )
        conn.commit()
    finally:
        conn.close()

def delete_client(client_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
        conn.commit()
    finally:
        conn.close()

def get_all_clients():
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    finally:
        conn.close()

def get_client(client_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    finally:
        conn.close()


# ===== 專案 =====

def add_project(client_id, name, code='', notes=''):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO projects (client_id, name, code, notes) VALUES (?, ?, ?, ?)",
            (client_id, name, code or None, notes)
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()

def update_project(project_id, name, code='', notes=''):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE projects SET name=?, code=?, notes=?,
               updated_at=datetime('now','localtime') WHERE id=?""",
            (name, code or None, notes, project_id)
        )
        conn.commit()
    finally:
        conn.close()

def delete_project(project_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()
    finally:
        conn.close()

def get_projects_by_client(client_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM projects WHERE client_id=? ORDER BY name", (client_id,)
        ).fetchall()
    finally:
        conn.close()

def get_project(project_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    finally:
        conn.close()


# ===== 圖面 =====

def add_drawing(project_id, drawing_number, title, file_path='', thumbnail_path='',
                current_rev='A', status='作業中', drawing_type='', created_by=''):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO drawings
               (project_id, drawing_number, title, file_path, thumbnail_path,
                current_rev, status, drawing_type, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, drawing_number, title, file_path, thumbnail_path,
             current_rev, status, drawing_type, created_by)
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()

def update_drawing(drawing_id, drawing_number, title, file_path='', thumbnail_path='',
                   current_rev='A', status='作業中', drawing_type='', created_by=''):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE drawings SET drawing_number=?, title=?, file_path=?, thumbnail_path=?,
               current_rev=?, status=?, drawing_type=?, created_by=?,
               updated_at=datetime('now','localtime') WHERE id=?""",
            (drawing_number, title, file_path, thumbnail_path,
             current_rev, status, drawing_type, created_by, drawing_id)
        )
        conn.commit()
    finally:
        conn.close()

def update_drawing_thumbnail(drawing_id, thumbnail_path):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE drawings SET thumbnail_path=?, updated_at=datetime('now','localtime') WHERE id=?",
            (thumbnail_path, drawing_id)
        )
        conn.commit()
    finally:
        conn.close()

def delete_drawing(drawing_id):
    """刪除圖面及所有關聯資料（僅刪資料庫記錄，不刪除原始檔案）"""
    conn = get_connection()
    try:
        # 先取得關聯的 circulation_orders id 清單
        order_ids = [r['id'] for r in conn.execute(
            "SELECT id FROM circulation_orders WHERE drawing_id=?", (drawing_id,)
        ).fetchall()]

        # 依序刪除關聯表（由子到父，確保外鍵不阻擋）
        for oid in order_ids:
            conn.execute("DELETE FROM circulation_logs WHERE order_id=?", (oid,))
            conn.execute("DELETE FROM circulation_tasks WHERE order_id=?", (oid,))
        conn.execute("DELETE FROM circulation_orders WHERE drawing_id=?", (drawing_id,))
        conn.execute("DELETE FROM access_logs WHERE drawing_id=?", (drawing_id,))
        conn.execute("DELETE FROM revisions WHERE drawing_id=?", (drawing_id,))

        # 最後刪除圖面本身
        conn.execute("DELETE FROM drawings WHERE id=?", (drawing_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_drawings_by_project(project_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM drawings WHERE project_id=? ORDER BY drawing_number",
            (project_id,)
        ).fetchall()
    finally:
        conn.close()

def get_drawing(drawing_id):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM drawings WHERE id=?", (drawing_id,)).fetchone()
    finally:
        conn.close()

def get_all_drawings():
    conn = get_connection()
    try:
        return conn.execute("""
            SELECT d.*, p.name as project_name, c.name as client_name
            FROM drawings d
            JOIN projects p ON d.project_id = p.id
            JOIN clients c ON p.client_id = c.id
            ORDER BY c.name, p.name, d.drawing_number
        """).fetchall()
    finally:
        conn.close()


# ===== 版次 =====

def add_revision(drawing_id, rev_code, rev_date, saved_by, notes='', file_path=''):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO revisions (drawing_id, rev_code, rev_date, saved_by, notes, file_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (drawing_id, rev_code, rev_date, saved_by, notes, file_path)
        )
        # 更新圖面目前版次
        conn.execute(
            """UPDATE drawings SET current_rev=?, updated_at=datetime('now','localtime')
               WHERE id=?""",
            (rev_code, drawing_id)
        )
        # 如果有新檔案路徑，也更新圖面的檔案路徑
        if file_path:
            conn.execute(
                "UPDATE drawings SET file_path=? WHERE id=?",
                (file_path, drawing_id)
            )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()

def get_revisions(drawing_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM revisions WHERE drawing_id=? ORDER BY created_at DESC",
            (drawing_id,)
        ).fetchall()
    finally:
        conn.close()

def suggest_next_rev(current_rev):
    """建議下一個版次代號"""
    if not current_rev:
        return 'A'
    if current_rev.isalpha() and len(current_rev) == 1:
        if current_rev.upper() == 'Z':
            return 'AA'
        return chr(ord(current_rev.upper()) + 1)
    if current_rev.isdigit():
        return str(int(current_rev) + 1)
    return current_rev + '.1'


# ===== 搜尋 =====

def search_drawings(keyword='', client_name='', project_name='', status='',
                    drawing_type='', date_from='', date_to='', created_by=''):
    """多條件搜尋圖面"""
    conn = get_connection()
    try:
        conditions = []
        params = []

        if keyword:
            # 同時使用 FTS5（英數）和 LIKE（中文）搜尋
            conditions.append(
                "(d.id IN (SELECT rowid FROM drawings_fts WHERE drawings_fts MATCH ?) "
                "OR d.drawing_number LIKE ? OR d.title LIKE ?)"
            )
            params.append(f'"{keyword}"*')
            params.append(f"%{keyword}%")
            params.append(f"%{keyword}%")

        if client_name:
            conditions.append("c.name LIKE ?")
            params.append(f"%{client_name}%")

        if project_name:
            conditions.append("p.name LIKE ?")
            params.append(f"%{project_name}%")

        if status:
            conditions.append("d.status = ?")
            params.append(status)

        if drawing_type:
            conditions.append("d.drawing_type = ?")
            params.append(drawing_type)

        if date_from:
            conditions.append("d.created_at >= ?")
            params.append(date_from)

        if date_to:
            conditions.append("d.created_at <= ?")
            params.append(date_to + ' 23:59:59')

        if created_by:
            conditions.append("d.created_by LIKE ?")
            params.append(f"%{created_by}%")

        where = " AND ".join(conditions) if conditions else "1=1"

        return conn.execute(f"""
            SELECT d.*, p.name as project_name, c.name as client_name
            FROM drawings d
            JOIN projects p ON d.project_id = p.id
            JOIN clients c ON p.client_id = c.id
            WHERE {where}
            ORDER BY c.name, p.name, d.drawing_number
        """, params).fetchall()
    finally:
        conn.close()


def get_drawing_count():
    """取得圖面總數"""
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM drawings").fetchone()[0]
    finally:
        conn.close()


# ===== 存取紀錄 =====

def log_access(drawing_id, user_name, action='view'):
    """記錄圖面存取紀錄"""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO access_logs (drawing_id, user_name, action) VALUES (?, ?, ?)",
            (drawing_id, user_name, action)
        )
        conn.commit()
    finally:
        conn.close()

def get_access_logs(drawing_id, limit=50):
    """取得指定圖面的存取紀錄（最新在前）"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM access_logs WHERE drawing_id=? ORDER BY accessed_at DESC LIMIT ?",
            (drawing_id, limit)
        ).fetchall()
    finally:
        conn.close()


# ===== 部門 =====

def get_departments():
    """取得所有部門"""
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM departments ORDER BY id").fetchall()
    finally:
        conn.close()

def add_department(name):
    """新增部門"""
    conn = get_connection()
    try:
        conn.execute("INSERT INTO departments (name) VALUES (?)", (name,))
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()


# ===== 發行流程 =====

def _log_circulation(conn, order_id, action, operator, task_id=None,
                     department=None, file_path=None, description=None):
    """（內部）記錄發行歷程"""
    conn.execute(
        """INSERT INTO circulation_logs
           (order_id, task_id, action, operator, department, file_path, description)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (order_id, task_id, action, operator, department, file_path, description)
    )

def create_circulation_order(drawing_id, rev_code, issued_by, departments, notes=''):
    """建立發行單，並為每個指定部門建立任務"""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO circulation_orders (drawing_id, rev_code, issued_by, notes)
               VALUES (?, ?, ?, ?)""",
            (drawing_id, rev_code, issued_by, notes)
        )
        order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for dept in departments:
            conn.execute(
                """INSERT INTO circulation_tasks (order_id, department)
                   VALUES (?, ?)""",
                (order_id, dept)
            )

        _log_circulation(conn, order_id, '發行', issued_by,
                         description=notes or f'發行至 {", ".join(departments)}')

        # 更新圖面狀態為「發行中」
        conn.execute(
            """UPDATE drawings SET status='發行中', updated_at=datetime('now','localtime')
               WHERE id=?""",
            (drawing_id,)
        )
        conn.commit()
        return order_id
    finally:
        conn.close()

def get_circulation_order(order_id):
    """取得單一發行單"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM circulation_orders WHERE id=?", (order_id,)
        ).fetchone()
    finally:
        conn.close()

def get_active_order(drawing_id, rev_code):
    """取得指定圖面版次目前進行中的發行單（最新一筆）"""
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT * FROM circulation_orders
               WHERE drawing_id=? AND rev_code=?
               ORDER BY id DESC LIMIT 1""",
            (drawing_id, rev_code)
        ).fetchone()
    finally:
        conn.close()

def get_all_orders_for_drawing(drawing_id):
    """取得指定圖面的所有發行單"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM circulation_orders WHERE drawing_id=? ORDER BY id DESC",
            (drawing_id,)
        ).fetchall()
    finally:
        conn.close()

def get_circulation_tasks(order_id):
    """取得發行單的所有部門任務"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM circulation_tasks WHERE order_id=? ORDER BY id",
            (order_id,)
        ).fetchall()
    finally:
        conn.close()

def get_task(task_id):
    """取得單一任務"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM circulation_tasks WHERE id=?", (task_id,)
        ).fetchone()
    finally:
        conn.close()

def download_task(task_id, operator):
    """部門下載圖面（記錄下載動作）"""
    conn = get_connection()
    try:
        task = conn.execute("SELECT * FROM circulation_tasks WHERE id=?", (task_id,)).fetchone()
        if not task:
            return
        conn.execute(
            """UPDATE circulation_tasks
               SET status='已下載', assignee=?, downloaded_at=datetime('now','localtime')
               WHERE id=?""",
            (operator, task_id)
        )
        _log_circulation(conn, task['order_id'], '下載', operator,
                         task_id=task_id, department=task['department'])
        conn.commit()
    finally:
        conn.close()

def upload_task(task_id, operator, file_path, description=''):
    """部門上傳修改後的檔案"""
    conn = get_connection()
    try:
        task = conn.execute("SELECT * FROM circulation_tasks WHERE id=?", (task_id,)).fetchone()
        if not task:
            return
        conn.execute(
            """UPDATE circulation_tasks
               SET status='已上傳', assignee=?, uploaded_at=datetime('now','localtime'),
                   uploaded_file=?, description=?
               WHERE id=?""",
            (operator, file_path, description, task_id)
        )
        _log_circulation(conn, task['order_id'], '上傳', operator,
                         task_id=task_id, department=task['department'],
                         file_path=file_path, description=description)
        conn.commit()
    finally:
        conn.close()

def confirm_task(task_id, confirmed_by):
    """管理部確認收回某部門的任務"""
    conn = get_connection()
    try:
        task = conn.execute("SELECT * FROM circulation_tasks WHERE id=?", (task_id,)).fetchone()
        if not task:
            return
        conn.execute(
            """UPDATE circulation_tasks
               SET status='已確認', confirmed_by=?, confirmed_at=datetime('now','localtime')
               WHERE id=?""",
            (confirmed_by, task_id)
        )
        _log_circulation(conn, task['order_id'], '確認', confirmed_by,
                         task_id=task_id, department=task['department'],
                         description=f'確認收回 {task["department"]} 上傳內容')

        # 檢查是否全部任務都已確認 → 自動更新發行單狀態
        all_confirmed = conn.execute(
            """SELECT COUNT(*) FROM circulation_tasks
               WHERE order_id=? AND status != '已確認'""",
            (task['order_id'],)
        ).fetchone()[0]

        if all_confirmed == 0:
            conn.execute(
                """UPDATE circulation_orders
                   SET status='已回收'
                   WHERE id=?""",
                (task['order_id'],)
            )
            # 更新圖面狀態
            order = conn.execute(
                "SELECT drawing_id FROM circulation_orders WHERE id=?",
                (task['order_id'],)
            ).fetchone()
            if order:
                conn.execute(
                    """UPDATE drawings SET status='已回收', updated_at=datetime('now','localtime')
                       WHERE id=?""",
                    (order['drawing_id'],)
                )
            _log_circulation(conn, task['order_id'], '全部回收', confirmed_by,
                             description='所有部門任務已確認收回')

        conn.commit()
    finally:
        conn.close()

def mark_client_sent(order_id, operator, notes=''):
    """標記已寄出客戶"""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE circulation_orders
               SET client_sent=1, client_sent_at=datetime('now','localtime'), status='已完成'
               WHERE id=?""",
            (order_id,)
        )
        order = conn.execute(
            "SELECT drawing_id FROM circulation_orders WHERE id=?", (order_id,)
        ).fetchone()
        if order:
            conn.execute(
                """UPDATE drawings SET status='已完成', updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (order['drawing_id'],)
            )
        _log_circulation(conn, order_id, '寄出客戶', operator,
                         description=notes or '已寄出客戶確認')
        conn.commit()
    finally:
        conn.close()

def cancel_order(order_id, operator, reason=''):
    """取消發行單"""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE circulation_orders SET status='已取消' WHERE id=?",
            (order_id,)
        )
        order = conn.execute(
            "SELECT drawing_id FROM circulation_orders WHERE id=?", (order_id,)
        ).fetchone()
        if order:
            conn.execute(
                """UPDATE drawings SET status='作業中', updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (order['drawing_id'],)
            )
        _log_circulation(conn, order_id, '取消', operator,
                         description=reason or '發行單已取消')
        conn.commit()
    finally:
        conn.close()

def get_circulation_logs(order_id):
    """取得發行單的所有歷程紀錄（最新在前）"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM circulation_logs WHERE order_id=? ORDER BY created_at DESC",
            (order_id,)
        ).fetchall()
    finally:
        conn.close()


# ===== 三流程系統 (A/B/C) =====

def get_active_flow(drawing_id):
    """取得圖面最新的進行中流程（任何 flow_type），若無進行中則取最新一筆"""
    conn = get_connection()
    try:
        # 優先找進行中的
        row = conn.execute(
            """SELECT * FROM circulation_orders
               WHERE drawing_id=? AND status='發行中'
               ORDER BY id DESC LIMIT 1""",
            (drawing_id,)
        ).fetchone()
        if row:
            return row
        # 否則取最新一筆
        return conn.execute(
            """SELECT * FROM circulation_orders
               WHERE drawing_id=?
               ORDER BY id DESC LIMIT 1""",
            (drawing_id,)
        ).fetchone()
    finally:
        conn.close()


def get_all_flows_for_drawing(drawing_id):
    """取得圖面的所有流程（含 flow_type），newest first"""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM circulation_orders WHERE drawing_id=? ORDER BY id DESC",
            (drawing_id,)
        ).fetchall()
    finally:
        conn.close()


# ----- A流程：客戶圖面 -----

def create_flow_a(drawing_id, rev_code, issued_by, notes=''):
    """建立A流程：車工部整理→管理部寄客戶→客戶確認

    自動建立3個步驟任務。
    """
    conn = get_connection()
    try:
        from config import FLOW_A_STEPS
        conn.execute(
            """INSERT INTO circulation_orders
               (drawing_id, rev_code, issued_by, notes, flow_type, flow_a_step)
               VALUES (?, ?, ?, ?, 'A', ?)""",
            (drawing_id, rev_code, issued_by, notes, FLOW_A_STEPS[0])
        )
        order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 建立3個步驟任務
        steps = [
            (1, '車工部整理', '車工部'),
            (2, '管理部寄客戶', '管理部'),
            (3, '客戶確認', '管理部'),
        ]
        for step_num, step_name, dept in steps:
            status = '進行中' if step_num == 1 else '待處理'
            conn.execute(
                """INSERT INTO circulation_tasks
                   (order_id, department, step_number, step_name, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_id, dept, step_num, step_name, status)
            )

        _log_circulation(conn, order_id, '建立A流程', issued_by,
                         description=notes or '客戶圖面流程：車工部整理→管理部寄客戶→客戶確認')

        conn.execute(
            """UPDATE drawings SET status='發行中', updated_at=datetime('now','localtime')
               WHERE id=?""",
            (drawing_id,)
        )
        conn.commit()
        return order_id
    finally:
        conn.close()


def advance_flow_a(order_id, operator, notes=''):
    """推進A流程到下一步

    車工部整理 → 管理部寄客戶 → 客戶確認 → 已完成
    """
    conn = get_connection()
    try:
        from config import FLOW_A_STEPS
        order = conn.execute(
            "SELECT * FROM circulation_orders WHERE id=?", (order_id,)
        ).fetchone()
        if not order:
            return

        current_step = order['flow_a_step']
        if current_step not in FLOW_A_STEPS:
            return

        idx = FLOW_A_STEPS.index(current_step)

        # 標記目前步驟的 task 為已完成
        task = conn.execute(
            """SELECT * FROM circulation_tasks
               WHERE order_id=? AND step_number=?""",
            (order_id, idx + 1)
        ).fetchone()
        if task:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute(
                """UPDATE circulation_tasks
                   SET status='已完成', confirmed_by=?, confirmed_at=?
                   WHERE id=?""",
                (operator, now, task['id'])
            )
            _log_circulation(conn, order_id, f'完成：{current_step}', operator,
                             task_id=task['id'], department=task['department'],
                             description=notes or f'{current_step} 已完成')

        if idx + 1 < len(FLOW_A_STEPS) - 1:
            # 推進到下一步
            next_step = FLOW_A_STEPS[idx + 1]
            conn.execute(
                "UPDATE circulation_orders SET flow_a_step=? WHERE id=?",
                (next_step, order_id)
            )
            # 啟動下一步的 task
            next_task = conn.execute(
                """SELECT * FROM circulation_tasks
                   WHERE order_id=? AND step_number=?""",
                (order_id, idx + 2)
            ).fetchone()
            if next_task:
                conn.execute(
                    "UPDATE circulation_tasks SET status='進行中' WHERE id=?",
                    (next_task['id'],)
                )
        else:
            # 最後一步完成 → 整個流程完成
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute(
                """UPDATE circulation_orders
                   SET flow_a_step='已完成', status='已完成',
                       client_approval_date=?
                   WHERE id=?""",
                (now, order_id)
            )
            conn.execute(
                """UPDATE drawings SET status='已完成', updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (order['drawing_id'],)
            )
            _log_circulation(conn, order_id, '客戶同意', operator,
                             description=f'客戶確認完成，同意日期：{now[:10]}')

        conn.commit()
    finally:
        conn.close()


def get_flow_a_status(order_id):
    """取得A流程狀態（含各步驟完成狀態）"""
    conn = get_connection()
    try:
        order = conn.execute(
            "SELECT * FROM circulation_orders WHERE id=?", (order_id,)
        ).fetchone()
        tasks = conn.execute(
            "SELECT * FROM circulation_tasks WHERE order_id=? ORDER BY step_number",
            (order_id,)
        ).fetchall()
        return order, tasks
    finally:
        conn.close()


# ----- B流程：劦佑圖面 -----

def create_flow_b(drawing_id, rev_code, issued_by, departments, notes=''):
    """建立B流程：管理部發行給多個部門，各部門需確認收到"""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO circulation_orders
               (drawing_id, rev_code, issued_by, notes, flow_type)
               VALUES (?, ?, ?, ?, 'B')""",
            (drawing_id, rev_code, issued_by, notes)
        )
        order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for dept in departments:
            conn.execute(
                """INSERT INTO circulation_tasks
                   (order_id, department, status)
                   VALUES (?, ?, '待通知')""",
                (order_id, dept)
            )

        _log_circulation(conn, order_id, '建立B流程', issued_by,
                         description=notes or f'劦佑圖面發行至 {", ".join(departments)}')

        conn.execute(
            """UPDATE drawings SET status='發行中', updated_at=datetime('now','localtime')
               WHERE id=?""",
            (drawing_id,)
        )
        conn.commit()
        return order_id
    finally:
        conn.close()


def confirm_receipt_b(task_id, received_by):
    """B流程：部門確認收到通知"""
    conn = get_connection()
    try:
        task = conn.execute(
            "SELECT * FROM circulation_tasks WHERE id=?", (task_id,)
        ).fetchone()
        if not task:
            return

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            """UPDATE circulation_tasks
               SET status='已收到', received_by=?, received_at=?
               WHERE id=?""",
            (received_by, now, task_id)
        )
        _log_circulation(conn, task['order_id'], '收到通知', received_by,
                         task_id=task_id, department=task['department'],
                         description=f'{task["department"]} {received_by} 已收到')

        # 檢查是否全部收到 → 自動完成
        pending = conn.execute(
            """SELECT COUNT(*) FROM circulation_tasks
               WHERE order_id=? AND status != '已收到'""",
            (task['order_id'],)
        ).fetchone()[0]

        if pending == 0:
            conn.execute(
                "UPDATE circulation_orders SET status='已完成' WHERE id=?",
                (task['order_id'],)
            )
            order = conn.execute(
                "SELECT drawing_id FROM circulation_orders WHERE id=?",
                (task['order_id'],)
            ).fetchone()
            if order:
                conn.execute(
                    """UPDATE drawings SET status='已完成', updated_at=datetime('now','localtime')
                       WHERE id=?""",
                    (order['drawing_id'],)
                )
            _log_circulation(conn, task['order_id'], '全部收到', received_by,
                             description='所有部門已確認收到')

        conn.commit()
    finally:
        conn.close()


# ----- C流程：修改發行 -----

def create_flow_c(drawing_id, rev_code, issued_by, dept_person_list, notes=''):
    """建立C流程：發行更改圖面給指定人員

    dept_person_list = [{'department': '車工部', 'assignee': '張三'}, ...]
    """
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO circulation_orders
               (drawing_id, rev_code, issued_by, notes, flow_type)
               VALUES (?, ?, ?, ?, 'C')""",
            (drawing_id, rev_code, issued_by, notes)
        )
        order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        dept_names = []
        for item in dept_person_list:
            dept = item['department']
            person = item['assignee']
            dept_names.append(f'{dept}-{person}')
            conn.execute(
                """INSERT INTO circulation_tasks
                   (order_id, department, assignee, status)
                   VALUES (?, ?, ?, '待通知')""",
                (order_id, dept, person)
            )

        _log_circulation(conn, order_id, '建立C流程', issued_by,
                         description=notes or f'修改發行至 {", ".join(dept_names)}')

        conn.execute(
            """UPDATE drawings SET status='發行中', updated_at=datetime('now','localtime')
               WHERE id=?""",
            (drawing_id,)
        )
        conn.commit()
        return order_id
    finally:
        conn.close()


def confirm_receipt_c(task_id, received_by):
    """C流程：指定人員確認收到更改圖面"""
    conn = get_connection()
    try:
        task = conn.execute(
            "SELECT * FROM circulation_tasks WHERE id=?", (task_id,)
        ).fetchone()
        if not task:
            return

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            """UPDATE circulation_tasks
               SET status='已收到', received_by=?, received_at=?
               WHERE id=?""",
            (received_by, now, task_id)
        )
        _log_circulation(conn, task['order_id'], '收到更改', received_by,
                         task_id=task_id, department=task['department'],
                         description=f'{task["department"]} {received_by} 已收到更改圖面')

        # 檢查是否全部收到 → 自動完成
        pending = conn.execute(
            """SELECT COUNT(*) FROM circulation_tasks
               WHERE order_id=? AND status != '已收到'""",
            (task['order_id'],)
        ).fetchone()[0]

        if pending == 0:
            conn.execute(
                "UPDATE circulation_orders SET status='已完成' WHERE id=?",
                (task['order_id'],)
            )
            order = conn.execute(
                "SELECT drawing_id FROM circulation_orders WHERE id=?",
                (task['order_id'],)
            ).fetchone()
            if order:
                conn.execute(
                    """UPDATE drawings SET status='已完成', updated_at=datetime('now','localtime')
                       WHERE id=?""",
                    (order['drawing_id'],)
                )
            _log_circulation(conn, task['order_id'], '全部收到更改', received_by,
                             description='所有指定人員已確認收到更改圖面')

        conn.commit()
    finally:
        conn.close()
