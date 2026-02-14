import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
from db import queries
from core.thumbnail_manager import save_thumbnail_full, load_full_image
from core.file_manager import open_file
from config import IMAGE_FILETYPES, DEFAULT_OPERATOR
from ui.dialogs.revision_dialog import RevisionDialog
from ui.dialogs.drawing_dialog import DrawingDialog
from ui.dialogs.circulation_dialog import CirculationFlowPanel
from ui.widgets.zoomable_viewer import ZoomableImageViewer


class DetailPanel(ttk.Frame):
    """右側面板：圖面詳情 + 可縮放預覽 + 版次紀錄

    佈局（由上而下，可拖拉）：
      1. 圖面預覽（按鈕固定在上方）
      2. 發行流程（左右分割：左=流程+按鈕, 右=歷程紀錄）
      3. 基本資訊
      4. 操作按鈕列（固定底部）
      5. 版次紀錄 + 存取紀錄
    """

    def __init__(self, parent, on_refresh=None):
        super().__init__(parent)
        self.on_refresh = on_refresh
        self._current_drawing_id = None

        self._create_widgets()

    def _create_widgets(self):
        # 最外層使用垂直 PanedWindow，讓各區塊可拖拉
        self._vpaned = tk.PanedWindow(
            self, orient=tk.VERTICAL,
            sashrelief=tk.FLAT, sashwidth=4,
            bg='#D8D8D8', opaqueresize=True
        )
        self._vpaned.pack(fill=BOTH, expand=True)

        # ============================
        # 面板 1: 圖面預覽（按鈕固定在上方）
        # ============================
        preview_frame = ttk.LabelFrame(self._vpaned, text="圖面預覽")
        preview_inner = ttk.Frame(preview_frame, padding=5)
        preview_inner.pack(fill=BOTH, expand=True)

        # 縮圖按鈕固定在最上方
        thumb_btn_frame = ttk.Frame(preview_inner)
        thumb_btn_frame.pack(side=TOP, fill=X, pady=(0, 3))
        self.btn_thumb_upload = ttk.Button(thumb_btn_frame, text="上傳縮圖",
                                            command=self._upload_thumbnail,
                                            bootstyle=INFO+OUTLINE, width=10)
        self.btn_thumb_upload.pack(side=LEFT, padx=2)
        self.btn_thumb_from_file = ttk.Button(thumb_btn_frame, text="從圖檔讀取",
                                               command=self._read_from_drawing_file,
                                               bootstyle=SUCCESS+OUTLINE, width=10)
        self.btn_thumb_from_file.pack(side=LEFT, padx=2)

        # 圖片預覽（佔據剩餘空間）
        self.image_viewer = ZoomableImageViewer(preview_inner, height=220)
        self.image_viewer.pack(fill=BOTH, expand=True)

        self._vpaned.add(preview_frame, minsize=120, stretch='always')

        # ============================
        # 面板 2: 發行流程（移至預覽下方）
        # ============================
        self.circulation_panel = CirculationFlowPanel(self._vpaned)
        self._vpaned.add(self.circulation_panel, minsize=100, stretch='always')

        # ============================
        # 面板 3: 基本資訊（只有標籤，不含按鈕）
        # ============================
        info_outer = ttk.LabelFrame(self._vpaned, text="基本資訊")
        info_frame = ttk.Frame(info_outer, padding=8)
        info_frame.pack(fill=BOTH, expand=True)
        info_frame.columnconfigure(1, weight=1)

        labels = [
            ("圖號", "number"), ("標題", "title"), ("版次", "rev"),
            ("狀態", "status"), ("類型", "type"), ("建立者", "creator"),
            ("建立日期", "created"), ("更新日期", "updated"), ("檔案路徑", "filepath"),
        ]
        self._info_vars = {}
        for i, (text, key) in enumerate(labels):
            ttk.Label(info_frame, text=f"{text}：").grid(row=i, column=0, sticky=W, pady=1)
            var = ttk.StringVar()
            lbl = ttk.Label(info_frame, textvariable=var, wraplength=250)
            lbl.grid(row=i, column=1, sticky=W, pady=1)
            self._info_vars[key] = var

        self._vpaned.add(info_outer, minsize=80, stretch='never')

        # ============================
        # 操作按鈕列（固定高度，直接 pack 在主框架底部外側）
        # ============================
        self._vpaned.pack_forget()

        btn_bar = ttk.Frame(self, padding=(8, 4))
        btn_bar.pack(side=BOTTOM, fill=X)
        ttk.Separator(self, orient=HORIZONTAL).pack(side=BOTTOM, fill=X)

        self.btn_open = ttk.Button(btn_bar, text="開啟檔案", command=self._open_file,
                                   bootstyle=PRIMARY, width=10)
        self.btn_open.pack(side=LEFT, padx=3, pady=2)

        self.btn_rev = ttk.Button(btn_bar, text="新增版次", command=self._add_revision,
                                  bootstyle=SUCCESS, width=10)
        self.btn_rev.pack(side=LEFT, padx=3, pady=2)

        self.btn_edit = ttk.Button(btn_bar, text="編輯圖面", command=self._edit_drawing,
                                   bootstyle=WARNING, width=10)
        self.btn_edit.pack(side=LEFT, padx=3, pady=2)

        self.btn_delete = ttk.Button(btn_bar, text="刪除圖面", command=self._delete_drawing,
                                     bootstyle=DANGER, width=10)
        self.btn_delete.pack(side=LEFT, padx=3, pady=2)

        # 重新 pack vpaned（佔據按鈕列上方全部空間）
        self._vpaned.pack(fill=BOTH, expand=True)

        # ============================
        # 面板 4: 版次紀錄 + 存取紀錄（用內部 PanedWindow）
        # ============================
        records_frame = ttk.Frame(self._vpaned)
        records_pw = tk.PanedWindow(
            records_frame, orient=tk.VERTICAL,
            sashrelief=tk.FLAT, sashwidth=4,
            bg='#D8D8D8', opaqueresize=True
        )
        records_pw.pack(fill=BOTH, expand=True)

        # --- 版次紀錄 ---
        rev_outer = ttk.LabelFrame(records_pw, text="版次紀錄")
        rev_frame = ttk.Frame(rev_outer, padding=5)
        rev_frame.pack(fill=BOTH, expand=True)

        rev_cols = ('rev_code', 'rev_date', 'saved_by', 'notes')
        self.rev_tree = ttk.Treeview(rev_frame, columns=rev_cols, show='headings', height=4)
        self.rev_tree.heading('rev_code', text='版次')
        self.rev_tree.heading('rev_date', text='日期')
        self.rev_tree.heading('saved_by', text='儲存者')
        self.rev_tree.heading('notes', text='說明')
        self.rev_tree.column('rev_code', width=50, minwidth=40)
        self.rev_tree.column('rev_date', width=90, minwidth=70)
        self.rev_tree.column('saved_by', width=70, minwidth=50)
        self.rev_tree.column('notes', width=120, minwidth=80)
        rev_scroll = ttk.Scrollbar(rev_frame, orient=VERTICAL, command=self.rev_tree.yview)
        self.rev_tree.configure(yscrollcommand=rev_scroll.set)
        self.rev_tree.pack(side=LEFT, fill=BOTH, expand=True)
        rev_scroll.pack(side=RIGHT, fill=Y)

        records_pw.add(rev_outer, minsize=80, stretch='always')

        # --- 存取紀錄 ---
        access_outer = ttk.LabelFrame(records_pw, text="存取紀錄")
        access_frame = ttk.Frame(access_outer, padding=5)
        access_frame.pack(fill=BOTH, expand=True)

        access_cols = ('access_user', 'access_action', 'access_time')
        self.access_tree = ttk.Treeview(access_frame, columns=access_cols, show='headings', height=3)
        self.access_tree.heading('access_user', text='使用者')
        self.access_tree.heading('access_action', text='動作')
        self.access_tree.heading('access_time', text='時間')
        self.access_tree.column('access_user', width=80, minwidth=60)
        self.access_tree.column('access_action', width=70, minwidth=50)
        self.access_tree.column('access_time', width=130, minwidth=100)
        access_scroll = ttk.Scrollbar(access_frame, orient=VERTICAL, command=self.access_tree.yview)
        self.access_tree.configure(yscrollcommand=access_scroll.set)
        self.access_tree.pack(side=LEFT, fill=BOTH, expand=True)
        access_scroll.pack(side=RIGHT, fill=Y)

        records_pw.add(access_outer, minsize=70, stretch='always')

        self._vpaned.add(records_frame, minsize=120, stretch='always')

        # 初始時停用按鈕
        self._set_buttons_state(DISABLED)

    def load_drawing(self, drawing_id):
        """載入指定圖面的詳細資訊"""
        self._current_drawing_id = drawing_id
        drawing = queries.get_drawing(drawing_id)
        if not drawing:
            self.clear()
            return

        self._info_vars['number'].set(drawing['drawing_number'] or '')
        self._info_vars['title'].set(drawing['title'] or '')
        self._info_vars['rev'].set(drawing['current_rev'] or '')
        self._info_vars['status'].set(drawing['status'] or '')
        self._info_vars['type'].set(drawing['drawing_type'] or '')
        self._info_vars['creator'].set(drawing['created_by'] or '')
        self._info_vars['created'].set((drawing['created_at'] or '')[:16])
        self._info_vars['updated'].set((drawing['updated_at'] or '')[:16])
        self._info_vars['filepath'].set(drawing['file_path'] or '（未設定）')

        self._load_preview(drawing_id)
        self._load_revisions(drawing_id)

        queries.log_access(drawing_id, DEFAULT_OPERATOR, '檢視')
        self._load_access_logs(drawing_id)

        self.circulation_panel.load(drawing_id, drawing['current_rev'] or 'A')
        self._set_buttons_state(NORMAL)

    def clear(self):
        self._current_drawing_id = None
        for var in self._info_vars.values():
            var.set('')
        self.image_viewer.clear()
        self.rev_tree.delete(*self.rev_tree.get_children())
        self.access_tree.delete(*self.access_tree.get_children())
        self.circulation_panel.clear()
        self._set_buttons_state(DISABLED)

    def _load_preview(self, drawing_id):
        img = load_full_image(drawing_id)
        self.image_viewer.set_image(img)

    def _load_revisions(self, drawing_id):
        self.rev_tree.delete(*self.rev_tree.get_children())
        revisions = queries.get_revisions(drawing_id)
        for rev in revisions:
            self.rev_tree.insert('', 'end', values=(
                rev['rev_code'], rev['rev_date'],
                rev['saved_by'], rev['notes'] or '',
            ))

    def _load_access_logs(self, drawing_id):
        self.access_tree.delete(*self.access_tree.get_children())
        logs = queries.get_access_logs(drawing_id)
        for log in logs:
            self.access_tree.insert('', 'end', values=(
                log['user_name'], log['action'],
                (log['accessed_at'] or '')[:19],
            ))

    def _set_buttons_state(self, state):
        for btn in [self.btn_open, self.btn_rev, self.btn_edit, self.btn_delete,
                    self.btn_thumb_upload, self.btn_thumb_from_file]:
            btn.config(state=state)

    def _open_file(self):
        if not self._current_drawing_id:
            return
        drawing = queries.get_drawing(self._current_drawing_id)
        if drawing and drawing['file_path']:
            if open_file(drawing['file_path']):
                queries.log_access(self._current_drawing_id, DEFAULT_OPERATOR, '開啟檔案')
                self._load_access_logs(self._current_drawing_id)
            else:
                ttk.dialogs.Messagebox.show_warning(
                    f"找不到檔案：\n{drawing['file_path']}",
                    title="檔案不存在", parent=self.winfo_toplevel()
                )
        else:
            ttk.dialogs.Messagebox.show_info("尚未設定檔案路徑", title="提示", parent=self.winfo_toplevel())

    def _upload_thumbnail(self):
        if not self._current_drawing_id:
            return
        path = filedialog.askopenfilename(
            title="選擇縮圖來源檔案",
            filetypes=IMAGE_FILETYPES, parent=self.winfo_toplevel()
        )
        if path:
            self._save_and_refresh(path)

    def _read_from_drawing_file(self):
        if not self._current_drawing_id:
            return
        drawing = queries.get_drawing(self._current_drawing_id)
        if not drawing or not drawing['file_path']:
            ttk.dialogs.Messagebox.show_info("此圖面尚未設定檔案路徑", title="提示",
                                              parent=self.winfo_toplevel())
            return
        import os
        if not os.path.exists(drawing['file_path']):
            ttk.dialogs.Messagebox.show_warning(
                f"找不到檔案：\n{drawing['file_path']}",
                title="檔案不存在", parent=self.winfo_toplevel()
            )
            return
        self._save_and_refresh(drawing['file_path'])

    def _save_and_refresh(self, source_path):
        thumb_path = save_thumbnail_full(source_path, self._current_drawing_id)
        if thumb_path:
            queries.update_drawing_thumbnail(self._current_drawing_id, thumb_path)
            self._load_preview(self._current_drawing_id)
            ttk.dialogs.Messagebox.show_info("縮圖已更新", title="成功",
                                              parent=self.winfo_toplevel())
        else:
            ttk.dialogs.Messagebox.show_error(
                "無法從此檔案讀取預覽圖。\n請確認檔案格式是否正確。",
                title="讀取失敗", parent=self.winfo_toplevel()
            )

    def _add_revision(self):
        if not self._current_drawing_id:
            return
        drawing = queries.get_drawing(self._current_drawing_id)
        if not drawing:
            return
        dialog = RevisionDialog(
            self.winfo_toplevel(), self._current_drawing_id,
            drawing['current_rev'] or 'A'
        )
        if dialog.result:
            self.load_drawing(self._current_drawing_id)
            if self.on_refresh:
                self.on_refresh()

    def _edit_drawing(self):
        if not self._current_drawing_id:
            return
        dialog = DrawingDialog(self.winfo_toplevel(), drawing_id=self._current_drawing_id)
        if dialog.result:
            self.load_drawing(self._current_drawing_id)
            if self.on_refresh:
                self.on_refresh()

    def _delete_drawing(self):
        if not self._current_drawing_id:
            return
        drawing = queries.get_drawing(self._current_drawing_id)
        if not drawing:
            return
        confirm = ttk.dialogs.Messagebox.yesno(
            f"確定要刪除圖面「{drawing['drawing_number']} - {drawing['title']}」？\n\n"
            f"（會同時刪除備份目錄中的檔案，不會刪除電腦上的原始檔案）",
            title="確認刪除", parent=self.winfo_toplevel()
        )
        if confirm == "Yes":
            try:
                import os
                from config import THUMBNAIL_DIR
                from core.file_manager import delete_backup_files

                # 取得客戶/專案名稱（刪除備份用）
                project = queries.get_project(drawing['project_id'])
                client = queries.get_client(project['client_id']) if project else None

                # 刪除備份目錄中該圖面的所有檔案
                delete_backup_files(
                    client_name=client['name'] if client else '',
                    project_name=project['name'] if project else '',
                    drawing_number=drawing['drawing_number']
                )

                # 刪除本地縮圖檔案（這些是軟體自己建立的）
                for suffix in ['', '_full']:
                    thumb = os.path.join(THUMBNAIL_DIR, f"{self._current_drawing_id}{suffix}.png")
                    if os.path.exists(thumb):
                        os.remove(thumb)

                queries.delete_drawing(self._current_drawing_id)
                self.clear()
                if self.on_refresh:
                    self.on_refresh()
            except Exception as e:
                ttk.dialogs.Messagebox.show_error(
                    f"刪除失敗：{e}", title="錯誤", parent=self.winfo_toplevel()
                )
