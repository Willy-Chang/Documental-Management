"""
全域 UI 樣式設定 — 柔和配色、平面按鈕
在主視窗初始化後呼叫 apply_styles(root) 即可套用

重要：ttkbootstrap cosmo 主題使用全小寫 style name
  - 實心按鈕: primary.TButton, success.TButton ...
  - 外框按鈕: primary.Outline.TButton, success.Outline.TButton ...
"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


# ===== 柔和色系 =====
SOFT_COLORS = {
    'primary':   '#5B9BD5',   # 柔和藍
    'secondary': '#A6A6A6',   # 灰色
    'success':   '#6BBF7B',   # 柔和綠
    'info':      '#6CC3D5',   # 柔和青
    'warning':   '#E8B84B',   # 柔和琥珀
    'danger':    '#E07070',   # 柔和紅
}

SOFT_COLORS_ACTIVE = {
    'primary':   '#4A8AC4',
    'secondary': '#8C8C8C',
    'success':   '#5AAE6A',
    'info':      '#5BB2C4',
    'warning':   '#D7A73A',
    'danger':    '#CF5F5F',
}


def apply_styles(root):
    """套用全域柔和色彩樣式

    ttkbootstrap 的 style name 規則：
      bootstyle=PRIMARY  → style = 'primary.TButton'  (全小寫)
      bootstyle=SUCCESS+OUTLINE → style = 'success.Outline.TButton'
    """
    style = ttk.Style()

    # ===== 柔和按鈕：每種 bootstyle =====
    for name, color in SOFT_COLORS.items():
        active_color = SOFT_COLORS_ACTIVE[name]

        # --- 實心按鈕 (e.g. primary.TButton) ---
        btn_style = f'{name}.TButton'
        try:
            style.configure(btn_style,
                            background=color,
                            foreground='white',
                            bordercolor=color,
                            darkcolor=color,
                            lightcolor=color,
                            borderwidth=0,
                            focusthickness=0,
                            focuscolor=color,
                            padding=(14, 7),
                            relief='flat')
            style.map(btn_style,
                      background=[('pressed !disabled', active_color),
                                  ('hover !disabled', active_color),
                                  ('disabled', '#D0D0D0')],
                      foreground=[('disabled', '#888888')],
                      darkcolor=[('pressed !disabled', active_color),
                                 ('hover !disabled', active_color)],
                      lightcolor=[('pressed !disabled', active_color),
                                  ('hover !disabled', active_color)],
                      bordercolor=[('pressed !disabled', active_color),
                                   ('hover !disabled', active_color),
                                   ('disabled', '#D0D0D0')],
                      relief=[('pressed', 'flat'), ('hover', 'flat')])
        except Exception:
            pass

        # --- OUTLINE 按鈕 (e.g. primary.Outline.TButton) ---
        outline_style = f'{name}.Outline.TButton'
        try:
            style.configure(outline_style,
                            background='#FFFFFF',
                            foreground=color,
                            bordercolor=color,
                            darkcolor='#FFFFFF',
                            lightcolor='#FFFFFF',
                            borderwidth=1,
                            focusthickness=0,
                            focuscolor=color,
                            padding=(14, 7),
                            relief='flat')
            style.map(outline_style,
                      background=[('pressed !disabled', color),
                                  ('hover !disabled', color)],
                      foreground=[('pressed !disabled', 'white'),
                                  ('hover !disabled', 'white'),
                                  ('disabled', '#AAAAAA')],
                      darkcolor=[('pressed !disabled', color),
                                 ('hover !disabled', color)],
                      lightcolor=[('pressed !disabled', color),
                                  ('hover !disabled', color)],
                      bordercolor=[('disabled', '#CCCCCC')],
                      relief=[('pressed', 'flat'), ('hover', 'flat')])
        except Exception:
            pass

    # ===== 預設 TButton =====
    try:
        style.configure('TButton',
                        padding=(14, 7),
                        borderwidth=0,
                        focusthickness=0,
                        relief='flat')
        style.map('TButton',
                  relief=[('pressed', 'flat'), ('hover', 'flat')])
    except Exception:
        pass

    # ===== LabelFrame 柔和邊框 =====
    try:
        style.configure('TLabelframe',
                        borderwidth=1,
                        relief='groove')
        style.configure('TLabelframe.Label',
                        foreground='#555555')
    except Exception:
        pass

    # ===== Treeview =====
    try:
        style.configure("Treeview", rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading",
                        padding=(6, 4),
                        relief='flat',
                        borderwidth=0)
        style.map("Treeview.Heading",
                  relief=[('active', 'flat')])
    except Exception:
        pass

    # ===== Entry / Combobox =====
    try:
        style.configure("TEntry", padding=(8, 5), borderwidth=1)
        style.configure("TCombobox", padding=(8, 5), borderwidth=1)
    except Exception:
        pass

    # ===== Checkbutton =====
    try:
        style.configure("TCheckbutton", focusthickness=0)
    except Exception:
        pass

    # ===== Scrollbar 細化 =====
    try:
        style.configure("Vertical.TScrollbar", width=10)
        style.configure("Horizontal.TScrollbar", width=10)
    except Exception:
        pass
