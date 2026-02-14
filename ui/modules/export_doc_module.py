"""出口文件紀錄管理模組"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
import os

from db import business_queries as bq
from config import (EXPORT_DOC_TYPES, EXPORT_DOC_STATUS, SHIPPING_METHODS, FONT_FAMILY)


class ExportDocModule(ttk.Frame):
    """出口文件管理模組"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_toolbar()
        self._create_content()
        self.refresh()

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=(5, 5))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="出口文件紀錄", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="+ 新增文件", command=self._on_add,
                   bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="編輯", command=self._on_edit,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除", command=self._on_delete,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="附加檔案", command=self._attach_file,
                   bootstyle=PRIMARY+OUTLINE, width=10).pack(side=LEFT, padx=2)

        ttk.Label(toolbar, text="狀態：").pack(side=RIGHT, padx=(10, 2))
        self.filter_status = ttk.Combobox(toolbar, values=['全部'] + EXPORT_DOC_STATUS,
                                          width=10, state='readonly')
        self.filter_status.set('全部')
        self.filter_status.pack(side=RIGHT, padx=2)
        self.filter_status.bind('<<ComboboxSelected>>', lambda e: self.refresh())

    def _create_content(self):
        frame = ttk.Frame(self, padding=5)
        frame.pack(fill=BOTH, expand=True)

        cols = ('id', 'type', 'number', 'order', 'client', 'dest', 'ship_method',
                'ship_date', 'bl', 'status', 'date')
        self.tree = ttk.Treeview(frame, columns=cols, show='headings', height=18)
        self.tree.heading('id', text='ID')
        self.tree.heading('type', text='文件類型')
        self.tree.heading('number', text='文件號碼')
        self.tree.heading('order', text='訂單號')
        self.tree.heading('client', text='客戶')
        self.tree.heading('dest', text='目的國')
        self.tree.heading('ship_method', text='運輸方式')
        self.tree.heading('ship_date', text='出貨日')
        self.tree.heading('bl', text='提單號')
        self.tree.heading('status', text='狀態')
        self.tree.heading('date', text='開立日期')

        self.tree.column('id', width=30, anchor=CENTER)
        self.tree.column('type', width=160)
        self.tree.column('number', width=100)
        self.tree.column('order', width=110)
        self.tree.column('client', width=100)
        self.tree.column('dest', width=70)
        self.tree.column('ship_method', width=60)
        self.tree.column('ship_date', width=80)
        self.tree.column('bl', width=100)
        self.tree.column('status', width=60, anchor=CENTER)
        self.tree.column('date', width=80)

        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.bind('<Double-1>', lambda e: self._on_edit())

    def refresh(self):
        status_filter = self.filter_status.get()
        status = None if status_filter == '全部' else status_filter
        rows = bq.get_all_export_documents(status=status)
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert('', END, values=(
                r['id'], r['doc_type'], r['doc_number'] or '',
                r['order_number'] or '', r['client_name'] or '',
                r['destination_country'] or '', r['shipping_method'] or '',
                r['shipping_date'] or '', r['bl_number'] or '',
                r['status'], r['issue_date'] or ''
            ))

    def _get_selected_id(self):
        sel = self.tree.selection()
        return self.tree.item(sel[0])['values'][0] if sel else None

    def _on_add(self):
        dlg = ExportDocDialog(self.winfo_toplevel())
        if dlg.result:
            self.refresh()

    def _on_edit(self):
        doc_id = self._get_selected_id()
        if not doc_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆文件", parent=self.winfo_toplevel())
            return
        dlg = ExportDocDialog(self.winfo_toplevel(), doc_id=doc_id)
        if dlg.result:
            self.refresh()

    def _on_delete(self):
        doc_id = self._get_selected_id()
        if not doc_id:
            return
        if ttk.dialogs.Messagebox.yesno("確定要刪除此文件？", parent=self.winfo_toplevel()) == '是':
            bq.delete_export_document(doc_id)
            self.refresh()

    def _attach_file(self):
        doc_id = self._get_selected_id()
        if not doc_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆文件", parent=self.winfo_toplevel())
            return
        filepath = filedialog.askopenfilename(
            title="選擇附加檔案",
            filetypes=[("所有檔案", "*.*"), ("PDF", "*.pdf"), ("圖片", "*.png *.jpg")],
            parent=self.winfo_toplevel()
        )
        if filepath:
            bq.update_export_document(doc_id, file_path=filepath)
            ttk.dialogs.Messagebox.show_info(f"已附加檔案：\n{os.path.basename(filepath)}",
                                             parent=self.winfo_toplevel())


