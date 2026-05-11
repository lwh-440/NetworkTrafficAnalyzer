"""
自定义控件模块
"""
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns

class MetricCard(QWidget):
    """指标卡片控件"""
    
    def __init__(self, title, unit, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.value = "0"
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        layout.addWidget(title_label)
        
        # 数值
        self.value_label = QLabel(self.value)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        layout.addWidget(self.value_label)
        
        # 单位
        unit_label = QLabel(self.unit)
        unit_label.setAlignment(Qt.AlignCenter)
        unit_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(unit_label)
        
        # 设置卡片样式
        self.setStyleSheet("""
            MetricCard {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                min-width: 120px;
            }
        """)
        
    def set_value(self, value):
        """设置数值"""
        self.value = value
        self.value_label.setText(value)

class RealTimeChart(QWidget):
    """实时图表基类"""
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.data = []
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 图表 - 使用 matplotlib 替代 pyqtgraph
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
    def update_data(self, new_data):
        """更新数据 - 子类实现"""
        pass

class ProtocolDistributionWidget(RealTimeChart):
    """协议分布图表 - 使用 matplotlib 绘制"""
    
    def __init__(self, parent=None):
        super().__init__("协议分布", parent)
        self.threshold = 1.0  # 默认1%的阈值
        
    def update_data(self, distribution):
        """更新协议分布数据 - 使用 matplotlib 绘制饼图"""
        if not distribution:
            self.ax.clear()
            self.ax.text(0.5, 0.5, '无数据', ha='center', va='center', 
                        transform=self.ax.transAxes, fontsize=14)
            self.canvas.draw()
            return
            
        # 准备数据
        labels = list(distribution.keys())
        sizes = [data['count'] for data in distribution.values()]
        total = sum(sizes)
        
        if total == 0:
            self.ax.clear()
            self.ax.text(0.5, 0.5, '无数据', ha='center', va='center', 
                        transform=self.ax.transAxes, fontsize=14)
            self.canvas.draw()
            return
        
        # 处理小占比协议 - 合并为"其他"
        processed_labels, processed_sizes = self.process_small_slices(labels, sizes, total)
        
        # 清除之前的图形
        self.ax.clear()
        
        # 创建饼图
        colors = plt.cm.Set3(np.linspace(0, 1, len(processed_labels)))
        
        # 设置自动标签引导线
        wedges, texts, autotexts = self.ax.pie(
            processed_sizes, 
            labels=processed_labels, 
            autopct=lambda pct: self.custom_autopct(pct, processed_sizes),
            colors=colors, 
            startangle=90,
            pctdistance=0.85,  # 百分比文本距离圆心的距离
            labeldistance=1.05,  # 标签距离圆心的距离
            wedgeprops={'edgecolor': 'w', 'linewidth': 1},  # 设置扇形边框
            textprops={'fontsize': 9}  # 设置文本字体大小
        )
        
        # 设置引导线样式
        for text in texts:
            text.set_fontsize(9)
            # 为小扇区添加更明显的引导线
            if text.get_text() == '其他':
                text.set_fontweight('bold')
                text.set_color('darkred')
        
        # 美化百分比文本
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
            
        # 添加提示信息
        if len(processed_labels) < len(labels):
            self.ax.text(0.5, -0.1, 
                        f'占比小于{self.threshold}%的部分已合并为"其他"',
                        ha='center', va='center', 
                        transform=self.ax.transAxes,
                        fontsize=8, style='italic', color='gray')
            
        self.ax.set_title('协议分布', fontsize=12, fontweight='bold')
        self.ax.axis('equal')  # 确保饼图是圆的
        
        # 如果扇区较多，添加图例
        if len(processed_labels) > 5:
            self.ax.legend(wedges, processed_labels, 
                          title="协议类型",
                          loc="center left",
                          bbox_to_anchor=(1, 0, 0.5, 1),
                          fontsize=8)
        
        self.canvas.draw()
    
    def process_small_slices(self, labels, sizes, total):
        """处理小占比扇区，合并为'其他'"""
        if total == 0:
            return labels, sizes
            
        # 计算每个协议的百分比
        percentages = [(size / total) * 100 for size in sizes]
        
        # 找出占比小于阈值的协议
        small_slices_indices = [i for i, pct in enumerate(percentages) if pct < self.threshold]
        
        # 如果没有小占比协议，直接返回原数据
        if not small_slices_indices:
            return labels, sizes
        
        # 计算小占比协议的总和
        other_size = sum(sizes[i] for i in small_slices_indices)
        
        # 构建新的标签和大小列表
        new_labels = [labels[i] for i in range(len(labels)) if i not in small_slices_indices]
        new_sizes = [sizes[i] for i in range(len(sizes)) if i not in small_slices_indices]
        
        # 添加"其他"类别
        if other_size > 0:
            new_labels.append('其他')
            new_sizes.append(other_size)
        
        return new_labels, new_sizes
    
    def custom_autopct(self, pct, all_sizes):
        """自定义百分比显示格式，只显示大于阈值的百分比"""
        total = sum(all_sizes)
        actual_pct = (pct / 100) * total
        actual_pct_percentage = (actual_pct / total) * 100 if total > 0 else 0
        
        # 只显示大于阈值的百分比
        if actual_pct_percentage >= self.threshold:
            return f'{pct:.1f}%'
        else:
            return ''  # 不显示小扇区的百分比
    
    def set_threshold(self, threshold):
        """设置小扇区合并阈值"""
        self.threshold = max(0, min(threshold, 50))  # 限制在0-50%之间

class TrafficRateWidget(RealTimeChart):
    """流量速率图表 - 使用 matplotlib 绘制"""
    
    def __init__(self, parent=None):
        super().__init__("流量速率", parent)
        self.time_data = []
        self.rate_data = []
        self.max_points = 60  # 显示60个数据点
        self.start_time = None  # 添加起始时间记录
        
    def update_data(self, timeline_data):
        """更新流量速率数据"""
        if len(timeline_data) < 2:
            self.ax.clear()
            self.ax.text(0.5, 0.5, '数据不足', ha='center', va='center', 
                        transform=self.ax.transAxes, fontsize=14)
            self.ax.set_xlabel('时间')
            self.ax.set_ylabel('报文速率 (pkt/s)')
            self.ax.set_title('实时流量速率')
            self.canvas.draw()
            return
            
        # 设置起始时间
        if self.start_time is None:
            self.start_time = timeline_data[0]['timestamp'] if timeline_data else time.time()
        
        # 计算最近时间窗口内的速率
        current_time = timeline_data[-1]['timestamp'] if timeline_data else time.time()
        window_seconds = 30
        
        # 按时间窗口分组计算速率
        time_segments = 20
        segment_duration = window_seconds / time_segments
        
        rates = []
        segment_times = []
        for i in range(time_segments):
            segment_start = current_time - window_seconds + i * segment_duration
            segment_end = segment_start + segment_duration
            
            segment_packets = [
                p for p in timeline_data 
                if segment_start <= p['timestamp'] <= segment_end
            ]
            
            packet_rate = len(segment_packets) / segment_duration
            rates.append(packet_rate)
            # 计算相对于起始时间的秒数
            relative_time = segment_start - self.start_time
            segment_times.append(relative_time)
        
        # 更新数据
        self.rate_data = rates
        self.time_data = segment_times
        
        # 更新图表
        self.ax.clear()
        self.ax.plot(self.time_data, self.rate_data, 'g-', linewidth=2, marker='o', markersize=3)
        
        # 设置坐标轴标签
        self.ax.set_xlabel('时间 (秒)')
        self.ax.set_ylabel('报文速率 (pkt/s)')
        self.ax.set_title('实时流量速率')
        self.ax.grid(True, alpha=0.3)
        
        # 格式化X轴时间显示
        self.format_time_axis(self.ax, self.time_data)
        
        self.canvas.draw()
    
    def format_time_axis(self, ax, time_data):
        """格式化时间轴显示"""
        if not time_data:
            return
            
        def format_time_seconds(seconds):
            """将秒数格式化为 HH:MM:SS 或 秒"""
            if seconds < 60:
                return f"{seconds:.0f}秒"
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.0f}分"
            else:
                hours = seconds / 3600
                return f"{hours:.1f}小时"
        
        # 设置X轴刻度
        max_time = max(time_data) if time_data else 0
        if max_time > 0:
            # 根据总时间长度设置合适的刻度间隔
            if max_time <= 60:  # 1分钟以内
                tick_interval = 10  # 10秒
            elif max_time <= 3600:  # 1小时以内
                tick_interval = 60  # 1分钟
            elif max_time <= 86400:  # 1天以内
                tick_interval = 3600  # 1小时
            else:  # 超过1天
                tick_interval = 21600  # 6小时
            
            # 生成刻度位置和标签
            tick_positions = []
            tick_labels = []
            current_tick = 0
            while current_tick <= max_time:
                tick_positions.append(current_tick)
                tick_labels.append(format_time_seconds(current_tick))
                current_tick += tick_interval
            
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=45)

