"""
發行流程對話框 — 三種流程 (A/B/C)

A流程（客戶圖面）：客戶寄圖→車工部整理→管理部寄客戶確認→客戶同意
B流程（劦佑圖面）：管理部發行給各單位→各單位按收到通知
C流程（修改發行）：發行更改圖面給指定單位人員→指定人員按收到

重要：所有 Toplevel 對話框改為「先 withdraw 選擇窗→開子對話框→
子對話框結束後再 destroy 選擇窗」的模式，避免 grab 衝突。
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from db import queries
from config import DEFAULT_OPERATOR, FLOW_TYPES, FLOW_A_STEPS


def _rget(row, key, default=None):
    """安全取值：sqlite3.Row 不支援 .get()，用 try/except 模擬"""
    try:
        v = row[key]
        return v if v is not None else default
    except (IndexError, KeyError):
        return default


# ============================================================
# 流程選擇對話框
# ============================================================

class FlowTypeSelectDialog(ttk.Toplevel):
    """選擇要啟動哪種流程"""

    def __init__(self, parent, drawing_id, rev_code):
        super().__init__(parent)
        self.result = None  # order_id or None
        self.drawing_id = drawing_id
        self.rev_code = rev_code
        self._parent = parent

        self.title("選擇發行流程類型")
        self.geometry("440x420")
        self.minsize(380, 380)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="請選擇發行流程類型：",
                  font=('', 11, 'bold')).pack(anchor=W, pady=(0, 12))

        self._flow_var = ttk.StringVar(value='A')

        # A流程
        a_frame = ttk.Frame(frame)
        a_frame.pack(fill=X, pady=4)
        ttk.Radiobutton(a_frame, text="A流程（客戶圖面）",
                        variable=self._flow_var, value='A').pack(anchor=W)
        ttk.Label(a_frame, text="  客戶寄圖 → 車工部整理 → 管理部寄客戶確認 → 客戶同意",
                  foreground='#888888', wraplength=380).pack(anchor=W, padx=(20, 0))

        ttk.Separator(frame, orient=HORIZONTAL).pack(fill=X, pady=8)

        # B流程
        b_frame = ttk.Frame(frame)
        b_frame.pack(fill=X, pady=4)
        ttk.Radiobutton(b_frame, text="B流程（劦佑圖面）",
                        variable=self._flow_var, value='B').pack(anchor=W)
        ttk.Label(b_frame, text="  管理部發行給各單位 → 各單位按「收到通知」",
                  foreground='#888888', wraplength=380).pack(anchor=W, padx=(20, 0))

        ttk.Separator(frame, orient=HORIZONTAL).pack(fill=X, pady=8)

        # C流程
        c_frame = ttk.Frame(frame)
        c_frame.pack(fill=X, pady=4)
        ttk.Radiobutton(c_frame, text="C流程（修改發行）",
                        variable=self._flow_var, value='C').pack(anchor=W)
        ttk.Label(c_frame, text="  發行更改圖面給指定單位人員 → 指定人員按「收到」",
                  foreground='#888888', wraplength=380).pack(anchor=W, padx=(20, 0))

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(20, 0))
        ttk.Button(btn_frame, text="下一步", command=self._on_next,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _on_next(self):
        flow_type = self._flow_var.get()

        # 先釋放 grab 並隱藏自己，避免與子對話框的 grab 衝突
        self.grab_release()
        self.withdraw()

        try:
            if flow_type == 'A':
                dialog = FlowAIssueDialog(self._parent, self.drawing_id, self.rev_code)
            elif flow_type == 'B':
                dialog = FlowBIssueDialog(self._parent, self.drawing_id, self.rev_code)
            elif flow_type == 'C':
                dialog = FlowCIssueDialog(self._parent, self.drawing_id, self.rev_code)
            else:
                self.destroy()
                return

            if dialog.result:
                self.result = dialog.result
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            self.destroy()


# ============================================================
# A流程啟動對話框
# ============================================================

class FlowAIssueDialog(ttk.Toplevel):
    """A流程：客戶圖面 — 啟動對話框"""

    def __init__(self, parent, drawing_id, rev_code):
        super().__init__(parent)
        self.result = None
        self.drawing_id = drawing_id
        self.rev_code = rev_code

        self.title("A流程：客戶圖面")
        self.geometry("420x320")
        self.minsize(360, 280)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="A流程：客戶圖面",
                  font=('', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky=W, pady=(0, 5))

        ttk.Label(frame, text="流程：客戶寄圖 → 車工部整理 → 管理部寄客戶確認 → 客戶同意",
                  foreground='#888888', wraplength=360).grid(row=1, column=0, columnspan=2, sticky=W, pady=(0, 12))

        ttk.Label(frame, text=f"版次：{self.rev_code}").grid(row=2, column=0, columnspan=2, sticky=W, pady=3)

        ttk.Label(frame, text="發行人：").grid(row=3, column=0, sticky=W, pady=3)
        self.issuer_var = ttk.StringVar(value=DEFAULT_OPERATOR)
        ttk.Entry(frame, textvariable=self.issuer_var, width=20).grid(row=3, column=1, sticky=W, pady=3)

        ttk.Label(frame, text="備註：").grid(row=4, column=0, sticky=NW, pady=3)
        self.notes_text = ttk.Text(frame, width=35, height=3)
        self.notes_text.grid(row=4, column=1, sticky=NSEW, pady=3)
        frame.rowconfigure(4, weight=1)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn_frame, text="啟動流程", command=self._on_submit,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _on_submit(self):
        issuer = self.issuer_var.get().strip()
        if not issuer:
            ttk.dialogs.Messagebox.show_error("請輸入發行人", title="錯誤", parent=self)
            return

        notes = self.notes_text.get('1.0', 'end-1c').strip()

        try:
            order_id = queries.create_flow_a(
                self.drawing_id, self.rev_code, issuer, notes
            )
            self.result = order_id
            self.destroy()
        except Exception as e:
            import traceback
            traceback.print_exc()
            ttk.dialogs.Messagebox.show_error(f"啟動失敗：{e}", title="錯誤", parent=self)


# ============================================================
# B流程啟動對話框
# ============================================================

class FlowBIssueDialog(ttk.Toplevel):
    """B流程：劦佑圖面 — 選擇部門發行"""

    def __init__(self, parent, drawing_id, rev_code):
        super().__init__(parent)
        self.result = None
        self.drawing_id = drawing_id
        self.rev_code = rev_code

        self.title("B流程：劦佑圖面")
        self.geometry("460x440")
        self.minsize(400, 380)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)
        frame.rowconfigure(5, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="B流程：劦佑圖面",
                  font=('', 12, 'bold')).grid(row=0, column=0, sticky=W, pady=(0, 5))

        ttk.Label(frame, text="管理部發行給各單位 → 各單位按「收到通知」",
                  foreground='#888888', wraplength=400).grid(row=1, column=0, sticky=W, pady=(0, 10))

        # 發行資訊
        info_frame = ttk.Frame(frame)
        info_frame.grid(row=2, column=0, sticky=EW, pady=(0, 8))
        ttk.Label(info_frame, text=f"版次：{self.rev_code}").pack(side=LEFT, padx=(0, 15))
        ttk.Label(info_frame, text="發行人：").pack(side=LEFT)
        self.issuer_var = ttk.StringVar(value=DEFAULT_OPERATOR)
        ttk.Entry(info_frame, textvariable=self.issuer_var, width=15).pack(side=LEFT, padx=(5, 0))

        # 選擇部門
        dept_lf = ttk.LabelFrame(frame, text="選擇發行部門")
        dept_lf.grid(row=3, column=0, sticky=EW, pady=(0, 8))
        dept_inner = ttk.Frame(dept_lf, padding=10)
        dept_inner.pack(fill=BOTH, expand=True)

        self._dept_vars = {}
        departments = queries.get_departments()
        for dept in departments:
            name = dept['name']
            if name == '管理部':
                continue
            var = ttk.BooleanVar(value=True)
            cb = ttk.Checkbutton(dept_inner, text=name, variable=var)
            cb.pack(anchor=W, pady=2)
            self._dept_vars[name] = var

        # 備註
        ttk.Label(frame, text="備註：").grid(row=4, column=0, sticky=W)
        self.notes_text = ttk.Text(frame, width=40, height=3)
        self.notes_text.grid(row=5, column=0, sticky=NSEW, pady=(3, 8))

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, pady=(0, 5))
        ttk.Button(btn_frame, text="發行", command=self._on_submit,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _on_submit(self):
        issuer = self.issuer_var.get().strip()
        if not issuer:
            ttk.dialogs.Messagebox.show_error("請輸入發行人", title="錯誤", parent=self)
            return

        selected = [name for name, var in self._dept_vars.items() if var.get()]
        if not selected:
            ttk.dialogs.Messagebox.show_error("請至少選擇一個部門", title="錯誤", parent=self)
            return

        notes = self.notes_text.get('1.0', 'end-1c').strip()

        try:
            order_id = queries.create_flow_b(
                self.drawing_id, self.rev_code, issuer, selected, notes
            )
            self.result = order_id
            self.destroy()
        except Exception as e:
            import traceback
            traceback.print_exc()
            ttk.dialogs.Messagebox.show_error(f"發行失敗：{e}", title="錯誤", parent=self)


# ============================================================
# C流程啟動對話框
# ============================================================

class FlowCIssueDialog(ttk.Toplevel):
    """C流程：修改發行 — 指定部門+人員"""

    def __init__(self, parent, drawing_id, rev_code):
        super().__init__(parent)
        self.result = None
        self.drawing_id = drawing_id
        self.rev_code = rev_code

        self.title("C流程：修改發行")
        self.geometry("500x480")
        self.minsize(440, 400)
        self.transient(parent)
        self.grab_set()

        self._person_rows = []
        self._create_widgets()
        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)
        frame.rowconfigure(4, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="C流程：修改發行",
                  font=('', 12, 'bold')).grid(row=0, column=0, sticky=W, pady=(0, 5))

        ttk.Label(frame, text="發行更改圖面給指定單位人員 → 指定人員按「收到」",
                  foreground='#888888', wraplength=440).grid(row=1, column=0, sticky=W, pady=(0, 10))

        # 發行資訊
        info_frame = ttk.Frame(frame)
        info_frame.grid(row=2, column=0, sticky=EW, pady=(0, 8))
        ttk.Label(info_frame, text=f"版次：{self.rev_code}").pack(side=LEFT, padx=(0, 15))
        ttk.Label(info_frame, text="發行人：").pack(side=LEFT)
        self.issuer_var = ttk.StringVar(value=DEFAULT_OPERATOR)
        ttk.Entry(info_frame, textvariable=self.issuer_var, width=15).pack(side=LEFT, padx=(5, 0))

        # 指定人員區
        person_lf = ttk.LabelFrame(frame, text="指定接收人員")
        person_lf.grid(row=3, column=0, sticky=EW, pady=(0, 8))
        person_inner = ttk.Frame(person_lf, padding=10)
        person_inner.pack(fill=BOTH, expand=True)

        self._persons_frame = person_inner

        # 取得部門列表
        self._dept_names = [d['name'] for d in queries.get_departments()]

        # 預設加一列
        self._add_person_row()

        ttk.Button(person_inner, text="+ 新增一列", command=self._add_person_row,
                   bootstyle=INFO+OUTLINE, width=12).pack(anchor=W, pady=(5, 0))

        # 備註
        ttk.Label(frame, text="備註：").grid(row=4, column=0, sticky=NW)
        self.notes_text = ttk.Text(frame, width=40, height=2)
        self.notes_text.grid(row=5, column=0, sticky=NSEW, pady=(3, 8))

        # 按鈕
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, pady=(0, 5))
        ttk.Button(btn_frame, text="發行", command=self._on_submit,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

    def _add_person_row(self):
        row_frame = ttk.Frame(self._persons_frame)
        row_frame.pack(fill=X, pady=2)

        ttk.Label(row_frame, text="部門：").pack(side=LEFT)
        dept_var = ttk.StringVar(value=self._dept_names[0] if self._dept_names else '')
        dept_combo = ttk.Combobox(row_frame, textvariable=dept_var,
                                   values=self._dept_names, width=10, state='readonly')
        dept_combo.pack(side=LEFT, padx=(2, 10))

        ttk.Label(row_frame, text="人員：").pack(side=LEFT)
        person_var = ttk.StringVar()
        ttk.Entry(row_frame, textvariable=person_var, width=12).pack(side=LEFT, padx=(2, 5))

        # 刪除按鈕
        def remove_row():
            row_frame.destroy()
            self._person_rows = [(d, p, f) for d, p, f in self._person_rows if f != row_frame]

        ttk.Button(row_frame, text="✕", command=remove_row,
                   bootstyle=DANGER+OUTLINE, width=3).pack(side=LEFT)

        self._person_rows.append((dept_var, person_var, row_frame))

    def _on_submit(self):
        issuer = self.issuer_var.get().strip()
        if not issuer:
            ttk.dialogs.Messagebox.show_error("請輸入發行人", title="錯誤", parent=self)
            return

        dept_person_list = []
        for dept_var, person_var, _ in self._person_rows:
            dept = dept_var.get().strip()
            person = person_var.get().strip()
            if dept and person:
                dept_person_list.append({'department': dept, 'assignee': person})

        if not dept_person_list:
            ttk.dialogs.Messagebox.show_error("請至少指定一位接收人員", title="錯誤", parent=self)
            return

        notes = self.notes_text.get('1.0', 'end-1c').strip()

        try:
            order_id = queries.create_flow_c(
                self.drawing_id, self.rev_code, issuer, dept_person_list, notes
            )
            self.result = order_id
            self.destroy()
        except Exception as e:
            import traceback
            traceback.print_exc()
            ttk.dialogs.Messagebox.show_error(f"發行失敗：{e}", title="錯誤", parent=self)


# ============================================================
# 收到確認對話框（B/C流程共用）
# ============================================================

class ReceiptConfirmDialog(ttk.Toplevel):
    """選擇哪個部門/人員確認收到"""

    def __init__(self, parent, order_id, flow_type):
        super().__init__(parent)
        self.result = None
        self.order_id = order_id
        self.flow_type = flow_type

        title = "確認收到通知" if flow_type == 'B' else "確認收到更改圖面"
        self.title(title)
        self.geometry("440x380")
        self.minsize(380, 300)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self.wait_window()

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="選擇要確認收到的項目：",
                  font=('', 11, 'bold')).pack(anchor=W, pady=(0, 8))

        # 操作者
        op_frame = ttk.Frame(frame)
        op_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(op_frame, text="確認人：").pack(side=LEFT)
        self.operator_var = ttk.StringVar(value=DEFAULT_OPERATOR)
        ttk.Entry(op_frame, textvariable=self.operator_var, width=15).pack(side=LEFT, padx=(5, 0))

        # 任務列表（可捲動）
        scroll_container = ttk.Frame(frame)
        scroll_container.pack(fill=BOTH, expand=True, pady=(0, 8))

        import tkinter as tk
        canvas = tk.Canvas(scroll_container, highlightthickness=0)
        v_scroll = ttk.Scrollbar(scroll_container, orient=VERTICAL, command=canvas.yview)
        inner_frame = ttk.Frame(canvas)

        inner_frame.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner_frame, anchor=NW)
        canvas.configure(yscrollcommand=v_scroll.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        v_scroll.pack(side=RIGHT, fill=Y)

        # 滾輪支援
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        inner_frame.bind("<MouseWheel>", _on_mousewheel)

        tasks = queries.get_circulation_tasks(self.order_id)

        for task in tasks:
            task_frame = ttk.Frame(inner_frame)
            task_frame.pack(fill=X, pady=3, padx=2)

            status = task['status']
            if status == '已收到':
                icon = '\u2714'  # ✔
                color = '#6BBF7B'
                info = f"{task['department']}"
                if _rget(task, 'assignee'):
                    info += f" — {task['assignee']}"
                info += f"  {icon} 已收到"
                if _rget(task, 'received_by'):
                    info += f"  ({task['received_by']})"
                if _rget(task, 'received_at'):
                    info += f"  {(task['received_at'] or '')[:16]}"
                ttk.Label(task_frame, text=info, foreground=color).pack(anchor=W)
            else:
                info = f"{task['department']}"
                if _rget(task, 'assignee'):
                    info += f" — {task['assignee']}"
                info += f"  ⏳ {status}"

                ttk.Label(task_frame, text=info, foreground='#E8B84B').pack(side=LEFT)

                def _confirm(tid=task['id'], tf=task_frame):
                    self._do_confirm(tid, tf)

                ttk.Button(task_frame, text="確認收到", command=_confirm,
                           bootstyle=SUCCESS, width=8).pack(side=RIGHT, padx=(10, 0))

        # 關閉按鈕
        ttk.Button(frame, text="關閉", command=self._on_close,
                   bootstyle=SECONDARY, width=10).pack(pady=(5, 0))

    def _do_confirm(self, task_id, task_frame):
        operator = self.operator_var.get().strip() or DEFAULT_OPERATOR
        try:
            if self.flow_type == 'B':
                queries.confirm_receipt_b(task_id, operator)
            else:
                queries.confirm_receipt_c(task_id, operator)

            # 更新該行的顯示
            for w in task_frame.winfo_children():
                w.destroy()
            ttk.Label(task_frame, text=f"\u2714 已確認收到 ({operator})",
                      foreground='#6BBF7B').pack(anchor=W)
            self.result = True
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(f"確認失敗：{e}", title="錯誤", parent=self)

    def _on_close(self):
        if self.result is None:
            self.result = False
        self.destroy()


# ============================================================
# 發行流程面板 — 嵌入在 detail_panel 中
# 佈局：左右分割（左=按鈕+流程資訊, 右=歷程紀錄）
# ============================================================

class CirculationFlowPanel(ttk.LabelFrame):
    """發行流程面板 — 根據 flow_type 顯示不同 UI

    左右兩格佈局：
      左側：操作按鈕（固定上方）+ 流程資訊/步驟
      右側：歷程紀錄 Treeview
    """

    # A流程步驟圖示
    STEP_ICONS = {
        '已完成': '\u2714',   # ✔
        '進行中': '\u25b6',   # ▶
        '待處理': '\u25a1',   # □
    }

    STEP_COLORS = {
        '已完成': '#6BBF7B',
        '進行中': '#5B9BD5',
        '待處理': '#A6A6A6',
    }

    # B/C流程圖示
    RECEIPT_ICONS = {
        '已收到': '\u2714',   # ✔
        '待通知': '\u25a1',   # □
    }

    RECEIPT_COLORS = {
        '已收到': '#6BBF7B',
        '待通知': '#E8B84B',
    }

    def __init__(self, parent):
        super().__init__(parent, text="發行流程")
        self._drawing_id = None
        self._rev_code = None
        self._order = None
        self._tasks = []
        self._create_widgets()

    def _create_widgets(self):
        import tkinter as tk
        from config import FONT_FAMILY

        # 左右分割用 PanedWindow
        self._hpaned = tk.PanedWindow(
            self, orient=tk.HORIZONTAL,
            sashrelief=tk.FLAT, sashwidth=4,
            bg='#D8D8D8', opaqueresize=True
        )
        self._hpaned.pack(fill=BOTH, expand=True, padx=2, pady=2)

        # ========== 左側：操作按鈕 + 流程資訊 ==========
        left_frame = ttk.Frame(self._hpaned)

        # 操作按鈕區（固定在上方）
        self.btn_frame = ttk.Frame(left_frame, padding=(6, 4))
        self.btn_frame.pack(side=TOP, fill=X)
        ttk.Separator(left_frame, orient=HORIZONTAL).pack(side=TOP, fill=X)

        # 流程內容（可捲動）
        left_scroll = ttk.Frame(left_frame, padding=6)
        left_scroll.pack(fill=BOTH, expand=True)

        # 流程資訊
        self.info_var = ttk.StringVar()
        self.info_label = ttk.Label(left_scroll, textvariable=self.info_var,
                                     wraplength=280, font=(FONT_FAMILY, 9))
        self.info_label.pack(anchor=W)

        # 任務/步驟顯示區（動態生成）
        self.tasks_frame = ttk.Frame(left_scroll)
        self.tasks_frame.pack(fill=X, pady=(5, 0))

        # 客戶同意日期（A流程專用）
        self.approval_date_var = ttk.StringVar()
        self.approval_date_label = ttk.Label(
            left_scroll, textvariable=self.approval_date_var,
            foreground='#6BBF7B', font=(FONT_FAMILY, 9, 'bold'))
        self.approval_date_label.pack(anchor=W, pady=(3, 0))

        self._hpaned.add(left_frame, minsize=200, stretch='always')

        # ========== 右側：歷程紀錄 ==========
        right_frame = ttk.LabelFrame(self._hpaned, text="歷程紀錄")
        right_inner = ttk.Frame(right_frame, padding=4)
        right_inner.pack(fill=BOTH, expand=True)

        log_cols = ('log_time', 'log_operator', 'log_action', 'log_dept', 'log_desc')
        self.log_tree = ttk.Treeview(right_inner, columns=log_cols, show='headings', height=5)
        self.log_tree.heading('log_time', text='時間')
        self.log_tree.heading('log_operator', text='操作者')
        self.log_tree.heading('log_action', text='動作')
        self.log_tree.heading('log_dept', text='部門')
        self.log_tree.heading('log_desc', text='說明')
        self.log_tree.column('log_time', width=100, minwidth=80)
        self.log_tree.column('log_operator', width=55, minwidth=45)
        self.log_tree.column('log_action', width=60, minwidth=45)
        self.log_tree.column('log_dept', width=50, minwidth=40)
        self.log_tree.column('log_desc', width=100, minwidth=70)

        log_scroll = ttk.Scrollbar(right_inner, orient=VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=log_scroll.set)
        self.log_tree.pack(side=LEFT, fill=BOTH, expand=True)
        log_scroll.pack(side=RIGHT, fill=Y)

        self._hpaned.add(right_frame, minsize=200, stretch='always')

        # 保留字體參照供 render 使用
        self._font = (FONT_FAMILY, 9)
        self._font_bold = (FONT_FAMILY, 9, 'bold')

    def load(self, drawing_id, rev_code=None):
        """載入指定圖面的流程"""
        self._drawing_id = drawing_id
        self._rev_code = rev_code
        self._order = queries.get_active_flow(drawing_id)
        if self._order:
            self._tasks = queries.get_circulation_tasks(self._order['id'])
        else:
            self._tasks = []
        self._refresh_ui()

    def clear(self):
        """清除面板"""
        self._drawing_id = None
        self._rev_code = None
        self._order = None
        self._tasks = []
        self._clear_dynamic()
        self.info_var.set('')
        self.approval_date_var.set('')
        self.log_tree.delete(*self.log_tree.get_children())

    def _clear_dynamic(self):
        """清除動態生成的元件"""
        for w in self.tasks_frame.winfo_children():
            w.destroy()
        for w in self.btn_frame.winfo_children():
            w.destroy()

    def _refresh_ui(self):
        self._clear_dynamic()
        self.approval_date_var.set('')

        if not self._order:
            self._render_no_flow()
            return

        flow_type = _rget(self._order, 'flow_type', 'B')

        if flow_type == 'A':
            self._render_flow_a()
        elif flow_type == 'B':
            self._render_flow_b()
        elif flow_type == 'C':
            self._render_flow_c()
        else:
            # 舊版流程（相容）
            self._render_flow_b()

        self._load_logs()

    def _render_no_flow(self):
        """無流程時顯示"""
        self.info_var.set('尚未啟動發行流程')
        self.log_tree.delete(*self.log_tree.get_children())

        if self._drawing_id:
            ttk.Button(self.btn_frame, text="啟動新流程", command=self._start_new_flow,
                       bootstyle=SUCCESS, width=12).pack(side=LEFT, padx=2, pady=2)

    # ========== A流程 ==========

    def _render_flow_a(self):
        order = self._order
        step = _rget(order, 'flow_a_step', FLOW_A_STEPS[0])
        status = order['status']

        flow_label = FLOW_TYPES.get('A', 'A流程')
        self.info_var.set(
            f"{flow_label}  狀態：{status}\n"
            f"發行人：{order['issued_by']}  日期：{(order['issued_at'] or '')[:16]}"
        )

        # 顯示步驟
        for task in self._tasks:
            row = ttk.Frame(self.tasks_frame)
            row.pack(fill=X, pady=2)

            task_status = task['status']
            icon = self.STEP_ICONS.get(task_status, '?')
            color = self.STEP_COLORS.get(task_status, '#999999')

            step_text = f"步驟{_rget(task, 'step_number', '')}：{_rget(task, 'step_name', task['department'])}"
            ttk.Label(row, text=f"{icon} {step_text}",
                      foreground=color, font=self._font, anchor=W).pack(side=LEFT)

            ttk.Label(row, text=task_status, foreground=color,
                      font=self._font, width=6).pack(side=LEFT)

            time_str = ''
            if _rget(task, 'confirmed_at'):
                time_str = (task['confirmed_at'] or '')[:16]
            ttk.Label(row, text=time_str, foreground='#999999',
                      font=self._font).pack(side=LEFT, padx=(5, 0))

        # 客戶同意日期
        if _rget(order, 'client_approval_date'):
            self.approval_date_var.set(f"客戶同意日期：{order['client_approval_date'][:16]}")
        elif status != '已完成' and status != '已取消':
            self.approval_date_var.set("客戶同意日期：（尚未完成）")

        # 操作按鈕
        if status == '發行中':
            ttk.Button(self.btn_frame, text="推進到下一步", command=self._advance_a,
                       bootstyle=PRIMARY, width=14).pack(side=LEFT, padx=2, pady=2)

        if status not in ('已完成', '已取消'):
            ttk.Button(self.btn_frame, text="取消流程", command=self._cancel_flow,
                       bootstyle=DANGER+OUTLINE, width=10).pack(side=LEFT, padx=2, pady=2)

        if status in ('已完成', '已取消'):
            ttk.Button(self.btn_frame, text="啟動新流程", command=self._start_new_flow,
                       bootstyle=SUCCESS, width=12).pack(side=LEFT, padx=2, pady=2)

    # ========== B流程 ==========

    def _render_flow_b(self):
        order = self._order
        status = order['status']

        flow_label = FLOW_TYPES.get('B', 'B流程')
        self.info_var.set(
            f"{flow_label}  狀態：{status}\n"
            f"發行人：{order['issued_by']}  日期：{(order['issued_at'] or '')[:16]}"
        )

        for task in self._tasks:
            row = ttk.Frame(self.tasks_frame)
            row.pack(fill=X, pady=2)

            task_status = task['status']
            icon = self.RECEIPT_ICONS.get(task_status, '?')
            color = self.RECEIPT_COLORS.get(task_status, '#999999')

            dept_text = f"{icon} {task['department']}"
            ttk.Label(row, text=dept_text, foreground=color,
                      font=self._font, anchor=W).pack(side=LEFT, padx=(0, 6))

            # 收到人
            received = _rget(task, 'received_by') or _rget(task, 'assignee') or '—'
            ttk.Label(row, text=received, foreground='#888888',
                      font=self._font).pack(side=LEFT, padx=(0, 6))

            ttk.Label(row, text=task_status, foreground=color,
                      font=self._font).pack(side=LEFT, padx=(0, 6))

            # 收到時間
            time_str = ''
            if _rget(task, 'received_at'):
                time_str = (task['received_at'] or '')[:16]
            ttk.Label(row, text=time_str, foreground='#999999',
                      font=self._font).pack(side=LEFT)

        # 操作按鈕
        has_pending = any(t['status'] == '待通知' for t in self._tasks)

        if status == '發行中' and has_pending:
            ttk.Button(self.btn_frame, text="確認收到", command=self._confirm_receipt_b,
                       bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2, pady=2)

        if status not in ('已完成', '已取消'):
            ttk.Button(self.btn_frame, text="取消流程", command=self._cancel_flow,
                       bootstyle=DANGER+OUTLINE, width=10).pack(side=LEFT, padx=2, pady=2)

        if status in ('已完成', '已取消'):
            ttk.Button(self.btn_frame, text="啟動新流程", command=self._start_new_flow,
                       bootstyle=SUCCESS, width=12).pack(side=LEFT, padx=2, pady=2)

    # ========== C流程 ==========

    def _render_flow_c(self):
        order = self._order
        status = order['status']

        flow_label = FLOW_TYPES.get('C', 'C流程')
        self.info_var.set(
            f"{flow_label}  狀態：{status}\n"
            f"發行人：{order['issued_by']}  日期：{(order['issued_at'] or '')[:16]}"
        )

        for task in self._tasks:
            row = ttk.Frame(self.tasks_frame)
            row.pack(fill=X, pady=2)

            task_status = task['status']
            icon = self.RECEIPT_ICONS.get(task_status, '?')
            color = self.RECEIPT_COLORS.get(task_status, '#999999')

            dept_text = f"{icon} {task['department']}"
            ttk.Label(row, text=dept_text, foreground=color,
                      font=self._font, anchor=W).pack(side=LEFT, padx=(0, 6))

            # 指定人員
            assignee = _rget(task, 'assignee') or '—'
            ttk.Label(row, text=assignee, foreground='#888888',
                      font=self._font).pack(side=LEFT, padx=(0, 6))

            ttk.Label(row, text=task_status, foreground=color,
                      font=self._font).pack(side=LEFT, padx=(0, 6))

            # 收到時間
            time_str = ''
            if _rget(task, 'received_at'):
                time_str = (task['received_at'] or '')[:16]
            ttk.Label(row, text=time_str, foreground='#999999',
                      font=self._font).pack(side=LEFT)

        # 操作按鈕
        has_pending = any(t['status'] == '待通知' for t in self._tasks)

        if status == '發行中' and has_pending:
            ttk.Button(self.btn_frame, text="確認收到", command=self._confirm_receipt_c,
                       bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2, pady=2)

        if status not in ('已完成', '已取消'):
            ttk.Button(self.btn_frame, text="取消流程", command=self._cancel_flow,
                       bootstyle=DANGER+OUTLINE, width=10).pack(side=LEFT, padx=2, pady=2)

        if status in ('已完成', '已取消'):
            ttk.Button(self.btn_frame, text="啟動新流程", command=self._start_new_flow,
                       bootstyle=SUCCESS, width=12).pack(side=LEFT, padx=2, pady=2)

    # ========== 歷程紀錄 ==========

    def _load_logs(self):
        self.log_tree.delete(*self.log_tree.get_children())
        if not self._order:
            return
        logs = queries.get_circulation_logs(self._order['id'])
        for log in logs:
            self.log_tree.insert('', 'end', values=(
                (log['created_at'] or '')[:16],
                log['operator'] or '',
                log['action'] or '',
                log['department'] or '',
                (log['description'] or '')[:40],
            ))

    # ========== 操作函數 ==========

    def _start_new_flow(self):
        if not self._drawing_id:
            return
        drawing = queries.get_drawing(self._drawing_id)
        rev_code = self._rev_code or (drawing['current_rev'] if drawing else 'A')

        dialog = FlowTypeSelectDialog(
            self.winfo_toplevel(), self._drawing_id, rev_code
        )
        if dialog.result:
            self.load(self._drawing_id, rev_code)
            self._notify_parent_refresh()

    def _advance_a(self):
        if not self._order:
            return
        step = _rget(self._order, 'flow_a_step', '')
        confirm = ttk.dialogs.Messagebox.yesno(
            f"確定完成目前步驟「{step}」並推進到下一步？",
            title="推進流程",
            parent=self.winfo_toplevel()
        )
        if confirm == "Yes":
            try:
                queries.advance_flow_a(self._order['id'], DEFAULT_OPERATOR)
                self.load(self._drawing_id, self._rev_code)
                self._notify_parent_refresh()
            except Exception as e:
                ttk.dialogs.Messagebox.show_error(f"操作失敗：{e}", title="錯誤",
                                                   parent=self.winfo_toplevel())

    def _confirm_receipt_b(self):
        if not self._order:
            return
        dialog = ReceiptConfirmDialog(
            self.winfo_toplevel(), self._order['id'], 'B'
        )
        if dialog.result:
            self.load(self._drawing_id, self._rev_code)
            self._notify_parent_refresh()

    def _confirm_receipt_c(self):
        if not self._order:
            return
        dialog = ReceiptConfirmDialog(
            self.winfo_toplevel(), self._order['id'], 'C'
        )
        if dialog.result:
            self.load(self._drawing_id, self._rev_code)
            self._notify_parent_refresh()

    def _cancel_flow(self):
        if not self._order:
            return
        confirm = ttk.dialogs.Messagebox.yesno(
            "確定要取消此發行流程？",
            title="取消流程",
            parent=self.winfo_toplevel()
        )
        if confirm == "Yes":
            try:
                queries.cancel_order(self._order['id'], DEFAULT_OPERATOR)
                self.load(self._drawing_id, self._rev_code)
                self._notify_parent_refresh()
            except Exception as e:
                ttk.dialogs.Messagebox.show_error(f"操作失敗：{e}", title="錯誤",
                                                   parent=self.winfo_toplevel())

    def _notify_parent_refresh(self):
        """向上尋找 DetailPanel 觸發刷新

        PanedWindow 的 parent chain:
          CirculationFlowPanel → PanedWindow(._vpaned) → DetailPanel
        """
        # 直接透過 winfo 往上找
        widget = self
        for _ in range(20):
            widget = getattr(widget, 'master', None)
            if widget is None:
                break
            if hasattr(widget, 'load_drawing') and hasattr(widget, '_current_drawing_id'):
                if widget._current_drawing_id:
                    widget.load_drawing(widget._current_drawing_id)
                if hasattr(widget, 'on_refresh') and widget.on_refresh:
                    widget.on_refresh()
                return
