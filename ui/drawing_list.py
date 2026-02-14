import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from db import queries
from config import FONT_FAMILY
from core.icon_extractor import get_file_icon_cache


class DrawingList(ttk.Frame):
    """中間面板：圖面清單表格"""

    COLUMNS = {
        'drawing_number': {'text': '圖號', 'width': 120},
        'title': {'text': '標題', 'width': 160},
        'file_ext': {'text': '格式', 'width': 55},
        'current_rev': {'text': '版次', 'width': 50},
        'status': {'text': '狀態', 'width': 70},
        'drawing_type': {'text': '類型', 'width': 70},
        'updated_at': {'text': '更新日期', 'width': 130},
    }

    def __init__(self, parent, on_drawing_selected=None):
        super().__init__(parent)
        self.on_drawing_selected = on_drawing_selected
        self._current_project_id = None
        self._current_drawings = []
        self._sort_col = 'drawing_number'
        self._sort_reverse = False
        self._icon_refs = {}  # 保持 PhotoImage 參照避免被 GC 回收

        self._create_widgets()

    def _create_widgets(self):
        # 標題
        header = ttk.Frame(self)
        header.pack(fill=X, padx=5, pady=(5, 0))
        self.header_label = ttk.Label(header, text="圖面清單", font=(FONT_FAMILY, 11, 'bold'))
        self.header_label.pack(side=LEFT)
        self.count_label = ttk.Label(header, text="")
        self.count_label.pack(side=RIGHT)

        # 表格
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        cols = list(self.COLUMNS.keys())
        # 使用 'tree headings' 模式，讓 #0 欄位顯示圖示
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='tree headings', selectmode='browse')

        # #0 欄位（tree column）用於顯示圖示
        self.tree.heading('#0', text='')
        self.tree.column('#0', width=30, minwidth=30, stretch=False)

        for col_id, col_info in self.COLUMNS.items():
            self.tree.heading(col_id, text=col_info['text'],
                            command=lambda c=col_id: self._sort_by(c))
            self.tree.column(col_id, width=col_info['width'], minwidth=40)

        v_scroll = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky=NSEW)
        v_scroll.grid(row=0, column=1, sticky=NS)
        h_scroll.grid(row=1, column=0, sticky=EW)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', self._on_double_click)

    def load_by_project(self, project_id):
        """載入指定專案的圖面"""
        self._current_project_id = project_id
        project = queries.get_project(project_id)
        if project:
            self.header_label.config(text=f"圖面清單 - {project['name']}")

        self._current_drawings = queries.get_drawings_by_project(project_id)
        self._display_drawings(self._current_drawings)

    def load_by_client(self, client_id):
        """載入指定客戶所有圖面"""
        self._current_project_id = None
        client = queries.get_client(client_id)
        if client:
            self.header_label.config(text=f"圖面清單 - {client['name']}（所有專案）")

        drawings = []
        for p in queries.get_projects_by_client(client_id):
            drawings.extend(queries.get_drawings_by_project(p['id']))
        self._current_drawings = drawings
        self._display_drawings(self._current_drawings)

    def load_search_results(self, drawings):
        """載入搜尋結果"""
        self.header_label.config(text="搜尋結果")
        self._current_project_id = None
        self._current_drawings = drawings
        self._display_drawings(drawings)

    def load_all(self):
        """載入所有圖面"""
        self.header_label.config(text="所有圖面")
        self._current_project_id = None
        self._current_drawings = queries.get_all_drawings()
        self._display_drawings(self._current_drawings)

    def _display_drawings(self, drawings):
        """顯示圖面到表格"""
        self.tree.delete(*self.tree.get_children())
        self._icon_refs.clear()

        icon_cache = get_file_icon_cache()

        for d in drawings:
            file_path = d['file_path'] or ''
            ext = os.path.splitext(file_path)[1].lower() if file_path else ''
            ext_display = ext.lstrip('.').upper() if ext else ''

            # 取得系統圖示
            icon = None
            if ext:
                try:
                    icon = icon_cache.get_icon(ext, widget=self.tree)
                except Exception:
                    pass

            iid = str(d['id'])
            if icon:
                self._icon_refs[iid] = icon  # 防止 GC 回收
                self.tree.insert('', 'end', iid=iid, image=icon, values=(
                    d['drawing_number'],
                    d['title'],
                    ext_display,
                    d['current_rev'] or '',
                    d['status'] or '',
                    d['drawing_type'] or '',
                    (d['updated_at'] or '')[:16],
                ))
            else:
                self.tree.insert('', 'end', iid=iid, values=(
                    d['drawing_number'],
                    d['title'],
                    ext_display,
                    d['current_rev'] or '',
                    d['status'] or '',
                    d['drawing_type'] or '',
                    (d['updated_at'] or '')[:16],
                ))

        self.count_label.config(text=f"共 {len(drawings)} 張")

    def _sort_by(self, col):
        """按欄位排序"""
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False

        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        items.sort(reverse=self._sort_reverse)

        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        drawing_id = int(selection[0])
        if self.on_drawing_selected:
            self.on_drawing_selected(drawing_id)

    def _on_double_click(self, event):
        """雙擊開啟圖檔"""
        selection = self.tree.selection()
        if not selection:
            return
        drawing_id = int(selection[0])
        drawing = queries.get_drawing(drawing_id)
        if drawing and drawing['file_path']:
            from core.file_manager import open_file
            if not open_file(drawing['file_path']):
                ttk.dialogs.Messagebox.show_warning(
                    f"找不到檔案：\n{drawing['file_path']}",
                    title="檔案不存在",
                    parent=self.winfo_toplevel()
                )

    def refresh(self):
        """重新載入目前的圖面"""
        if self._current_project_id:
            self.load_by_project(self._current_project_id)
        else:
            self._display_drawings(self._current_drawings)

    def get_selected_drawing_id(self):
        selection = self.tree.selection()
        if selection:
            return int(selection[0])
        return None
