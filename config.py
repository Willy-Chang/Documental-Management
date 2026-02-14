import os
import sys

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
import getpass
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

# 確保必要目錄存在
for d in [DATA_DIR, STORAGE_DIR, THUMBNAIL_DIR, DRAWINGS_DIR, ASSETS_DIR, BACKUP_DIR]:
    os.makedirs(d, exist_ok=True)
