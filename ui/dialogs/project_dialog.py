import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from db import queries


class ProjectDialog(ttk.Toplevel):
    """新增/編輯專案對話框"""

    def __init__(self, parent, client_id=None, project_id=None):
        super().__init__(parent)
        self.result = None
        self.client_id = client_id
        self.project_id = project_id

        if project_id:
            self.title("編輯專案")
        else:
            self.title("新增專案")

        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

        if project_id:
            self._load_data()

        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        # 所屬客戶
        ttk.Label(frame, text="所屬客戶").grid(row=0, column=0, sticky=W, pady=(0, 5))
        self.clients = queries.get_all_clients()
        client_names = [c['name'] for c in self.clients]
        self.client_combo = ttk.Combobox(frame, values=client_names, state='readonly', width=27)
        self.client_combo.grid(row=0, column=1, pady=(0, 5))

        # 預選客戶
        if self.client_id:
            for i, c in enumerate(self.clients):
                if c['id'] == self.client_id:
                    self.client_combo.current(i)
                    break

        # 專案名稱
        ttk.Label(frame, text="專案名稱 *").grid(row=1, column=0, sticky=W, pady=(0, 5))
        self.name_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=1, column=1, pady=(0, 5))

        # 專案代碼
        ttk.Label(frame, text="專案代碼").grid(row=2, column=0, sticky=W, pady=(0, 5))
        self.code_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.code_var, width=30).grid(row=2, column=1, pady=(0, 5))

        # 備註
        ttk.Label(frame, text="備註").grid(row=3, column=0, sticky=NW, pady=(0, 5))
        self.notes_text = ttk.Text(frame, width=30, height=4)
        self.notes_text.grid(row=3, column=1, pady=(0, 5))

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="確定", command=self._on_ok, bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy, bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _load_data(self):
        project = queries.get_project(self.project_id)
        if project:
            self.name_var.set(project['name'] or '')
            self.code_var.set(project['code'] or '')
            if project['notes']:
                self.notes_text.insert('1.0', project['notes'])
            # 設定所屬客戶
            for i, c in enumerate(self.clients):
                if c['id'] == project['client_id']:
                    self.client_combo.current(i)
                    break

    def _on_ok(self):
        name = self.name_var.get().strip()
        if not name:
            ttk.dialogs.Messagebox.show_error("請輸入專案名稱", title="錯誤", parent=self)
            return

        idx = self.client_combo.current()
        if idx < 0:
            ttk.dialogs.Messagebox.show_error("請選擇所屬客戶", title="錯誤", parent=self)
            return

        client_id = self.clients[idx]['id']

        try:
            if self.project_id:
                queries.update_project(
                    self.project_id, name,
                    self.code_var.get().strip(),
                    self.notes_text.get('1.0', 'end-1c').strip()
                )
                self.result = self.project_id
            else:
                self.result = queries.add_project(
                    client_id, name,
                    self.code_var.get().strip(),
                    self.notes_text.get('1.0', 'end-1c').strip()
                )
            self.destroy()
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(f"儲存失敗：{e}", title="錯誤", parent=self)
