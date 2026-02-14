"""儀表板模組 — 系統總覽"""
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from db import business_queries as bq
from config import COMPANY_NAME, FONT_FAMILY


class DashboardModule(ttk.Frame):
    """首頁儀表板"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._create_content()
        self.refresh()

    def _create_content(self):
        # 頂部標題
        header = ttk.Frame(self, padding=(15, 10))
        header.pack(fill=X)
        ttk.Label(header, text=f"{COMPANY_NAME}", font=(FONT_FAMILY, 18, 'bold'),
                  bootstyle=PRIMARY).pack(side=LEFT)
        ttk.Label(header, text="行政管理系統", font=(FONT_FAMILY, 14),
                  foreground='#666666').pack(side=LEFT, padx=(10, 0), pady=(4, 0))

        ttk.Button(header, text="重新整理", command=self.refresh,
                   bootstyle=INFO+OUTLINE, width=8).pack(side=RIGHT)

        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, padx=10)

        # 卡片容器
        self.card_container = ttk.Frame(self, padding=15)
        self.card_container.pack(fill=BOTH, expand=True)

    def refresh(self):
        # 清除舊內容
        for w in self.card_container.winfo_children():
            w.destroy()

        try:
            stats = bq.get_dashboard_stats()
        except Exception:
            stats = {}

        # 第一行卡片
        row1 = ttk.Frame(self.card_container)
        row1.pack(fill=X, pady=(0, 10))

        self._create_card(row1, "客戶", str(stats.get('client_count', 0)),
                          "家客戶", '#5B9BD5')
        self._create_card(row1, "待處理報價", str(stats.get('quotation_pending', 0)),
                          f"/ 共 {stats.get('quotation_count', 0)} 張", '#6CC3D5')
        self._create_card(row1, "進行中訂單", str(stats.get('order_active', 0)),
                          f"/ 共 {stats.get('order_count', 0)} 張", '#6BBF7B')
        self._create_card(row1, "待請購/審核", str(stats.get('pr_pending', 0)),
                          "張請購單", '#E8B84B')

        # 第二行卡片
        row2 = ttk.Frame(self.card_container)
        row2.pack(fill=X, pady=(0, 10))

        unpaid = stats.get('invoice_unpaid_amount', 0)
        self._create_card(row2, "未收款發票", str(stats.get('invoice_unpaid', 0)),
                          f"金額：${unpaid:,.0f}", '#E07070')
        self._create_card(row2, "生產中", str(stats.get('production_active', 0)),
                          "張生產單", '#FFA726')
        self._create_card(row2, "待處理維修", str(stats.get('maintenance_pending', 0)),
                          f"/ 共 {stats.get('machine_count', 0)} 台設備", '#9575CD')
        self._create_card(row2, "異常設備", str(stats.get('machine_down', 0)),
                          "台設備停機/待修", '#EF5350')

        # 系統資訊
        info_frame = ttk.LabelFrame(self.card_container, text="系統資訊")
        info_frame.pack(fill=X, pady=(15, 0))

        features = [
            ("報價單管理", "報價單建立、品項管理、PDF匯出、轉訂單"),
            ("請購單管理", "原物料/零件/工具請購、供應商管理、審核流程"),
            ("客戶訂單管理", "訂單建立、品項明細、出貨追蹤"),
            ("發票紀錄", "發票開立、品項管理、PDF匯出、付款追蹤"),
            ("出口文件紀錄", "商業發票、裝箱單、提單、產地證明等文件管理"),
            ("生產進度甘特圖", "生產排程、任務分配、進度追蹤、甘特圖視覺化"),
            ("機器維修彙報", "設備清單、維修紀錄、停機統計、保養排程"),
        ]

        for i, (name, desc) in enumerate(features):
            row = ttk.Frame(info_frame)
            row.pack(fill=X, pady=2)
            ttk.Label(row, text=f"  {name}", font=(FONT_FAMILY, 10, 'bold'),
                      width=18, anchor=W).pack(side=LEFT)
            ttk.Label(row, text=f"— {desc}", foreground='#666666').pack(side=LEFT)

    def _create_card(self, parent, title, value, subtitle, color):
        """建立統計卡片"""
        card = ttk.Frame(parent, padding=15)
        card.pack(side=LEFT, fill=BOTH, expand=True, padx=5)

        # 色彩指示條
        indicator = ttk.Frame(card, width=4)
        indicator.pack(side=LEFT, fill=Y, padx=(0, 10))
        # 使用 label 做色條
        ttk.Label(indicator, text=" ", background=color, width=1).pack(fill=BOTH, expand=True)

        content = ttk.Frame(card)
        content.pack(side=LEFT, fill=BOTH, expand=True)

        ttk.Label(content, text=title, font=(FONT_FAMILY, 9),
                  foreground='#888888').pack(anchor=W)
        ttk.Label(content, text=value, font=(FONT_FAMILY, 24, 'bold'),
                  foreground=color).pack(anchor=W)
        ttk.Label(content, text=subtitle, font=(FONT_FAMILY, 9),
                  foreground='#AAAAAA').pack(anchor=W)
