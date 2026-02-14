"""報價單管理模組"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
from datetime import datetime

from db import business_queries as bq
from config import (QUOTATION_STATUS, CURRENCY_OPTIONS, UNIT_OPTIONS,
                    PAYMENT_TERMS_OPTIONS, DELIVERY_TERMS_OPTIONS,
                    DOC_NUMBER_PREFIX, DEFAULT_OPERATOR, FONT_FAMILY)


class QuotationModule(ttk.Frame):
    """報價單管理模組"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_toolbar()
        self._create_content()
        self.refresh()

    def _create_toolbar(self):
        toolbar = ttk.Frame(self, padding=(5, 5))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="報價單管理", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        ttk.Button(toolbar, text="+ 新增報價單", command=self._on_add,
                   bootstyle=SUCCESS, width=12).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="編輯", command=self._on_edit,
                   bootstyle=INFO, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="刪除", command=self._on_delete,
                   bootstyle=DANGER, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="轉訂單", command=self._on_convert_to_order,
                   bootstyle=WARNING, width=8).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="匯出 PDF", command=self._on_export_pdf,
                   bootstyle=PRIMARY+OUTLINE, width=10).pack(side=LEFT, padx=2)

        # 篩選
        ttk.Label(toolbar, text="狀態：").pack(side=RIGHT, padx=(10, 2))
        self.filter_status = ttk.Combobox(toolbar, values=['全部'] + QUOTATION_STATUS,
                                          width=10, state='readonly')
        self.filter_status.set('全部')
        self.filter_status.pack(side=RIGHT, padx=2)
        self.filter_status.bind('<<ComboboxSelected>>', lambda e: self.refresh())

    def _create_content(self):
        paned = ttk.PanedWindow(self, orient=VERTICAL)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 上方：報價單清單
        list_frame = ttk.LabelFrame(paned, text="報價單清單")
        paned.add(list_frame, weight=3)

        cols = ('id', 'number', 'client', 'subject', 'currency', 'total', 'status', 'date')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=10)
        self.tree.heading('id', text='ID')
        self.tree.heading('number', text='報價單號')
        self.tree.heading('client', text='客戶')
        self.tree.heading('subject', text='主旨')
        self.tree.heading('currency', text='幣別')
        self.tree.heading('total', text='金額')
        self.tree.heading('status', text='狀態')
        self.tree.heading('date', text='建立日期')
        self.tree.column('id', width=40, anchor=CENTER)
        self.tree.column('number', width=140)
        self.tree.column('client', width=120)
        self.tree.column('subject', width=200)
        self.tree.column('currency', width=60, anchor=CENTER)
        self.tree.column('total', width=100, anchor=E)
        self.tree.column('status', width=80, anchor=CENTER)
        self.tree.column('date', width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda e: self._on_edit())

        # 下方：品項明細
        detail_frame = ttk.LabelFrame(paned, text="品項明細")
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

        item_cols = ('id', 'no', 'part', 'desc', 'spec', 'qty', 'unit', 'price', 'amount')
        self.item_tree = ttk.Treeview(detail_frame, columns=item_cols, show='headings', height=6)
        self.item_tree.heading('id', text='ID')
        self.item_tree.heading('no', text='項次')
        self.item_tree.heading('part', text='料號')
        self.item_tree.heading('desc', text='品名')
        self.item_tree.heading('spec', text='規格')
        self.item_tree.heading('qty', text='數量')
        self.item_tree.heading('unit', text='單位')
        self.item_tree.heading('price', text='單價')
        self.item_tree.heading('amount', text='小計')
        self.item_tree.column('id', width=35, anchor=CENTER)
        self.item_tree.column('no', width=40, anchor=CENTER)
        self.item_tree.column('part', width=90)
        self.item_tree.column('desc', width=180)
        self.item_tree.column('spec', width=120)
        self.item_tree.column('qty', width=60, anchor=E)
        self.item_tree.column('unit', width=45, anchor=CENTER)
        self.item_tree.column('price', width=80, anchor=E)
        self.item_tree.column('amount', width=90, anchor=E)

        item_scroll = ttk.Scrollbar(detail_frame, orient=VERTICAL, command=self.item_tree.yview)
        self.item_tree.configure(yscrollcommand=item_scroll.set)
        self.item_tree.pack(side=LEFT, fill=BOTH, expand=True)
        item_scroll.pack(side=RIGHT, fill=Y)
        self.item_tree.bind('<Double-1>', lambda e: self._on_edit_item())

    def refresh(self):
        status_filter = self.filter_status.get()
        status = None if status_filter == '全部' else status_filter
        rows = bq.get_all_quotations(status=status)
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            total = bq.get_quotation_total(r['id'])
            self.tree.insert('', END, values=(
                r['id'], r['quotation_number'],
                r['client_name'] or '', r['subject'] or '',
                r['currency'], f'{total:,.2f}',
                r['status'], r['created_at'][:10] if r['created_at'] else ''
            ))
        self._clear_items()

    def _clear_items(self):
        self.item_tree.delete(*self.item_tree.get_children())
        self.item_total_label.config(text="合計：$0")

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0])['values'][0]

    def _get_selected_item_id(self):
        sel = self.item_tree.selection()
        if not sel:
            return None
        return self.item_tree.item(sel[0])['values'][0]

    def _on_select(self, event=None):
        qid = self._get_selected_id()
        if not qid:
            return
        items = bq.get_quotation_items(qid)
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
                f'{qty:,.2f}', item['unit'], f'{price:,.2f}', f'{amount:,.2f}'
            ))
        self.item_total_label.config(text=f"合計：${total:,.2f}")

    # === 報價單 CRUD ===

    def _on_add(self):
        dlg = QuotationDialog(self.winfo_toplevel())
        if dlg.result:
            self.refresh()

    def _on_edit(self):
        qid = self._get_selected_id()
        if not qid:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆報價單", parent=self.winfo_toplevel())
            return
        dlg = QuotationDialog(self.winfo_toplevel(), quotation_id=qid)
        if dlg.result:
            self.refresh()

    def _on_delete(self):
        qid = self._get_selected_id()
        if not qid:
            return
        if ttk.dialogs.Messagebox.yesno("確定要刪除此報價單？", parent=self.winfo_toplevel()) == '是':
            bq.delete_quotation(qid)
            self.refresh()

    def _on_convert_to_order(self):
        qid = self._get_selected_id()
        if not qid:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆報價單", parent=self.winfo_toplevel())
            return
        q = bq.get_quotation(qid)
        if not q or not q['client_id']:
            ttk.dialogs.Messagebox.show_warning("此報價單無客戶資料，無法轉訂單",
                                                parent=self.winfo_toplevel())
            return
        order_num = bq.generate_next_number(
            DOC_NUMBER_PREFIX['customer_order'], 'customer_orders', 'order_number')
        order_id = bq.copy_quotation_to_order(qid, order_num, bq._today())
        if order_id:
            ttk.dialogs.Messagebox.show_info(
                f"已成功轉為訂單：{order_num}", parent=self.winfo_toplevel())
            self.refresh()

    def _on_export_pdf(self):
        qid = self._get_selected_id()
        if not qid:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆報價單", parent=self.winfo_toplevel())
            return
        q = bq.get_quotation(qid)
        items = bq.get_quotation_items(qid)
        filepath = filedialog.asksaveasfilename(
            title="匯出報價單 PDF",
            initialfile=f"{q['quotation_number']}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF 檔案", "*.pdf")],
            parent=self.winfo_toplevel()
        )
        if filepath:
            try:
                from core.pdf_generator import generate_quotation_pdf
                generate_quotation_pdf(filepath, dict(q), [dict(i) for i in items],
                                       client_name=q['client_name'] or '')
                ttk.dialogs.Messagebox.show_info(
                    f"PDF 已匯出至：\n{filepath}", parent=self.winfo_toplevel())
            except Exception as e:
                ttk.dialogs.Messagebox.show_error(
                    f"PDF 匯出失敗：{e}", parent=self.winfo_toplevel())

    # === 品項 CRUD ===

    def _on_add_item(self):
        qid = self._get_selected_id()
        if not qid:
            ttk.dialogs.Messagebox.show_info("請先選擇一筆報價單", parent=self.winfo_toplevel())
            return
        items = bq.get_quotation_items(qid)
        next_no = max([i['item_no'] for i in items], default=0) + 1
        dlg = ItemDialog(self.winfo_toplevel(), title="新增品項")
        if dlg.result:
            bq.add_quotation_item(qid, next_no, **dlg.result)
            self._on_select()

    def _on_edit_item(self):
        item_id = self._get_selected_item_id()
        if not item_id:
            return
        # 從 item_tree 取得現有值
        sel = self.item_tree.selection()
        vals = self.item_tree.item(sel[0])['values']
        existing = {
            'part_number': vals[2], 'description': vals[3],
            'specification': vals[4], 'quantity': vals[5],
            'unit': vals[6], 'unit_price': vals[7],
        }
        dlg = ItemDialog(self.winfo_toplevel(), title="編輯品項", data=existing)
        if dlg.result:
            bq.update_quotation_item(item_id, **dlg.result)
            self._on_select()

    def _on_delete_item(self):
        item_id = self._get_selected_item_id()
        if item_id:
            bq.delete_quotation_item(item_id)
            self._on_select()


