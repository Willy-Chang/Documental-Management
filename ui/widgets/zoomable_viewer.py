import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import tkinter as tk
from config import FONT_FAMILY


class ZoomableImageViewer(ttk.Frame):
    """可縮放、可拖曳的圖片預覽元件

    功能：
    - 滑鼠滾輪縮放（以游標為中心）
    - 滑鼠拖曳平移
    - 按鈕控制：放大、縮小、適合視窗、原始大小
    - 顯示縮放比例
    """

    ZOOM_MIN = 0.1    # 最小 10%
    ZOOM_MAX = 10.0   # 最大 1000%
    ZOOM_STEP = 1.2   # 每次滾輪縮放倍率

    def __init__(self, parent, height=280):
        super().__init__(parent)
        self._pil_image = None       # 原始 PIL Image（完整解析度）
        self._tk_image = None        # 目前顯示的 PhotoImage（保持參照）
        self._zoom = 1.0             # 目前縮放倍率
        self._pan_x = 0              # 平移 X 偏移
        self._pan_y = 0              # 平移 Y 偏移
        self._drag_start = None      # 拖曳起始座標
        self._canvas_height = height

        self._create_widgets()

    def _create_widgets(self):
        # === 控制列 ===
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(fill=X, padx=2, pady=(2, 0))

        ttk.Button(ctrl_frame, text="－", command=self._zoom_out,
                   bootstyle=SECONDARY+OUTLINE, width=3).pack(side=LEFT, padx=1)
        ttk.Button(ctrl_frame, text="＋", command=self._zoom_in,
                   bootstyle=SECONDARY+OUTLINE, width=3).pack(side=LEFT, padx=1)
        ttk.Button(ctrl_frame, text="適合", command=self._zoom_fit,
                   bootstyle=INFO+OUTLINE, width=4).pack(side=LEFT, padx=1)
        ttk.Button(ctrl_frame, text="1:1", command=self._zoom_100,
                   bootstyle=INFO+OUTLINE, width=3).pack(side=LEFT, padx=1)

        self._zoom_label = ttk.Label(ctrl_frame, text="100%", width=6, anchor=CENTER)
        self._zoom_label.pack(side=LEFT, padx=(5, 0))

        self._size_label = ttk.Label(ctrl_frame, text="", anchor=E)
        self._size_label.pack(side=RIGHT, padx=2)

        # === 畫布 ===
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=BOTH, expand=True, padx=2, pady=2)

        self._canvas = tk.Canvas(canvas_frame, bg='#e8e8e8',
                                 highlightthickness=1, highlightbackground='#cccccc',
                                 height=self._canvas_height)
        self._canvas.pack(fill=BOTH, expand=True)

        # 佔位文字（無圖片時顯示）
        self._placeholder_id = self._canvas.create_text(
            0, 0, text="尚未上傳縮圖", fill='#999999',
            font=(FONT_FAMILY, 11), anchor=CENTER
        )
        self._image_id = None

        # === 事件綁定 ===
        self._canvas.bind('<MouseWheel>', self._on_mousewheel)
        self._canvas.bind('<ButtonPress-1>', self._on_drag_start)
        self._canvas.bind('<B1-Motion>', self._on_drag_move)
        self._canvas.bind('<ButtonRelease-1>', self._on_drag_end)
        self._canvas.bind('<Configure>', self._on_canvas_resize)
        # Linux 滾輪
        self._canvas.bind('<Button-4>', lambda e: self._on_mousewheel_linux(e, 1))
        self._canvas.bind('<Button-5>', lambda e: self._on_mousewheel_linux(e, -1))

    # ===== 公開方法 =====

    def set_image(self, pil_image):
        """設定要顯示的 PIL Image（完整解析度）"""
        self._pil_image = pil_image
        if pil_image is None:
            self._clear_display()
            return

        w, h = pil_image.size
        self._size_label.config(text=f"{w}x{h}")
        self._zoom_fit()

    def clear(self):
        """清除圖片"""
        self._pil_image = None
        self._clear_display()

    # ===== 縮放操作 =====

    def _zoom_in(self):
        self._set_zoom(self._zoom * self.ZOOM_STEP)

    def _zoom_out(self):
        self._set_zoom(self._zoom / self.ZOOM_STEP)

    def _zoom_fit(self):
        """縮放至適合畫布大小"""
        if self._pil_image is None:
            return
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()
        if cw < 10 or ch < 10:
            # 畫布尚未顯示，延遲執行
            self.after(50, self._zoom_fit)
            return
        iw, ih = self._pil_image.size
        zoom_x = cw / iw
        zoom_y = ch / ih
        self._zoom = min(zoom_x, zoom_y) * 0.95  # 留一點邊距
        self._pan_x = 0
        self._pan_y = 0
        self._redraw()

    def _zoom_100(self):
        """縮放至 100%"""
        self._pan_x = 0
        self._pan_y = 0
        self._set_zoom(1.0)

    def _set_zoom(self, new_zoom, center_x=None, center_y=None):
        """設定縮放倍率，可指定縮放中心點"""
        new_zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, new_zoom))

        if center_x is not None and center_y is not None:
            # 以指定點為中心縮放
            ratio = new_zoom / self._zoom
            self._pan_x = center_x - ratio * (center_x - self._pan_x)
            self._pan_y = center_y - ratio * (center_y - self._pan_y)

        self._zoom = new_zoom
        self._redraw()

    # ===== 顯示更新 =====

    def _redraw(self):
        """重新繪製圖片"""
        if self._pil_image is None:
            return

        self._canvas.delete('image')
        self._canvas.itemconfigure(self._placeholder_id, state='hidden')

        iw, ih = self._pil_image.size
        new_w = max(1, int(iw * self._zoom))
        new_h = max(1, int(ih * self._zoom))

        # 限制記憶體使用：太大時先降取樣再放大
        if new_w > 4000 or new_h > 4000:
            scale = min(4000 / new_w, 4000 / new_h)
            new_w = int(new_w * scale)
            new_h = int(new_h * scale)

        resized = self._pil_image.resize((new_w, new_h), Image.LANCZOS)
        self._tk_image = ImageTk.PhotoImage(resized)

        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()

        # 計算繪製位置（置中 + 平移）
        x = cw / 2 + self._pan_x
        y = ch / 2 + self._pan_y

        self._image_id = self._canvas.create_image(x, y, image=self._tk_image,
                                                    anchor=CENTER, tags='image')

        # 更新縮放比例顯示
        self._zoom_label.config(text=f"{int(self._zoom * 100)}%")

    def _clear_display(self):
        """清除畫布顯示"""
        self._canvas.delete('image')
        self._tk_image = None
        self._image_id = None
        self._zoom = 1.0
        self._pan_x = 0
        self._pan_y = 0
        self._zoom_label.config(text="--")
        self._size_label.config(text="")
        self._canvas.itemconfigure(self._placeholder_id, state='normal')
        # 把佔位文字放到中心
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()
        self._canvas.coords(self._placeholder_id, cw / 2, ch / 2)

    # ===== 事件處理 =====

    def _on_mousewheel(self, event):
        """滑鼠滾輪縮放（以游標位置為中心）"""
        if self._pil_image is None:
            return

        # 計算游標相對於畫布中心的偏移
        cx = event.x - self._canvas.winfo_width() / 2
        cy = event.y - self._canvas.winfo_height() / 2

        if event.delta > 0:
            self._set_zoom(self._zoom * self.ZOOM_STEP, cx, cy)
        else:
            self._set_zoom(self._zoom / self.ZOOM_STEP, cx, cy)

        return 'break'  # 阻止事件冒泡到外層捲動

    def _on_mousewheel_linux(self, event, direction):
        """Linux 滑鼠滾輪"""
        cx = event.x - self._canvas.winfo_width() / 2
        cy = event.y - self._canvas.winfo_height() / 2
        if direction > 0:
            self._set_zoom(self._zoom * self.ZOOM_STEP, cx, cy)
        else:
            self._set_zoom(self._zoom / self.ZOOM_STEP, cx, cy)

    def _on_drag_start(self, event):
        """開始拖曳"""
        self._drag_start = (event.x, event.y)
        self._canvas.config(cursor='fleur')

    def _on_drag_move(self, event):
        """拖曳移動"""
        if self._drag_start is None or self._pil_image is None:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self._pan_x += dx
        self._pan_y += dy
        self._drag_start = (event.x, event.y)
        self._redraw()

    def _on_drag_end(self, event):
        """結束拖曳"""
        self._drag_start = None
        self._canvas.config(cursor='')

    def _on_canvas_resize(self, event):
        """畫布大小變更時更新佔位文字位置"""
        self._canvas.coords(self._placeholder_id, event.width / 2, event.height / 2)
        if self._pil_image is not None:
            self._redraw()
