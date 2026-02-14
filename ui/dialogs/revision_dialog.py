import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
from datetime import date
from db import queries
from config import CAD_FILETYPES, DEFAULT_OPERATOR
from core.file_manager import backup_file


class RevisionDialog(ttk.Toplevel):
    """新增版次對話框"""

    def __init__(self, parent, drawing_id, current_rev='A'):
        super().__init__(parent)
        self.result = None
        self.drawing_id = drawing_id

        self.title("新增版次")
        self.geometry("450x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.suggested_rev = queries.suggest_next_rev(current_rev)
        self._create_widgets()
        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        row = 0

        # 版次代號
        ttk.Label(frame, text="版次代號 *").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.rev_var = ttk.StringVar(value=self.suggested_rev)
        ttk.Entry(frame, textvariable=self.rev_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 日期
        ttk.Label(frame, text="日期 *").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.date_var = ttk.StringVar(value=date.today().isoformat())
        ttk.Entry(frame, textvariable=self.date_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 儲存者
        ttk.Label(frame, text="儲存者 *").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.saved_by_var = ttk.StringVar(value=DEFAULT_OPERATOR)
        ttk.Entry(frame, textvariable=self.saved_by_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 檔案路徑（選用）
        ttk.Label(frame, text="新版圖檔").grid(row=row, column=0, sticky=W, pady=(0, 5))
        path_frame = ttk.Frame(frame)
        path_frame.grid(row=row, column=1, pady=(0, 5), sticky=W)
        self.filepath_var = ttk.StringVar()
        ttk.Entry(path_frame, textvariable=self.filepath_var, width=20).pack(side=LEFT)
        ttk.Button(path_frame, text="瀏覽", command=self._browse_file, bootstyle=INFO, width=6).pack(side=LEFT, padx=(5, 0))
        row += 1

        # 說明
        ttk.Label(frame, text="修改說明").grid(row=row, column=0, sticky=NW, pady=(0, 5))
        self.notes_text = ttk.Text(frame, width=30, height=5)
        self.notes_text.grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="確定", command=self._on_ok, bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy, bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="選擇新版圖檔",
            filetypes=CAD_FILETYPES,
            parent=self
        )
        if path:
            self.filepath_var.set(path)

    def _on_ok(self):
        rev_code = self.rev_var.get().strip()
        rev_date = self.date_var.get().strip()
        saved_by = self.saved_by_var.get().strip()

        if not rev_code:
            ttk.dialogs.Messagebox.show_error("請輸入版次代號", title="錯誤", parent=self)
            return
        if not rev_date:
            ttk.dialogs.Messagebox.show_error("請輸入日期", title="錯誤", parent=self)
            return
        if not saved_by:
            ttk.dialogs.Messagebox.show_error("請輸入儲存者", title="錯誤", parent=self)
            return

        try:
            file_path = self.filepath_var.get().strip()
            self.result = queries.add_revision(
                self.drawing_id,
                rev_code,
                rev_date,
                saved_by,
                self.notes_text.get('1.0', 'end-1c').strip(),
                file_path
            )

            # 備份檔案到公司圖面目錄
            if file_path:
                drawing = queries.get_drawing(self.drawing_id)
                if drawing:
                    project = queries.get_project(drawing['project_id'])
                    client = queries.get_client(project['client_id']) if project else None
                    backup_file(
                        file_path,
                        client_name=client['name'] if client else '',
                        project_name=project['name'] if project else '',
                        drawing_number=drawing['drawing_number'],
                        rev_code=rev_code
                    )

            self.destroy()
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(f"儲存失敗：{e}", title="錯誤", parent=self)
