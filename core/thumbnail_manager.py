import os
import struct
import io
import shutil
import subprocess
import tempfile
from PIL import Image, ImageTk
from config import THUMBNAIL_DIR, THUMBNAIL_MAX_SIZE


# ===== 格式偵測與轉換 =====

def _get_file_ext(file_path):
    """取得小寫副檔名"""
    return os.path.splitext(file_path)[1].lower()


def _find_oda_converter():
    """尋找 ODA File Converter 執行檔路徑"""
    possible_paths = [
        r'C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe',
        r'C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe',
        r'C:\Program Files\ODA\ODAFileConverter 25.12\ODAFileConverter.exe',
    ]
    # 搜尋 Program Files 下所有 ODA 目錄
    for pf in [r'C:\Program Files', r'C:\Program Files (x86)']:
        oda_dir = os.path.join(pf, 'ODA')
        if os.path.isdir(oda_dir):
            for sub in os.listdir(oda_dir):
                exe = os.path.join(oda_dir, sub, 'ODAFileConverter.exe')
                if os.path.exists(exe):
                    possible_paths.append(exe)
    for p in possible_paths:
        if os.path.exists(p):
            return p
    # 嘗試 PATH
    if shutil.which('ODAFileConverter'):
        return 'ODAFileConverter'
    return None


def _dwg_to_dxf_via_oda(dwg_path):
    """用 ODA File Converter 將 DWG 轉為 DXF，回傳 DXF 暫存路徑"""
    oda = _find_oda_converter()
    if not oda:
        return None
    try:
        src_dir = os.path.dirname(os.path.abspath(dwg_path))
        dst_dir = tempfile.mkdtemp(prefix='dwg2dxf_')
        dwg_name = os.path.basename(dwg_path)
        # ODA 參數: 輸入目錄 輸出目錄 版本 格式 遞迴 audit 過濾
        # "ACAD2018" "DXF" "0" "1" "*.dwg"
        subprocess.run(
            [oda, src_dir, dst_dir, 'ACAD2018', 'DXF', '0', '1', dwg_name],
            timeout=30, capture_output=True
        )
        # 尋找輸出的 DXF
        base = os.path.splitext(dwg_name)[0]
        dxf_path = os.path.join(dst_dir, base + '.dxf')
        if os.path.exists(dxf_path):
            return dxf_path
        # 也可能是小寫
        for f in os.listdir(dst_dir):
            if f.lower().endswith('.dxf'):
                return os.path.join(dst_dir, f)
        return None
    except Exception as e:
        print(f"[ODA 轉檔失敗] {e}")
        return None