class QuotationDialog(ttk.Toplevel):
    """報價單新增/編輯對話框"""

    def __init__(self, parent, quotation_id=None):
        super().__init__(parent)
        self.result = None
        self.quotation_id = quotation_id
        self.title("編輯報價單" if quotation_id else "新增報價單")
        self.geometry("550x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        clients = bq.get_all_clients_for_combo()
        self.client_map = {c['name']: c['id'] for c in clients}
        client_names = list(self.client_map.keys())

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="報價單號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_number = ttk.Entry(frame, width=30)
        self.e_number.grid(row=row, column=1, columnspan=2, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="客戶：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_client = ttk.Combobox(frame, values=client_names, width=28)
        self.e_client.grid(row=row, column=1, columnspan=2, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="主旨：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_subject = ttk.Entry(frame, width=40)
        self.e_subject.grid(row=row, column=1, columnspan=2, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="幣別：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_currency = ttk.Combobox(frame, values=CURRENCY_OPTIONS, width=10, state='readonly')
        self.e_currency.set('TWD')
        self.e_currency.grid(row=row, column=1, sticky=W, pady=3)

        ttk.Label(frame, text="稅率：").grid(row=row, column=2, sticky=W, pady=3, padx=(10, 0))
        self.e_tax = ttk.Entry(frame, width=8)
        self.e_tax.insert(0, '0.05')
        self.e_tax.grid(row=row, column=3, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="付款條件：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_payment = ttk.Combobox(frame, values=PAYMENT_TERMS_OPTIONS, width=28)
        self.e_payment.grid(row=row, column=1, columnspan=2, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="交貨條件：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_delivery = ttk.Combobox(frame, values=DELIVERY_TERMS_OPTIONS, width=28)
        self.e_delivery.grid(row=row, column=1, columnspan=2, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="有效天數：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_validity = ttk.Entry(frame, width=10)
        self.e_validity.insert(0, '30')
        self.e_validity.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="狀態：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_status = ttk.Combobox(frame, values=QUOTATION_STATUS, width=10, state='readonly')
        self.e_status.set('草稿')
        self.e_status.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="備註：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_notes = ttk.Text(frame, width=40, height=4)
        self.e_notes.grid(row=row, column=1, columnspan=3, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=15)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        # 載入現有資料
        if quotation_id:
            q = bq.get_quotation(quotation_id)
            if q:
                self.e_number.insert(0, q['quotation_number'])
                self.e_number.config(state='readonly')
                if q['client_name']:
                    self.e_client.set(q['client_name'])
                self.e_subject.insert(0, q['subject'] or '')
                self.e_currency.set(q['currency'] or 'TWD')
                self.e_tax.delete(0, 'end')
                self.e_tax.insert(0, str(q['tax_rate'] or 0.05))
                if q['payment_terms']:
                    self.e_payment.set(q['payment_terms'])
                if q['delivery_terms']:
                    self.e_delivery.set(q['delivery_terms'])
                self.e_validity.delete(0, 'end')
                self.e_validity.insert(0, str(q['validity_days'] or 30))
                self.e_status.set(q['status'] or '草稿')
                if q['notes']:
                    self.e_notes.insert('1.0', q['notes'])
        else:
            num = bq.generate_next_number(
                DOC_NUMBER_PREFIX['quotation'], 'quotations', 'quotation_number')
            self.e_number.insert(0, num)

        self.wait_window()

    def _on_ok(self):
        number = self.e_number.get().strip()
        client_name = self.e_client.get().strip()
        client_id = self.client_map.get(client_name)

        if not number:
            ttk.dialogs.Messagebox.show_warning("報價單號不可為空", parent=self)
            return

        data = dict(
            client_id=client_id,
            subject=self.e_subject.get().strip() or None,
            currency=self.e_currency.get(),
            tax_rate=float(self.e_tax.get() or 0.05),
            payment_terms=self.e_payment.get().strip() or None,
            delivery_terms=self.e_delivery.get().strip() or None,
            validity_days=int(self.e_validity.get() or 30),
            status=self.e_status.get(),
            notes=self.e_notes.get('1.0', 'end').strip() or None,
        )

        if self.quotation_id:
            bq.update_quotation(self.quotation_id, **data)
        else:
            bq.add_quotation(quotation_number=number, created_by=DEFAULT_OPERATOR, **data)

        self.result = True
        self.destroy()


class ItemDialog(ttk.Toplevel):
    """品項新增/編輯對話框（報價單 / 訂單通用）"""

    def __init__(self, parent, title="品項", data=None):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.geometry("420x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="料號：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_part = ttk.Entry(frame, width=25)
        self.e_part.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="品名：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_desc = ttk.Entry(frame, width=35)
        self.e_desc.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="規格：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_spec = ttk.Entry(frame, width=35)
        self.e_spec.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="數量：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_qty = ttk.Entry(frame, width=12)
        self.e_qty.insert(0, '1')
        self.e_qty.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="單位：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_unit = ttk.Combobox(frame, values=UNIT_OPTIONS, width=10)
        self.e_unit.set('PCS')
        self.e_unit.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="單價：").grid(row=row, column=0, sticky=W, pady=3)
        self.e_price = ttk.Entry(frame, width=12)
        self.e_price.insert(0, '0')
        self.e_price.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        ttk.Label(frame, text="備註：").grid(row=row, column=0, sticky=NW, pady=3)
        self.e_notes = ttk.Text(frame, width=35, height=3)
        self.e_notes.grid(row=row, column=1, sticky=W, pady=3)

        row += 1
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="確定", command=self._on_ok,
                   bootstyle=PRIMARY, width=10).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy,
                   bootstyle=SECONDARY, width=10).pack(side=LEFT, padx=5)

        if data:
            self.e_part.insert(0, str(data.get('part_number', '') or ''))
            self.e_desc.delete(0, 'end')
            self.e_desc.insert(0, str(data.get('description', '')))
            self.e_spec.insert(0, str(data.get('specification', '') or ''))
            self.e_qty.delete(0, 'end')
            self.e_qty.insert(0, str(data.get('quantity', 1)))
            self.e_unit.set(data.get('unit', 'PCS'))
            self.e_price.delete(0, 'end')
            self.e_price.insert(0, str(data.get('unit_price', 0)))

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

        self.result = dict(
            part_number=self.e_part.get().strip() or None,
            description=desc,
            specification=self.e_spec.get().strip() or None,
            quantity=qty,
            unit=self.e_unit.get(),
            unit_price=price,
            notes=self.e_notes.get('1.0', 'end').strip() or None,
        )
        self.destroy()
