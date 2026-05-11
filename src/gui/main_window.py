"""
主窗口模块
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime

# 修改导入方式 - 使用绝对导入
try:
    from src.core.packet_capture import PacketCapture
    from src.core.statistics import TrafficStatistics
    from src.core.file_manager import FileManager
    from src.utils.resource_monitor import ResourceMonitor
    from src.utils.filters import PacketFilter
    
    from src.gui.packet_viewer import PacketViewer
    from src.gui.statistics_panel import StatisticsPanel
    from src.gui.charts import ChartsPanel
except ImportError:
    # 如果绝对导入失败，尝试相对导入
    from ..core.packet_capture import PacketCapture
    from ..core.statistics import TrafficStatistics
    from ..core.file_manager import FileManager
    from ..utils.resource_monitor import ResourceMonitor
    from ..utils.filters import PacketFilter
    
    from .packet_viewer import PacketViewer
    from .statistics_panel import StatisticsPanel
    from .charts import ChartsPanel

# 尝试导入matplotlib和numpy，如果失败则提供友好的错误信息
try:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    
    # 设置matplotlib支持中文显示
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    
    MATPLOTLIB_AVAILABLE = True
except ImportError as e:
    print(f"警告: matplotlib/numpy 未安装，图表功能将不可用: {e}")
    print("请运行: pip install matplotlib numpy")
    MATPLOTLIB_AVAILABLE = False
    # 创建虚拟类以避免导入错误
    class FigureCanvasTkAgg:
        def __init__(self, *args, **kwargs):
            pass
        def get_tk_widget(self):
            return tk.Frame()

class MainWindow:
    """主窗口类"""
    
    def __init__(self, root):
        self.root = root
        self.setup_window()
        
        # 初始化核心组件
        self.packet_capture = PacketCapture()
        self.statistics = TrafficStatistics()
        self.file_manager = FileManager()
        self.resource_monitor = ResourceMonitor()
        self.packet_filter = PacketFilter()
        
        # 子面板
        self.packet_viewer = None
        self.statistics_panel = None
        self.charts_panel = None
        
        # 状态变量
        self.is_capturing = False
        self.last_update_time = 0
        self.update_interval = 0.5  # 界面更新间隔(秒)
        
        # 实时监控相关变量
        self.realtime_metric_vars = {}
        
        # 设置相关变量
        self.buffer_size_var = None
        self.auto_save_var = None
        self.capture_mode_var = None
        self.refresh_interval_var = None
        self.theme_var = None
        self.font_size_var = None
        self.save_format_var = None
        self.auto_clean_var = None
        self.data_path_var = None
        self.performance_mode_var = None
        self.log_level_var = None
        self.check_update_var = None
        
        # 初始化字体设置
        self.current_font_size = 9
        self.font_family = "Arial"
        self.setup_fonts()
        
        self.setup_ui()
        self.load_config()
        self.load_settings()
        
        # 在UI设置完成后设置回调
        self.packet_capture.set_stats_callback(self.on_packet_received)
        self.resource_monitor.set_update_callback(self.on_resource_update)
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)
        
        # 存储窗口大小
        self.window_width = 1200
        self.window_height = 800
    
    def setup_fonts(self):
        """初始化字体设置"""
        # 创建不同大小的字体
        self.fonts = {}
        sizes = [8, 9, 10, 11, 12]
        for size in sizes:
            self.fonts[size] = {
                'default': ('Arial', size),
                'bold': ('Arial', size, 'bold'),
                'title': ('Arial', size + 2, 'bold')
            }
    
    def setup_window(self):
        """设置窗口属性"""
        self.root.title("网络流量分析器 v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 设置窗口可调整大小
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # 设置样式
        self.setup_styles()
    
    def on_window_resize(self, event):
        """处理窗口大小变化事件"""
        if event.widget == self.root:
            # 更新存储的窗口大小
            self.window_width = event.width
            self.window_height = event.height
            
            # 可以在这里添加其他响应窗口大小变化的逻辑
            # 例如调整字体大小、重新布局等
            
            # 更新状态栏信息
            self.status_label.config(text=f"窗口大小: {event.width}x{event.height}")
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义样式
        style.configure('Red.TButton', foreground='red')
        style.configure('Green.TButton', foreground='green')
        style.configure('Status.TLabel', padding=5, relief='sunken')
    
    def setup_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 顶部控制面板
        self.setup_control_panel(main_frame)
        
        # 创建笔记本(标签页)
        self.setup_notebook(main_frame)
        
        # 底部状态栏
        self.setup_status_bar(main_frame)
    
    def setup_control_panel(self, parent):
        """设置控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 配置控制面板的网格权重
        control_frame.columnconfigure(1, weight=1)  # 接口选择区域可扩展
        control_frame.columnconfigure(4, weight=1)  # 过滤器状态区域可扩展
        
        # 第一行：接口选择和基本控制
        ttk.Label(control_frame, text="网络接口:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.interface_var = tk.StringVar()
        interfaces = self.packet_capture.get_available_interfaces()
        self.interface_combo = ttk.Combobox(control_frame, textvariable=self.interface_var, 
                                          values=interfaces, width=20)
        if interfaces:
            self.interface_var.set(interfaces[0])
        self.interface_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="开始捕获", 
                                     command=self.start_capture, style='Green.TButton')
        self.start_button.grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="停止捕获", 
                                    command=self.stop_capture, style='Red.TButton',
                                    state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        # 过滤器按钮
        ttk.Button(control_frame, text="设置过滤器", 
                  command=self.show_filter_dialog).grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        
        self.filter_status = ttk.Label(control_frame, text="无过滤器", foreground="blue")
        self.filter_status.grid(row=0, column=5, sticky=tk.W, padx=(0, 10))
        
        # 第二行：统计信息和资源显示
        self.stats_label = ttk.Label(control_frame, text="就绪")
        self.stats_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        self.resource_label = ttk.Label(control_frame, text="CPU: --% 内存: --%")
        self.resource_label.grid(row=1, column=4, columnspan=2, sticky=tk.E, pady=(5, 0))
    
    def setup_notebook(self, parent):
        """设置标签页"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 实时监控标签页
        self.setup_realtime_tab()
        
        # 报文详情标签页
        self.setup_packets_tab()
        
        # 统计分析标签页
        self.setup_statistics_tab()
        
        # 图表分析标签页
        self.setup_charts_tab()
        
        # 设置标签页
        self.setup_settings_tab()
    
    def setup_realtime_tab(self):
        """设置实时监控标签页"""
        realtime_frame = ttk.Frame(self.notebook)
        self.notebook.add(realtime_frame, text="实时监控")
        
        if not MATPLOTLIB_AVAILABLE:
            # 如果matplotlib不可用，显示错误信息
            error_frame = ttk.Frame(realtime_frame)
            error_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            ttk.Label(error_frame, text="实时监控功能需要 matplotlib 和 numpy", 
                     font=('Arial', 12), foreground='red').pack(expand=True)
            ttk.Label(error_frame, text="请运行: pip install matplotlib numpy", 
                     font=('Arial', 10)).pack(expand=True)
            return
        
        # 配置实时监控框架的网格布局
        realtime_frame.columnconfigure(0, weight=1)
        realtime_frame.rowconfigure(1, weight=1)  # 图表区域可扩展
        
        # 上半部分：实时指标卡片
        metrics_frame = ttk.LabelFrame(realtime_frame, text="实时指标", padding=10)
        metrics_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=(10, 5))
        
        # 创建指标卡片
        self.setup_realtime_metrics(metrics_frame)
        
        # 下半部分：实时图表
        charts_frame = ttk.LabelFrame(realtime_frame, text="实时图表", padding=10)
        charts_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=10, pady=(5, 10))
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.rowconfigure(0, weight=1)
        
        # 创建实时图表
        self.setup_realtime_charts(charts_frame)
    
    def setup_realtime_metrics(self, parent):
        """设置实时指标显示"""
        metrics = [
            ("总报文数", "total_packets", "个"),
            ("报文速率", "packet_rate", "pkt/s"),
            ("IPv6占比", "ipv6_ratio", "%"),
            ("TCP报文", "tcp_packets", "个"),
            ("UDP报文", "udp_packets", "个"),
            ("ARP报文", "arp_packets", "个")
        ]
        
        self.realtime_metric_vars = {}
        
        # 配置父框架的网格权重
        for i in range(6):  # 6列
            parent.columnconfigure(i, weight=1, uniform="metrics")
        
        for i, (label, key, unit) in enumerate(metrics):
            # 创建指标卡片框架
            card_frame = ttk.Frame(parent, relief="solid", borderwidth=1)
            card_frame.grid(row=0, column=i, sticky=tk.NSEW, padx=5, pady=5)
            card_frame.columnconfigure(0, weight=1)
            
            # 指标标签
            ttk.Label(card_frame, text=label, font=('Arial', 10, 'bold'), 
                     foreground='darkblue').grid(row=0, column=0, sticky=tk.W, padx=5, pady=(5, 2))
            
            # 指标值
            var = tk.StringVar(value="0")
            value_label = ttk.Label(card_frame, textvariable=var, 
                                   font=('Arial', 14, 'bold'), foreground='blue')
            value_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
            
            # 单位
            ttk.Label(card_frame, text=unit, font=('Arial', 9)).grid(
                row=2, column=0, sticky=tk.W, padx=5, pady=(2, 5))
            
            self.realtime_metric_vars[key] = var
    
    def setup_realtime_charts(self, parent):
        """设置实时图表"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # 创建笔记本用于切换不同图表
        chart_notebook = ttk.Notebook(parent)
        chart_notebook.grid(row=0, column=0, sticky=tk.NSEW)
        
        # 配置父框架的网格权重
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        # 协议分布图
        protocol_frame = ttk.Frame(chart_notebook)
        chart_notebook.add(protocol_frame, text="协议分布")
        protocol_frame.columnconfigure(0, weight=1)
        protocol_frame.rowconfigure(0, weight=1)
        
        self.protocol_fig, self.protocol_ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.protocol_canvas = FigureCanvasTkAgg(self.protocol_fig, protocol_frame)
        self.protocol_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
        self.protocol_canvas.get_tk_widget().columnconfigure(0, weight=1)
        self.protocol_canvas.get_tk_widget().rowconfigure(0, weight=1)
        
        # 流量速率图
        rate_frame = ttk.Frame(chart_notebook)
        chart_notebook.add(rate_frame, text="流量速率")
        rate_frame.columnconfigure(0, weight=1)
        rate_frame.rowconfigure(0, weight=1)
        
        self.rate_fig, self.rate_ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.rate_canvas = FigureCanvasTkAgg(self.rate_fig, rate_frame)
        self.rate_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
        self.rate_canvas.get_tk_widget().columnconfigure(0, weight=1)
        self.rate_canvas.get_tk_widget().rowconfigure(0, weight=1)
        
        # IPv6趋势图
        ipv6_frame = ttk.Frame(chart_notebook)
        chart_notebook.add(ipv6_frame, text="IPv6趋势")
        ipv6_frame.columnconfigure(0, weight=1)
        ipv6_frame.rowconfigure(0, weight=1)
        
        self.ipv6_fig, self.ipv6_ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.ipv6_canvas = FigureCanvasTkAgg(self.ipv6_fig, ipv6_frame)
        self.ipv6_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
        self.ipv6_canvas.get_tk_widget().columnconfigure(0, weight=1)
        self.ipv6_canvas.get_tk_widget().rowconfigure(0, weight=1)
    
    def setup_packets_tab(self):
        """设置报文详情标签页"""
        packets_frame = ttk.Frame(self.notebook)
        self.notebook.add(packets_frame, text="报文详情")
        
        self.packet_viewer = PacketViewer(packets_frame)
        self.packet_viewer.pack(fill=tk.BOTH, expand=True)
    
    def setup_statistics_tab(self):
        """设置统计分析标签页"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="统计分析")
        
        self.statistics_panel = StatisticsPanel(stats_frame, self.statistics, self.file_manager)
        self.statistics_panel.pack(fill=tk.BOTH, expand=True)
    
    def setup_charts_tab(self):
        """设置图表分析标签页"""
        charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(charts_frame, text="图表分析")
        
        self.charts_panel = ChartsPanel(charts_frame, self.statistics)
        self.charts_panel.pack(fill=tk.BOTH, expand=True)
    
    def setup_settings_tab(self):
        """设置设置标签页"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="设置")
        
        # 配置设置框架的网格权重
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.rowconfigure(0, weight=1)
        
        # 创建主框架和滚动条
        main_frame = ttk.Frame(settings_frame)
        main_frame.grid(row=0, column=0, sticky=tk.NSEW)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 创建Canvas和Scrollbar以实现滚动
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        # 配置滚动区域的网格权重
        scrollable_frame.columnconfigure(0, weight=1)
        
        # 捕获设置
        capture_frame = ttk.LabelFrame(scrollable_frame, text="捕获设置", padding=10)
        capture_frame.grid(row=0, column=0, sticky=tk.EW, padx=10, pady=(10, 5))
        capture_frame.columnconfigure(1, weight=1)  # 输入框列可扩展
        
        self.setup_capture_settings(capture_frame)
        
        # 显示设置
        display_frame = ttk.LabelFrame(scrollable_frame, text="显示设置", padding=10)
        display_frame.grid(row=1, column=0, sticky=tk.EW, padx=10, pady=5)
        display_frame.columnconfigure(1, weight=1)  # 输入框列可扩展
        
        self.setup_display_settings(display_frame)
        
        # 存储设置
        storage_frame = ttk.LabelFrame(scrollable_frame, text="存储设置", padding=10)
        storage_frame.grid(row=2, column=0, sticky=tk.EW, padx=10, pady=5)
        storage_frame.columnconfigure(1, weight=1)  # 输入框列可扩展
        
        self.setup_storage_settings(storage_frame)
        
        # 高级设置
        advanced_frame = ttk.LabelFrame(scrollable_frame, text="高级设置", padding=10)
        advanced_frame.grid(row=3, column=0, sticky=tk.EW, padx=10, pady=5)
        advanced_frame.columnconfigure(1, weight=1)  # 输入框列可扩展
        
        self.setup_advanced_settings(advanced_frame)
        
        # 按钮框架
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=4, column=0, sticky=tk.EW, padx=10, pady=10)
        button_frame.columnconfigure(0, weight=1)  # 按钮区域可扩展
        
        ttk.Button(button_frame, text="保存设置", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="恢复默认", command=self.reset_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="应用设置", command=self.apply_settings).pack(side=tk.RIGHT, padx=5)
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # 更新滚动区域
        def update_scroll_region():
            canvas.configure(scrollregion=canvas.bbox("all"))
            self.root.after(100, update_scroll_region)
        
        self.root.after(100, update_scroll_region)
    
    def setup_capture_settings(self, parent):
        """设置捕获相关设置"""
        # 缓冲区大小
        ttk.Label(parent, text="缓冲区大小:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.buffer_size_var = tk.StringVar(value="1000")
        buffer_spinbox = ttk.Spinbox(parent, from_=100, to=10000, textvariable=self.buffer_size_var, width=10)
        buffer_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text="个报文").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 自动保存间隔
        ttk.Label(parent, text="自动保存间隔:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.auto_save_var = tk.StringVar(value="300")
        save_spinbox = ttk.Spinbox(parent, from_=60, to=3600, textvariable=self.auto_save_var, width=10)
        save_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text="秒").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 捕获模式
        ttk.Label(parent, text="捕获模式:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.capture_mode_var = tk.StringVar(value="promiscuous")
        mode_frame = ttk.Frame(parent)
        mode_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="混杂模式", variable=self.capture_mode_var, 
                       value="promiscuous").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="非混杂模式", variable=self.capture_mode_var, 
                       value="non_promiscuous").pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_display_settings(self, parent):
        """设置显示相关设置"""
        # 刷新间隔
        ttk.Label(parent, text="界面刷新间隔:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.refresh_interval_var = tk.StringVar(value="500")
        refresh_spinbox = ttk.Spinbox(parent, from_=100, to=5000, textvariable=self.refresh_interval_var, width=10)
        refresh_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text="毫秒").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 主题选择
        ttk.Label(parent, text="界面主题:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.theme_var = tk.StringVar(value="clam")
        theme_combo = ttk.Combobox(parent, textvariable=self.theme_var, 
                                  values=['clam', 'alt', 'default', 'classic'], width=15)
        theme_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 字体大小
        ttk.Label(parent, text="字体大小:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.font_size_var = tk.StringVar(value="9")
        font_combo = ttk.Combobox(parent, textvariable=self.font_size_var, 
                                 values=['8', '9', '10', '11', '12'], width=10)
        font_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 字体预览
        preview_frame = ttk.Frame(parent)
        preview_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=10)
        preview_frame.columnconfigure(0, weight=1)
        
        ttk.Label(preview_frame, text="字体预览:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.font_preview_label = ttk.Label(preview_frame, text="这是字体大小预览文本 ABCabc123")
        self.font_preview_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        # 绑定字体大小变化事件
        def on_font_size_change(*args):
            try:
                new_size = int(self.font_size_var.get())
                self.font_preview_label.config(font=('Arial', new_size))
            except ValueError:
                pass
        
        self.font_size_var.trace('w', on_font_size_change)
        
        # 初始预览
        on_font_size_change()
    
    def setup_storage_settings(self, parent):
        """设置存储相关设置"""
        # 默认保存格式
        ttk.Label(parent, text="默认保存格式:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.save_format_var = tk.StringVar(value="pcap")
        format_combo = ttk.Combobox(parent, textvariable=self.save_format_var, 
                                   values=['pcap', 'json', 'csv'], width=10)
        format_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 自动清理旧数据
        self.auto_clean_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="自动清理超过7天的数据", 
                       variable=self.auto_clean_var).grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # 数据保存路径
        ttk.Label(parent, text="数据保存路径:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.data_path_var = tk.StringVar(value="data")
        path_entry = ttk.Entry(parent, textvariable=self.data_path_var)
        path_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(parent, text="浏览", command=self.browse_data_path).grid(row=2, column=2, padx=5, pady=5)
    
    def setup_advanced_settings(self, parent):
        """设置高级设置"""
        # 性能优化
        ttk.Label(parent, text="性能模式:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.performance_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="启用高性能模式（可能增加CPU使用）", 
                       variable=self.performance_mode_var).grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 详细日志
        ttk.Label(parent, text="日志级别:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_combo = ttk.Combobox(parent, textvariable=self.log_level_var, 
                                values=['DEBUG', 'INFO', 'WARNING', 'ERROR'], width=10)
        log_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 启动时检查更新
        self.check_update_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="启动时检查更新", 
                       variable=self.check_update_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
    
    def setup_status_bar(self, parent):
        """设置状态栏"""
        status_frame = ttk.Frame(parent, relief='sunken', style='Status.TLabel')
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 运行时间显示
        self.uptime_label = ttk.Label(status_frame, text="运行时间: 00:00:00")
        self.uptime_label.pack(side=tk.RIGHT, padx=5)
    
    def start_capture(self):
        """开始捕获"""
        if self.is_capturing:
            return
        
        interface = self.interface_var.get()
        if not interface:
            messagebox.showerror("错误", "请选择网络接口")
            return
        
        self.packet_capture.set_interface(interface)
        
        # 应用过滤器
        filter_rules = self.packet_filter.get_bpf_filter()
        
        if self.packet_capture.start_capture(filter_rules):
            self.is_capturing = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="正在捕获网络流量...")
            
            # 启动资源监控
            self.resource_monitor.start_monitoring()
            
            # 重置统计
            self.statistics.reset_stats()
            
            # 启动实时监控更新
            if MATPLOTLIB_AVAILABLE:
                self.update_realtime_display()
            
            messagebox.showinfo("成功", "网络流量捕获已开始")
        else:
            messagebox.showerror("错误", "无法开始网络流量捕获")
    
    def stop_capture(self):
        """停止捕获"""
        if not self.is_capturing:
            return
        
        self.packet_capture.stop_capture()
        self.is_capturing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="捕获已停止")
        
        # 停止资源监控
        self.resource_monitor.stop_monitoring()
        
        messagebox.showinfo("成功", "网络流量捕获已停止")
    
    def on_packet_received(self, packet_info):
        """处理接收到的报文"""
        self.statistics.update_stats(packet_info)
        
        # 更新报文查看器
        if self.packet_viewer:
            self.packet_viewer.add_packet(packet_info)
        
        # 限制界面更新频率
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            self.update_display()
    
    def on_resource_update(self, resource_stats):
        """处理资源更新"""
        cpu_text = f"CPU: {resource_stats['cpu_percent']:.1f}%"
        mem_text = f"内存: {resource_stats['memory_usage']:.1f}%"
        self.resource_label.config(text=f"{cpu_text} {mem_text}")
        
        # 更新运行时间
        if hasattr(self, 'capture_start_time'):
            uptime = datetime.now() - self.capture_start_time
            hours, remainder = divmod(uptime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.config(text=f"运行时间: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    
    def update_display(self):
        """更新界面显示"""
        # 更新统计标签
        stats = self.statistics.get_real_time_metrics()
        stats_text = (f"报文: {stats['total_packets']} | "
                     f"速率: {stats['packet_rate']:.1f} pkt/s | "
                     f"IPv6: {stats['ipv6_ratio']:.1f}%")
        self.stats_label.config(text=stats_text)
        
        # 更新统计面板
        if self.statistics_panel:
            self.statistics_panel.update_display()
        
        # 更新图表面板
        if self.charts_panel:
            self.charts_panel.update_charts()
    
    def update_realtime_display(self):
        """更新实时监控显示"""
        if not self.is_capturing:
            return
        
        # 获取实时统计
        metrics = self.statistics.get_real_time_metrics()
        distribution = self.statistics.get_protocol_distribution()
        
        # 更新指标显示
        self.realtime_metric_vars['total_packets'].set(str(metrics['total_packets']))
        self.realtime_metric_vars['packet_rate'].set(f"{metrics['packet_rate']:.1f}")
        self.realtime_metric_vars['ipv6_ratio'].set(f"{metrics['ipv6_ratio']:.1f}")
        self.realtime_metric_vars['tcp_packets'].set(str(distribution.get('TCP', {}).get('count', 0)))
        self.realtime_metric_vars['udp_packets'].set(str(distribution.get('UDP', {}).get('count', 0)))
        self.realtime_metric_vars['arp_packets'].set(str(distribution.get('ARP', {}).get('count', 0)))
        
        # 更新实时图表
        if MATPLOTLIB_AVAILABLE:
            self.update_realtime_charts()
        
        # 定时继续更新
        if self.is_capturing:
            self.root.after(1000, self.update_realtime_display)  # 每秒更新一次
    
    def update_realtime_charts(self):
        """更新实时图表"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # 更新协议分布图
        distribution = self.statistics.get_protocol_distribution()
        if distribution:
            self.protocol_ax.clear()
            labels = list(distribution.keys())
            sizes = [data['count'] for data in distribution.values()]
            
            if sum(sizes) > 0:
                colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
                self.protocol_ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors)
                self.protocol_ax.set_title('实时协议分布')
                self.protocol_canvas.draw()
        
        # 更新流量速率图
        self.rate_ax.clear()
        timeline_data = list(self.statistics.timeline_data)
        if len(timeline_data) > 10:
            # 计算最近时间窗口内的速率
            window_seconds = 30  # 30秒窗口
            current_time = time.time()
            
            # 按时间分段计算速率
            time_segments = 15
            segment_duration = window_seconds / time_segments
            
            rates = []
            segment_labels = []
            
            for i in range(time_segments):
                segment_start = current_time - window_seconds + i * segment_duration
                segment_end = segment_start + segment_duration
                
                segment_packets = [
                    p for p in timeline_data 
                    if segment_start <= p['timestamp'] <= segment_end
                ]
                
                packet_rate = len(segment_packets) / segment_duration
                rates.append(packet_rate)
                segment_labels.append(f'{i+1}')
            
            self.rate_ax.plot(segment_labels, rates, 'g-', linewidth=2, marker='o', markersize=3)
            self.rate_ax.set_xlabel('时间段')
            self.rate_ax.set_ylabel('报文速率 (pkt/s)')
            self.rate_ax.set_title('实时流量速率')
            self.rate_ax.grid(True, alpha=0.3)
            self.rate_canvas.draw()
        
        # 更新IPv6趋势图
        self.ipv6_ax.clear()
        if len(timeline_data) > 10:
            # 计算IPv6占比趋势
            window_size = min(50, len(timeline_data) // 5)  # 动态窗口大小
            ipv6_ratios = []
            time_points = []
            
            for i in range(0, len(timeline_data), window_size):
                if i + window_size > len(timeline_data):
                    break
                    
                window = timeline_data[i:i+window_size]
                ipv6_count = sum(1 for p in window if 'v6' in p.get('protocol', '').lower() or p.get('protocol') == 'IPv6')
                total_count = len(window)
                ratio = (ipv6_count / total_count * 100) if total_count > 0 else 0
                
                ipv6_ratios.append(ratio)
                time_points.append(i)
            
            if ipv6_ratios:
                self.ipv6_ax.plot(time_points, ipv6_ratios, 'r-', linewidth=2, marker='s', markersize=2)
                self.ipv6_ax.set_xlabel('报文序列')
                self.ipv6_ax.set_ylabel('IPv6占比 (%)')
                self.ipv6_ax.set_title('IPv6流量趋势')
                self.ipv6_ax.grid(True, alpha=0.3)
                self.ipv6_ax.set_ylim(0, max(ipv6_ratios) * 1.1 if ipv6_ratios else 100)
        
        self.ipv6_canvas.draw()
    
    def show_filter_dialog(self):
        """显示过滤器设置对话框"""
        from .filter_dialog import FilterDialog
        FilterDialog(self.root, self.packet_filter, self.on_filters_updated)
    
    def on_filters_updated(self):
        """过滤器更新回调"""
        filter_desc = self.packet_filter.get_filter_description()
        self.filter_status.config(text=filter_desc)
        
        # 如果正在捕获，需要重启捕获以应用新过滤器
        if self.is_capturing:
            response = messagebox.askyesno("确认", 
                                         "过滤器已更改，需要重启捕获以应用新设置。是否立即重启？")
            if response:
                self.stop_capture()
                self.start_capture()
    
    def browse_data_path(self):
        """浏览选择数据保存路径"""
        path = filedialog.askdirectory(initialdir=self.data_path_var.get())
        if path:
            self.data_path_var.set(path)
    
    def save_settings(self):
        """保存设置到配置文件"""
        settings = {
            'capture': {
                'buffer_size': int(self.buffer_size_var.get()),
                'auto_save_interval': int(self.auto_save_var.get()),
                'capture_mode': self.capture_mode_var.get()
            },
            'display': {
                'refresh_interval': int(self.refresh_interval_var.get()),
                'theme': self.theme_var.get(),
                'font_size': int(self.font_size_var.get())
            },
            'storage': {
                'default_format': self.save_format_var.get(),
                'auto_clean': self.auto_clean_var.get(),
                'data_path': self.data_path_var.get()
            },
            'advanced': {
                'performance_mode': self.performance_mode_var.get(),
                'log_level': self.log_level_var.get(),
                'check_update': self.check_update_var.get()
            }
        }
        
        if self.file_manager.save_config(settings, 'app_settings.json'):
            messagebox.showinfo("成功", "设置已保存")
        else:
            messagebox.showerror("错误", "保存设置失败")
    
    def load_settings(self):
        """从配置文件加载设置"""
        settings = self.file_manager.load_config('app_settings.json')
        if not settings:
            return
        
        # 加载捕获设置
        capture_settings = settings.get('capture', {})
        self.buffer_size_var.set(str(capture_settings.get('buffer_size', 1000)))
        self.auto_save_var.set(str(capture_settings.get('auto_save_interval', 300)))
        self.capture_mode_var.set(capture_settings.get('capture_mode', 'promiscuous'))
        
        # 加载显示设置
        display_settings = settings.get('display', {})
        self.refresh_interval_var.set(str(display_settings.get('refresh_interval', 500)))
        self.theme_var.set(display_settings.get('theme', 'clam'))
        self.font_size_var.set(str(display_settings.get('font_size', 9)))
        
        # 加载存储设置
        storage_settings = settings.get('storage', {})
        self.save_format_var.set(storage_settings.get('default_format', 'pcap'))
        self.auto_clean_var.set(storage_settings.get('auto_clean', True))
        self.data_path_var.set(storage_settings.get('data_path', 'data'))
        
        # 加载高级设置
        advanced_settings = settings.get('advanced', {})
        self.performance_mode_var.set(advanced_settings.get('performance_mode', False))
        self.log_level_var.set(advanced_settings.get('log_level', 'INFO'))
        self.check_update_var.set(advanced_settings.get('check_update', True))
    
    def reset_settings(self):
        """恢复默认设置"""
        if messagebox.askyesno("确认", "确定要恢复默认设置吗？"):
            # 重置所有设置变量
            self.buffer_size_var.set("1000")
            self.auto_save_var.set("300")
            self.capture_mode_var.set("promiscuous")
            self.refresh_interval_var.set("500")
            self.theme_var.set("clam")
            self.font_size_var.set("9")
            self.save_format_var.set("pcap")
            self.auto_clean_var.set(True)
            self.data_path_var.set("data")
            self.performance_mode_var.set(False)
            self.log_level_var.set("INFO")
            self.check_update_var.set(True)
            
            messagebox.showinfo("成功", "已恢复默认设置")
    
    def apply_font_settings(self):
        """应用字体设置"""
        try:
            new_size = int(self.font_size_var.get())
            if new_size != self.current_font_size:
                self.current_font_size = new_size
                self.update_all_fonts()
        except ValueError:
            pass
    
    def update_all_fonts(self):
        """更新所有控件的字体"""
        # 更新样式
        style = ttk.Style()
        
        # 更新ttk控件的字体
        font_config = ('Arial', self.current_font_size)
        
        # 配置各种ttk控件的样式
        style.configure('.', font=font_config)
        style.configure('TLabel', font=font_config)
        style.configure('TButton', font=font_config)
        style.configure('TEntry', font=font_config)
        style.configure('TCombobox', font=font_config)
        style.configure('TCheckbutton', font=font_config)
        style.configure('TRadiobutton', font=font_config)
        style.configure('TFrame', font=font_config)
        style.configure('TLabelframe', font=font_config)
        style.configure('TLabelframe.Label', font=('Arial', self.current_font_size, 'bold'))
        
        # 更新树形视图的字体
        style.configure('Treeview', font=font_config)
        style.configure('Treeview.Heading', font=('Arial', self.current_font_size, 'bold'))
        
        # 更新文本控件的字体
        self.update_text_widgets_font()
    
    def update_text_widgets_font(self):
        """更新文本控件的字体"""
        # 更新报文查看器中的文本框字体
        if hasattr(self, 'packet_viewer') and self.packet_viewer:
            if hasattr(self.packet_viewer, 'detail_text'):
                self.packet_viewer.detail_text.config(
                    font=('Courier New', self.current_font_size)
                )
            if hasattr(self.packet_viewer, 'hex_text'):
                self.packet_viewer.hex_text.config(
                    font=('Courier New', self.current_font_size)
                )
        
        # 更新统计面板中的文本框字体
        if hasattr(self, 'statistics_panel') and self.statistics_panel:
            # 可以添加统计面板中文本框的字体更新
            pass
    
    def apply_settings(self):
        """应用当前设置"""
        try:
            # 应用主题设置
            style = ttk.Style()
            selected_theme = self.theme_var.get()
            available_themes = style.theme_names()
            if selected_theme in available_themes:
                style.theme_use(selected_theme)
            else:
                print(f"主题 '{selected_theme}' 不可用，使用默认主题")
                style.theme_use('clam')
            
            # 应用刷新间隔
            try:
                self.update_interval = int(self.refresh_interval_var.get()) / 1000.0
            except ValueError:
                self.update_interval = 0.5  # 默认值
            
            # 应用字体设置
            self.apply_font_settings()
            
            # 重新配置样式以确保主题更改生效
            self.update_all_fonts()
            
            # 强制刷新界面
            self.root.update_idletasks()
            
            messagebox.showinfo("成功", "设置已应用")
            
        except Exception as e:
            messagebox.showerror("错误", f"应用设置时出错: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        config = self.file_manager.load_config()
        if config:
            # 应用配置
            if 'last_interface' in config:
                self.interface_var.set(config['last_interface'])
    
    def save_config(self):
        """保存配置"""
        config = {
            'last_interface': self.interface_var.get(),
            'last_update': datetime.now().isoformat()
        }
        self.file_manager.save_config(config)
    
    def on_closing(self):
        """程序关闭处理"""
        if self.is_capturing:
            self.stop_capture()
        
        self.save_config()
        self.save_settings()
        self.root.destroy()