def _image_from_pdf(file_path):
    """從 PDF 提取第一頁為 PIL Image"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        if doc.page_count == 0:
            doc.close()
            return None
        page = doc[0]
        mat = fitz.Matrix(200 / 72, 200 / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except Exception as e:
        print(f"[PDF 讀取失敗] {e}")
        return None


def _image_from_dwg_thumbnail(file_path):
    """從 DWG 檔案的二進位標頭提取內嵌預覽圖（低解析度縮圖）

    DWG 檔案格式說明：
    - 偏移 0x00: 版本字串 (6 bytes)，如 "AC1021"
    - 偏移 0x0D: Image Seeker (4 bytes LE) — 影像區段的絕對偏移
    - 影像區段結構：
      - 16 bytes Sentinel
      - 4 bytes Overall Size
      - 1 byte  Num Images
      - 每個影像 entry: 1 byte code + 4 bytes start(絕對偏移) + 4 bytes size
      - code: 1=header, 2=BMP, 3=WMF, 6=PNG
    - BMP 資料不含 14 bytes 的 BMP File Header，需手動補上
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(6)
            if len(header) < 4 or header[:4] != b'AC10':
                return None

            f.seek(0x0D)
            img_seeker = struct.unpack('<I', f.read(4))[0]

            if img_seeker == 0:
                return None

            f.seek(img_seeker)
            sentinel = f.read(16)
            overall_size = struct.unpack('<I', f.read(4))[0]
            num_images = f.read(1)[0]
            if num_images == 0 or num_images > 10:
                return None

            image_entries = []
            for i in range(num_images):
                code = f.read(1)[0]
                start = struct.unpack('<I', f.read(4))[0]
                size = struct.unpack('<I', f.read(4))[0]
                image_entries.append((code, start, size))

            png_entry = None
            bmp_entry = None
            for code, start, size in image_entries:
                if code == 6 and size > 0:
                    png_entry = (start, size)
                elif code == 2 and size > 0:
                    bmp_entry = (start, size)

            if png_entry:
                f.seek(png_entry[0])
                png_data = f.read(png_entry[1])
                if png_data[:4] == b'\x89PNG':
                    return Image.open(io.BytesIO(png_data))

            if bmp_entry:
                f.seek(bmp_entry[0])
                bmp_data = f.read(bmp_entry[1])

                if len(bmp_data) < 40:
                    return None

                hdr_size = struct.unpack('<I', bmp_data[:4])[0]
                if hdr_size not in (40, 108, 124):
                    return None

                bpp = struct.unpack('<H', bmp_data[14:16])[0]
                palette_size = 0
                if bpp <= 8:
                    colors_used = struct.unpack('<I', bmp_data[32:36])[0] if len(bmp_data) >= 36 else 0
                    if colors_used == 0:
                        colors_used = 1 << bpp
                    palette_size = colors_used * 4

                pixel_offset = 14 + hdr_size + palette_size
                file_size = 14 + len(bmp_data)
                bmp_file_header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, pixel_offset)

                full_bmp = bmp_file_header + bmp_data
                return Image.open(io.BytesIO(full_bmp))

        return None
    except Exception as e:
        print(f"[DWG 預覽提取失敗] {e}")
        return None


def _image_from_dxf(file_path, dpi=200, silent=False):
    """從 DXF 檔案用 ezdxf + matplotlib 渲染真實圖面內容"""
    try:
        import ezdxf
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        entity_count = sum(1 for _ in msp)
        if entity_count == 0:
            return None

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

        fig = plt.figure(dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(msp)
        ax.set_aspect('equal')
        ax.autoscale()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=dpi)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)
    except Exception as e:
        if not silent:
            print(f"[DXF 渲染失敗] {e}")
        return None


def _image_from_dwg(file_path):
    """從 DWG 讀取圖面內容：
    1. 嘗試 ODA 轉 DXF → ezdxf 渲染（真實內容、高解析度）
    2. 回退到內嵌預覽圖（低解析度縮圖）
    3. 最後嘗試 PyMuPDF
    """
    # 方法 1: ODA → DXF → ezdxf 渲染（靜默模式，失敗不報錯）
    dxf_temp = _dwg_to_dxf_via_oda(file_path)
    if dxf_temp:
        try:
            img = _image_from_dxf(dxf_temp, dpi=200, silent=True)
            if img:
                return img
        finally:
            tmp_dir = os.path.dirname(dxf_temp)
            if tmp_dir and 'dwg2dxf_' in tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    # 方法 2: 內嵌預覽圖
    img = _image_from_dwg_thumbnail(file_path)
    if img:
        return img

    # 方法 3: PyMuPDF
    img = _image_from_cad_via_pymupdf(file_path)
    if img:
        return img

    print(f"[DWG 預覽失敗] 所有方法均無法讀取: {os.path.basename(file_path)}")
    return None


