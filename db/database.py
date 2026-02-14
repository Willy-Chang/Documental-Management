import sqlite3
import os
from config import DB_PATH


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """初始化資料庫，建立所有資料表"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        -- ==================== 圖面管理 ====================

        -- 客戶資料表
        CREATE TABLE IF NOT EXISTS clients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            code        TEXT UNIQUE,
            contact     TEXT,
            phone       TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            updated_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 專案資料表
        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id   INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            name        TEXT NOT NULL,
            code        TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            updated_at  TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(client_id, name)
        );

        -- 圖面資料表
        CREATE TABLE IF NOT EXISTS drawings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            drawing_number  TEXT NOT NULL,
            title           TEXT NOT NULL,
            file_path       TEXT,
            thumbnail_path  TEXT,
            current_rev     TEXT DEFAULT 'A',
            status          TEXT DEFAULT '作業中',
            drawing_type    TEXT,
            created_by      TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 版次紀錄資料表
        CREATE TABLE IF NOT EXISTS revisions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            drawing_id  INTEGER NOT NULL REFERENCES drawings(id) ON DELETE CASCADE,
            rev_code    TEXT NOT NULL,
            rev_date    TEXT NOT NULL,
            saved_by    TEXT NOT NULL,
            file_path   TEXT,
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 存取紀錄資料表
        CREATE TABLE IF NOT EXISTS access_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            drawing_id  INTEGER NOT NULL REFERENCES drawings(id) ON DELETE CASCADE,
            user_name   TEXT NOT NULL,
            action      TEXT NOT NULL DEFAULT 'view',
            accessed_at TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 部門設定表
        CREATE TABLE IF NOT EXISTS departments (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL UNIQUE
        );

        -- 發行單表
        CREATE TABLE IF NOT EXISTS circulation_orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            drawing_id    INTEGER NOT NULL REFERENCES drawings(id) ON DELETE CASCADE,
            rev_code      TEXT NOT NULL,
            issued_by     TEXT NOT NULL,
            issued_at     TEXT DEFAULT (datetime('now','localtime')),
            status        TEXT NOT NULL DEFAULT '發行中',
            client_sent   INTEGER DEFAULT 0,
            client_sent_at TEXT,
            notes         TEXT,
            created_at    TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 發行任務表
        CREATE TABLE IF NOT EXISTS circulation_tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER NOT NULL REFERENCES circulation_orders(id) ON DELETE CASCADE,
            department      TEXT NOT NULL,
            assignee        TEXT,
            status          TEXT NOT NULL DEFAULT '待處理',
            downloaded_at   TEXT,
            uploaded_at     TEXT,
            uploaded_file   TEXT,
            confirmed_by    TEXT,
            confirmed_at    TEXT,
            description     TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        -- 發行歷程表
        CREATE TABLE IF NOT EXISTS circulation_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id      INTEGER NOT NULL REFERENCES circulation_orders(id) ON DELETE CASCADE,
            task_id       INTEGER REFERENCES circulation_tasks(id),
            action        TEXT NOT NULL,
            operator      TEXT NOT NULL,
            department    TEXT,
            file_path     TEXT,
            description   TEXT,
            created_at    TEXT DEFAULT (datetime('now','localtime'))
        );

        -- ==================== 供應商 ====================

        CREATE TABLE IF NOT EXISTS suppliers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            code          TEXT UNIQUE,
            contact       TEXT,
            phone         TEXT,
            email         TEXT,
            address       TEXT,
            payment_terms TEXT,
            notes         TEXT,
            created_at    TEXT DEFAULT (datetime('now','localtime')),
            updated_at    TEXT DEFAULT (datetime('now','localtime'))
        );

        -- ==================== 報價單 ====================

        CREATE TABLE IF NOT EXISTS quotations (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            quotation_number  TEXT NOT NULL UNIQUE,
            client_id         INTEGER REFERENCES clients(id),
            subject           TEXT,
            currency          TEXT DEFAULT 'TWD',
            exchange_rate     REAL DEFAULT 1.0,
            tax_rate          REAL DEFAULT 0.05,
            payment_terms     TEXT,
            delivery_terms    TEXT,
            validity_days     INTEGER DEFAULT 30,
            notes             TEXT,
            status            TEXT DEFAULT '草稿',
            created_by        TEXT,
            created_at        TEXT DEFAULT (datetime('now','localtime')),
            updated_at        TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS quotation_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            quotation_id    INTEGER NOT NULL REFERENCES quotations(id) ON DELETE CASCADE,
            item_no         INTEGER NOT NULL,
            part_number     TEXT,
            description     TEXT NOT NULL,
            specification   TEXT,
            quantity         REAL NOT NULL DEFAULT 1,
            unit            TEXT DEFAULT 'PCS',
            unit_price      REAL NOT NULL DEFAULT 0,
            notes           TEXT
        );

        -- ==================== 請購單 ====================

        CREATE TABLE IF NOT EXISTS purchase_requisitions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            pr_number     TEXT NOT NULL UNIQUE,
            requester     TEXT NOT NULL,
            department    TEXT,
            purpose       TEXT,
            urgency       TEXT DEFAULT '一般',
            status        TEXT DEFAULT '草稿',
            approved_by   TEXT,
            approved_at   TEXT,
            notes         TEXT,
            created_at    TEXT DEFAULT (datetime('now','localtime')),
            updated_at    TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS pr_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            pr_id           INTEGER NOT NULL REFERENCES purchase_requisitions(id) ON DELETE CASCADE,
            item_no         INTEGER NOT NULL,
            category        TEXT DEFAULT '零件',
            part_number     TEXT,
            description     TEXT NOT NULL,
            specification   TEXT,
            quantity         REAL NOT NULL DEFAULT 1,
            unit            TEXT DEFAULT 'PCS',
            estimated_price REAL DEFAULT 0,
            supplier_id     INTEGER REFERENCES suppliers(id),
            notes           TEXT
        );

        -- ==================== 客戶訂單 ====================

        CREATE TABLE IF NOT EXISTS customer_orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number    TEXT NOT NULL UNIQUE,
            client_id       INTEGER NOT NULL REFERENCES clients(id),
            quotation_id    INTEGER REFERENCES quotations(id),
            po_number       TEXT,
            order_date      TEXT NOT NULL,
            delivery_date   TEXT,
            currency        TEXT DEFAULT 'TWD',
            payment_terms   TEXT,
            delivery_terms  TEXT,
            status          TEXT DEFAULT '新訂單',
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER NOT NULL REFERENCES customer_orders(id) ON DELETE CASCADE,
            item_no         INTEGER NOT NULL,
            part_number     TEXT,
            description     TEXT NOT NULL,
            specification   TEXT,
            quantity         REAL NOT NULL DEFAULT 1,
            unit            TEXT DEFAULT 'PCS',
            unit_price      REAL NOT NULL DEFAULT 0,
            delivered_qty   REAL DEFAULT 0,
            notes           TEXT
        );

        -- ==================== 發票紀錄 ====================

        CREATE TABLE IF NOT EXISTS invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number  TEXT NOT NULL UNIQUE,
            order_id        INTEGER REFERENCES customer_orders(id),
            client_id       INTEGER NOT NULL REFERENCES clients(id),
            invoice_date    TEXT NOT NULL,
            due_date        TEXT,
            currency        TEXT DEFAULT 'TWD',
            subtotal        REAL DEFAULT 0,
            tax_amount      REAL DEFAULT 0,
            total_amount    REAL DEFAULT 0,
            payment_status  TEXT DEFAULT '未付',
            payment_date    TEXT,
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS invoice_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id      INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            item_no         INTEGER NOT NULL,
            description     TEXT NOT NULL,
            quantity         REAL NOT NULL DEFAULT 1,
            unit            TEXT DEFAULT 'PCS',
            unit_price      REAL NOT NULL DEFAULT 0,
            notes           TEXT
        );

        -- ==================== 出口文件 ====================

        CREATE TABLE IF NOT EXISTS export_documents (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id            INTEGER REFERENCES customer_orders(id),
            invoice_id          INTEGER REFERENCES invoices(id),
            doc_type            TEXT NOT NULL,
            doc_number          TEXT,
            issue_date          TEXT,
            destination_country TEXT,
            shipping_method     TEXT,
            shipping_date       TEXT,
            vessel_name         TEXT,
            bl_number           TEXT,
            container_number    TEXT,
            status              TEXT DEFAULT '準備中',
            file_path           TEXT,
            notes               TEXT,
            created_at          TEXT DEFAULT (datetime('now','localtime')),
            updated_at          TEXT DEFAULT (datetime('now','localtime'))
        );

        -- ==================== 生產管理 ====================

        CREATE TABLE IF NOT EXISTS production_orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER REFERENCES customer_orders(id),
            po_number       TEXT,
            product_name    TEXT NOT NULL,
            quantity         REAL NOT NULL DEFAULT 1,
            unit            TEXT DEFAULT 'PCS',
            start_date      TEXT,
            target_date     TEXT,
            actual_end_date TEXT,
            status          TEXT DEFAULT '待排程',
            priority        TEXT DEFAULT '中',
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS production_tasks (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            production_order_id   INTEGER NOT NULL REFERENCES production_orders(id) ON DELETE CASCADE,
            task_name             TEXT NOT NULL,
            department            TEXT,
            assignee              TEXT,
            start_date            TEXT,
            end_date              TEXT,
            actual_start          TEXT,
            actual_end            TEXT,
            progress_pct          INTEGER DEFAULT 0,
            depends_on            TEXT,
            status                TEXT DEFAULT '待開始',
            notes                 TEXT,
            created_at            TEXT DEFAULT (datetime('now','localtime'))
        );

        -- ==================== 機器維修 ====================

        CREATE TABLE IF NOT EXISTS machines (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_code    TEXT NOT NULL UNIQUE,
            machine_name    TEXT NOT NULL,
            model           TEXT,
            manufacturer    TEXT,
            purchase_date   TEXT,
            location        TEXT,
            department      TEXT,
            status          TEXT DEFAULT '正常',
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS maintenance_records (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id              INTEGER NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
            maintenance_type        TEXT NOT NULL DEFAULT '故障維修',
            reported_by             TEXT NOT NULL,
            reported_at             TEXT DEFAULT (datetime('now','localtime')),
            assigned_to             TEXT,
            started_at              TEXT,
            completed_at            TEXT,
            description             TEXT NOT NULL,
            cause                   TEXT,
            solution                TEXT,
            parts_used              TEXT,
            cost                    REAL DEFAULT 0,
            downtime_hours          REAL DEFAULT 0,
            status                  TEXT DEFAULT '待處理',
            next_maintenance_date   TEXT,
            notes                   TEXT,
            created_at              TEXT DEFAULT (datetime('now','localtime')),
            updated_at              TEXT DEFAULT (datetime('now','localtime'))
        );

        -- ==================== 索引 ====================

        CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_id);
        CREATE INDEX IF NOT EXISTS idx_drawings_project ON drawings(project_id);
        CREATE INDEX IF NOT EXISTS idx_revisions_drawing ON revisions(drawing_id);
        CREATE INDEX IF NOT EXISTS idx_drawings_number ON drawings(drawing_number);
        CREATE INDEX IF NOT EXISTS idx_access_logs_drawing ON access_logs(drawing_id);
        CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_name);
        CREATE INDEX IF NOT EXISTS idx_circulation_orders_drawing ON circulation_orders(drawing_id);
        CREATE INDEX IF NOT EXISTS idx_circulation_tasks_order ON circulation_tasks(order_id);
        CREATE INDEX IF NOT EXISTS idx_circulation_logs_order ON circulation_logs(order_id);

        -- 業務管理索引
        CREATE INDEX IF NOT EXISTS idx_quotations_client ON quotations(client_id);
        CREATE INDEX IF NOT EXISTS idx_quotation_items_quotation ON quotation_items(quotation_id);
        CREATE INDEX IF NOT EXISTS idx_pr_items_pr ON pr_items(pr_id);
        CREATE INDEX IF NOT EXISTS idx_pr_items_supplier ON pr_items(supplier_id);
        CREATE INDEX IF NOT EXISTS idx_customer_orders_client ON customer_orders(client_id);
        CREATE INDEX IF NOT EXISTS idx_customer_orders_quotation ON customer_orders(quotation_id);
        CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
        CREATE INDEX IF NOT EXISTS idx_invoices_order ON invoices(order_id);
        CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id);
        CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);
        CREATE INDEX IF NOT EXISTS idx_export_docs_order ON export_documents(order_id);
        CREATE INDEX IF NOT EXISTS idx_export_docs_invoice ON export_documents(invoice_id);
        CREATE INDEX IF NOT EXISTS idx_production_orders_order ON production_orders(order_id);
        CREATE INDEX IF NOT EXISTS idx_production_tasks_po ON production_tasks(production_order_id);
        CREATE INDEX IF NOT EXISTS idx_maintenance_records_machine ON maintenance_records(machine_id);
    """)

    # FTS5 全文搜尋
    try:
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS drawings_fts USING fts5(
                drawing_number, title,
                content='drawings',
                content_rowid='id'
            )
        """)
    except Exception:
        pass

    # FTS 同步觸發器
    triggers = [
        """CREATE TRIGGER IF NOT EXISTS drawings_ai AFTER INSERT ON drawings BEGIN
            INSERT INTO drawings_fts(rowid, drawing_number, title)
            VALUES (new.id, new.drawing_number, new.title);
        END""",
        """CREATE TRIGGER IF NOT EXISTS drawings_ad AFTER DELETE ON drawings BEGIN
            INSERT INTO drawings_fts(drawings_fts, rowid, drawing_number, title)
            VALUES ('delete', old.id, old.drawing_number, old.title);
        END""",
        """CREATE TRIGGER IF NOT EXISTS drawings_au AFTER UPDATE ON drawings BEGIN
            INSERT INTO drawings_fts(drawings_fts, rowid, drawing_number, title)
            VALUES ('delete', old.id, old.drawing_number, old.title);
            INSERT INTO drawings_fts(rowid, drawing_number, title)
            VALUES (new.id, new.drawing_number, new.title);
        END""",
    ]
    for trigger in triggers:
        try:
            cursor.execute(trigger)
        except Exception:
            pass

    # 初始化預設部門
    from config import DEPARTMENTS
    for dept in DEPARTMENTS:
        try:
            cursor.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,))
        except Exception:
            pass

    conn.commit()

    # 安全新增欄位（支援資料庫升級）
    _migrate_columns(conn)

    conn.close()


def _migrate_columns(conn):
    """安全新增欄位（若不存在則新增，已存在則跳過）"""
    migrations = [
        # circulation_orders: 流程類型 + A流程專用欄位
        ("circulation_orders", "flow_type", "TEXT NOT NULL DEFAULT 'B'"),
        ("circulation_orders", "flow_a_step", "TEXT"),
        ("circulation_orders", "client_approval_date", "TEXT"),
        # circulation_tasks: 步驟序號 + B/C流程收到確認欄位
        ("circulation_tasks", "step_number", "INTEGER DEFAULT 0"),
        ("circulation_tasks", "step_name", "TEXT"),
        ("circulation_tasks", "received_by", "TEXT"),
        ("circulation_tasks", "received_at", "TEXT"),
        # clients: 擴充欄位（業務管理用）
        ("clients", "email", "TEXT"),
        ("clients", "address", "TEXT"),
        ("clients", "tax_id", "TEXT"),
        ("clients", "fax", "TEXT"),
    ]
    for table, col, col_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            conn.commit()
        except Exception:
            pass
