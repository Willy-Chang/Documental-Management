"""生產進度管理模組（含甘特圖）"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from db import business_queries as bq
from config import (PRODUCTION_STATUS, PRODUCTION_PRIORITY, PRODUCTION_TASK_STATUS,
                    DEPARTMENTS, DOC_NUMBER_PREFIX, UNIT_OPTIONS, FONT_FAMILY)


class ProductionModule(ttk.Frame):
    """生產進度管理模組"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_toolbar()
        self._create_content()
        self.refresh()

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=(5, 5))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="生產進度管理", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="+ 新增生產單", command=self._on_add,
                   bootstyle=SUCCESS, width=12).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="編輯", command=self._on_edit,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除", command=self._on_delete,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)

        ttk.Separator(toolbar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=8, pady=2)

        ttk.Button(toolbar, text="甘特圖", command=self._show_gantt,
                   bootstyle=WARNING, width=8).pack(side=LEFT, padx=2)

        ttk.Label(toolbar, text="狀態：").pack(side=RIGHT, padx=(10, 2))
        self.filter_status = ttk.Combobox(toolbar, values=['全部'] + PRODUCTION_STATUS,
                                          width=10, state='readonly')
        self.filter_status.set('全部')
        self.filter_status.pack(side=RIGHT, padx=2)
        self.filter_status.bind('<<ComboboxSelected>>', lambda e: self.refresh())

    def _create_content(self):
        paned = ttk.PanedWindow(self, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 上方：生產單清單
        list_frame = ttk.LabelFrame(paned, text="生產單清單", padding=5)
        paned.add(list_frame, weight=2)

        cols = ('id', 'po', 'product', 'qty', 'order', 'client',
                'start', 'target', 'priority', 'status')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=8)
        self.tree.heading('id', text='ID')
        self.tree.heading('po', text='生產單號')
        self.tree.heading('product', text='產品名稱')
        self.tree.heading('qty', text='數量')
        self.tree.heading('order', text='關聯訂單')
        self.tree.heading('client', text='客戶')
        self.tree.heading('start', text='開始日期')
        self.tree.heading('target', text='目標完成')
        self.tree.heading('priority', text='優先')
        self.tree.heading('status', text='狀態')
        self.tree.column('id', width=30, anchor=CENTER)
        self.tree.column('po', width=110)
        self.tree.column('product', width=140)
        self.tree.column('qty', width=55, anchor=E)
        self.tree.column('order', width=100)
        self.tree.column('client', width=90)
        self.tree.column('start', width=85)
        self.tree.column('target', width=85)
        self.tree.column('priority', width=45, anchor=CENTER)
        self.tree.column('status', width=60, anchor=CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda e: self._on_edit())

        # 下方：生產任務清單
        task_frame = ttk.LabelFrame(paned, text="生產任務", padding=5)
        paned.add(task_frame, weight=2)

        task_toolbar = ttk.Frame(task_frame)
        task_toolbar.pack(fill=X, pady=(0, 3))
        ttk.Button(task_toolbar, text="+ 新增任務", command=self._on_add_task,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(task_toolbar, text="編輯任務", command=self._on_edit_task,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(task_toolbar, text="刪除任務", command=self._on_delete_task,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)

        task_cols = ('id', 'name', 'dept', 'assignee', 'start', 'end',
                     'progress', 'status')
        self.task_tree = ttk.Treeview(task_frame, columns=task_cols,
                                      show='headings', height=6)
        self.task_tree.heading('id', text='ID')
        self.task_tree.heading('name', text='任務名稱')
        self.task_tree.heading('dept', text='部門')
        self.task_tree.heading('assignee', text='負責人')
        self.task_tree.heading('start', text='開始日期')
        self.task_tree.heading('end', text='結束日期')
        self.task_tree.heading('progress', text='進度')
        self.task_tree.heading('status', text='狀態')
        self.task_tree.column('id', width=30, anchor=CENTER)
        self.task_tree.column('name', width=150)
        self.task_tree.column('dept', width=70)
        self.task_tree.column('assignee', width=70)
        self.task_tree.column('start', width=85)
        self.task_tree.column('end', width=85)
        self.task_tree.column('progress', width=55, anchor=CENTER)
        self.task_tree.column('status', width=60, anchor=CENTER)

        task_scroll = ttk.Scrollbar(task_frame, orient=VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=task_scroll.set)
        self.task_tree.pack(side=LEFT, fill=BOTH, expand=True)
        task_scroll.pack(side=RIGHT, fill=Y)
        self.task_tree.bind('<Double-1>', lambda e: self._on_edit_task())

    def refresh(self):
        status_filter = self.filter_status.get()
        status = None if status_filter == '全部' else status_filter
        rows = bq.get_all_production_orders(status=status)
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert('', END, values=(
                r['id'], r['po_number'] or '', r['product_name'],
                f'{float(r["quantity"] or 0):,.0f}',
                r['order_number'] or '', r['client_name'] or '',
                r['start_date'] or '', r['target_date'] or '',
                r['priority'], r['status']
            ))
        self.task_tree.delete(*self.task_tree.get_children())

    def _get_selected_id(self):
        sel = self.tree.selection()
        return self.tree.item(sel[0])['values'][0] if sel else None

    def _on_select(self, event=None):
        po_id = self._get_selected_id()
        if not po_id:
            return
        tasks = bq.get_production_tasks(po_id)
        self.task_tree.delete(*self.task_tree.get_children())
        for t in tasks:
            self.task_tree.insert('', END, values=(
                t['id'], t['task_name'], t['department'] or '',
                t['assignee'] or '', t['start_date'] or '', t['end_date'] or '',
                f'{t["progress_pct"]}%', t['status']
            ))

    def _on_add(self):
        dlg = ProductionDialog(self.winfo_toplevel())
        if dlg.result:
            self.refresh()

    def _on_edit(self):
        po_id = self._get_selected_id()
        if not po_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆生產單", parent=self.winfo_toplevel())
            return
        dlg = ProductionDialog(self.winfo_toplevel(), po_id=po_id)
        if dlg.result:
            self.refresh()

    def _on_delete(self):
        po_id = self._get_selected_id()
        if not po_id:
            return
        if ttk.dialogs.Messagebox.yesno("確定要刪除此生產單？", parent=self.winfo_toplevel()) == '是':
            bq.delete_production_order(po_id)
            self.refresh()

    def _on_add_task(self):
        po_id = self._get_selected_id()
        if not po_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆生產單", parent=self.winfo_toplevel())
            return
        dlg = TaskDialog(self.winfo_toplevel())
        if dlg.result:
            bq.add_production_task(po_id, **dlg.result)
            self._on_select()

    def _on_edit_task(self):
        sel = self.task_tree.selection()
        if not sel:
            return
        task_id = self.task_tree.item(sel[0])['values'][0]
        vals = self.task_tree.item(sel[0])['values']
        existing = {
            'task_name': vals[1], 'department': vals[2],
            'assignee': vals[3], 'start_date': vals[4],
            'end_date': vals[5], 'progress_pct': int(str(vals[6]).replace('%', '')),
            'status': vals[7],
        }
        dlg = TaskDialog(self.winfo_toplevel(), data=existing)
        if dlg.result:
            bq.update_production_task(task_id, **dlg.result)
            self._on_select()

    def _on_delete_task(self):
        sel = self.task_tree.selection()
        if sel:
            task_id = self.task_tree.item(sel[0])['values'][0]
            bq.delete_production_task(task_id)
            self._on_select()

    def _show_gantt(self):
        """顯示甘特圖視窗"""
        gantt_win = ttk.Toplevel(self.winfo_toplevel())
        gantt_win.title("生產進度甘特圖")
        gantt_win.geometry("1100x600")
        gantt_win.transient(self.winfo_toplevel())

        toolbar = ttk.Frame(gantt_win, padding=5)
        toolbar.pack(fill=X)
        ttk.Label(toolbar, text="生產進度甘特圖", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT)

        filter_var = ttk.StringVar(value='全部')
        filter_combo = ttk.Combobox(toolbar, textvariable=filter_var,
                                    values=['全部'] + PRODUCTION_STATUS,
                                    width=10, state='readonly')
        filter_combo.pack(side=RIGHT, padx=5)
        ttk.Label(toolbar, text="篩選：").pack(side=RIGHT)

        from ui.widgets.gantt_chart import GanttChart
        gantt = GanttChart(gantt_win)
        gantt.pack(fill=BOTH, expand=True, padx=5, pady=5)

        def update_gantt(*_args):
            status = filter_var.get()
            status_filter = None if status == '全部' else status
            tasks = bq.get_all_production_tasks_for_gantt(status_filter=status_filter)
            chart_data = []
            for t in tasks:
                if t['start_date'] and t['end_date']:
                    chart_data.append({
                        'label': f"{t['product_name']} - {t['task_name']}",
                        'start': t['start_date'],
                        'end': t['end_date'],
                        'progress': t['progress_pct'] or 0,
                        'status': t['status'],
                        'group': t['product_name'],
                    })
            gantt.update_chart(chart_data)

        filter_combo.bind('<<ComboboxSelected>>', update_gantt)
        update_gantt()


class ProductionDialog(ttk.Toplevel):
    """生產單對話框"""

    def __init__(self, parent, po_id=None):
        super().__init__(parent)
        self.result = None
        self.po_id = po_id
        self.title("編輯生產單" if po_id else "新增生產單")
        self.geometry("500x440")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        orders = bq.get_all_orders_for_combo()
        self.order_map = {o['order_number']: o['id'] for o in orders}

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="生產單號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_po = ttk.Entry(frame, width=25)
        self.e_po.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="產品名稱：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_product = ttk.Entry(frame, width=30)
        self.e_product.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="數量：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_qty = ttk.Entry(frame, width=10)
        self.e_qty.insert(0, '1')
        self.e_qty.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="單位：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_unit = ttk.Combobox(frame, values=UNIT_OPTIONS, width=10)
        self.e_unit.set('PCS')
        self.e_unit.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="關聯訂單：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_order = ttk.Combobox(frame, values=[''] + list(self.order_map.keys()), width=25)
        self.e_order.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="開始日期：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_start = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_start.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="目標完成：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_target = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_target.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="優先順序：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_priority = ttk.Combobox(frame, values=PRODUCTION_PRIORITY,
                                       width=10, state='readonly')
        self.e_priority.set('中')
        self.e_priority.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=PRODUCTION_STATUS,
                                     width=10, state='readonly')
        self.e_status.set('待排程')
        self.e_status.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="備註：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_notes = ttk.Text(frame, width=35, height=3)
        self.e_notes.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        if po_id:
            po = bq.get_production_order(po_id)
            if po:
                self.e_po.insert(0, po['po_number'] or '')
                self.e_product.insert(0, po['product_name'])
                self.e_qty.delete(0, 'end')
                self.e_qty.insert(0, str(po['quantity'] or 1))
                self.e_unit.set(po['unit'] or 'PCS')
                if po.get('order_number'):
                    self.e_order.set(po['order_number'])
                self.e_priority.set(po['priority'] or '中')
                self.e_status.set(po['status'] or '待排程')
                if po['notes']:
                    self.e_notes.insert('1.0', po['notes'])
        else:
            num = bq.generate_next_number(
                DOC_NUMBER_PREFIX['production_order'],
                'production_orders', 'po_number')
            self.e_po.insert(0, num)

        self.wait_window()

    def _on_ok(self):
        product = self.e_product.get().strip()
        if not product:
            ttk.dialogs.Messagebox.show_warning("產品名稱為必填", parent=self)
            return

        order_name = self.e_order.get().strip()
        order_id = self.order_map.get(order_name)

        data = dict(
            product_name=product,
            quantity=float(self.e_qty.get() or 1),
            unit=self.e_unit.get(),
            order_id=order_id,
            po_number=self.e_po.get().strip() or None,
            start_date=self.e_start.entry.get().strip() or None,
            target_date=self.e_target.entry.get().strip() or None,
            priority=self.e_priority.get(),
            status=self.e_status.get(),
            notes=self.e_notes.get('1.0', 'end').strip() or None,
        )

        if self.po_id:
            bq.update_production_order(self.po_id, **data)
        else:
            bq.add_production_order(**data)

        self.result = True
        self.destroy()


