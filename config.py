import os
import sys
import getpass

# 應用程式根目錄
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# 資料目錄
DATA_DIR = os.path.join(APP_DIR, 'data')
STORAGE_DIR = os.path.join(APP_DIR, 'storage')
THUMBNAIL_DIR = os.path.join(STORAGE_DIR, 'thumbnails')
DRAWINGS_DIR = os.path.join(STORAGE_DIR, 'drawings')

# 資料庫路徑
DB_PATH = os.path.join(DATA_DIR, 'dwg_manager.db')

# 縮圖最大尺寸
THUMBNAIL_MAX_SIZE = (400, 300)

# 預設操作人員（使用 Windows 登入名稱）
DEFAULT_OPERATOR = getpass.getuser()

# 圖面狀態選項
STATUS_OPTIONS = ['作業中', '發行中', '已回收', '已完成', '已廢止']

# 圖面類型選項
DRAWING_TYPE_OPTIONS = ['平面圖', '立面圖', '剖面圖', '細部圖', '配置圖', '配管圖', '電氣圖', '結構圖', '其他']

# 支援的圖片/文檔格式（縮圖上傳用）
IMAGE_FILETYPES = [
    ('所有支援格式', '*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.pdf *.dwg *.dxf *.igs *.iges'),
    ('圖片檔案', '*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff'),
    ('PDF 文件', '*.pdf'),
    ('AutoCAD 檔案', '*.dwg *.dxf'),
    ('IGES 檔案', '*.igs *.iges'),
    ('所有檔案', '*.*'),
]

# 支援的圖檔格式
CAD_FILETYPES = [
    ('所有工程圖檔', '*.dwg *.dxf *.igs *.iges'),
    ('AutoCAD 檔案', '*.dwg *.dxf'),
    ('DWG 檔案', '*.dwg'),
    ('DXF 檔案', '*.dxf'),
    ('IGES 檔案', '*.igs *.iges'),
    ('所有檔案', '*.*'),
]

# 公司名稱（顯示於工具列與關於對話框）
COMPANY_NAME = '劦佑機械股份有限公司'

# 全域字體設定（使用 Medium 字重，視覺更舒適）
FONT_FAMILY = 'Noto Sans TC Medium'

# 部門設定（預設部門清單，資料庫可動態新增）
DEPARTMENTS = ['管理部', '車工部', '銅極部', '刻字部']

# 發行單狀態
CIRCULATION_STATUS = ['發行中', '已回收', '已完成', '已取消']

# 發行任務狀態
TASK_STATUS = ['待處理', '已下載', '處理中', '已上傳', '已確認']

# 流程類型
FLOW_TYPES = {
    'A': '客戶圖面流程',
    'B': '劦佑圖面流程',
    'C': '修改發行流程',
}

# A流程步驟（線性推進）
FLOW_A_STEPS = ['車工部整理', '管理部寄客戶', '客戶確認', '已完成']

# B/C流程任務狀態
FLOW_BC_TASK_STATUS = ['待通知', '已收到']

# 備份目錄（所有上傳到軟體的檔案都會備份到此路徑）
BACKUP_DIR = r'D:\OneDrive\公司圖面'

# 資源目錄
ASSETS_DIR = os.path.join(APP_DIR, 'assets')


def get_icon_path():
    """自動尋找 assets/ 下的 ICO 圖示檔"""
    ico_path = os.path.join(ASSETS_DIR, 'icon.ico')
    if os.path.exists(ico_path):
        return ico_path
    if os.path.exists(ASSETS_DIR):
        for f in os.listdir(ASSETS_DIR):
            if f.lower().endswith('.ico'):
                return os.path.join(ASSETS_DIR, f)
    return None


# ==================== 行政管理系統設定 ====================

# 幣別選項
CURRENCY_OPTIONS = ['TWD', 'USD', 'EUR', 'JPY', 'CNY', 'GBP']

# 單位選項
UNIT_OPTIONS = ['PCS', 'SET', 'KG', 'G', 'M', 'CM', 'MM', 'L', 'LOT', '式']

# 付款條件選項
PAYMENT_TERMS_OPTIONS = [
    '月結30天',
    '月結60天',
    '月結90天',
    '貨到付款',
    'T/T 預付',
    'T/T 30天',
    'T/T 60天',
    'L/C 即期',
    'L/C 30天',
    'D/P 即期',
    '訂金50% / 出貨前50%',
    '其他',
]

# 交貨條件選項 (Incoterms)
DELIVERY_TERMS_OPTIONS = [
    'EXW 工廠交貨',
    'FOB 船上交貨',
    'CIF 到岸價',
    'CFR 運費在內價',
    'DAP 目的地交貨',
    'DDP 稅訖交貨',
    '自取',
    '含運送',
    '其他',
]

# 報價單狀態
QUOTATION_STATUS = ['草稿', '已報價', '已成交', '已失效', '已取消']

# 請購單狀態
PR_STATUS = ['草稿', '待審核', '已核准', '已採購', '已驗收', '已取消']

# 請購品項分類
PR_CATEGORIES = ['原物料', '零件', '工具', '耗材', '設備', '外包加工', '其他']

# 請購緊急程度
PR_URGENCY = ['一般', '急件', '特急']

# 客戶訂單狀態
ORDER_STATUS = ['新訂單', '生產中', '部分出貨', '已出貨', '已完成', '已取消']

# 發票狀態
INVOICE_STATUS = ['未付', '部分付款', '已付清', '逾期', '已作廢']

# 出口文件類型
EXPORT_DOC_TYPES = [
    '商業發票 (Commercial Invoice)',
    '裝箱單 (Packing List)',
    '提單 (Bill of Lading)',
    '產地證明 (Certificate of Origin)',
    '檢驗報告 (Inspection Report)',
    '保險單 (Insurance Policy)',
    '報關單 (Customs Declaration)',
    '其他',
]

# 出口文件狀態
EXPORT_DOC_STATUS = ['準備中', '已出具', '已寄出', '已歸檔']

# 運輸方式
SHIPPING_METHODS = ['海運', '空運', '快遞', '陸運', '自取']

# 生產訂單狀態
PRODUCTION_STATUS = ['待排程', '生產中', '暫停', '已完成', '已取消']

# 生產優先順序
PRODUCTION_PRIORITY = ['低', '中', '高', '緊急']

# 生產任務狀態
PRODUCTION_TASK_STATUS = ['待開始', '進行中', '已完成', '已取消']

# 機器狀態
MACHINE_STATUS = ['正常', '維修中', '待維修', '已報廢', '停用']

# 維修類型
MAINTENANCE_TYPES = ['定期保養', '故障維修', '預防維修', '緊急維修', '改善維修']

# 維修紀錄狀態
MAINTENANCE_STATUS = ['待處理', '處理中', '已完成', '已關閉']

# 自動編號前綴
DOC_NUMBER_PREFIX = {
    'quotation': 'QT',
    'purchase_requisition': 'PR',
    'customer_order': 'SO',
    'invoice': 'INV',
    'production_order': 'MO',
    'maintenance': 'MR',
}


# 確保必要目錄存在
for d in [DATA_DIR, STORAGE_DIR, THUMBNAIL_DIR, DRAWINGS_DIR, ASSETS_DIR]:
    os.makedirs(d, exist_ok=True)
# 備份目錄容錯（外部磁碟可能不存在）
try:
    os.makedirs(BACKUP_DIR, exist_ok=True)
except OSError:
    pass
