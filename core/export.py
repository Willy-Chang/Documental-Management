import csv
import os
from db import queries


def export_drawings_to_csv(file_path, drawings=None):
    """匯出圖面清單為 CSV 檔案"""
    if drawings is None:
        drawings = queries.get_all_drawings()

    headers = ['客戶', '專案', '圖號', '標題', '版次', '狀態', '類型', '建立者', '建立日期', '更新日期', '檔案路徑']

    with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for d in drawings:
            writer.writerow([
                d['client_name'] if 'client_name' in d.keys() else '',
                d['project_name'] if 'project_name' in d.keys() else '',
                d['drawing_number'],
                d['title'],
                d['current_rev'],
                d['status'],
                d['drawing_type'] or '',
                d['created_by'] or '',
                d['created_at'] or '',
                d['updated_at'] or '',
                d['file_path'] or '',
            ])
    return True
