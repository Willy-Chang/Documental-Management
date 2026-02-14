"""
Windows 檔案類型圖示擷取工具

使用 Windows Shell API (SHGetFileInfo) 擷取各副檔名對應的系統圖示，
轉換為 tkinter PhotoImage 供 Treeview 使用。
"""
import os
import sys
import ctypes
import ctypes.wintypes
from PIL import Image, ImageTk, ImageDraw

# Windows Shell API 常數
SHGFI_ICON = 0x000000100
SHGFI_SMALLICON = 0x000000001
SHGFI_LARGEICON = 0x000000000
SHGFI_USEFILEATTRIBUTES = 0x000000010
FILE_ATTRIBUTE_NORMAL = 0x00000080

# 使用 c_void_p 確保 64 位元相容
HICON = ctypes.c_void_p
HBITMAP = ctypes.c_void_p
HDC = ctypes.c_void_p
HWND = ctypes.c_void_p


class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", ctypes.c_ulong),
        ("szDisplayName", ctypes.c_wchar * 260),
        ("szTypeName", ctypes.c_wchar * 80),
    ]


class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", ctypes.c_int),
        ("xHotspot", ctypes.c_ulong),
        ("yHotspot", ctypes.c_ulong),
        ("hbmMask", HBITMAP),
        ("hbmColor", HBITMAP),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_ulong),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", ctypes.c_ushort),
        ("biBitCount", ctypes.c_ushort),
        ("biCompression", ctypes.c_ulong),
        ("biSizeImage", ctypes.c_ulong),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", ctypes.c_ulong),
        ("biClrImportant", ctypes.c_ulong),
    ]


# Windows API 函數設定（使用 argtypes/restype 確保正確的型別轉換）
_HAS_WIN_API = False
try:
    _shell32 = ctypes.windll.shell32
    _user32 = ctypes.windll.user32
    _gdi32 = ctypes.windll.gdi32

    # SHGetFileInfoW
    _SHGetFileInfoW = _shell32.SHGetFileInfoW
    _SHGetFileInfoW.argtypes = [
        ctypes.c_wchar_p,       # pszPath
        ctypes.c_ulong,         # dwFileAttributes
        ctypes.POINTER(SHFILEINFO),  # psfi
        ctypes.c_uint,          # cbFileInfo
        ctypes.c_uint,          # uFlags
    ]
    _SHGetFileInfoW.restype = ctypes.c_void_p  # DWORD_PTR

    # DestroyIcon
    _DestroyIcon = _user32.DestroyIcon
    _DestroyIcon.argtypes = [HICON]
    _DestroyIcon.restype = ctypes.c_int

    # GetIconInfo
    _GetIconInfo = _user32.GetIconInfo
    _GetIconInfo.argtypes = [HICON, ctypes.POINTER(ICONINFO)]
    _GetIconInfo.restype = ctypes.c_int

    # GetDC / ReleaseDC
    _GetDC = _user32.GetDC
    _GetDC.argtypes = [HWND]
    _GetDC.restype = HDC

    _ReleaseDC = _user32.ReleaseDC
    _ReleaseDC.argtypes = [HWND, HDC]
    _ReleaseDC.restype = ctypes.c_int

    # GetDIBits
    _GetDIBits = _gdi32.GetDIBits
    _GetDIBits.argtypes = [
        HDC,                             # hdc
        HBITMAP,                         # hbm
        ctypes.c_uint,                   # start
        ctypes.c_uint,                   # cLines
        ctypes.c_void_p,                 # lpvBits
        ctypes.POINTER(BITMAPINFOHEADER),  # lpbmi
        ctypes.c_uint,                   # usage
    ]
    _GetDIBits.restype = ctypes.c_int

    # DeleteObject
    _DeleteObject = _gdi32.DeleteObject
    _DeleteObject.argtypes = [ctypes.c_void_p]
    _DeleteObject.restype = ctypes.c_int

    _HAS_WIN_API = True
except (AttributeError, OSError):
    _HAS_WIN_API = False


