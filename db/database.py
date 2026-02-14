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

        -- 存取紀錄資料表（追蹤誰在何時開啟/檢視了哪張圖面）
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

        -- 發行單表（管理部發行圖面給各部門處理）
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

        -- 發行任務表（每個部門的處理任務）
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

        -- 發行歷程表（完整記錄每一步操作）
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

        -- 索引
        CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_id);
        CREATE INDEX IF NOT EXISTS idx_drawings_project ON drawings(project_id);
        CREATE INDEX IF NOT EXISTS idx_revisions_drawing ON revisions(drawing_id);
        CREATE INDEX IF NOT EXISTS idx_drawings_number ON drawings(drawing_number);
        CREATE INDEX IF NOT EXISTS idx_access_logs_drawing ON access_logs(drawing_id);
        CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_name);
        CREATE INDEX IF NOT EXISTS idx_circulation_orders_drawing ON circulation_orders(drawing_id);
        CREATE INDEX IF NOT EXISTS idx_circulation_tasks_order ON circulation_tasks(order_id);
        CREATE INDEX IF NOT EXISTS idx_circulation_logs_order ON circulation_logs(order_id);
    """)

    # FTS5 全文搜尋（分開建立，避免 IF NOT EXISTS 在某些版本不支援）
    try:
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS drawings_fts USING fts5(
                drawing_number, title,
                content='drawings',
                content_rowid='id'
            )
        """)
    except Exception:
        pass  # 已存在則忽略

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

    # 安全新增欄位（支援資料庫升級，已有欄位則跳過）
    _migrate_columns(conn)

    conn.close()


def _migrate_columns(conn):
    """安全新增三流程所需的欄位（若不存在則新增，已存在則跳過）"""
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
    ]
    for table, col, col_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            conn.commit()
        except Exception:
            pass  # 欄位已存在，跳過