def _image_from_cad_via_pymupdf(file_path):
    """用 PyMuPDF 嘗試開啟 DWG/DXF（某些版本支援）"""
    try:
        import fitz
        doc = fitz.open(file_path)
        if doc.page_count == 0:
            doc.close()
            return None
        page = doc[0]
        mat = fitz.Matrix(200 / 72, 200 / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except Exception:
        return None


def _image_from_iges(file_path):
    """從 IGS/IGES 檔案渲染 3D 線框預覽圖（高品質版）

    IGES 格式解析：
    - 固定 80 字元欄寬格式
    - D 段（Directory Entry）描述實體類型
    - P 段（Parameter Data）描述實體座標
    - 支援實體類型：110=Line, 116=Point, 100=Circular Arc,
      126=B-Spline Curve, 128=B-Spline Surface 等
    """
    try:
        import math
        lines_3d = []
        points_3d = []

        with open(file_path, 'r', errors='ignore') as f:
            raw_lines = f.readlines()

        # 分段
        d_lines = []
        p_lines = []
        for line in raw_lines:
            if len(line) < 73:
                continue
            section = line[72]
            if section == 'D':
                d_lines.append(line)
            elif section == 'P':
                p_lines.append(line)

        # 解析 D 段
        d_entries = []
        for i in range(0, len(d_lines) - 1, 2):
            try:
                entity_type = int(d_lines[i][:8].strip())
                p_ptr = int(d_lines[i][8:16].strip())
                p_count = int(d_lines[i + 1][24:32].strip()) if len(d_lines[i + 1]) > 32 else 1
                d_entries.append((entity_type, p_ptr, p_count))
            except (ValueError, IndexError):
                continue

        # 建立 P 段索引
        p_dict = {}
        for line in p_lines:
            try:
                seq = int(line[73:80].strip())
                data = line[:64].strip()
                if seq in p_dict:
                    p_dict[seq] += data
                else:
                    p_dict[seq] = data
            except (ValueError, IndexError):
                continue

        def _get_params(ptr, cnt):
            raw = ''
            for offset in range(cnt):
                if (ptr + offset) in p_dict:
                    raw += p_dict[ptr + offset]
            return [p.strip() for p in raw.split(';')[0].split(',') if p.strip()]

        # 解析實體
        for entity_type, p_ptr, p_count in d_entries:
            parts = _get_params(p_ptr, p_count)

            if entity_type == 110 and len(parts) >= 7:
                # Line
                try:
                    x1, y1, z1 = float(parts[1]), float(parts[2]), float(parts[3])
                    x2, y2, z2 = float(parts[4]), float(parts[5]), float(parts[6])
                    lines_3d.append(((x1, y1, z1), (x2, y2, z2)))
                except (ValueError, IndexError):
                    pass

            elif entity_type == 100 and len(parts) >= 7:
                # Circular Arc: zt, cx, cy, x_start, y_start, x_end, y_end
                try:
                    zt = float(parts[1])
                    cx, cy = float(parts[2]), float(parts[3])
                    xs, ys = float(parts[4]), float(parts[5])
                    xe = float(parts[6])
                    ye = float(parts[7]) if len(parts) > 7 else ys

                    r = math.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
                    if r < 1e-10:
                        continue
                    a_s = math.atan2(ys - cy, xs - cx)
                    a_e = math.atan2(ye - cy, xe - cx)
                    if a_e <= a_s:
                        a_e += 2 * math.pi

                    n_seg = max(16, int(abs(a_e - a_s) / (math.pi / 24)))
                    prev = None
                    for si in range(n_seg + 1):
                        a = a_s + (a_e - a_s) * si / n_seg
                        pt = (cx + r * math.cos(a), cy + r * math.sin(a), zt)
                        if prev is not None:
                            lines_3d.append((prev, pt))
                        prev = pt
                except (ValueError, IndexError):
                    pass

            elif entity_type == 116 and len(parts) >= 4:
                # Point
                try:
                    points_3d.append((float(parts[1]), float(parts[2]), float(parts[3])))
                except (ValueError, IndexError):
                    pass

            elif entity_type == 126 and len(parts) > 10:
                # B-Spline Curve
                try:
                    K = int(parts[1])
                    M = int(parts[2])
                    N = K + 1
                    A = N + M + 1
                    cp_start = 1 + 4 + A + N
                    cp_pts = []
                    for j in range(N):
                        idx = cp_start + j * 3
                        if idx + 2 < len(parts):
                            cp_pts.append((float(parts[idx]), float(parts[idx + 1]), float(parts[idx + 2])))
                    for j in range(len(cp_pts) - 1):
                        lines_3d.append((cp_pts[j], cp_pts[j + 1]))
                except (ValueError, IndexError):
                    pass

            elif entity_type == 128 and len(parts) > 15:
                # B-Spline Surface — 提取邊緣 + 稀疏網格線
                try:
                    K1, K2 = int(parts[1]), int(parts[2])
                    M1, M2 = int(parts[3]), int(parts[4])
                    N1, N2 = K1 + 1, K2 + 1
                    A1, A2 = N1 + M1 + 1, N2 + M2 + 1
                    cp_start = 1 + 9 + A1 + A2 + N1 * N2
                    cp_grid = []
                    for j2 in range(N2):
                        row = []
                        for j1 in range(N1):
                            idx = cp_start + (j2 * N1 + j1) * 3
                            if idx + 2 < len(parts):
                                row.append((float(parts[idx]), float(parts[idx + 1]), float(parts[idx + 2])))
                        if row:
                            cp_grid.append(row)
                    if cp_grid:
                        # 邊緣線
                        for row in [cp_grid[0], cp_grid[-1]]:
                            for j in range(len(row) - 1):
                                lines_3d.append((row[j], row[j + 1]))
                        for j2 in range(len(cp_grid) - 1):
                            if cp_grid[j2] and cp_grid[j2 + 1]:
                                lines_3d.append((cp_grid[j2][0], cp_grid[j2 + 1][0]))
                                lines_3d.append((cp_grid[j2][-1], cp_grid[j2 + 1][-1]))
                        # 稀疏中間網格
                        step_r = max(1, len(cp_grid) // 5)
                        for ri in range(0, len(cp_grid), step_r):
                            for j in range(len(cp_grid[ri]) - 1):
                                lines_3d.append((cp_grid[ri][j], cp_grid[ri][j + 1]))
                        if cp_grid[0]:
                            step_c = max(1, len(cp_grid[0]) // 5)
                            for ci in range(0, len(cp_grid[0]), step_c):
                                for j2 in range(len(cp_grid) - 1):
                                    if ci < len(cp_grid[j2]) and ci < len(cp_grid[j2 + 1]):
                                        lines_3d.append((cp_grid[j2][ci], cp_grid[j2 + 1][ci]))
                except (ValueError, IndexError):
                    pass

        if not lines_3d and not points_3d:
            return None

        # === 高品質 matplotlib 渲染 ===
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Line3DCollection
        import numpy as np

        fig = plt.figure(figsize=(10, 8), dpi=180, facecolor='white')
        ax = fig.add_subplot(111, projection='3d', facecolor='#FAFAFA')

        if lines_3d:
            segments = [((x1, y1, z1), (x2, y2, z2)) for (x1, y1, z1), (x2, y2, z2) in lines_3d]
            lc = Line3DCollection(segments, colors='#2B5C8A', linewidths=0.6, alpha=0.85)
            ax.add_collection3d(lc)

            # 等比例軸範圍
            all_pts = []
            for (a, b), (c, d) in zip(segments, segments):
                all_pts.append(a)
                all_pts.append(c)
            pts_arr = np.array(all_pts)
            x_mn, x_mx = pts_arr[:, 0].min(), pts_arr[:, 0].max()
            y_mn, y_mx = pts_arr[:, 1].min(), pts_arr[:, 1].max()
            z_mn, z_mx = pts_arr[:, 2].min(), pts_arr[:, 2].max()
            max_range = max(x_mx - x_mn, y_mx - y_mn, z_mx - z_mn, 1e-6) * 0.55
            mx, my, mz = (x_mx + x_mn) / 2, (y_mx + y_mn) / 2, (z_mx + z_mn) / 2
            ax.set_xlim(mx - max_range, mx + max_range)
            ax.set_ylim(my - max_range, my + max_range)
            ax.set_zlim(mz - max_range, mz + max_range)

        if points_3d:
            xs, ys, zs = zip(*points_3d)
            ax.scatter(xs, ys, zs, c='#E07070', s=3, alpha=0.8, depthshade=True)

        ax.set_xlabel('X', fontsize=8, labelpad=2)
        ax.set_ylabel('Y', fontsize=8, labelpad=2)
        ax.set_zlabel('Z', fontsize=8, labelpad=2)
        ax.tick_params(axis='both', labelsize=6, pad=0)
        ax.view_init(elev=25, azim=135)

        # 清爽背景
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor('#DDDDDD')
        ax.yaxis.pane.set_edgecolor('#DDDDDD')
        ax.zaxis.pane.set_edgecolor('#DDDDDD')
        ax.grid(True, alpha=0.3, linestyle='--')

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.15, dpi=180)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)
    except Exception as e:
        print(f"[IGES 渲染失敗] {e}")
        return None


def _image_from_file(file_path):
    """根據副檔名自動選擇對應方式讀取圖片"""
    ext = _get_file_ext(file_path)

    if ext == '.pdf':
        return _image_from_pdf(file_path)
    elif ext == '.dwg':
        return _image_from_dwg(file_path)
    elif ext == '.dxf':
        img = _image_from_dxf(file_path)
        if img is None:
            img = _image_from_cad_via_pymupdf(file_path)
        return img
    elif ext in ('.igs', '.iges'):
        return _image_from_iges(file_path)
    else:
        # PIL 原生支援: PNG, JPG, JPEG, BMP, GIF, TIFF, TIF 等
        try:
            img = Image.open(file_path)
            img.load()
            return img.convert('RGB') if img.mode not in ('RGB', 'RGBA') else img
        except Exception as e:
            print(f"[圖片讀取失敗] {e}")
            return None


# ===== 主要 API =====

def save_thumbnail(image_path, drawing_id):
    """儲存縮圖：自動偵測格式，轉換並存為 PNG"""
    if not image_path or not os.path.exists(image_path):
        return None

    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    dest_path = os.path.join(THUMBNAIL_DIR, f"{drawing_id}.png")

    img = _image_from_file(image_path)
    if img is None:
        return None

    img = _ensure_rgb(img)
    img.save(dest_path, 'PNG')
    return dest_path


def save_thumbnail_full(image_path, drawing_id):
    """儲存完整解析度的預覽圖（供縮放用），同時也存縮圖"""
    if not image_path or not os.path.exists(image_path):
        return None

    os.makedirs(THUMBNAIL_DIR, exist_ok=True)

    img = _image_from_file(image_path)
    if img is None:
        return None

    img = _ensure_rgb(img)

    # 儲存完整解析度版本（供縮放瀏覽用）
    full_path = os.path.join(THUMBNAIL_DIR, f"{drawing_id}_full.png")
    img.save(full_path, 'PNG')

    # 也存一份縮圖版本
    thumb_path = os.path.join(THUMBNAIL_DIR, f"{drawing_id}.png")
    img_thumb = img.copy()
    img_thumb.thumbnail(THUMBNAIL_MAX_SIZE, Image.LANCZOS)
    img_thumb.save(thumb_path, 'PNG')

    return thumb_path


def load_thumbnail(thumbnail_path, max_size=None):
    """載入縮圖，回傳 PIL Image 物件"""
    if not thumbnail_path or not os.path.exists(thumbnail_path):
        return None
    img = Image.open(thumbnail_path)
    if max_size:
        img.thumbnail(max_size, Image.LANCZOS)
    return img


def load_thumbnail_tk(thumbnail_path, max_size=None):
    """載入縮圖，回傳 tkinter 可用的 PhotoImage"""
    img = load_thumbnail(thumbnail_path, max_size)
    if img is None:
        return None
    return ImageTk.PhotoImage(img)


def load_full_image(drawing_id):
    """載入完整解析度圖片，供縮放預覽器使用"""
    full_path = os.path.join(THUMBNAIL_DIR, f"{drawing_id}_full.png")
    if os.path.exists(full_path):
        return Image.open(full_path)
    thumb_path = os.path.join(THUMBNAIL_DIR, f"{drawing_id}.png")
    if os.path.exists(thumb_path):
        return Image.open(thumb_path)
    return None


def get_thumbnail_path(drawing_id):
    """取得縮圖檔案路徑"""
    path = os.path.join(THUMBNAIL_DIR, f"{drawing_id}.png")
    if os.path.exists(path):
        return path
    return None


def _ensure_rgb(img):
    """確保圖片是 RGB 模式"""
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        return background
    elif img.mode != 'RGB':
        return img.convert('RGB')
    return img
