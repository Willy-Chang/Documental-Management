"""機器維修彙報紀錄模組"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from db import business_queries as bq
from config import (MACHINE_STATUS, MAINTENANCE_TYPES, MAINTENANCE_STATUS,
                    DEPARTMENTS, DEFAULT_OPERATOR, FONT_FAMILY)


class MaintenanceModule(ttk.Frame):
    """機器維修管理模組"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_toolbar()
        self._create_content()
        self.refresh()

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=(5, 5))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="機器維修管理", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="+ 新增機器", command=self._add_machine,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="編輯機器", command=self._edit_machine,
                   bootstyle=INFO, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除機器", command=self._delete_machine,
                   bootstyle=DANGER, width=10).pack(side=LEFT, padx=2)

        ttk.Separator(toolbar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=8, pady=2)

        ttk.Button(toolbar, text="+ 維修紀錄", command=self._add_record,
                   bootstyle=WARNING, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="編輯紀錄", command=self._edit_record,
                   bootstyle=INFO+OUTLINE, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除紀錄", command=self._delete_record,
                   bootstyle=DANGER+OUTLINE, width=10).pack(side=LEFT, padx=2)

    def _create_content(self):
        paned = ttk.PanedWindow(self, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 上方：機器清單
        machine_frame = ttk.LabelFrame(paned, text="機器設備清單", padding=5)
        paned.add(machine_frame, weight=2)

        machine_toolbar = ttk.Frame(machine_frame)
        machine_toolbar.pack(fill=X, pady=(0, 3))
        ttk.Label(machine_toolbar, text="狀態：").pack(side=LEFT, padx=(0, 2))
        self.filter_machine_status = ttk.Combobox(
            machine_toolbar, values=['全部'] + MACHINE_STATUS,
            width=10, state='readonly')
        self.filter_machine_status.set('全部')
        self.filter_machine_status.pack(side=LEFT, padx=2)
        self.filter_machine_status.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        cols = ('id', 'code', 'name', 'model', 'mfr', 'dept', 'location', 'status')
        self.machine_tree = ttk.Treeview(machine_frame, columns=cols,
                                         show='headings', height=7)
        self.machine_tree.heading('id', text='ID')
        self.machine_tree.heading('code', text='機器編號')
        self.machine_tree.heading('name', text='機器名稱')
        self.machine_tree.heading('model', text='型號')
        self.machine_tree.heading('mfr', text='製造商')
        self.machine_tree.heading('dept', text='部門')
        self.machine_tree.heading('location', text='位置')
        self.machine_tree.heading('status', text='狀態')
        self.machine_tree.column('id', width=30, anchor=CENTER)
        self.machine_tree.column('code', width=90)
        self.machine_tree.column('name', width=130)
        self.machine_tree.column('model', width=100)
        self.machine_tree.column('mfr', width=100)
        self.machine_tree.column('dept', width=70)
        self.machine_tree.column('location', width=80)
        self.machine_tree.column('status', width=60, anchor=CENTER)

        m_scroll = ttk.Scrollbar(machine_frame, orient=VERTICAL,
                                 command=self.machine_tree.yview)
        self.machine_tree.configure(yscrollcommand=m_scroll.set)
        self.machine_tree.pack(side=LEFT, fill=BOTH, expand=True)
        m_scroll.pack(side=RIGHT, fill=Y)
        self.machine_tree.bind('<<TreeviewSelect>>', self._on_machine_select)
        self.machine_tree.bind('<Double-1>', lambda e: self._edit_machine())

        # 下方：維修紀錄
        record_frame = ttk.LabelFrame(paned, text="維修紀錄", padding=5)
        paned.add(record_frame, weight=3)

        record_toolbar = ttk.Frame(record_frame)
        record_toolbar.pack(fill=X, pady=(0, 3))
        ttk.Label(record_toolbar, text="篩選：").pack(side=LEFT, padx=(0, 2))
        self.filter_mr_status = ttk.Combobox(
            record_toolbar, values=['全部'] + MAINTENANCE_STATUS,
            width=10, state='readonly')
        self.filter_mr_status.set('全部')
        self.filter_mr_status.pack(side=LEFT, padx=2)
        self.filter_mr_status.bind('<<ComboboxSelected>>', lambda e: self._on_machine_select())

        self.mr_summary = ttk.Label(record_toolbar, text="",
                                    font=(FONT_FAMILY, 10, 'bold'))
        self.mr_summary.pack(side=RIGHT, padx=10)

        r_cols = ('id', 'type', 'desc', 'reported_by', 'reported_at',
                  'assigned', 'cause', 'solution', 'cost', 'downtime', 'status')
        self.record_tree = ttk.Treeview(record_frame, columns=r_cols,
                                        show='headings', height=8)
        self.record_tree.heading('id', text='ID')
        self.record_tree.heading('type', text='維修類型')
        self.record_tree.heading('desc', text='問題描述')
        self.record_tree.heading('reported_by', text='回報人')
        self.record_tree.heading('reported_at', text='回報時間')
        self.record_tree.heading('assigned', text='處理人')
        self.record_tree.heading('cause', text='原因')
        self.record_tree.heading('solution', text='處理方式')
        self.record_tree.heading('cost', text='費用')
        self.record_tree.heading('downtime', text='停機(hr)')
        self.record_tree.heading('status', text='狀態')
        self.record_tree.column('id', width=30, anchor=CENTER)
        self.record_tree.column('type', width=70)
        self.record_tree.column('desc', width=160)
        self.record_tree.column('reported_by', width=60)
        self.record_tree.column('reported_at', width=90)
        self.record_tree.column('assigned', width=60)
        self.record_tree.column('cause', width=100)
        self.record_tree.column('solution', width=100)
        self.record_tree.column('cost', width=60, anchor=E)
        self.record_tree.column('downtime', width=55, anchor=E)
        self.record_tree.column('status', width=55, anchor=CENTER)

        r_scroll = ttk.Scrollbar(record_frame, orient=VERTICAL,
                                 command=self.record_tree.yview)
        self.record_tree.configure(yscrollcommand=r_scroll.set)
        self.record_tree.pack(side=LEFT, fill=BOTH, expand=True)
        r_scroll.pack(side=RIGHT, fill=Y)
        self.record_tree.bind('<Double-1>', lambda e: self._edit_record())

    def refresh(self):
        ms = self.filter_machine_status.get()
        status = None if ms == '全部' else ms
        machines = bq.get_all_machines(status=status)
        self.machine_tree.delete(*self.machine_tree.get_children())
        for m in machines:
            self.machine_tree.insert('', END, values=(
                m['id'], m['machine_code'], m['machine_name'],
                m['model'] or '', m['manufacturer'] or '',
                m['department'] or '', m['location'] or '', m['status']
            ))
        self.record_tree.delete(*self.record_tree.get_children())
        self.mr_summary.config(text="")

    def _get_selected_machine_id(self):
        sel = self.machine_tree.selection()
        return self.machine_tree.item(sel[0])['values'][0] if sel else None

    def _get_selected_record_id(self):
        sel = self.record_tree.selection()
        return self.record_tree.item(sel[0])['values'][0] if sel else None

    def _on_machine_select(self, event=None):
        mid = self._get_selected_machine_id()
        if not mid:
            return
        mr_status = self.filter_mr_status.get()
        status = None if mr_status == '全部' else mr_status
        records = bq.get_all_maintenance_records(machine_id=mid, status=status)
        self.record_tree.delete(*self.record_tree.get_children())
        total_cost = 0
        total_downtime = 0
        for r in records:
            cost = float(r['cost'] or 0)
            dt = float(r['downtime_hours'] or 0)
            total_cost += cost
            total_downtime += dt
            self.record_tree.insert('', END, values=(
                r['id'], r['maintenance_type'], r['description'],
                r['reported_by'], r['reported_at'][:16] if r['reported_at'] else '',
                r['assigned_to'] or '', r['cause'] or '',
                r['solution'] or '', f'{cost:,.0f}', f'{dt:.1f}', r['status']
            ))
        self.mr_summary.config(
            text=f"共 {len(records)} 筆 | 總費用：${total_cost:,.0f} | 總停機：{total_downtime:.1f} hr"
        )

    # === 機器 CRUD ===

    def _add_machine(self):
        dlg = MachineDialog(self.winfo_toplevel())
        if dlg.result:
            self.refresh()

    def _edit_machine(self):
        mid = self._get_selected_machine_id()
        if not mid:
            ttk.dialogs.Messagebox.show_info("請先選擇一台機器", parent=self.winfo_toplevel())
            return
        dlg = MachineDialog(self.winfo_toplevel(), machine_id=mid)
        if dlg.result:
            self.refresh()

    def _delete_machine(self):
        mid = self._get_selected_machine_id()
        if not mid:
            return
        if ttk.dialogs.Messagebox.yesno("確定要刪除此機器？", parent=self.winfo_toplevel()) == '是':
            bq.delete_machine(mid)
            self.refresh()

    # === 維修紀錄 CRUD ===

    def _add_record(self):
        mid = self._get_selected_machine_id()
        if not mid:
            ttk.dialogs.Messagebox.show_info("請先選擇一台機器", parent=self.winfo_toplevel())
            return
        dlg = MaintenanceRecordDialog(self.winfo_toplevel(), machine_id=mid)
        if dlg.result:
            self._on_machine_select()

    def _edit_record(self):
        rid = self._get_selected_record_id()
        mid = self._get_selected_machine_id()
        if not rid or not mid:
            return
        dlg = MaintenanceRecordDialog(self.winfo_toplevel(), machine_id=mid, record_id=rid)
        if dlg.result:
            self._on_machine_select()

    def _delete_record(self):
        rid = self._get_selected_record_id()
        if rid:
            bq.delete_maintenance_record(rid)
            self._on_machine_select()


class MachineDialog(ttk.Toplevel):
    """機器設備對話框"""

    def __init__(self, parent, machine_id=None):
        super().__init__(parent)
        self.result = None
        self.machine_id = machine_id
        self.title("編輯機器" if machine_id else "新增機器")
        self.geometry("450x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        fields = [
            ('機器編號', 'machine_code', 20),
            ('機器名稱', 'machine_name', 25),
            ('型號', 'model', 20),
            ('製造商', 'manufacturer', 20),
            ('位置', 'location', 20),
        ]
        self.entries = {}
        for i, (label, key, width) in enumerate(fields):
            ttk.Label(frame, text=f"{label}：").grid(row=i, column=0, sticky=W, pady=3)
            e = ttk.Entry(frame, width=width)
            e.grid(row=i, column=1, sticky=W, pady=3)
            self.entries[key] = e

        row = len(fields)
        ttk.Label(frame, text="部門：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_dept = ttk.Combobox(frame, values=DEPARTMENTS, width=15)
        self.e_dept.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=MACHINE_STATUS, width=10, state='readonly')
        self.e_status.set('正常')
        self.e_status.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="備註：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_notes = ttk.Text(frame, width=30, height=3)
        self.e_notes.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        if machine_id:
            m = bq.get_machine(machine_id)
            if m:
                for key, entry in self.entries.items():
                    val = m[key] or ''
                    entry.insert(0, str(val))
                if m['department']:
                    self.e_dept.set(m['department'])
                self.e_status.set(m['status'] or '正常')
                if m['notes']:
                    self.e_notes.insert('1.0', m['notes'])

        self.wait_window()

    def _on_ok(self):
        code = self.entries['machine_code'].get().strip()
        name = self.entries['machine_name'].get().strip()
        if not code or not name:
            ttk.dialogs.Messagebox.show_warning("機器編號與名稱為必填", parent=self)
            return

        data = {k: e.get().strip() or None for k, e in self.entries.items()}
        data['department'] = self.e_dept.get().strip() or None
        data['status'] = self.e_status.get()
        data['notes'] = self.e_notes.get('1.0', 'end').strip() or None

        if self.machine_id:
            bq.update_machine(self.machine_id, **data)
        else:
            bq.add_machine(**data)

        self.result = True
        self.destroy()


class MaintenanceRecordDialog(ttk.Toplevel):
    """維修紀錄對話框"""

    def __init__(self, parent, machine_id, record_id=None):
        super().__init__(parent)
        self.result = None
        self.machine_id = machine_id
        self.record_id = record_id
        self.title("編輯維修紀錄" if record_id else "新增維修紀錄")
        self.geometry("500x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="維修類型：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_type = ttk.Combobox(frame, values=MAINTENANCE_TYPES, width=15, state='readonly')
        self.e_type.set('故障維修')
        self.e_type.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="問題描述：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_desc = ttk.Text(frame, width=35, height=3)
        self.e_desc.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="回報人：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_reporter = ttk.Entry(frame, width=15)
        self.e_reporter.insert(0, DEFAULT_OPERATOR)
        self.e_reporter.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="處理人：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_assigned = ttk.Entry(frame, width=15)
        self.e_assigned.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="原因：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_cause = ttk.Text(frame, width=35, height=2)
        self.e_cause.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="處理方式：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_solution = ttk.Text(frame, width=35, height=2)
        self.e_solution.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="使用零件：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_parts = ttk.Entry(frame, width=30)
        self.e_parts.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="費用：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_cost = ttk.Entry(frame, width=10)
        self.e_cost.insert(0, '0')
        self.e_cost.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="停機時數：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_downtime = ttk.Entry(frame, width=10)
        self.e_downtime.insert(0, '0')
        self.e_downtime.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=MAINTENANCE_STATUS,
                                     width=10, state='readonly')
        self.e_status.set('待處理')
        self.e_status.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        if record_id:
            r = bq.get_maintenance_record(record_id)
            if r:
                self.e_type.set(r['maintenance_type'])
                self.e_desc.insert('1.0', r['description'] or '')
                self.e_reporter.delete(0, 'end')
                self.e_reporter.insert(0, r['reported_by'])
                self.e_assigned.insert(0, r['assigned_to'] or '')
                if r['cause']:
                    self.e_cause.insert('1.0', r['cause'])
                if r['solution']:
                    self.e_solution.insert('1.0', r['solution'])
                self.e_parts.insert(0, r['parts_used'] or '')
                self.e_cost.delete(0, 'end')
                self.e_cost.insert(0, str(r['cost'] or 0))
                self.e_downtime.delete(0, 'end')
                self.e_downtime.insert(0, str(r['downtime_hours'] or 0))
                self.e_status.set(r['status'] or '待處理')

        self.wait_window()

    def _on_ok(self):
        desc = self.e_desc.get('1.0', 'end').strip()
        reporter = self.e_reporter.get().strip()
        if not desc or not reporter:
            ttk.dialogs.Messagebox.show_warning("問題描述與回報人為必填", parent=self)
            return

        data = dict(
            machine_id=self.machine_id,
            maintenance_type=self.e_type.get(),
            description=desc,
            reported_by=reporter,
            assigned_to=self.e_assigned.get().strip() or None,
            cause=self.e_cause.get('1.0', 'end').strip() or None,
            solution=self.e_solution.get('1.0', 'end').strip() or None,
            parts_used=self.e_parts.get().strip() or None,
            cost=float(self.e_cost.get() or 0),
            downtime_hours=float(self.e_downtime.get() or 0),
            status=self.e_status.get(),
        )

        if self.record_id:
            bq.update_maintenance_record(self.record_id, **data)
        else:
            bq.add_maintenance_record(**data)

        self.result = True
        self.destroy()
