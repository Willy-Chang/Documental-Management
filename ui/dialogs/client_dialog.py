import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from db import queries


class ClientDialog(ttk.Toplevel):
    """新增/編輯客戶對話框"""

    def __init__(self, parent, client_id=None):
        super().__init__(parent)
        self.result = None
        self.client_id = client_id

        if client_id:
            self.title("編輯客戶")
        else:
            self.title("新增客戶")

        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

        if client_id:
            self._load_data()

        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        # 客戶名稱
        ttk.Label(frame, text="客戶名稱 *").grid(row=0, column=0, sticky=W, pady=(0, 5))
        self.name_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=(0, 5))

        # 客戶代碼
        ttk.Label(frame, text="客戶代碼").grid(row=1, column=0, sticky=W, pady=(0, 5))
        self.code_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.code_var, width=30).grid(row=1, column=1, pady=(0, 5))

        # 聯絡人
        ttk.Label(frame, text="聯絡人").grid(row=2, column=0, sticky=W, pady=(0, 5))
        self.contact_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.contact_var, width=30).grid(row=2, column=1, pady=(0, 5))

        # 電話
        ttk.Label(frame, text="電話").grid(row=3, column=0, sticky=W, pady=(0, 5))
        self.phone_var = ttk.StringVar()
        ttk.Entry(frame, textvariable=self.phone_var, width=30).grid(row=3, column=1, pady=(0, 5))

        # 備註
        ttk.Label(frame, text="備註").grid(row=4, column=0, sticky=NW, pady=(0, 5))
        self.notes_text = ttk.Text(frame, width=30, height=4)
        self.notes_text.grid(row=4, column=1, pady=(0, 5))

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="確定", command=self._on_ok, bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy, bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _load_data(self):
        client = queries.get_client(self.client_id)
        if client:
            self.name_var.set(client['name'] or '')
            self.code_var.set(client['code'] or '')
            self.contact_var.set(client['contact'] or '')
            self.phone_var.set(client['phone'] or '')
            if client['notes']:
                self.notes_text.insert('1.0', client['notes'])

    def _on_ok(self):
        name = self.name_var.get().strip()
        if not name:
            ttk.dialogs.Messagebox.show_error("請輸入客戶名稱", title="錯誤", parent=self)
            return

        try:
            if self.client_id:
                queries.update_client(
                    self.client_id, name,
                    self.code_var.get().strip(),
                    self.contact_var.get().strip(),
                    self.phone_var.get().strip(),
                    self.notes_text.get('1.0', 'end-1c').strip()
                )
                self.result = self.client_id
            else:
                self.result = queries.add_client(
                    name,
                    self.code_var.get().strip(),
                    self.contact_var.get().strip(),
                    self.phone_var.get().strip(),
                    self.notes_text.get('1.0', 'end-1c').strip()
                )
            self.destroy()
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(f"儲存失敗：{e}", title="錯誤", parent=self)
