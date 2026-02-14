"""發票紀錄管理模組"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog

from db import business_queries as bq
from config import (INVOICE_STATUS, CURRENCY_OPTIONS, UNIT_OPTIONS,
                    DOC_NUMBER_PREFIX, FONT_FAMILY)


class InvoiceModule(ttk.Frame):
    """發票紀錄管理模組"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_toolbar()
        self._create_content()
        self.refresh()

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=(5, 5))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="發票紀錄", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="+ 新增發票", command=self._on_add,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="編輯", command=self._on_edit,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除", command=self._on_delete,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="標記已付", command=self._mark_paid,
                   bootstyle=WARNING, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="匯出 PDF", command=self._on_export_pdf,
                   bootstyle=PRIMARY+OUTLINE, width=10).pack(side=LEFT, padx=2)

        ttk.Label(toolbar, text="狀態：").pack(side=RIGHT, padx=(10, 2))
        self.filter_status = ttk.Combobox(toolbar, values=['全部'] + INVOICE_STATUS,
                                          width=10, state='readonly')
        self.filter_status.set('全部')
        self.filter_status.pack(side=RIGHT, padx=2)
        self.filter_status.bind('<<ComboboxSelected>>', lambda e: self.refresh())

    def _create_content(self):
        paned = ttk.PanedWindow(self, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        list_frame = ttk.LabelFrame(paned, text="發票清單", padding=5)
        paned.add(list_frame, weight=3)

        cols = ('id', 'number', 'client', 'order', 'date', 'due',
                'total', 'payment_status')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=10)
        self.tree.heading('id', text='ID')
        self.tree.heading('number', text='發票號碼')
        self.tree.heading('client', text='客戶')
        self.tree.heading('order', text='訂單號')
        self.tree.heading('date', text='開票日期')
        self.tree.heading('due', text='到期日')
        self.tree.heading('total', text='總金額')
        self.tree.heading('payment_status', text='付款狀態')
        self.tree.column('id', width=35, anchor=CENTER)
        self.tree.column('number', width=120)
        self.tree.column('client', width=110)
        self.tree.column('order', width=110)
        self.tree.column('date', width=90)
        self.tree.column('due', width=90)
        self.tree.column('total', width=100, anchor=E)
        self.tree.column('payment_status', width=80, anchor=CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda e: self._on_edit())

        detail_frame = ttk.LabelFrame(paned, text="發票品項", padding=5)
        paned.add(detail_frame, weight=2)

        item_toolbar = ttk.Frame(detail_frame)
        item_toolbar.pack(fill=X, pady=(0, 3))
        ttk.Button(item_toolbar, text="+ 新增品項", command=self._on_add_item,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(item_toolbar, text="刪除品項", command=self._on_delete_item,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)
        ttk.Button(item_toolbar, text="重算金額", command=self._recalculate,
                   bootstyle=INFO+OUTLINE, width=10).pack(side=LEFT, padx=2)

        item_cols = ('id', 'no', 'desc', 'qty', 'unit', 'price', 'amount')
        self.item_tree = ttk.Treeview(detail_frame, columns=item_cols,
                                      show='headings', height=6)
        self.item_tree.heading('id', text='ID')
        self.item_tree.heading('no', text='項次')
        self.item_tree.heading('desc', text='品名')
        self.item_tree.heading('qty', text='數量')
        self.item_tree.heading('unit', text='單位')
        self.item_tree.heading('price', text='單價')
        self.item_tree.heading('amount', text='小計')
        self.item_tree.column('id', width=30, anchor=CENTER)
        self.item_tree.column('no', width=35, anchor=CENTER)
        self.item_tree.column('desc', width=250)
        self.item_tree.column('qty', width=60, anchor=E)
        self.item_tree.column('unit', width=45, anchor=CENTER)
        self.item_tree.column('price', width=80, anchor=E)
        self.item_tree.column('amount', width=90, anchor=E)

        item_scroll = ttk.Scrollbar(detail_frame, orient=VERTICAL, command=self.item_tree.yview)
        self.item_tree.configure(yscrollcommand=item_scroll.set)
        self.item_tree.pack(side=LEFT, fill=BOTH, expand=True)
        item_scroll.pack(side=RIGHT, fill=Y)

    def refresh(self):
        status_filter = self.filter_status.get()
        status = None if status_filter == '全部' else status_filter
        rows = bq.get_all_invoices(payment_status=status)
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert('', END, values=(
                r['id'], r['invoice_number'], r['client_name'] or '',
                r['order_number'] or '', r['invoice_date'],
                r['due_date'] or '', f'{float(r["total_amount"] or 0):,.2f}',
                r['payment_status']
            ))
        self.item_tree.delete(*self.item_tree.get_children())

    def _get_selected_id(self):
        sel = self.tree.selection()
        return self.tree.item(sel[0])['values'][0] if sel else None

    def _on_select(self, event=None):
        inv_id = self._get_selected_id()
        if not inv_id:
            return
        items = bq.get_invoice_items(inv_id)
        self.item_tree.delete(*self.item_tree.get_children())
        for item in items:
            qty = float(item['quantity'] or 0)
            price = float(item['unit_price'] or 0)
            self.item_tree.insert('', END, values=(
                item['id'], item['item_no'], item['description'],
                f'{qty:,.2f}', item['unit'], f'{price:,.2f}',
                f'{qty * price:,.2f}'
            ))

    def _on_add(self):
        dlg = InvoiceDialog(self.winfo_toplevel())
        if dlg.result:
            self.refresh()

    def _on_edit(self):
        inv_id = self._get_selected_id()
        if not inv_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆發票", parent=self.winfo_toplevel())
            return
        dlg = InvoiceDialog(self.winfo_toplevel(), invoice_id=inv_id)
        if dlg.result:
            self.refresh()

    def _on_delete(self):
        inv_id = self._get_selected_id()
        if not inv_id:
            return
        if ttk.dialogs.Messagebox.yesno("確定要刪除此發票？", parent=self.winfo_toplevel()) == '是':
            bq.delete_invoice(inv_id)
            self.refresh()

    def _mark_paid(self):
        inv_id = self._get_selected_id()
        if inv_id:
            bq.update_invoice(inv_id, payment_status='已付清', payment_date=bq._today())
            self.refresh()

    def _recalculate(self):
        inv_id = self._get_selected_id()
        if inv_id:
            bq.recalculate_invoice(inv_id)
            self.refresh()
            self._on_select()

    def _on_add_item(self):
        inv_id = self._get_selected_id()
        if not inv_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆發票", parent=self.winfo_toplevel())
            return
        items = bq.get_invoice_items(inv_id)
        next_no = max([i['item_no'] for i in items], default=0) + 1
        from ui.modules.quotation_module import ItemDialog
        dlg = ItemDialog(self.winfo_toplevel(), title="新增發票品項")
        if dlg.result:
            bq.add_invoice_item(inv_id, next_no, description=dlg.result['description'],
                                quantity=dlg.result['quantity'], unit=dlg.result['unit'],
                                unit_price=dlg.result['unit_price'])
            bq.recalculate_invoice(inv_id)
            self._on_select()

    def _on_delete_item(self):
        sel = self.item_tree.selection()
        if sel:
            item_id = self.item_tree.item(sel[0])['values'][0]
            inv_id = self._get_selected_id()
            bq.delete_invoice_item(item_id)
            if inv_id:
                bq.recalculate_invoice(inv_id)
            self._on_select()

    def _on_export_pdf(self):
        inv_id = self._get_selected_id()
        if not inv_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆發票", parent=self.winfo_toplevel())
            return
        inv = bq.get_invoice(inv_id)
        items = bq.get_invoice_items(inv_id)
        filepath = filedialog.asksaveasfilename(
            title="匯出發票 PDF",
            initialfile=f"{inv['invoice_number']}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF 檔案", "*.pdf")],
            parent=self.winfo_toplevel()
        )
        if filepath:
            try:
                from core.pdf_generator import generate_invoice_pdf
                generate_invoice_pdf(filepath, dict(inv), [dict(i) for i in items],
                                     client_name=inv['client_name'] or '')
                ttk.dialogs.Messagebox.show_info(
                    f"PDF 已匯出至：\n{filepath}", parent=self.winfo_toplevel())
            except Exception as e:
                ttk.dialogs.Messagebox.show_error(
                    f"PDF 匯出失敗：{e}", parent=self.winfo_toplevel())


