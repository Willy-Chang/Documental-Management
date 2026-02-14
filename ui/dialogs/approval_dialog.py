import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from db import queries
from config import APPROVAL_ROLES, DEFAULT_OPERATOR


class ApprovalDialog(ttk.Toplevel):
    """簽核對話框 — 針對某個角色進行核准/退回"""

    def __init__(self, parent, drawing_id, rev_code, role, record_id):
        super().__init__(parent)
        self.result = None
        self.drawing_id = drawing_id
        self.rev_code = rev_code
        self.role = role
        self.record_id = record_id

        self.title(f"簽核 — {role}")
        self.geometry("420x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        # 資訊區
        info_frame = ttk.LabelFrame(frame, text="簽核資訊", padding=10)
        info_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(info_frame, text=f"版次：{self.rev_code}").pack(anchor=W)
        ttk.Label(info_frame, text=f"簽核角色：{self.role}").pack(anchor=W)

        # 簽核人
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=X, pady=(0, 5))
        ttk.Label(input_frame, text="簽核人 *").grid(row=0, column=0, sticky=W, pady=3)
        self.signer_var = ttk.StringVar(value=DEFAULT_OPERATOR)
        ttk.Entry(input_frame, textvariable=self.signer_var, width=28).grid(row=0, column=1, pady=3, padx=(10, 0))

        # 意見
        ttk.Label(input_frame, text="備註").grid(row=1, column=0, sticky=NW, pady=3)
        self.comments_text = ttk.Text(input_frame, width=28, height=4)
        self.comments_text.grid(row=1, column=1, pady=3, padx=(10, 0))

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(15, 0))

        ttk.Button(
            btn_frame, text="核准", command=self._on_approve,
            bootstyle=SUCCESS, width=10
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame, text="退回", command=self._on_reject,
            bootstyle=DANGER, width=10
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame, text="取消", command=self.destroy,
            bootstyle=SECONDARY, width=10
        ).pack(side=LEFT, padx=5)

    def _on_approve(self):
        self._do_sign('核准')

    def _on_reject(self):
        self._do_sign('退回')

    def _do_sign(self, status):
        signer = self.signer_var.get().strip()
        if not signer:
            ttk.dialogs.Messagebox.show_error("請輸入簽核人", title="錯誤", parent=self)
            return

        comments = self.comments_text.get('1.0', 'end-1c').strip()

        try:
            queries.sign_approval(self.record_id, signer, status, comments)

            # 如果全部核准，自動更新圖面狀態為「已核准」
            if status == '核准' and queries.is_fully_approved(self.drawing_id, self.rev_code):
                drawing = queries.get_drawing(self.drawing_id)
                if drawing:
                    queries.update_drawing(
                        self.drawing_id,
                        drawing['drawing_number'],
                        drawing['title'],
                        drawing['file_path'] or '',
                        drawing['thumbnail_path'] or '',
                        drawing['current_rev'] or 'A',
                        '已核准',
                        drawing['drawing_type'] or '',
                        drawing['created_by'] or ''
                    )

            self.result = status
            self.destroy()
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(f"簽核失敗：{e}", title="錯誤", parent=self)