class SystemMonitorWidget(QWidget):
    """系统监控控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("系统监控")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # CPU使用率
        cpu_group = QGroupBox("CPU使用率")
        cpu_layout = QVBoxLayout(cpu_group)
        
        self.cpu_label = QLabel("0%")
        self.cpu_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        cpu_layout.addWidget(self.cpu_label)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        self.cpu_progress.setValue(0)
        cpu_layout.addWidget(self.cpu_progress)
        
        layout.addWidget(cpu_group)
        
        # 内存使用率
        memory_group = QGroupBox("内存使用率")
        memory_layout = QVBoxLayout(memory_group)
        
        self.memory_label = QLabel("0%")
        self.memory_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        memory_layout.addWidget(self.memory_label)
        
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(100)
        self.memory_progress.setValue(0)
        memory_layout.addWidget(self.memory_progress)
        
        layout.addWidget(memory_group)
        
        # 网络IO
        network_group = QGroupBox("网络IO")
        network_layout = QVBoxLayout(network_group)
        
        self.network_sent_label = QLabel("发送: 0 B/s")
        network_layout.addWidget(self.network_sent_label)
        
        self.network_recv_label = QLabel("接收: 0 B/s")
        network_layout.addWidget(self.network_recv_label)
        
        layout.addWidget(network_group)
        
        # 磁盘IO
        disk_group = QGroupBox("磁盘IO")
        disk_layout = QVBoxLayout(disk_group)
        
        self.disk_read_label = QLabel("读取: 0 B/s")
        disk_layout.addWidget(self.disk_read_label)
        
        self.disk_write_label = QLabel("写入: 0 B/s")
        disk_layout.addWidget(self.disk_write_label)
        
        layout.addWidget(disk_group)
        
    def update_data(self, resource_stats):
        """更新系统监控数据 - 线程安全"""
        try:
            # CPU
            cpu_percent = resource_stats.get('cpu_percent', 0)
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            self.cpu_progress.setValue(int(cpu_percent))
            
            # 设置进度条颜色
            if cpu_percent > 80:
                self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; }")
            elif cpu_percent > 60:
                self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #ffaa00; }")
            else:
                self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #44ff44; }")
            
            # 内存
            memory_usage = resource_stats.get('memory_usage', 0)
            self.memory_label.setText(f"{memory_usage:.1f}%")
            self.memory_progress.setValue(int(memory_usage))
            
            # 设置进度条颜色
            if memory_usage > 80:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; }")
            elif memory_usage > 60:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #ffaa00; }")
            else:
                self.memory_progress.setStyleSheet("QProgressBar::chunk { background-color: #44ff44; }")
            
            # 网络
            sent_rate = resource_stats.get('network_sent_bps', 0)
            recv_rate = resource_stats.get('network_recv_bps', 0)
            self.network_sent_label.setText(f"发送: {self.format_bytes(sent_rate)}/s")
            self.network_recv_label.setText(f"接收: {self.format_bytes(recv_rate)}/s")
            
            # 磁盘
            disk_read = resource_stats.get('disk_read_bps', 0)
            disk_write = resource_stats.get('disk_write_bps', 0)
            self.disk_read_label.setText(f"读取: {self.format_bytes(disk_read)}/s")
            self.disk_write_label.setText(f"写入: {self.format_bytes(disk_write)}/s")
            
        except Exception as e:
            print(f"更新系统监控数据错误: {e}")
        
    def format_bytes(self, size):
        """格式化字节大小"""
        if size == 0:
            return "0 B"
            
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs(size) < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def format_duration(self, seconds):
        """格式化时间间隔"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
    
    def get_current_stats(self):
        """获取当前统计信息"""
        return self.current_stats