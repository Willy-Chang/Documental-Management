"""請購單管理模組"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime

from db import business_queries as bq
from config import (PR_STATUS, PR_CATEGORIES, PR_URGENCY, UNIT_OPTIONS,
                    DOC_NUMBER_PREFIX, DEFAULT_OPERATOR, DEPARTMENTS, FONT_FAMILY)


class PurchaseModule(ttk.Frame):
    """請購單管理模組"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_toolbar()
        self._create_content()
        self.refresh()

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=(5, 5))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="請購單管理", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="+ 新增請購單", command=self._on_add,
                   bootstyle=SUCCESS, width=12).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="編輯", command=self._on_edit,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除", command=self._on_delete,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="核准", command=self._on_approve,
                   bootstyle=WARNING, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="供應商管理", command=self._manage_suppliers,
                   bootstyle=PRIMARY+OUTLINE, width=10).pack(side=LEFT, padx=2)

        ttk.Label(toolbar, text="狀態：").pack(side=RIGHT, padx=(10, 2))
        self.filter_status = ttk.Combobox(toolbar, values=['全部'] + PR_STATUS,
                                          width=10, state='readonly')
        self.filter_status.set('全部')
        self.filter_status.pack(side=RIGHT, padx=2)
        self.filter_status.bind('<<ComboboxSelected>>', lambda e: self.refresh())

    def _create_content(self):
        paned = ttk.PanedWindow(self, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 上方：請購單清單
        list_frame = ttk.LabelFrame(paned, text="請購單清單")
        paned.add(list_frame, weight=3)

        cols = ('id', 'number', 'requester', 'dept', 'purpose', 'urgency',
                'total', 'status', 'date')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=10)
        self.tree.heading('id', text='ID')
        self.tree.heading('number', text='請購單號')
        self.tree.heading('requester', text='請購人')
        self.tree.heading('dept', text='部門')
        self.tree.heading('purpose', text='用途')
        self.tree.heading('urgency', text='急迫性')
        self.tree.heading('total', text='預估金額')
        self.tree.heading('status', text='狀態')
        self.tree.heading('date', text='建立日期')
        self.tree.column('id', width=35, anchor=CENTER)
        self.tree.column('number', width=130)
        self.tree.column('requester', width=80)
        self.tree.column('dept', width=70)
        self.tree.column('purpose', width=160)
        self.tree.column('urgency', width=60, anchor=CENTER)
        self.tree.column('total', width=90, anchor=E)
        self.tree.column('status', width=70, anchor=CENTER)
        self.tree.column('date', width=90)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda e: self._on_edit())

        # 下方：品項明細
        detail_frame = ttk.LabelFrame(paned, text="請購品項")
        paned.add(detail_frame, weight=2)

        item_toolbar = ttk.Frame(detail_frame)
        item_toolbar.pack(fill=X, pady=(0, 3))
        ttk.Button(item_toolbar, text="+ 新增品項", command=self._on_add_item,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(item_toolbar, text="編輯品項", command=self._on_edit_item,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(item_toolbar, text="刪除品項", command=self._on_delete_item,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)

        self.item_total_label = ttk.Label(item_toolbar, text="預估合計：$0",
                                          font=(FONT_FAMILY, 11, 'bold'))
        self.item_total_label.pack(side=RIGHT, padx=10)

        item_cols = ('id', 'no', 'cat', 'part', 'desc', 'spec', 'qty', 'unit',
                     'price', 'supplier')
        self.item_tree = ttk.Treeview(detail_frame, columns=item_cols,
                                      show='headings', height=6)
        self.item_tree.heading('id', text='ID')
        self.item_tree.heading('no', text='項次')
        self.item_tree.heading('cat', text='分類')
        self.item_tree.heading('part', text='料號')
        self.item_tree.heading('desc', text='品名')
        self.item_tree.heading('spec', text='規格')
        self.item_tree.heading('qty', text='數量')
        self.item_tree.heading('unit', text='單位')
        self.item_tree.heading('price', text='預估單價')
        self.item_tree.heading('supplier', text='供應商')
        self.item_tree.column('id', width=30, anchor=CENTER)
        self.item_tree.column('no', width=35, anchor=CENTER)
        self.item_tree.column('cat', width=60)
        self.item_tree.column('part', width=80)
        self.item_tree.column('desc', width=150)
        self.item_tree.column('spec', width=100)
        self.item_tree.column('qty', width=50, anchor=E)
        self.item_tree.column('unit', width=40, anchor=CENTER)
        self.item_tree.column('price', width=70, anchor=E)
        self.item_tree.column('supplier', width=90)

        item_scroll = ttk.Scrollbar(detail_frame, orient=VERTICAL, command=self.item_tree.yview)
        self.item_tree.configure(yscrollcommand=item_scroll.set)
        self.item_tree.pack(side=LEFT, fill=BOTH, expand=True)
        item_scroll.pack(side=RIGHT, fill=Y)

    def refresh(self):
        status_filter = self.filter_status.get()
        status = None if status_filter == '全部' else status_filter
        rows = bq.get_all_purchase_requisitions(status=status)
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            total = bq.get_pr_total(r['id'])
            self.tree.insert('', END, values=(
                r['id'], r['pr_number'], r['requester'],
                r['department'] or '', r['purpose'] or '',
                r['urgency'], f'{total:,.2f}',
                r['status'], r['created_at'][:10] if r['created_at'] else ''
            ))
        self._clear_items()

    def _clear_items(self):
        self.item_tree.delete(*self.item_tree.get_children())
        self.item_total_label.config(text="預估合計：$0")

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0])['values'][0]

    def _on_select(self, event=None):
        pr_id = self._get_selected_id()
        if not pr_id:
            return
        items = bq.get_pr_items(pr_id)
        self.item_tree.delete(*self.item_tree.get_children())
        total = 0
        for item in items:
            qty = float(item['quantity'] or 0)
            price = float(item['estimated_price'] or 0)
            total += qty * price
            self.item_tree.insert('', END, values=(
                item['id'], item['item_no'], item['category'],
                item['part_number'] or '', item['description'],
                item['specification'] or '', f'{qty:,.2f}', item['unit'],
                f'{price:,.2f}', item['supplier_name'] or ''
            ))
        self.item_total_label.config(text=f"預估合計：${total:,.2f}")

    def _on_add(self):
        dlg = PRDialog(self.winfo_toplevel())
        if dlg.result:
            self.refresh()

    def _on_edit(self):
        pr_id = self._get_selected_id()
        if not pr_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆請購單", parent=self.winfo_toplevel())
            return
        dlg = PRDialog(self.winfo_toplevel(), pr_id=pr_id)
        if dlg.result:
            self.refresh()

    def _on_delete(self):
        pr_id = self._get_selected_id()
        if not pr_id:
            return
        if ttk.dialogs.Messagebox.yesno("確定要刪除此請購單？", parent=self.winfo_toplevel()) == '是':
            bq.delete_purchase_requisition(pr_id)
            self.refresh()

    def _on_approve(self):
        pr_id = self._get_selected_id()
        if not pr_id:
            return
        bq.update_purchase_requisition(pr_id, status='已核准',
                                       approved_by=DEFAULT_OPERATOR,
                                       approved_at=bq._now())
        self.refresh()

    def _on_add_item(self):
        pr_id = self._get_selected_id()
        if not pr_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆請購單", parent=self.winfo_toplevel())
            return
        items = bq.get_pr_items(pr_id)
        next_no = max([i['item_no'] for i in items], default=0) + 1
        dlg = PRItemDialog(self.winfo_toplevel())
        if dlg.result:
            bq.add_pr_item(pr_id, next_no, **dlg.result)
            self._on_select()

    def _on_edit_item(self):
        sel = self.item_tree.selection()
        if not sel:
            return
        item_id = self.item_tree.item(sel[0])['values'][0]
        vals = self.item_tree.item(sel[0])['values']
        existing = {
            'category': vals[2], 'part_number': vals[3],
            'description': vals[4], 'specification': vals[5],
            'quantity': vals[6], 'unit': vals[7], 'estimated_price': vals[8],
        }
        dlg = PRItemDialog(self.winfo_toplevel(), data=existing)
        if dlg.result:
            bq.update_pr_item(item_id, **dlg.result)
            self._on_select()

    def _on_delete_item(self):
        sel = self.item_tree.selection()
        if not sel:
            return
        item_id = self.item_tree.item(sel[0])['values'][0]
        bq.delete_pr_item(item_id)
        self._on_select()

    def _manage_suppliers(self):
        SupplierDialog(self.winfo_toplevel())


