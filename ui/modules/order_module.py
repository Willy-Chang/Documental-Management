"""客戶訂單管理模組"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from db import business_queries as bq
from config import (ORDER_STATUS, CURRENCY_OPTIONS, UNIT_OPTIONS,
                    PAYMENT_TERMS_OPTIONS, DELIVERY_TERMS_OPTIONS,
                    DOC_NUMBER_PREFIX, FONT_FAMILY)


class OrderModule(ttk.Frame):
    """客戶訂單管理模組"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_toolbar()
        self._create_content()
        self.refresh()

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=(5, 5))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="客戶訂單管理", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="+ 新增訂單", command=self._on_add,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="編輯", command=self._on_edit,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除", command=self._on_delete,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)

        ttk.Label(toolbar, text="狀態：").pack(side=RIGHT, padx=(10, 2))
        self.filter_status = ttk.Combobox(toolbar, values=['全部'] + ORDER_STATUS,
                                          width=10, state='readonly')
        self.filter_status.set('全部')
        self.filter_status.pack(side=RIGHT, padx=2)
        self.filter_status.bind('<<ComboboxSelected>>', lambda e: self.refresh())

    def _create_content(self):
        paned = ttk.PanedWindow(self, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        list_frame = ttk.LabelFrame(paned, text="訂單清單", padding=5)
        paned.add(list_frame, weight=3)

        cols = ('id', 'number', 'client', 'po', 'order_date', 'delivery',
                'total', 'status')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=10)
        self.tree.heading('id', text='ID')
        self.tree.heading('number', text='訂單號')
        self.tree.heading('client', text='客戶')
        self.tree.heading('po', text='客戶PO')
        self.tree.heading('order_date', text='訂單日期')
        self.tree.heading('delivery', text='交期')
        self.tree.heading('total', text='金額')
        self.tree.heading('status', text='狀態')
        self.tree.column('id', width=35, anchor=CENTER)
        self.tree.column('number', width=130)
        self.tree.column('client', width=120)
        self.tree.column('po', width=100)
        self.tree.column('order_date', width=90)
        self.tree.column('delivery', width=90)
        self.tree.column('total', width=100, anchor=E)
        self.tree.column('status', width=80, anchor=CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda e: self._on_edit())

        detail_frame = ttk.LabelFrame(paned, text="訂單品項", padding=5)
        paned.add(detail_frame, weight=2)

        item_toolbar = ttk.Frame(detail_frame)
        item_toolbar.pack(fill=X, pady=(0, 3))
        ttk.Button(item_toolbar, text="+ 新增品項", command=self._on_add_item,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(item_toolbar, text="編輯品項", command=self._on_edit_item,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(item_toolbar, text="刪除品項", command=self._on_delete_item,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)

        self.item_total_label = ttk.Label(item_toolbar, text="合計：$0",
                                          font=(FONT_FAMILY, 11, 'bold'))
        self.item_total_label.pack(side=RIGHT, padx=10)

        item_cols = ('id', 'no', 'part', 'desc', 'spec', 'qty', 'unit',
                     'price', 'amount', 'delivered')
        self.item_tree = ttk.Treeview(detail_frame, columns=item_cols,
                                      show='headings', height=6)
        self.item_tree.heading('id', text='ID')
        self.item_tree.heading('no', text='項次')
        self.item_tree.heading('part', text='料號')
        self.item_tree.heading('desc', text='品名')
        self.item_tree.heading('spec', text='規格')
        self.item_tree.heading('qty', text='數量')
        self.item_tree.heading('unit', text='單位')
        self.item_tree.heading('price', text='單價')
        self.item_tree.heading('amount', text='小計')
        self.item_tree.heading('delivered', text='已出貨')
        self.item_tree.column('id', width=30, anchor=CENTER)
        self.item_tree.column('no', width=35, anchor=CENTER)
        self.item_tree.column('part', width=80)
        self.item_tree.column('desc', width=150)
        self.item_tree.column('spec', width=100)
        self.item_tree.column('qty', width=50, anchor=E)
        self.item_tree.column('unit', width=40, anchor=CENTER)
        self.item_tree.column('price', width=70, anchor=E)
        self.item_tree.column('amount', width=80, anchor=E)
        self.item_tree.column('delivered', width=60, anchor=E)

        item_scroll = ttk.Scrollbar(detail_frame, orient=VERTICAL, command=self.item_tree.yview)
        self.item_tree.configure(yscrollcommand=item_scroll.set)
        self.item_tree.pack(side=LEFT, fill=BOTH, expand=True)
        item_scroll.pack(side=RIGHT, fill=Y)

    def refresh(self):
        status_filter = self.filter_status.get()
        status = None if status_filter == '全部' else status_filter
        rows = bq.get_all_customer_orders(status=status)
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            total = bq.get_order_total(r['id'])
            self.tree.insert('', END, values=(
                r['id'], r['order_number'], r['client_name'] or '',
                r['po_number'] or '', r['order_date'],
                r['delivery_date'] or '', f'{total:,.2f}', r['status']
            ))
        self.item_tree.delete(*self.item_tree.get_children())
        self.item_total_label.config(text="合計：$0")

    def _get_selected_id(self):
        sel = self.tree.selection()
        return self.tree.item(sel[0])['values'][0] if sel else None

    def _on_select(self, event=None):
        oid = self._get_selected_id()
        if not oid:
            return
        items = bq.get_order_items(oid)
        self.item_tree.delete(*self.item_tree.get_children())
        total = 0
        for item in items:
            qty = float(item['quantity'] or 0)
            price = float(item['unit_price'] or 0)
            amount = qty * price
            total += amount
            self.item_tree.insert('', END, values=(
                item['id'], item['item_no'], item['part_number'] or '',
                item['description'], item['specification'] or '',
                f'{qty:,.2f}', item['unit'], f'{price:,.2f}',
                f'{amount:,.2f}', f'{float(item["delivered_qty"] or 0):,.2f}'
            ))
        self.item_total_label.config(text=f"合計：${total:,.2f}")

    def _on_add(self):
        dlg = OrderDialog(self.winfo_toplevel())
        if dlg.result:
            self.refresh()

    def _on_edit(self):
        oid = self._get_selected_id()
        if not oid:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆訂單", parent=self.winfo_toplevel())
            return
        dlg = OrderDialog(self.winfo_toplevel(), order_id=oid)
        if dlg.result:
            self.refresh()

    def _on_delete(self):
        oid = self._get_selected_id()
        if not oid:
            return
        if ttk.dialogs.Messagebox.yesno("確定要刪除此訂單？", parent=self.winfo_toplevel()) == '是':
            bq.delete_customer_order(oid)
            self.refresh()

    def _on_add_item(self):
        oid = self._get_selected_id()
        if not oid:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆訂單", parent=self.winfo_toplevel())
            return
        items = bq.get_order_items(oid)
        next_no = max([i['item_no'] for i in items], default=0) + 1
        from ui.modules.quotation_module import ItemDialog
        dlg = ItemDialog(self.winfo_toplevel(), title="新增訂單品項")
        if dlg.result:
            bq.add_order_item(oid, next_no, **dlg.result)
            self._on_select()

    def _on_edit_item(self):
        sel = self.item_tree.selection()
        if not sel:
            return
        item_id = self.item_tree.item(sel[0])['values'][0]
        vals = self.item_tree.item(sel[0])['values']
        existing = {
            'part_number': vals[2], 'description': vals[3],
            'specification': vals[4], 'quantity': vals[5],
            'unit': vals[6], 'unit_price': vals[7],
        }
        from ui.modules.quotation_module import ItemDialog
        dlg = ItemDialog(self.winfo_toplevel(), title="編輯訂單品項", data=existing)
        if dlg.result:
            bq.update_order_item(item_id, **dlg.result)
            self._on_select()

    def _on_delete_item(self):
        sel = self.item_tree.selection()
        if sel:
            item_id = self.item_tree.item(sel[0])['values'][0]
            bq.delete_order_item(item_id)
            self._on_select()


class OrderDialog(ttk.Toplevel):
    """客戶訂單對話框"""

    def __init__(self, parent, order_id=None):
        super().__init__(parent)
        self.result = None
        self.order_id = order_id
        self.title("編輯訂單" if order_id else "新增訂單")
        self.geometry("520x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        clients = bq.get_all_clients_for_combo()
        self.client_map = {c['name']: c['id'] for c in clients}

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="訂單號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_number = ttk.Entry(frame, width=25)
        self.e_number.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="客戶：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_client = ttk.Combobox(frame, values=list(self.client_map.keys()), width=25)
        self.e_client.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="客戶PO號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_po = ttk.Entry(frame, width=25)
        self.e_po.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="訂單日期：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_date = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_date.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="交貨日期：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_delivery = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_delivery.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="幣別：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_currency = ttk.Combobox(frame, values=CURRENCY_OPTIONS, width=10, state='readonly')
        self.e_currency.set('TWD')
        self.e_currency.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="付款條件：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_payment = ttk.Combobox(frame, values=PAYMENT_TERMS_OPTIONS, width=25)
        self.e_payment.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="交貨條件：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_delivery_terms = ttk.Combobox(frame, values=DELIVERY_TERMS_OPTIONS, width=25)
        self.e_delivery_terms.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=ORDER_STATUS, width=10, state='readonly')
        self.e_status.set('新訂單')
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

        if order_id:
            o = bq.get_customer_order(order_id)
            if o:
                self.e_number.insert(0, o['order_number'])
                self.e_number.config(state='readonly')
                if o['client_name']:
                    self.e_client.set(o['client_name'])
                self.e_po.insert(0, o['po_number'] or '')
                self.e_currency.set(o['currency'] or 'TWD')
                if o['payment_terms']:
                    self.e_payment.set(o['payment_terms'])
                if o['delivery_terms']:
                    self.e_delivery_terms.set(o['delivery_terms'])
                self.e_status.set(o['status'] or '新訂單')
                if o['notes']:
                    self.e_notes.insert('1.0', o['notes'])
        else:
            num = bq.generate_next_number(
                DOC_NUMBER_PREFIX['customer_order'], 'customer_orders', 'order_number')
            self.e_number.insert(0, num)

        self.wait_window()

    def _on_ok(self):
        number = self.e_number.get().strip()
        client_name = self.e_client.get().strip()
        client_id = self.client_map.get(client_name)
        order_date = self.e_date.entry.get().strip()

        if not number or not client_id or not order_date:
            ttk.dialogs.Messagebox.show_warning("訂單號、客戶、訂單日期為必填",
                                                parent=self)
            return

        data = dict(
            client_id=client_id,
            po_number=self.e_po.get().strip() or None,
            order_date=order_date,
            delivery_date=self.e_delivery.entry.get().strip() or None,
            currency=self.e_currency.get(),
            payment_terms=self.e_payment.get().strip() or None,
            delivery_terms=self.e_delivery_terms.get().strip() or None,
            status=self.e_status.get(),
            notes=self.e_notes.get('1.0', 'end').strip() or None,
        )

        if self.order_id:
            bq.update_customer_order(self.order_id, **data)
        else:
            bq.add_customer_order(order_number=number, **data)

        self.result = True
        self.destroy()
