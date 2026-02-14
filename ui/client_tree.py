import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Menu
from db import queries
from ui.dialogs.client_dialog import ClientDialog
from ui.dialogs.project_dialog import ProjectDialog
from config import FONT_FAMILY


class ClientTree(ttk.Frame):
    """左側面板：客戶/專案樹狀圖"""

    def __init__(self, parent, on_project_selected=None, on_client_selected=None):
        super().__init__(parent)
        self.on_project_selected = on_project_selected
        self.on_client_selected = on_client_selected

        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        # 標題
        header = ttk.Frame(self)
        header.pack(fill=X, padx=5, pady=(5, 0))
        ttk.Label(header, text="客戶 / 專案", font=(FONT_FAMILY, 11, 'bold')).pack(side=LEFT)

        # 樹狀圖
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(tree_frame, show='tree', selectmode='browse')
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Button-3>', self._on_right_click)

        # 按鈕列
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=X, padx=5, pady=(0, 5))
        ttk.Button(btn_frame, text="+ 客戶", command=self._add_client, bootstyle=SUCCESS+OUTLINE, width=8).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="+ 專案", command=self._add_project, bootstyle=INFO+OUTLINE, width=8).pack(side=LEFT, padx=2)

        # 右鍵選單
        self.context_menu = Menu(self, tearoff=0)

    def refresh(self):
        """重新載入樹狀圖"""
        self.tree.delete(*self.tree.get_children())

        clients = queries.get_all_clients()
        for client in clients:
            client_node = self.tree.insert(
                '', 'end',
                iid=f"c_{client['id']}",
                text=f"📁 {client['name']}",
                open=False
            )
            projects = queries.get_projects_by_client(client['id'])
            for project in projects:
                self.tree.insert(
                    client_node, 'end',
                    iid=f"p_{project['id']}",
                    text=f"📋 {project['name']}"
                )

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        if item_id.startswith('p_'):
            project_id = int(item_id.split('_')[1])
            if self.on_project_selected:
                self.on_project_selected(project_id)
        elif item_id.startswith('c_'):
            client_id = int(item_id.split('_')[1])
            if self.on_client_selected:
                self.on_client_selected(client_id)

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)

        self.context_menu = Menu(self, tearoff=0)

        if item.startswith('c_'):
            client_id = int(item.split('_')[1])
            self.context_menu.add_command(label="編輯客戶", command=lambda: self._edit_client(client_id))
            self.context_menu.add_command(label="新增專案", command=lambda: self._add_project(client_id))
            self.context_menu.add_separator()
            self.context_menu.add_command(label="刪除客戶", command=lambda: self._delete_client(client_id))
        elif item.startswith('p_'):
            project_id = int(item.split('_')[1])
            self.context_menu.add_command(label="編輯專案", command=lambda: self._edit_project(project_id))
            self.context_menu.add_separator()
            self.context_menu.add_command(label="刪除專案", command=lambda: self._delete_project(project_id))

        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _add_client(self):
        dialog = ClientDialog(self.winfo_toplevel())
        if dialog.result:
            self.refresh()

    def _edit_client(self, client_id):
        dialog = ClientDialog(self.winfo_toplevel(), client_id=client_id)
        if dialog.result:
            self.refresh()

    def _delete_client(self, client_id):
        client = queries.get_client(client_id)
        if not client:
            return
        confirm = ttk.dialogs.Messagebox.yesno(
            f"確定要刪除客戶「{client['name']}」？\n（包含其下所有專案和圖面都會被刪除）",
            title="確認刪除",
            parent=self.winfo_toplevel()
        )
        if confirm == "Yes":
            queries.delete_client(client_id)
            self.refresh()

    def _add_project(self, client_id=None):
        if client_id is None:
            # 嘗試從選中的節點取得客戶 ID
            selection = self.tree.selection()
            if selection:
                item = selection[0]
                if item.startswith('c_'):
                    client_id = int(item.split('_')[1])
                elif item.startswith('p_'):
                    # 取得專案的父節點（客戶）
                    parent = self.tree.parent(item)
                    if parent:
                        client_id = int(parent.split('_')[1])

        dialog = ProjectDialog(self.winfo_toplevel(), client_id=client_id)
        if dialog.result:
            self.refresh()

    def _edit_project(self, project_id):
        dialog = ProjectDialog(self.winfo_toplevel(), project_id=project_id)
        if dialog.result:
            self.refresh()

    def _delete_project(self, project_id):
        project = queries.get_project(project_id)
        if not project:
            return
        confirm = ttk.dialogs.Messagebox.yesno(
            f"確定要刪除專案「{project['name']}」？\n（包含其下所有圖面都會被刪除）",
            title="確認刪除",
            parent=self.winfo_toplevel()
        )
        if confirm == "Yes":
            queries.delete_project(project_id)
            self.refresh()

    def get_selected_client_id(self):
        """取得目前選中的客戶 ID"""
        selection = self.tree.selection()
        if not selection:
            return None
        item = selection[0]
        if item.startswith('c_'):
            return int(item.split('_')[1])
        elif item.startswith('p_'):
            parent = self.tree.parent(item)
            if parent:
                return int(parent.split('_')[1])
        return None

    def get_selected_project_id(self):
        """取得目前選中的專案 ID"""
        selection = self.tree.selection()
        if not selection:
            return None
        item = selection[0]
        if item.startswith('p_'):
            return int(item.split('_')[1])
        return None