class PRDialog(ttk.Toplevel):
    """請購單新增/編輯對話框"""

    def __init__(self, parent, pr_id=None):
        super().__init__(parent)
        self.result = None
        self.pr_id = pr_id
        self.title("編輯請購單" if pr_id else "新增請購單")
        self.geometry("480x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="請購單號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_number = ttk.Entry(frame, width=25)
        self.e_number.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="請購人：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_requester = ttk.Entry(frame, width=20)
        self.e_requester.insert(0, DEFAULT_OPERATOR)
        self.e_requester.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="部門：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_dept = ttk.Combobox(frame, values=DEPARTMENTS, width=15)
        self.e_dept.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="用途：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_purpose = ttk.Entry(frame, width=35)
        self.e_purpose.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="急迫性：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_urgency = ttk.Combobox(frame, values=PR_URGENCY, width=10, state='readonly')
        self.e_urgency.set('一般')
        self.e_urgency.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=PR_STATUS, width=10, state='readonly')
        self.e_status.set('草稿')
        self.e_status.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="備註：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_notes = ttk.Text(frame, width=35, height=3)
        self.e_notes.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        if pr_id:
            pr = bq.get_purchase_requisition(pr_id)
            if pr:
                self.e_number.insert(0, pr['pr_number'])
                self.e_number.config(state='readonly')
                self.e_requester.delete(0, 'end')
                self.e_requester.insert(0, pr['requester'])
                if pr['department']:
                    self.e_dept.set(pr['department'])
                self.e_purpose.insert(0, pr['purpose'] or '')
                self.e_urgency.set(pr['urgency'] or '一般')
                self.e_status.set(pr['status'] or '草稿')
                if pr['notes']:
                    self.e_notes.insert('1.0', pr['notes'])
        else:
            num = bq.generate_next_number(
                DOC_NUMBER_PREFIX['purchase_requisition'],
                'purchase_requisitions', 'pr_number')
            self.e_number.insert(0, num)

        self.wait_window()

    def _on_ok(self):
        number = self.e_number.get().strip()
        requester = self.e_requester.get().strip()
        if not number or not requester:
            ttk.dialogs.Messagebox.show_warning("單號與請購人不可為空", parent=self)
            return

        data = dict(
            department=self.e_dept.get().strip() or None,
            purpose=self.e_purpose.get().strip() or None,
            urgency=self.e_urgency.get(),
            status=self.e_status.get(),
            notes=self.e_notes.get('1.0', 'end').strip() or None,
        )

        if self.pr_id:
            data['requester'] = requester
            bq.update_purchase_requisition(self.pr_id, **data)
        else:
            bq.add_purchase_requisition(pr_number=number, requester=requester, **data)

        self.result = True
        self.destroy()


