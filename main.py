import sys
import os

# 確保模組路徑正確
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter.font as tkfont
import ttkbootstrap as ttk
from db.database import init_db
from ui.main_window import MainWindow
from ui.styles import apply_styles
from config import get_icon_path, FONT_FAMILY


def main():
    # 初始化資料庫
    init_db()

    # 建立主視窗
    root = ttk.Window(
        title="工程圖管理系統",
        themename="cosmo",
        size=(1200, 700),
        minsize=(900, 500),
    )

    # 設定全域字體 (Noto Sans CJK TC)
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family=FONT_FAMILY, size=10)
    text_font = tkfont.nametofont("TkTextFont")
    text_font.configure(family=FONT_FAMILY, size=10)
    heading_font = tkfont.nametofont("TkHeadingFont")
    heading_font.configure(family=FONT_FAMILY, size=10)
    root.option_add("*Font", default_font)

    # 套用圓角、柔和色彩樣式
    apply_styles(root)

    # 設定視窗圖示（ICO 檔案）
    icon_path = get_icon_path()
    if icon_path:
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    app = MainWindow(root)
    root.mainloop()


if __name__ == '__main__':
    main()
