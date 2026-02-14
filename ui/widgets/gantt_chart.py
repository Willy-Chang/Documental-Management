"""生產進度甘特圖 Widget — 使用 matplotlib 嵌入 Tkinter"""
import tkinter as tk
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter, DayLocator, WeekdayLocator
import matplotlib.dates as mdates


class GanttChart(tk.Frame):
    """可嵌入 Tkinter 的甘特圖元件"""

    # 狀態對應色彩
    STATUS_COLORS = {
        '待開始': '#BDBDBD',
        '進行中': '#42A5F5',
        '已完成': '#66BB6A',
        '已取消': '#EF5350',
    }

    PRIORITY_COLORS = {
        '緊急': '#EF5350',
        '高': '#FFA726',
        '中': '#42A5F5',
        '低': '#66BB6A',
    }

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.figure = plt.Figure(figsize=(10, 5), dpi=96, facecolor='white')
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._tasks = []

    def update_chart(self, tasks):
        """更新甘特圖

        tasks: list of dict, 每個 dict 需包含：
            - label: str (顯示名稱)
            - start: str (YYYY-MM-DD)
            - end: str (YYYY-MM-DD)
            - progress: int (0-100)
            - status: str
            - group: str (分組名稱，如產品名稱)
        """
        self._tasks = tasks
        self.ax.clear()

        if not tasks:
            self.ax.text(0.5, 0.5, '尚無排程資料', ha='center', va='center',
                         fontsize=14, color='#888888', transform=self.ax.transAxes)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw()
            return

        labels = []
        starts = []
        durations = []
        colors = []
        progress_list = []

        for i, task in enumerate(reversed(tasks)):
            labels.append(task.get('label', f'任務 {i+1}'))
            try:
                start_dt = datetime.strptime(task['start'], '%Y-%m-%d')
                end_dt = datetime.strptime(task['end'], '%Y-%m-%d')
            except (ValueError, KeyError):
                start_dt = datetime.now()
                end_dt = start_dt + timedelta(days=1)

            starts.append(start_dt)
            dur = (end_dt - start_dt).days
            if dur < 1:
                dur = 1
            durations.append(dur)

            status = task.get('status', '待開始')
            colors.append(self.STATUS_COLORS.get(status, '#90A4AE'))
            progress_list.append(task.get('progress', 0))

        y_positions = range(len(labels))

        # 繪製背景條（灰色底）
        self.ax.barh(y_positions, durations, left=starts, height=0.6,
                     color='#E0E0E0', edgecolor='none', zorder=1)

        # 繪製進度條
        for i, (start, dur, prog, color) in enumerate(
                zip(starts, durations, progress_list, colors)):
            prog_dur = dur * prog / 100
            if prog_dur > 0:
                self.ax.barh(i, prog_dur, left=start, height=0.6,
                             color=color, edgecolor='none', zorder=2, alpha=0.85)

            # 在條上顯示百分比
            bar_center = start + timedelta(days=dur / 2)
            self.ax.text(bar_center, i, f'{prog}%',
                         ha='center', va='center', fontsize=8,
                         color='#333333', fontweight='bold', zorder=3)

        # 今日線
        today = datetime.now()
        self.ax.axvline(today, color='#E53935', linewidth=1.5,
                        linestyle='--', zorder=4, label='今日')

        # 設定 Y 軸
        self.ax.set_yticks(y_positions)
        self.ax.set_yticklabels(labels, fontsize=9)

        # 設定 X 軸（日期格式）
        self.ax.xaxis.set_major_formatter(DateFormatter('%m/%d'))
        if len(starts) > 0:
            all_dates = starts + [s + timedelta(days=d) for s, d in zip(starts, durations)]
            min_date = min(all_dates) - timedelta(days=2)
            max_date = max(all_dates) + timedelta(days=2)
            date_range = (max_date - min_date).days
            if date_range <= 30:
                self.ax.xaxis.set_major_locator(DayLocator(interval=2))
            elif date_range <= 90:
                self.ax.xaxis.set_major_locator(WeekdayLocator(byweekday=0))
            else:
                self.ax.xaxis.set_major_locator(mdates.MonthLocator())
            self.ax.set_xlim(min_date, max_date)

        self.ax.tick_params(axis='x', rotation=45, labelsize=8)
        self.ax.grid(axis='x', alpha=0.3, linestyle='--')
        self.ax.set_axisbelow(True)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        self.figure.tight_layout()
        self.canvas.draw()

    def clear_chart(self):
        self.ax.clear()
        self.canvas.draw()