class PRItemDialog(ttk.Toplevel):
    """請購品項對話框"""

    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.result = None
        self.title("請購品項")
        self.geometry("420x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        suppliers = bq.get_all_suppliers()
        self.supplier_map = {s['name']: s['id'] for s in suppliers}
        supplier_names = [''] + list(self.supplier_map.keys())

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="分類：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_cat = ttk.Combobox(frame, values=PR_CATEGORIES, width=12, state='readonly')
        self.e_cat.set('零件')
        self.e_cat.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="料號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_part = ttk.Entry(frame, width=20)
        self.e_part.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="品名：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_desc = ttk.Entry(frame, width=30)
        self.e_desc.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="規格：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_spec = ttk.Entry(frame, width=30)
        self.e_spec.grid(row=row, column=1, sticky=W, pady=3)

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
        ttk.Label(frame, text="預估單價：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_price = ttk.Entry(frame, width=12)
        self.e_price.insert(0, '0')
        self.e_price.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="供應商：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_supplier = ttk.Combobox(frame, values=supplier_names, width=20)
        self.e_supplier.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        if data:
            if data.get('category'):
                self.e_cat.set(data['category'])
            self.e_part.insert(0, str(data.get('part_number', '') or ''))
            self.e_desc.insert(0, str(data.get('description', '')))
            self.e_spec.insert(0, str(data.get('specification', '') or ''))
            self.e_qty.delete(0, 'end')
            self.e_qty.insert(0, str(data.get('quantity', 1)))
            self.e_unit.set(data.get('unit', 'PCS'))
            self.e_price.delete(0, 'end')
            self.e_price.insert(0, str(data.get('estimated_price', 0)))

        self.wait_window()

    def _on_ok(self):
        desc = self.e_desc.get().strip()
        if not desc:
            ttk.dialogs.Messagebox.show_warning("品名不可為空", parent=self)
            return
        try:
            qty = float(self.e_qty.get() or 1)
            price = float(self.e_price.get() or 0)
        except ValueError:
            ttk.dialogs.Messagebox.show_warning("數量或單價格式不正確", parent=self)
            return

        supplier_name = self.e_supplier.get().strip()
        supplier_id = self.supplier_map.get(supplier_name)

        self.result = dict(
            category=self.e_cat.get(),
            part_number=self.e_part.get().strip() or None,
            description=desc,
            specification=self.e_spec.get().strip() or None,
            quantity=qty,
            unit=self.e_unit.get(),
            estimated_price=price,
            supplier_id=supplier_id,
        )
        self.destroy()


class SupplierDialog(ttk.Toplevel):
    """供應商管理對話框"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("供應商管理")
        self.geometry("650x420")
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=BOTH, expand=True)

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=X, pady=(0, 5))
        ttk.Button(toolbar, text="+ 新增", command=self._on_add,
                   bootstyle=SUCCESS, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除", command=self._on_delete,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)

        cols = ('id', 'name', 'code', 'contact', 'phone', 'email')
        self.tree = ttk.Treeview(frame, columns=cols, show='headings', height=12)
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='名稱')
        self.tree.heading('code', text='代碼')
        self.tree.heading('contact', text='聯絡人')
        self.tree.heading('phone', text='電話')
        self.tree.heading('email', text='Email')
        self.tree.column('id', width=35, anchor=CENTER)
        self.tree.column('name', width=150)
        self.tree.column('code', width=80)
        self.tree.column('contact', width=80)
        self.tree.column('phone', width=110)
        self.tree.column('email', width=150)
        self.tree.pack(fill=BOTH, expand=True)
        self._refresh()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for s in bq.get_all_suppliers():
            self.tree.insert('', END, values=(
                s['id'], s['name'], s['code'] or '',
                s['contact'] or '', s['phone'] or '', s['email'] or ''
            ))

    def _on_add(self):
        dlg = _SupplierEditDialog(self)
        if dlg.result:
            bq.add_supplier(**dlg.result)
            self._refresh()

    def _on_delete(self):
        sel = self.tree.selection()
        if sel:
            sid = self.tree.item(sel[0])['values'][0]
            bq.delete_supplier(sid)
            self._refresh()


class _SupplierEditDialog(ttk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("新增供應商")
        self.geometry("380x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        fields = [('名稱', 'name'), ('代碼', 'code'), ('聯絡人', 'contact'),
                  ('電話', 'phone'), ('Email', 'email'), ('地址', 'address')]
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label}：").grid(row=i, column=0, sticky=W, pady=2)
            e = ttk.Entry(frame, width=30)
            e.grid(row=i, column=1, sticky=W, pady=2)
            self.entries[key] = e

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)
        self.wait_window()

    def _on_ok(self):
        name = self.entries['name'].get().strip()
        if not name:
            ttk.dialogs.Messagebox.show_warning("名稱不可為空", parent=self)
            return
        self.result = {k: e.get().strip() or None for k, e in self.entries.items()}
        self.destroy()