class ExportDocDialog(ttk.Toplevel):
    """出口文件對話框"""

    def __init__(self, parent, doc_id=None):
        super().__init__(parent)
        self.result = None
        self.doc_id = doc_id
        self.title("編輯出口文件" if doc_id else "新增出口文件")
        self.geometry("520x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        orders = bq.get_all_orders_for_combo()
        self.order_map = {o['order_number']: o['id'] for o in orders}
        invoices = bq.get_all_invoices_for_combo()
        self.invoice_map = {i['invoice_number']: i['id'] for i in invoices}

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="文件類型：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_type = ttk.Combobox(frame, values=EXPORT_DOC_TYPES, width=30)
        self.e_type.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="文件號碼：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_number = ttk.Entry(frame, width=25)
        self.e_number.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="關聯訂單：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_order = ttk.Combobox(frame, values=[''] + list(self.order_map.keys()), width=25)
        self.e_order.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="關聯發票：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_invoice = ttk.Combobox(frame, values=[''] + list(self.invoice_map.keys()), width=25)
        self.e_invoice.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="開立日期：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_date = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_date.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="目的國：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_dest = ttk.Entry(frame, width=20)
        self.e_dest.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="運輸方式：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_ship = ttk.Combobox(frame, values=SHIPPING_METHODS, width=10)
        self.e_ship.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="出貨日期：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_ship_date = ttk.DateEntry(frame, dateformat='%Y-%m-%d', width=12)
        self.e_ship_date.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="船名/航班：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_vessel = ttk.Entry(frame, width=25)
        self.e_vessel.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="提單號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_bl = ttk.Entry(frame, width=25)
        self.e_bl.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="貨櫃號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_container = ttk.Entry(frame, width=25)
        self.e_container.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=EXPORT_DOC_STATUS, width=10, state='readonly')
        self.e_status.set('準備中')
        self.e_status.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="備註：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_notes = ttk.Text(frame, width=35, height=2)
        self.e_notes.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        if doc_id:
            doc = bq.get_export_document(doc_id)
            if doc:
                self.e_type.set(doc['doc_type'])
                self.e_number.insert(0, doc['doc_number'] or '')
                if doc.get('order_number'):
                    self.e_order.set(doc['order_number'])
                self.e_dest.insert(0, doc['destination_country'] or '')
                if doc['shipping_method']:
                    self.e_ship.set(doc['shipping_method'])
                self.e_vessel.insert(0, doc['vessel_name'] or '')
                self.e_bl.insert(0, doc['bl_number'] or '')
                self.e_container.insert(0, doc['container_number'] or '')
                self.e_status.set(doc['status'] or '準備中')
                if doc['notes']:
                    self.e_notes.insert('1.0', doc['notes'])

        self.wait_window()

    def _on_ok(self):
        doc_type = self.e_type.get().strip()
        if not doc_type:
            ttk.dialogs.Messagebox.show_warning("文件類型為必填", parent=self)
            return

        order_name = self.e_order.get().strip()
        order_id = self.order_map.get(order_name)
        invoice_name = self.e_invoice.get().strip()
        invoice_id = self.invoice_map.get(invoice_name)

        data = dict(
            doc_type=doc_type,
            doc_number=self.e_number.get().strip() or None,
            order_id=order_id,
            invoice_id=invoice_id,
            issue_date=self.e_date.entry.get().strip() or None,
            destination_country=self.e_dest.get().strip() or None,
            shipping_method=self.e_ship.get().strip() or None,
            shipping_date=self.e_ship_date.entry.get().strip() or None,
            vessel_name=self.e_vessel.get().strip() or None,
            bl_number=self.e_bl.get().strip() or None,
            container_number=self.e_container.get().strip() or None,
            status=self.e_status.get(),
            notes=self.e_notes.get('1.0', 'end').strip() or None,
        )

        if self.doc_id:
            bq.update_export_document(self.doc_id, **data)
        else:
            bq.add_export_document(**data)

        self.result = True
        self.destroy()