class InvoiceDialog(ttk.Toplevel):
    """發票對話框"""

    def __init__(self, parent, invoice_id=None):
        super().__init__(parent)
        self.result = None
        self.invoice_id = invoice_id
        self.title("編輯發票" if invoice_id else "新增發票")
        self.geometry("480x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        clients = bq.get_all_clients_for_combo()
        self.client_map = {c['name']: c['id'] for c in clients}
        orders = bq.get_all_orders_for_combo()
        self.order_map = {o['order_number']: o['id'] for o in orders}

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="發票號碼：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_number = ttk.Entry(frame, width=25)
        self.e_number.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="客戶：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_client = ttk.Combobox(frame, values=list(self.client_map.keys()), width=25)
        self.e_client.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="關聯訂單：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_order = ttk.Combobox(frame, values=[''] + list(self.order_map.keys()), width=25)
        self.e_order.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="開票日期：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_date = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_date.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="到期日：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_due = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_due.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="幣別：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_currency = ttk.Combobox(frame, values=CURRENCY_OPTIONS, width=10, state='readonly')
        self.e_currency.set('TWD')
        self.e_currency.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="付款狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=INVOICE_STATUS, width=10, state='readonly')
        self.e_status.set('未付')
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

        if invoice_id:
            inv = bq.get_invoice(invoice_id)
            if inv:
                self.e_number.insert(0, inv['invoice_number'])
                self.e_number.config(state='readonly')
                if inv['client_name']:
                    self.e_client.set(inv['client_name'])
                if inv.get('order_number'):
                    self.e_order.set(inv['order_number'])
                self.e_currency.set(inv['currency'] or 'TWD')
                self.e_status.set(inv['payment_status'] or '未付')
                if inv['notes']:
                    self.e_notes.insert('1.0', inv['notes'])
        else:
            num = bq.generate_next_number(
                DOC_NUMBER_PREFIX['invoice'], 'invoices', 'invoice_number')
            self.e_number.insert(0, num)

        self.wait_window()

    def _on_ok(self):
        number = self.e_number.get().strip()
        client_name = self.e_client.get().strip()
        client_id = self.client_map.get(client_name)
        invoice_date = self.e_date.entry.get().strip()

        if not number or not client_id or not invoice_date:
            ttk.dialogs.Messagebox.show_warning("發票號碼、客戶、開票日期為必填",
                                                parent=self)
            return

        order_name = self.e_order.get().strip()
        order_id = self.order_map.get(order_name)

        data = dict(
            client_id=client_id,
            order_id=order_id,
            invoice_date=invoice_date,
            due_date=self.e_due.entry.get().strip() or None,
            currency=self.e_currency.get(),
            payment_status=self.e_status.get(),
            notes=self.e_notes.get('1.0', 'end').strip() or None,
        )

        if self.invoice_id:
            bq.update_invoice(self.invoice_id, **data)
        else:
            bq.add_invoice(invoice_number=number, **data)

        self.result = True
        self.destroy()
