import os
import shutil
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


class MainWindow:
    """主視窗"""

    def __init__(self, root):
        self.root = root
        self.root.title("工程圖管理系統")
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)

        self._create_menu()
        self._create_toolbar()
        self._create_panels()
        self._create_statusbar()
        self._update_statusbar()

    def _create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # 檔案選單
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="另存圖面檔案副本...", command=self._save_drawing_copy)
        file_menu.add_command(label="匯出圖面清單 (CSV)", command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="離開", command=self.root.quit)

        # 編輯選單
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編輯", menu=edit_menu)
        edit_menu.add_command(label="新增客戶", command=self._add_client)
        edit_menu.add_command(label="新增專案", command=self._add_project)
        edit_menu.add_command(label="新增圖面", command=self._add_drawing)

        # 檢視選單
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檢視", menu=view_menu)
        view_menu.add_command(label="顯示所有圖面", command=self._show_all_drawings)
        view_menu.add_command(label="重新整理", command=self._refresh_all)

        # 工具選單
        tool_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tool_menu)
        tool_menu.add_command(label="進階搜尋", command=self._advanced_search)
        tool_menu.add_command(label="批次另存所有圖面副本...", command=self._batch_save_copies)

        # 說明選單
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="說明", menu=help_menu)
        help_menu.add_command(label="關於", command=self._show_about)

    def _create_toolbar(self):
        toolbar = ttk.Frame(self.root, padding=(10, 5))
        toolbar.pack(fill=X)

        # 公司名稱
        ttk.Label(toolbar, text=COMPANY_NAME, font=(FONT_FAMILY, 12, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT, padx=(0, 15))

        # 分隔線
        ttk.Separator(toolbar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=(0, 10), pady=2)

        # 搜尋列
        ttk.Label(toolbar, text="快速搜尋：").pack(side=LEFT)
        self.search_var = ttk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=(5, 5))
        search_entry.bind('<Return>', lambda e: self._quick_search())

        ttk.Button(toolbar, text="搜尋", command=self._quick_search, bootstyle=PRIMARY, width=6).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="清除", command=self._clear_search, bootstyle=SECONDARY, width=6).pack(side=LEFT, padx=2)
        ttk.Button(toolbar, text="進階搜尋", command=self._advanced_search, bootstyle=INFO+OUTLINE, width=8).pack(side=LEFT, padx=(10, 2))

        # 右側快捷按鈕
        ttk.Button(toolbar, text="+ 圖面", command=self._add_drawing, bootstyle=SUCCESS, width=8).pack(side=RIGHT, padx=2)
        ttk.Button(toolbar, text="+ 專案", command=self._add_project, bootstyle=INFO, width=8).pack(side=RIGHT, padx=2)
        ttk.Button(toolbar, text="+ 客戶", command=self._add_client, bootstyle=WARNING, width=8).pack(side=RIGHT, padx=2)

    def _create_panels(self):
        # 三面板佈局 — 使用 tk.PanedWindow 支援 minsize
        import tkinter as tk

        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL,
                               sashrelief=tk.FLAT, sashwidth=5,
                               bg='#E0E0E0', opaqueresize=True)
        paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 左側：客戶樹（最小 160px）
        self.client_tree = ClientTree(
            paned,
            on_project_selected=self._on_project_selected,
            on_client_selected=self._on_client_selected
        )
        paned.add(self.client_tree, minsize=160, stretch='never')

        # 中間：圖面清單（最小 250px）
        self.drawing_list = DrawingList(
            paned,
            on_drawing_selected=self._on_drawing_selected
        )
        paned.add(self.drawing_list, minsize=250, stretch='always')

        # 右側：詳情面板（最小 280px）
        self.detail_panel = DetailPanel(
            paned,
            on_refresh=self._on_detail_refresh
        )
        paned.add(self.detail_panel, minsize=280, stretch='always')

    def _create_statusbar(self):
        self.statusbar = ttk.Frame(self.root, padding=(10, 3))
        self.statusbar.pack(fill=X, side=BOTTOM)

        self.status_total = ttk.Label(self.statusbar, text="")
        self.status_total.pack(side=LEFT)

        self.status_info = ttk.Label(self.statusbar, text="")
        self.status_info.pack(side=RIGHT)

    def _update_statusbar(self):
        total = queries.get_drawing_count()
        clients = len(queries.get_all_clients())
        self.status_total.config(text=f"共 {total} 張圖面 | {clients} 個客戶")

    # === 事件處理 ===

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
            self.client_tree.refresh()
            self._update_statusbar()

    def _add_project(self):
        client_id = self.client_tree.get_selected_client_id()
        dialog = ProjectDialog(self.root, client_id=client_id)
        if dialog.result:
            self.client_tree.refresh()
            self._update_statusbar()

    def _add_drawing(self):
        project_id = self.client_tree.get_selected_project_id()
        dialog = DrawingDialog(self.root, project_id=project_id)
        if dialog.result:
            self.drawing_list.refresh()
            self.client_tree.refresh()
            self._update_statusbar()

    def _quick_search(self):
        keyword = self.search_var.get().strip()
        if not keyword:
            return
        results = queries.search_drawings(keyword=keyword)
        self.drawing_list.load_search_results(results)
        self.detail_panel.clear()
        self.status_info.config(text=f"搜尋「{keyword}」找到 {len(results)} 筆結果")

    def _clear_search(self):
        self.search_var.set('')
        self.status_info.config(text="")
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
            results = queries.search_drawings(**dialog.result)
            self.drawing_list.load_search_results(results)
            self.detail_panel.clear()
            self.status_info.config(text=f"進階搜尋找到 {len(results)} 筆結果")

    def _show_all_drawings(self):
        self.drawing_list.load_all()
        self.detail_panel.clear()

    def _refresh_all(self):
        self.client_tree.refresh()
        self.drawing_list.refresh()
        self.detail_panel.clear()
        self._update_statusbar()

    # === 另存副本 ===

    def _save_drawing_copy(self):
        """另存目前選取的圖面檔案副本"""
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

        # 建議檔名: 客戶_專案_圖號_版次.副檔名
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
        # 清理不合法檔名字元
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
        """批次另存所有圖面檔案到指定目錄"""
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
                # 建立 客戶/專案/ 子目錄
                client_name = d['client_name'] if 'client_name' in d.keys() else 'unknown'
                project_name = d['project_name'] if 'project_name' in d.keys() else 'unknown'
                # 清理不合法目錄名
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

    # === 匯出 ===

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
        """顯示關於對話框（含公司名稱）"""
        about_win = ttk.Toplevel(self.root)
        about_win.title("關於")
        about_win.geometry("380x320")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()

        frame = ttk.Frame(about_win, padding=20)
        frame.pack(fill=BOTH, expand=True)

        # 顯示公司名稱
        ttk.Label(frame, text=COMPANY_NAME,
                  font=(FONT_FAMILY, 16, 'bold'),
                  bootstyle=PRIMARY).pack(pady=(0, 15))

        ttk.Label(frame, text="工程圖管理系統", font=(FONT_FAMILY, 14, 'bold')).pack()
        ttk.Label(frame, text="v1.1", font=(FONT_FAMILY, 10)).pack(pady=(0, 10))

        info_text = (
            "按客戶/專案分類管理工程圖面\n"
            "版次追蹤（版次、日期、儲存人員）\n"
            "可縮放預覽（支援 DWG/PDF/TIFF/JPG/PNG）\n"
            "快速搜尋與進階搜尋\n"
            "另存檔案副本 / 匯出 CSV"
        )
        ttk.Label(frame, text=info_text, justify=CENTER, wraplength=340).pack(pady=(0, 15))

        ttk.Button(frame, text="確定", command=about_win.destroy, bootstyle=PRIMARY, width=10).pack()
