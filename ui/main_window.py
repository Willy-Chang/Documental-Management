"""主視窗 — 整合模組導航側邊欄與內容區域

左側為模組導航按鈕，右側為模組內容顯示區。
支援模組：儀表板、圖面管理、報價單、請購單、客戶訂單、發票紀錄、出口文件、生產進度、機器維修
"""
import os
import shutil
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, Menu

from db import queries
from ui.client_tree import ClientTree
from ui.drawing_list import DrawingList
from ui.detail_panel import DetailPanel
from ui.dialogs.client_dialog import ClientDialog
from ui.dialogs.project_dialog import ProjectDialog
from ui.dialogs.drawing_dialog import DrawingDialog
from ui.dialogs.search_dialog import SearchDialog
from core.export import export_drawings_to_csv
from config import COMPANY_NAME, FONT_FAMILY


# 模組定義：(key, label, icon_char, bootstyle)
MODULE_DEFS = [
    ('dashboard',    '總覽',     'D', PRIMARY),
    ('drawing',      '圖面管理', 'G', INFO),
    ('quotation',    '報價單',   'Q', SUCCESS),
    ('purchase',     '請購單',   'P', WARNING),
    ('order',        '客戶訂單', 'O', PRIMARY),
    ('invoice',      '發票紀錄', 'I', DANGER),
    ('export_doc',   '出口文件', 'E', INFO),
    ('production',   '生產進度', 'M', WARNING),
    ('maintenance',  '機器維修', 'R', DANGER),
]


