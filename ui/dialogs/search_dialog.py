import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config import STATUS_OPTIONS, DRAWING_TYPE_OPTIONS


class SearchDialog(ttk.Toplevel):
    """進階搜尋對話框"""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None

        self.title("進階搜尋")
        self.geometry("450x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        row = 0

        # 關鍵字
        ttk.Label(frame, text="關鍵字（圖號/標題）").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.keyword_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.keyword_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 客戶名稱
        ttk.Label(frame, text="客戶名稱").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.client_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.client_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 專案名稱
        ttk.Label(frame, text="專案名稱").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.project_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.project_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 狀態
        ttk.Label(frame, text="狀態").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.status_combo = ttk.Combobox(frame, values=[''] + STATUS_OPTIONS, width=27)
        self.status_combo.grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 圖面類型
        ttk.Label(frame, text="圖面類型").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.type_combo = ttk.Combobox(frame, values=[''] + DRAWING_TYPE_OPTIONS, width=27)
        self.type_combo.grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 建立者
        ttk.Label(frame, text="建立者").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.creator_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.creator_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 日期範圍
        ttk.Label(frame, text="建立日期從").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.date_from_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.date_from_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        ttk.Label(frame, text="建立日期到").grid(row=row, column=0, sticky=W, pady=(0, 5))
        self.date_to_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.date_to_var, width=30).grid(row=row, column=1, pady=(0, 5))
        row += 1

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="搜尋", command=self._on_search, bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy, bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _on_search(self):
        self.result = {
            'keyword': self.keyword_var.get().strip(),
            'client_name': self.client_var.get().strip(),
            'project_name': self.project_var.get().strip(),
            'status': self.status_combo.get().strip(),
            'drawing_type': self.type_combo.get().strip(),
            'created_by': self.creator_var.get().strip(),
            'date_from': self.date_from_var.get().strip(),
            'date_to': self.date_to_var.get().strip(),
        }
        self.destroy()
