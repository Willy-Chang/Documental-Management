import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
from db import queries
from datetime import date
from config import STATUS_OPTIONS, DRAWING_TYPE_OPTIONS, CAD_FILETYPES, IMAGE_FILETYPES, DEFAULT_OPERATOR
from core.thumbnail_manager import save_thumbnail_full
from core.file_manager import backup_file


class DrawingDialog(ttk.Toplevel):
    """新增/編輯圖面對話框"""

    def __init__(self, parent, project_id=None, drawing_id=None):
        super().__init__(parent)
        self.result = None
        self.project_id = project_id
        self.drawing_id = drawing_id
        self.thumbnail_src = None

        if drawing_id:
            self.title("編輯圖面")
        else:
            self.title("新增圖面")

        self.geometry("500x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

        if drawing_id:
            self._load_data()

        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        row = 0

        # 所屬專案
        ttk.Label(frame, text="所屬專案").grid(row=row, column=0, sticky=W, pady=(0, 5))
        # 取得所有專案（含客戶名）
        self._projects = []
        self._project_labels = []
        for c in queries.get_all_clients():
            for p in queries.get_projects_by_client(c['id']):
                self._projects.append(p)
                self._project_labels.append(f"{c['name']} / {p['name']}")

        self.project_combo = ttk.Combobox(frame, values=self._project_labels, state='readonly', width=35)
        self.project_combo.grid(row=row, column=1, pady=(0, 5))

        # 預選專案
        if self.project_id:
            for i, p in enumerate(self._projects):
                if p['id'] == self.project_id:
                    self.project_combo.current(i)
                    break

        row += 1

        # 圖號
        ttk.Label(frame, text="圖號 *").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.number_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.number_var, width=38).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 標題
        ttk.Label(frame, text="圖面標題 *").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.title_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.title_var, width=38).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 圖面類型
        ttk.Label(frame, text="圖面類型").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.type_combo = ttk.Combobox(frame, values=DRAWING_TYPE_OPTIONS, width=35)
        self.type_combo.grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 狀態
        ttk.Label(frame, text="狀態").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.status_combo = ttk.Combobox(frame, values=STATUS_OPTIONS, state='readonly', width=35)
        self.status_combo.set('作業中')
        self.status_combo.grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 目前版次
        ttk.Label(frame, text="目前版次").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.rev_var = ttk.StringVar(value='A')
        ttk.Entry(frame, textvariable=self.rev_var, width=38).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 建立者
        ttk.Label(frame, text="建立者 *").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.creator_var = ttk.StringVar(value=DEFAULT_OPERATOR)
        ttk.Entry(frame, textvariable=self.creator_var, width=38).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 檔案路徑
        ttk.Label(frame, text="圖檔路徑").grid(row=row, column=0, sticky=W, pady=(0, 5))
        path_frame = ttk.Frame(frame)
        path_frame.grid(row=row, column=1, pady=(0, 5), sticky=W)
        self.filepath_var = ttk.StringVar()
        ttk.Entry(path_frame, textvariable=self.filepath_var, width=28).pack(side=LEFT)
        ttk.Button(path_frame, text="瀏覽", command=self._browse_file, bootstyle=INFO, width=6).pack(side=LEFT, padx=(5, 0))
        row += 1

        # 縮圖
        ttk.Label(frame, text="縮圖").grid(row=row, column=0, sticky=W, pady=(0, 5))
        thumb_frame = ttk.Frame(frame)
        thumb_frame.grid(row=row, column=1, pady=(0, 5), sticky=W)
        self.thumb_label = ttk.Label(thumb_frame, text="尚未選擇縮圖")
        self.thumb_label.pack(side=LEFT)
        ttk.Button(thumb_frame, text="選擇縮圖", command=self._browse_thumbnail, bootstyle=INFO, width=8).pack(side=LEFT, padx=(5, 0))
        row += 1

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="確定", command=self._on_ok, bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy, bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="選擇圖檔",
            filetypes=CAD_FILETYPES,
            parent=self
        )
        if path:
            self.filepath_var.set(path)

    def _browse_thumbnail(self):
        path = filedialog.askopenfilename(
            title="選擇縮圖來源（支援圖片/PDF/DWG）",
            filetypes=IMAGE_FILETYPES,
            parent=self
        )
        if path:
            self.thumbnail_src = path
            import os
            self.thumb_label.config(text=f"已選擇: {os.path.basename(path)}")

    def _load_data(self):
        drawing = queries.get_drawing(self.drawing_id)
        if drawing:
            self.number_var.set(drawing['drawing_number'] or '')
            self.title_var.set(drawing['title'] or '')
            self.rev_var.set(drawing['current_rev'] or 'A')
            self.creator_var.set(drawing['created_by'] or '')
            self.filepath_var.set(drawing['file_path'] or '')

            if drawing['status']:
                self.status_combo.set(drawing['status'])
            if drawing['drawing_type']:
                self.type_combo.set(drawing['drawing_type'])

            # 設定所屬專案
            for i, p in enumerate(self._projects):
                if p['id'] == drawing['project_id']:
                    self.project_combo.current(i)
                    break

    def _on_ok(self):
        number = self.number_var.get().strip()
        title = self.title_var.get().strip()
        creator = self.creator_var.get().strip()

        if not number:
            ttk.dialogs.Messagebox.show_error("請輸入圖號", title="錯誤", parent=self)
            return
        if not title:
            ttk.dialogs.Messagebox.show_error("請輸入圖面標題", title="錯誤", parent=self)
            return
        if not creator:
            ttk.dialogs.Messagebox.show_error("請輸入建立者", title="錯誤", parent=self)
            return

        idx = self.project_combo.current()
        if idx < 0:
            ttk.dialogs.Messagebox.show_error("請選擇所屬專案", title="錯誤", parent=self)
            return

        project_id = self._projects[idx]['id']

        try:
            file_path = self.filepath_var.get().strip()
            rev_code = self.rev_var.get().strip() or 'A'

            # 取得客戶/專案名稱（備份用）
            project = self._projects[idx]
            project_name = self._project_labels[idx].split(' / ')
            client_name = project_name[0] if len(project_name) > 1 else ''
            proj_name = project_name[1] if len(project_name) > 1 else project_name[0]

            if self.drawing_id:
                queries.update_drawing(
                    self.drawing_id, number, title,
                    file_path,
                    '',  # thumbnail_path 之後處理
                    rev_code,
                    self.status_combo.get(),
                    self.type_combo.get(),
                    creator
                )
                # 處理縮圖
                if self.thumbnail_src:
                    thumb_path = save_thumbnail_full(self.thumbnail_src, self.drawing_id)
                    if thumb_path:
                        queries.update_drawing_thumbnail(self.drawing_id, thumb_path)
                self.result = self.drawing_id
            else:
                drawing_id = queries.add_drawing(
                    project_id, number, title,
                    file_path,
                    '',
                    rev_code,
                    self.status_combo.get(),
                    self.type_combo.get(),
                    creator
                )
                # 自動建立 A 版版次紀錄（說明=創建）
                queries.add_revision(
                    drawing_id,
                    rev_code='A',
                    rev_date=date.today().isoformat(),
                    saved_by=creator,
                    notes='創建',
                    file_path=file_path
                )
                # 處理縮圖
                if self.thumbnail_src:
                    thumb_path = save_thumbnail_full(self.thumbnail_src, drawing_id)
                    if thumb_path:
                        queries.update_drawing_thumbnail(drawing_id, thumb_path)
                self.result = drawing_id

            # 備份檔案到公司圖面目錄
            if file_path:
                backup_file(file_path, client_name, proj_name, number, rev_code)

            self.destroy()
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(f"儲存失敗：{e}", title="錯誤", parent=self)