def _extract_icon_image(extension, large=False):
    """
    使用 Windows Shell API 擷取指定副檔名的檔案類型圖示。
    回傳 PIL Image 物件，失敗時回傳 None。
    """
    if not _HAS_WIN_API:
        return None

    shinfo = SHFILEINFO()
    flags = SHGFI_ICON | SHGFI_USEFILEATTRIBUTES
    flags |= SHGFI_LARGEICON if large else SHGFI_SMALLICON

    # 使用虛擬檔名（不需要實際存在）
    fake_file = f"fakefile{extension}"

    result = _SHGetFileInfoW(
        fake_file,
        FILE_ATTRIBUTE_NORMAL,
        ctypes.byref(shinfo),
        ctypes.sizeof(shinfo),
        flags
    )

    if not result or not shinfo.hIcon:
        return None

    hicon = shinfo.hIcon
    try:
        return _icon_handle_to_image(hicon, large)
    finally:
        _DestroyIcon(hicon)


def _icon_handle_to_image(hicon, large=False):
    """
    將 Windows HICON 句柄轉換為 PIL Image。
    使用 GetIconInfo + GetDIBits 讀取像素資料。
    """
    icon_info = ICONINFO()
    if not _GetIconInfo(hicon, ctypes.byref(icon_info)):
        return None

    size = 32 if large else 16

    try:
        if not icon_info.hbmColor:
            return None

        # 有彩色 bitmap — 讀取像素資料
        hdc = _GetDC(None)
        if not hdc:
            return None

        try:
            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = size
            bmi.biHeight = -size  # 負值 = top-down
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = 0  # BI_RGB

            pixel_data = (ctypes.c_ubyte * (size * size * 4))()
            rows = _GetDIBits(
                hdc, icon_info.hbmColor, 0, size,
                ctypes.cast(pixel_data, ctypes.c_void_p),
                ctypes.byref(bmi), 0
            )

            if rows == 0:
                return None

            # BGRA → RGBA
            img = Image.frombytes('RGBA', (size, size), bytes(pixel_data), 'raw', 'BGRA')
            return img
        finally:
            _ReleaseDC(None, hdc)
    finally:
        if icon_info.hbmMask:
            _DeleteObject(icon_info.hbmMask)
        if icon_info.hbmColor:
            _DeleteObject(icon_info.hbmColor)


def _create_fallback_icon(extension, size=16):
    """
    當無法取得系統圖示時，產生一個簡單的彩色方塊作為 fallback。
    """
    # 依副檔名類型選顏色
    color_map = {
        '.dwg': '#2196F3',   # 藍色 CAD
        '.dxf': '#1976D2',   # 深藍色 CAD
        '.pdf': '#F44336',   # 紅色 PDF
        '.igs': '#4CAF50',   # 綠色 3D
        '.iges': '#4CAF50',  # 綠色 3D
        '.jpg': '#FF9800',   # 橙色 Image
        '.jpeg': '#FF9800',
        '.png': '#FF9800',
        '.tif': '#FF9800',
        '.tiff': '#FF9800',
        '.bmp': '#FF9800',
    }
    color = color_map.get(extension.lower(), '#9E9E9E')

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 畫圓角矩形
    draw.rounded_rectangle([1, 1, size - 2, size - 2], radius=2, fill=color)
    return img


class FileIconCache:
    """
    檔案類型圖示快取管理器。
    針對每個副檔名只擷取一次系統圖示，快取為 PhotoImage。
    """

    def __init__(self):
        self._cache = {}       # ext -> PhotoImage
        self._pil_cache = {}   # ext -> PIL Image

    def get_icon(self, extension, widget=None):
        """
        取得指定副檔名的 PhotoImage 圖示。

        Parameters:
            extension: 副檔名（如 '.pdf', '.dwg'）
            widget: tkinter widget（用於建立 PhotoImage 的 master）

        Returns:
            ImageTk.PhotoImage 物件
        """
        ext = extension.lower()
        if ext in self._cache:
            return self._cache[ext]

        # 先嘗試系統圖示
        pil_img = None
        try:
            pil_img = _extract_icon_image(ext, large=False)
        except Exception:
            pass

        # fallback: 彩色方塊
        if pil_img is None:
            pil_img = _create_fallback_icon(ext, size=16)

        # 確保是 16x16
        if pil_img.size != (16, 16):
            pil_img = pil_img.resize((16, 16), Image.LANCZOS)

        self._pil_cache[ext] = pil_img
        photo = ImageTk.PhotoImage(pil_img, master=widget)
        self._cache[ext] = photo
        return photo

    def clear(self):
        """清除快取"""
        self._cache.clear()
        self._pil_cache.clear()


# 全域快取實例
_global_cache = None


def get_file_icon_cache():
    """取得全域圖示快取實例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = FileIconCache()
    return _global_cache