class MainWindow:
    """主視窗 — 模組導航 + 內容切換"""

    def __init__(self, root):
        self.root = root
        self.root.title(f"{COMPANY_NAME} — 行政管理系統")
        self.root.geometry("1280x750")
        self.root.minsize(1000, 600)

        self.modules = {}
        self.current_module = None
        self.nav_buttons = {}

        self._create_menu()
        self._create_layout()
        self._switch_module('dashboard')

    def _create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="另存圖面檔案副本...", command=self._save_drawing_copy)
        file_menu.add_command(label="匯出圖面清單 (CSV)", command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="離開", command=self.root.quit)

        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編輯", menu=edit_menu)
        edit_menu.add_command(label="新增客戶", command=self._add_client)
        edit_menu.add_command(label="新增專案", command=self._add_project)
        edit_menu.add_command(label="新增圖面", command=self._add_drawing)

        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檢視", menu=view_menu)
        view_menu.add_command(label="顯示所有圖面", command=self._show_all_drawings)
        view_menu.add_command(label="重新整理", command=self._refresh_all)

        tool_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tool_menu)
        tool_menu.add_command(label="進階搜尋", command=self._advanced_search)
        tool_menu.add_command(label="批次另存所有圖面副本...", command=self._batch_save_copies)

        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="說明", menu=help_menu)
        help_menu.add_command(label="關於", command=self._show_about)

    def _create_layout(self):
        """建立側邊欄 + 內容區主佈局"""
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True)

        # === 左側導航 ===
        self.sidebar = ttk.Frame(main_frame, width=110, padding=0)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        # 公司簡稱
        logo_frame = ttk.Frame(self.sidebar, padding=(5, 8))
        logo_frame.pack(fill=X)
        ttk.Label(logo_frame, text="劦佑機械", font=(FONT_FAMILY, 10, 'bold'),
                  bootstyle=PRIMARY, anchor=CENTER).pack(fill=X)
        ttk.Separator(self.sidebar, orient=HORIZONTAL).pack(fill=X, padx=5, pady=3)

        # 導航按鈕
        for key, label, icon, style in MODULE_DEFS:
            btn_frame = ttk.Frame(self.sidebar)
            btn_frame.pack(fill=X, padx=4, pady=1)

            btn = ttk.Button(
                btn_frame,
                text=f" {icon}  {label}",
                command=lambda k=key: self._switch_module(k),
                bootstyle=SECONDARY+OUTLINE,
                width=12,
            )
            btn.pack(fill=X, ipady=3)
            self.nav_buttons[key] = btn

        # 底部版本
        ttk.Frame(self.sidebar).pack(fill=BOTH, expand=True)
        ttk.Label(self.sidebar, text="v2.0", foreground='#AAAAAA',
                  font=(FONT_FAMILY, 8), anchor=CENTER).pack(fill=X, pady=5)

        # === 分隔線 ===
        ttk.Separator(main_frame, orient=VERTICAL).pack(side=LEFT, fill=Y)

        # === 右側內容區 ===
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # 狀態列
        self.statusbar = ttk.Frame(self.root, padding=(10, 3))
        self.statusbar.pack(fill=X, side=BOTTOM)
        self.status_total = ttk.Label(self.statusbar, text="")
        self.status_total.pack(side=LEFT)
        self.status_info = ttk.Label(self.statusbar, text="")
        self.status_info.pack(side=RIGHT)

    def _switch_module(self, module_key):
        """切換到指定模組"""
        if self.current_module == module_key:
            return

        # 更新按鈕樣式
        for key, btn in self.nav_buttons.items():
            if key == module_key:
                # 找到對應的 style
                style = next((s for k, l, i, s in MODULE_DEFS if k == key), PRIMARY)
                btn.configure(bootstyle=style)
            else:
                btn.configure(bootstyle=SECONDARY+OUTLINE)

        # 隱藏當前模組
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()

        # 建立或顯示目標模組
        if module_key not in self.modules:
            self.modules[module_key] = self._create_module(module_key)

        module_widget = self.modules[module_key]
        if module_widget:
            module_widget.pack(fill=BOTH, expand=True)

        self.current_module = module_key
        self._update_statusbar()

    def _create_module(self, key):
        """依 key 建立對應模組"""
        if key == 'dashboard':
            from ui.modules.dashboard_module import DashboardModule
            return DashboardModule(self.content_frame)

        elif key == 'drawing':
            return self._create_drawing_module()

        elif key == 'quotation':
            from ui.modules.quotation_module import QuotationModule
            return QuotationModule(self.content_frame)

        elif key == 'purchase':
            from ui.modules.purchase_module import PurchaseModule
            return PurchaseModule(self.content_frame)

        elif key == 'order':
            from ui.modules.order_module import OrderModule
            return OrderModule(self.content_frame)

        elif key == 'invoice':
            from ui.modules.invoice_module import InvoiceModule
            return InvoiceModule(self.content_frame)

        elif key == 'export_doc':
            from ui.modules.export_doc_module import ExportDocModule
            return ExportDocModule(self.content_frame)

        elif key == 'production':
            from ui.modules.production_module import ProductionModule
            return ProductionModule(self.content_frame)

        elif key == 'maintenance':
            from ui.modules.maintenance_module import MaintenanceModule
            return MaintenanceModule(self.content_frame)

        return None

    def _create_drawing_module(self):
        """建立圖面管理模組（包裹原有三面板佈局）"""
        container = ttk.Frame(self.content_frame)

        # 工具列
        toolbar = ttk.Frame(container, padding=(5, 5))
        toolbar.pack(fill=X)

        ttk.Label(toolbar, text="圖面管理", font=(FONT_FAMILY, 14, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        ttk.Separator(toolbar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=(0, 10), pady=2)

        ttk.Label(toolbar, text="快速搜尋：").pack(side=LEFT)
        self.search_var = ttk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=25)
        search_entry.pack(side=LEFT, padx=(5, 5))
        search_entry.bind('<Return>', lambda e: self._quick_search())

        ttk.Button(toolbar, text="搜尋", command=self._quick_search,
                   bootstyle=PRIMARY, width=6).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="清除", command=self._clear_search,
                   bootstyle=SECONDARY, width=6).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="進階搜尋", command=self._advanced_search,
                   bootstyle=INFO+OUTLINE, width=8).pack(side=LEFT, padx=(10, 2))

        ttk.Button(toolbar, text="+ 圖面", command=self._add_drawing,
                   bootstyle=SUCCESS, width=8).pack(side=RIGHT, padx=2)
        ttk.Button(toolbar, text="+ 專案", command=self._add_project,
                   bootstyle=INFO, width=8).pack(side=RIGHT, padx=2)
        ttk.Button(toolbar, text="+ 客戶", command=self._add_client,
                   bootstyle=WARNING, width=8).pack(side=RIGHT, padx=2)

        # 三面板佈局
        paned = tk.PanedWindow(container, orient=tk.HORIZONTAL,
                               sashrelief=tk.FLAT, sashwidth=5,
                               bg='#E0E0E0', opaqueresize=True)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.client_tree = ClientTree(
            paned,
            on_project_selected=self._on_project_selected,
            on_client_selected=self._on_client_selected
        )
        paned.add(self.client_tree, minsize=160, stretch='never')

        self.drawing_list = DrawingList(
            paned,
            on_drawing_selected=self._on_drawing_selected
        )
        paned.add(self.drawing_list, minsize=250, stretch='always')

        self.detail_panel = DetailPanel(
            paned,
            on_refresh=self._on_detail_refresh
        )
        paned.add(self.detail_panel, minsize=280, stretch='always')

        return container

    def _update_statusbar(self):
        try:
            total = queries.get_drawing_count()
            clients = len(queries.get_all_clients())
            self.status_total.config(text=f"共 {total} 張圖面 | {clients} 個客戶")
        except Exception:
            pass
        module_name = next((l for k, l, i, s in MODULE_DEFS
                           if k == self.current_module), '')
        self.status_info.config(text=f"目前模組：{module_name}")

    # === 圖面管理事件 ===

    def _on_project_selected(self, project_id):
        self.drawing_list.load_by_project(project_id)
        self.detail_panel.clear()
        self._update_statusbar()

    def _on_client_selected(self, client_id):
        self.drawing_list.load_by_client(client_id)
        self.detail_panel.clear()
        self._update_statusbar()

    def _on_drawing_selected(self, drawing_id):
        self.detail_panel.load_drawing(drawing_id)

    def _on_detail_refresh(self):
        self.drawing_list.refresh()
        self.client_tree.refresh()
        self._update_statusbar()

    # === 選單動作 ===

    def _add_client(self):
        dialog = ClientDialog(self.root)
        if dialog.result:
            if hasattr(self, 'client_tree'):
                self.client_tree.refresh()
            self._update_statusbar()

    def _add_project(self):
        client_id = None
        if hasattr(self, 'client_tree'):
            client_id = self.client_tree.get_selected_client_id()
        dialog = ProjectDialog(self.root, client_id=client_id)
        if dialog.result:
            if hasattr(self, 'client_tree'):
                self.client_tree.refresh()
            self._update_statusbar()

    def _add_drawing(self):
        project_id = None
        if hasattr(self, 'client_tree'):
            project_id = self.client_tree.get_selected_project_id()
        dialog = DrawingDialog(self.root, project_id=project_id)
        if dialog.result:
            if hasattr(self, 'drawing_list'):
                self.drawing_list.refresh()
                self.client_tree.refresh()
            self._update_statusbar()

    def _quick_search(self):
        if not hasattr(self, 'search_var'):
            return
        keyword = self.search_var.get().strip()
        if not keyword:
            return
        if self.current_module != 'drawing':
            self._switch_module('drawing')
        results = queries.search_drawings(keyword=keyword)
        self.drawing_list.load_search_results(results)
        self.detail_panel.clear()
        self.status_info.config(text=f"搜尋「{keyword}」找到 {len(results)} 筆結果")

    def _clear_search(self):
        if not hasattr(self, 'search_var'):
            return
        self.search_var.set('')
        self.status_info.config(text="")
        if hasattr(self, 'client_tree'):
            project_id = self.client_tree.get_selected_project_id()
            if project_id:
                self.drawing_list.load_by_project(project_id)
            else:
                client_id = self.client_tree.get_selected_client_id()
                if client_id:
                    self.drawing_list.load_by_client(client_id)

    def _advanced_search(self):
        dialog = SearchDialog(self.root)
        if dialog.result:
            if self.current_module != 'drawing':
                self._switch_module('drawing')
            results = queries.search_drawings(**dialog.result)
            self.drawing_list.load_search_results(results)
            self.detail_panel.clear()
            self.status_info.config(text=f"進階搜尋找到 {len(results)} 筆結果")

    def _show_all_drawings(self):
        if self.current_module != 'drawing':
            self._switch_module('drawing')
        if hasattr(self, 'drawing_list'):
            self.drawing_list.load_all()
            self.detail_panel.clear()

    def _refresh_all(self):
        if hasattr(self, 'client_tree'):
            self.client_tree.refresh()
            self.drawing_list.refresh()
            self.detail_panel.clear()
        # 重整當前模組
        if self.current_module in self.modules:
            module = self.modules[self.current_module]
            if hasattr(module, 'refresh'):
                module.refresh()
        self._update_statusbar()

    # === 另存副本 ===

    def _save_drawing_copy(self):
        if not hasattr(self, 'drawing_list'):
            return
        drawing_id = self.drawing_list.get_selected_drawing_id()
        if not drawing_id:
            ttk.dialogs.Messagebox.show_info("請先選擇一張圖面", title="提示", parent=self.root)
            return

        drawing = queries.get_drawing(drawing_id)
        if not drawing or not drawing['file_path']:
            ttk.dialogs.Messagebox.show_info("此圖面尚未設定檔案路徑", title="提示", parent=self.root)
            return

        src_path = drawing['file_path']
        if not os.path.exists(src_path):
            ttk.dialogs.Messagebox.show_warning(
                f"找不到原始檔案：\n{src_path}", title="檔案不存在", parent=self.root
            )
            return

        project = queries.get_project(drawing['project_id'])
        client = queries.get_client(project['client_id']) if project else None
        ext = os.path.splitext(src_path)[1]
        parts = []
        if client and client['name']:
            parts.append(client['name'])
        if project and project['name']:
            parts.append(project['name'])
        parts.append(drawing['drawing_number'])
        parts.append(f"Rev{drawing['current_rev']}")
        suggested_name = '_'.join(parts) + ext
        for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            suggested_name = suggested_name.replace(ch, '_')

        dest_path = filedialog.asksaveasfilename(
            title="另存圖面檔案副本",
            initialfile=suggested_name,
            defaultextension=ext,
            filetypes=[
                (f"{ext.upper().strip('.')} 檔案", f"*{ext}"),
                ("所有檔案", "*.*")
            ],
            parent=self.root
        )
        if dest_path:
            try:
                shutil.copy2(src_path, dest_path)
                ttk.dialogs.Messagebox.show_info(
                    f"檔案已另存至：\n{dest_path}", title="另存成功", parent=self.root
                )
            except Exception as e:
                ttk.dialogs.Messagebox.show_error(f"另存失敗：{e}", title="錯誤", parent=self.root)

    def _batch_save_copies(self):
        dest_dir = filedialog.askdirectory(title="選擇備份目標資料夾", parent=self.root)
        if not dest_dir:
            return

        all_drawings = queries.get_all_drawings()
        success = 0
        skip = 0
        fail = 0

        for d in all_drawings:
            if not d['file_path'] or not os.path.exists(d['file_path']):
                skip += 1
                continue
            try:
                client_name = d['client_name'] if 'client_name' in d.keys() else 'unknown'
                project_name = d['project_name'] if 'project_name' in d.keys() else 'unknown'
                for ch in [':', '*', '?', '"', '<', '>', '|']:
                    client_name = client_name.replace(ch, '_')
                    project_name = project_name.replace(ch, '_')
                sub_dir = os.path.join(dest_dir, client_name, project_name)
                os.makedirs(sub_dir, exist_ok=True)

                ext = os.path.splitext(d['file_path'])[1]
                dest_name = f"{d['drawing_number']}_Rev{d['current_rev']}{ext}"
                for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
                    dest_name = dest_name.replace(ch, '_')
                dest_path = os.path.join(sub_dir, dest_name)

                shutil.copy2(d['file_path'], dest_path)
                success += 1
            except Exception:
                fail += 1

        ttk.dialogs.Messagebox.show_info(
            f"批次另存完成！\n\n"
            f"成功：{success} 個檔案\n"
            f"跳過（無檔案路徑）：{skip} 個\n"
            f"失敗：{fail} 個\n\n"
            f"儲存位置：{dest_dir}",
            title="批次另存結果", parent=self.root
        )

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            title="匯出 CSV",
            defaultextension=".csv",
            filetypes=[("CSV 檔案", "*.csv"), ("所有檔案", "*.*")],
            parent=self.root
        )
        if path:
            try:
                export_drawings_to_csv(path)
                ttk.dialogs.Messagebox.show_info(
                    f"已匯出至：\n{path}", title="匯出成功", parent=self.root
                )
            except Exception as e:
                ttk.dialogs.Messagebox.show_error(
                    f"匯出失敗：{e}", title="錯誤", parent=self.root
                )

    def _show_about(self):
        about_win = ttk.Toplevel(self.root)
        about_win.title("關於")
        about_win.geometry("400x360")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()

        frame = ttk.Frame(about_win, padding=20)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text=COMPANY_NAME,
                  font=(FONT_FAMILY, 16, 'bold'),
                  bootstyle=PRIMARY).pack(pady=(0, 10))

        ttk.Label(frame, text="行政管理系統", font=(FONT_FAMILY, 14, 'bold')).pack()
        ttk.Label(frame, text="v2.0", font=(FONT_FAMILY, 10)).pack(pady=(0, 10))

        info_text = (
            "工程圖面管理 / 報價單生成\n"
            "請購單管理 / 客戶訂單整理\n"
            "發票紀錄 / 出口文件紀錄\n"
            "生產進度甘特圖 / 機器維修彙報\n"
            "\n"
            "支援 PDF 匯出 / CSV 匯出\n"
            "支援 DWG/DXF/PDF/IGES 圖檔"
        )
        ttk.Label(frame, text=info_text, justify=CENTER, wraplength=360).pack(pady=(0, 15))

        ttk.Button(frame, text="確定", command=about_win.destroy,
                   bootstyle=PRIMARY, width=10).pack()