class TaskDialog(ttk.Toplevel):
    """生產任務對話框"""

    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.result = None
        self.title("生產任務")
        self.geometry("420x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="任務名稱：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_name = ttk.Entry(frame, width=25)
        self.e_name.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="部門：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_dept = ttk.Combobox(frame, values=DEPARTMENTS, width=15)
        self.e_dept.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="負責人：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_assignee = ttk.Entry(frame, width=15)
        self.e_assignee.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="開始日期：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_start = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_start.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="結束日期：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_end = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_end.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="進度 (%)：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_progress = ttk.Entry(frame, width=8)
        self.e_progress.insert(0, '0')
        self.e_progress.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=PRODUCTION_TASK_STATUS,
                                     width=10, state='readonly')
        self.e_status.set('待開始')
        self.e_status.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="備註：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_notes = ttk.Text(frame, width=25, height=2)
        self.e_notes.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        if data:
            self.e_name.insert(0, data.get('task_name', ''))
            if data.get('department'):
                self.e_dept.set(data['department'])
            self.e_assignee.insert(0, data.get('assignee', '') or '')
            self.e_progress.delete(0, 'end')
            self.e_progress.insert(0, str(data.get('progress_pct', 0)))
            self.e_status.set(data.get('status', '待開始'))

        self.wait_window()

    def _on_ok(self):
        name = self.e_name.get().strip()
        if not name:
            ttk.dialogs.Messagebox.show_warning("任務名稱為必填", parent=self)
            return

        try:
            progress = int(self.e_progress.get() or 0)
            progress = max(0, min(100, progress))
        except ValueError:
            progress = 0

        self.result = dict(
            task_name=name,
            department=self.e_dept.get().strip() or None,
            assignee=self.e_assignee.get().strip() or None,
            start_date=self.e_start.entry.get().strip() or None,
            end_date=self.e_end.entry.get().strip() or None,
            progress_pct=progress,
            status=self.e_status.get(),
            notes=self.e_notes.get('1.0', 'end').strip() or None,
        )
        self.destroy()