class ApprovalFlowPanel(ttk.LabelFrame):
    """簽核流程面板 — 嵌入在 detail_panel 中，顯示流程狀態並提供簽核按鈕"""

    # 角色狀態顏色對照
    STATUS_COLORS = {
        '待審': '#999999',
        '核准': '#28a745',
        '退回': '#dc3545',
    }

    STATUS_ICONS = {
        '待審': '⏳',
        '核准': '✅',
        '退回': '❌',
    }

    def __init__(self, parent):
        super().__init__(parent, text="簽核流程")
        self._drawing_id = None
        self._rev_code = None
        self._records = []
        self._role_widgets = {}
        self._create_widgets()

    def _create_widgets(self):
        self.inner = ttk.Frame(self, padding=10)
        self.inner.pack(fill=BOTH, expand=True)

        # 流程步驟區（動態生成）
        self.steps_frame = ttk.Frame(self.inner)
        self.steps_frame.pack(fill=X)

        # 操作按鈕區
        self.btn_frame = ttk.Frame(self.inner)
        self.btn_frame.pack(fill=X, pady=(8, 0))

        self.btn_start = ttk.Button(
            self.btn_frame, text="送出簽核", command=self._start_approval,
            bootstyle=PRIMARY + OUTLINE, width=10
        )
        self.btn_start.pack(side=LEFT, padx=3)

        self.btn_sign = ttk.Button(
            self.btn_frame, text="執行簽核", command=self._do_approval,
            bootstyle=SUCCESS, width=10
        )
        self.btn_sign.pack(side=LEFT, padx=3)

        # 狀態提示
        self.status_var = ttk.StringVar()
        self.status_label = ttk.Label(self.inner, textvariable=self.status_var,
                                       wraplength=280)
        self.status_label.pack(fill=X, pady=(5, 0))

        # 初始隱藏
        self.btn_start.config(state=DISABLED)
        self.btn_sign.config(state=DISABLED)

    def load(self, drawing_id, rev_code):
        """載入指定圖面版次的簽核狀態"""
        self._drawing_id = drawing_id
        self._rev_code = rev_code

        # 取得簽核紀錄
        self._records = queries.get_approval_records(drawing_id, rev_code)

        # 更新步驟顯示
        self._refresh_steps()

        # 更新按鈕狀態
        self._update_buttons()

    def clear(self):
        """清空面板"""
        self._drawing_id = None
        self._rev_code = None
        self._records = []
        self._clear_steps()
        self.btn_start.config(state=DISABLED)
        self.btn_sign.config(state=DISABLED)
        self.status_var.set('')

    def _clear_steps(self):
        for w in self.steps_frame.winfo_children():
            w.destroy()
        self._role_widgets.clear()

    def _refresh_steps(self):
        self._clear_steps()

        if not self._records:
            # 尚未建立簽核流程
            ttk.Label(self.steps_frame, text="尚未送出簽核",
                      foreground='#999999').pack(anchor=W)
            return

        # 建立每個角色的顯示列
        record_map = {r['role']: r for r in self._records}

        for i, role in enumerate(APPROVAL_ROLES):
            row_frame = ttk.Frame(self.steps_frame)
            row_frame.pack(fill=X, pady=2)

            record = record_map.get(role)
            status = record['status'] if record else '待審'
            icon = self.STATUS_ICONS.get(status, '⏳')
            color = self.STATUS_COLORS.get(status, '#999999')

            # 箭頭連接（除了第一個）
            if i > 0:
                arrow_label = ttk.Label(self.steps_frame, text="    ↓",
                                         foreground='#cccccc')
                # 插入在 row_frame 之前
                arrow_label.pack(before=row_frame, anchor=W)

            # 角色名稱與狀態
            role_text = f"{icon} {role}"
            role_label = ttk.Label(row_frame, text=role_text, foreground=color,
                                    width=12, anchor=W)
            role_label.pack(side=LEFT)

            # 簽核人與日期
            if record and record['signer']:
                detail = f"{record['signer']}  {(record['sign_date'] or '')[:16]}"
                ttk.Label(row_frame, text=detail, foreground='#666666').pack(side=LEFT, padx=(5, 0))

            # 退回備註
            if record and status == '退回' and record['comments']:
                comment_text = f"（{record['comments'][:30]}）"
                ttk.Label(row_frame, text=comment_text,
                          foreground='#dc3545').pack(side=LEFT, padx=(5, 0))

            self._role_widgets[role] = row_frame

    def _update_buttons(self):
        has_records = len(self._records) > 0

        if not has_records:
            # 尚未建立流程 → 可送出簽核
            self.btn_start.config(state=NORMAL)
            self.btn_sign.config(state=DISABLED)
            self.status_var.set('')
        else:
            # 已有流程
            self.btn_start.config(state=DISABLED)
            next_role = queries.get_next_pending_role(self._drawing_id, self._rev_code)
            if next_role:
                self.btn_sign.config(state=NORMAL)
                self.status_var.set(f"下一步：{next_role}")
            else:
                # 全部核准
                self.btn_sign.config(state=DISABLED)
                self.status_var.set("✅ 全部簽核完成")

    def _start_approval(self):
        """送出簽核：建立簽核流程"""
        if not self._drawing_id or not self._rev_code:
            return

        try:
            queries.init_approval_flow(self._drawing_id, self._rev_code)

            # 更新圖面狀態為「審核中」
            drawing = queries.get_drawing(self._drawing_id)
            if drawing and drawing['status'] != '審核中':
                queries.update_drawing(
                    self._drawing_id,
                    drawing['drawing_number'],
                    drawing['title'],
                    drawing['file_path'] or '',
                    drawing['thumbnail_path'] or '',
                    drawing['current_rev'] or 'A',
                    '審核中',
                    drawing['drawing_type'] or '',
                    drawing['created_by'] or ''
                )

            # 重新載入
            self.load(self._drawing_id, self._rev_code)

            # 通知父面板刷新
            self._notify_parent_refresh()

        except Exception as e:
            ttk.dialogs.Messagebox.show_error(
                f"送出簽核失敗：{e}", title="錯誤",
                parent=self.winfo_toplevel()
            )

    def _do_approval(self):
        """執行簽核：開啟簽核對話框"""
        if not self._drawing_id or not self._rev_code:
            return

        next_role = queries.get_next_pending_role(self._drawing_id, self._rev_code)
        if not next_role:
            ttk.dialogs.Messagebox.show_info("所有簽核已完成", title="提示",
                                              parent=self.winfo_toplevel())
            return

        # 找到對應的 record_id
        record_map = {r['role']: r for r in self._records}
        record = record_map.get(next_role)
        if not record:
            return

        dialog = ApprovalDialog(
            self.winfo_toplevel(),
            self._drawing_id,
            self._rev_code,
            next_role,
            record['id']
        )

        if dialog.result:
            # 重新載入簽核狀態
            self.load(self._drawing_id, self._rev_code)
            self._notify_parent_refresh()

    def _notify_parent_refresh(self):
        """通知上層面板刷新資料"""
        # 向上尋找 DetailPanel 並觸發刷新
        parent = self.master
        while parent:
            if hasattr(parent, 'load_drawing') and hasattr(parent, '_current_drawing_id'):
                parent.load_drawing(parent._current_drawing_id)
                if hasattr(parent, 'on_refresh') and parent.on_refresh:
                    parent.on_refresh()
                break
            parent = getattr(parent, 'master', None)
