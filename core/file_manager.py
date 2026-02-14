import os
import shutil
from config import DRAWINGS_DIR, BACKUP_DIR


def open_file(file_path):
    """用系統預設程式開啟檔案"""
    if file_path and os.path.exists(file_path):
        os.startfile(file_path)
        return True
    return False


def copy_file_to_storage(src_path, drawing_id, rev_code=''):
    """複製檔案到管理目錄（選用功能）"""
    if not src_path or not os.path.exists(src_path):
        return None

    dest_dir = os.path.join(DRAWINGS_DIR, str(drawing_id))
    os.makedirs(dest_dir, exist_ok=True)

    ext = os.path.splitext(src_path)[1]
    if rev_code:
        dest_name = f"rev_{rev_code}{ext}"
    else:
        dest_name = os.path.basename(src_path)

    dest_path = os.path.join(dest_dir, dest_name)
    shutil.copy2(src_path, dest_path)
    return dest_path


def file_exists(file_path):
    """檢查檔案是否存在"""
    return file_path and os.path.exists(file_path)


def _clean_filename(name):
    """清理不合法目錄/檔名字元"""
    for ch in [':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, '_')
    return name.strip() or '_'


def get_backup_dir(client_name='', project_name=''):
    """取得備份目錄路徑（客戶/專案）"""
    folder_client = _clean_filename(client_name) if client_name else '未分類'
    folder_project = _clean_filename(project_name) if project_name else '未分類'
    return os.path.join(BACKUP_DIR, folder_client, folder_project)


def backup_file(src_path, client_name='', project_name='', drawing_number='', rev_code=''):
    """備份檔案到公司圖面目錄 (D:\\OneDrive\\公司圖面)

    目錄結構：客戶名/專案名/圖號_版次.副檔名
    不會刪除原始檔案。若備份失敗僅印出警告，不中斷主流程。
    """
    if not src_path or not os.path.exists(src_path):
        return None

    try:
        dest_dir = get_backup_dir(client_name, project_name)
        os.makedirs(dest_dir, exist_ok=True)

        ext = os.path.splitext(src_path)[1]
        if drawing_number and rev_code:
            dest_name = f"{_clean_filename(drawing_number)}_Rev{_clean_filename(rev_code)}{ext}"
        elif drawing_number:
            dest_name = f"{_clean_filename(drawing_number)}{ext}"
        else:
            dest_name = os.path.basename(src_path)

        dest_path = os.path.join(dest_dir, dest_name)
        shutil.copy2(src_path, dest_path)
        return dest_path
    except Exception as e:
        print(f"[備份失敗] {src_path} → {e}")
        return None


def delete_backup_files(client_name='', project_name='', drawing_number=''):
    """刪除指定圖面在備份目錄中的所有檔案（所有版次）

    搜尋 客戶/專案/ 下所有以 圖號 開頭的檔案並刪除。
    刪除後若資料夾為空則一併清理空資料夾。
    """
    if not drawing_number:
        return

    try:
        dest_dir = get_backup_dir(client_name, project_name)
        if not os.path.isdir(dest_dir):
            return

        prefix = _clean_filename(drawing_number)
        deleted = 0
        for fname in os.listdir(dest_dir):
            # 比對：圖號_RevX.ext 或 圖號.ext
            name_no_ext = os.path.splitext(fname)[0]
            if name_no_ext == prefix or name_no_ext.startswith(prefix + '_Rev'):
                fpath = os.path.join(dest_dir, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    deleted += 1

        # 清理空的專案資料夾
        if os.path.isdir(dest_dir) and not os.listdir(dest_dir):
            os.rmdir(dest_dir)
            # 清理空的客戶資料夾
            parent = os.path.dirname(dest_dir)
            if os.path.isdir(parent) and not os.listdir(parent):
                os.rmdir(parent)

        if deleted:
            print(f"[備份清理] 已刪除 {deleted} 個備份檔案")
    except Exception as e:
        print(f"[備份清理失敗] {e}")
