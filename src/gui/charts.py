"""
图表分析面板模块
"""
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time 
import seaborn as sns
from datetime import datetime, timedelta

class ChartsPanel(ttk.Frame):
    """图表分析面板"""
    
    def __init__(self, parent, statistics):
        super().__init__(parent)
        self.statistics = statistics
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 配置主框架的网格权重
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # 笔记本区域可扩展
        
        # 控制按钮框架
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)
        control_frame.columnconfigure(0, weight=1)  # 按钮区域可扩展
        
        ttk.Button(control_frame, text="刷新图表", 
                  command=self.update_charts).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出图表", 
                  command=self.export_charts).pack(side=tk.LEFT, padx=5)
        
        # 时间范围选择
        time_frame = ttk.Frame(control_frame)
        time_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(time_frame, text="时间范围:").pack(side=tk.LEFT)
        self.time_range_var = tk.StringVar(value="1h")
        time_combo = ttk.Combobox(time_frame, textvariable=self.time_range_var,
                                 values=['15分钟', '1小时', '6小时', '24小时'], width=10)
        time_combo.pack(side=tk.LEFT, padx=5)
        time_combo.bind('<<ComboboxSelected>>', self.on_time_range_changed)
        
        # 创建笔记本(标签页)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)
        
        # 协议分布图
        self.setup_protocol_chart_tab()
        
        # 流量趋势图
        self.setup_traffic_trend_tab()
        
        # IP地址分布图
        self.setup_ip_distribution_tab()
        
        # 端口分布图
        self.setup_port_distribution_tab()
    
    def setup_protocol_chart_tab(self):
        """设置协议分布图表标签页"""
        protocol_frame = ttk.Frame(self.notebook)
        self.notebook.add(protocol_frame, text="协议分布")
        protocol_frame.columnconfigure(0, weight=1)
        protocol_frame.rowconfigure(0, weight=1)
        
        # 创建饼图和柱状图
        fig, (self.pie_ax, self.bar_ax) = plt.subplots(1, 2, figsize=(12, 5))
        self.protocol_canvas = FigureCanvasTkAgg(fig, protocol_frame)
        self.protocol_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
    
    def setup_traffic_trend_tab(self):
        """设置流量趋势图表标签页"""
        trend_frame = ttk.Frame(self.notebook)
        self.notebook.add(trend_frame, text="流量趋势")
        trend_frame.columnconfigure(0, weight=1)
        trend_frame.rowconfigure(0, weight=1)
        
        # 创建流量趋势图
        self.trend_fig, self.trend_ax = plt.subplots(figsize=(10, 6))
        self.trend_canvas = FigureCanvasTkAgg(self.trend_fig, trend_frame)
        self.trend_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
    
    def setup_ip_distribution_tab(self):
        """设置IP地址分布图表标签页"""
        ip_frame = ttk.Frame(self.notebook)
        self.notebook.add(ip_frame, text="IP分布")
        ip_frame.columnconfigure(0, weight=1)
        ip_frame.rowconfigure(0, weight=1)
        
        # 创建IP分布图
        self.ip_fig, self.ip_ax = plt.subplots(figsize=(10, 6))
        self.ip_canvas = FigureCanvasTkAgg(self.ip_fig, ip_frame)
        self.ip_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
    
    def setup_port_distribution_tab(self):
        """设置端口分布图表标签页"""
        port_frame = ttk.Frame(self.notebook)
        self.notebook.add(port_frame, text="端口分布")
        port_frame.columnconfigure(0, weight=1)
        port_frame.rowconfigure(0, weight=1)
        
        # 创建端口分布图
        self.port_fig, self.port_ax = plt.subplots(figsize=(10, 6))
        self.port_canvas = FigureCanvasTkAgg(self.port_fig, port_frame)
        self.port_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
    
    def update_charts(self):
        """更新所有图表"""
        self.update_protocol_charts()
        self.update_traffic_trend()
        self.update_ip_distribution()
        self.update_port_distribution()
    
    def update_protocol_charts(self):
        """更新协议分布图表"""
        # 清空图表
        self.pie_ax.clear()
        self.bar_ax.clear()
        
        distribution = self.statistics.get_protocol_distribution()
        
        if not distribution:
            self.pie_ax.text(0.5, 0.5, '无数据', ha='center', va='center', 
                           transform=self.pie_ax.transAxes, fontsize=14)
            self.bar_ax.text(0.5, 0.5, '无数据', ha='center', va='center', 
                           transform=self.bar_ax.transAxes, fontsize=14)
        else:
            # 饼图
            labels = list(distribution.keys())
            sizes = [data['count'] for data in distribution.values()]
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
            
            self.pie_ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors,
                          startangle=90)
            self.pie_ax.set_title('协议分布饼图')
            
            # 柱状图
            y_pos = np.arange(len(labels))
            self.bar_ax.barh(y_pos, sizes, color=colors)
            self.bar_ax.set_yticks(y_pos)
            self.bar_ax.set_yticklabels(labels)
            self.bar_ax.set_xlabel('报文数量')
            self.bar_ax.set_title('协议分布柱状图')
            
            # 在柱状图上显示数值
            for i, v in enumerate(sizes):
                self.bar_ax.text(v + max(sizes)*0.01, i, str(v), va='center')
        
        self.protocol_canvas.draw()
    
    def update_traffic_trend(self):
        """更新流量趋势图表"""
        self.trend_ax.clear()
        
        timeline_data = list(self.statistics.timeline_data)
        if len(timeline_data) < 2:
            self.trend_ax.text(0.5, 0.5, '数据不足', ha='center', va='center', 
                             transform=self.trend_ax.transAxes, fontsize=14)
        else:
            # 按时间窗口计算流量趋势
            window_size = 60  # 60秒窗口
            current_time = time.time() if hasattr(time, 'time') else datetime.now().timestamp()
            
            # 创建时间序列数据
            time_points = []
            packet_counts = []
            byte_rates = []
            ipv6_ratios = []
            
            # 按时间窗口分组
            for i in range(0, len(timeline_data), window_size):
                window = timeline_data[i:i+window_size]
                if not window:
                    continue
                    
                # 计算窗口统计
                packet_count = len(window)
                total_bytes = sum(p['packet_size'] for p in window)
                ipv6_count = sum(1 for p in window if 'v6' in p.get('protocol', '').lower())
                
                time_points.append(i)
                packet_counts.append(packet_count)
                byte_rates.append(total_bytes / window_size)  # 字节/秒
                ipv6_ratios.append((ipv6_count / packet_count * 100) if packet_count > 0 else 0)
            
            if time_points:
                # 绘制多条趋势线
                self.trend_ax.plot(time_points, packet_counts, 'b-', label='报文速率 (pkt/min)', linewidth=2)
                self.trend_ax.plot(time_points, byte_rates, 'r-', label='字节速率 (B/s)', linewidth=2)
                self.trend_ax.plot(time_points, ipv6_ratios, 'g-', label='IPv6占比 (%)', linewidth=2)
                
                self.trend_ax.set_xlabel('时间序列')
                self.trend_ax.set_ylabel('数值')
                self.trend_ax.set_title('流量趋势分析')
                self.trend_ax.legend()
                self.trend_ax.grid(True, alpha=0.3)
        
        self.trend_canvas.draw()
    
    def update_ip_distribution(self):
        """更新IP地址分布图表"""
        self.ip_ax.clear()
        
        top_ips = self.statistics.get_top_ips(15)
        
        if not top_ips:
            self.ip_ax.text(0.5, 0.5, '无数据', ha='center', va='center', 
                          transform=self.ip_ax.transAxes, fontsize=14)
        else:
            ips = list(top_ips.keys())
            counts = list(top_ips.values())
            
            # 创建水平柱状图
            y_pos = np.arange(len(ips))
            colors = plt.cm.viridis(np.linspace(0, 1, len(ips)))
            
            bars = self.ip_ax.barh(y_pos, counts, color=colors)
            self.ip_ax.set_yticks(y_pos)
            self.ip_ax.set_yticklabels(ips, fontsize=8)
            self.ip_ax.set_xlabel('报文数量')
            self.ip_ax.set_title('Top 15 IP地址流量分布')
            
            # 在柱子上显示数值
            for bar, count in zip(bars, counts):
                width = bar.get_width()
                self.ip_ax.text(width + max(counts)*0.01, bar.get_y() + bar.get_height()/2, 
                              str(count), ha='left', va='center', fontsize=8)
        
        self.ip_canvas.draw()
    
    def update_port_distribution(self):
        """更新端口分布图表"""
        self.port_ax.clear()
        
        top_ports = self.statistics.get_top_ports(15)
        
        if not top_ports:
            self.port_ax.text(0.5, 0.5, '无数据', ha='center', va='center', 
                            transform=self.port_ax.transAxes, fontsize=14)
        else:
            ports = []
            counts = []
            port_types = []
            
            for port_key, count in top_ports.items():
                if port_key.startswith('src_'):
                    port_num = port_key.replace('src_', '')
                    port_type = '源端口'
                else:
                    port_num = port_key.replace('dst_', '')
                    port_type = '目标端口'
                
                ports.append(f"{port_num}\n({port_type})")
                counts.append(count)
                port_types.append(port_type)
            
            # 创建柱状图，按端口类型着色
            colors = ['skyblue' if pt == '源端口' else 'lightcoral' for pt in port_types]
            y_pos = np.arange(len(ports))
            
            bars = self.port_ax.barh(y_pos, counts, color=colors)
            self.port_ax.set_yticks(y_pos)
            self.port_ax.set_yticklabels(ports, fontsize=8)
            self.port_ax.set_xlabel('报文数量')
            self.port_ax.set_title('Top 15 端口流量分布')
            
            # 添加图例
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='skyblue', label='源端口'),
                Patch(facecolor='lightcoral', label='目标端口')
            ]
            self.port_ax.legend(handles=legend_elements, loc='lower right')
            
            # 在柱子上显示数值
            for bar, count in zip(bars, counts):
                width = bar.get_width()
                self.port_ax.text(width + max(counts)*0.01, bar.get_y() + bar.get_height()/2, 
                                str(count), ha='left', va='center', fontsize=8)
        
        self.port_canvas.draw()
    
    def on_time_range_changed(self, event):
        """时间范围改变事件"""
        self.update_charts()
    
    def export_charts(self):
        """导出图表"""
        try:
            from tkinter import filedialog
            import os
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_charts_{timestamp}.png"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"), 
                    ("All files", "*.*")
                ],
                initialfile=filename
            )
            
            if filepath:
                # 保存当前活动的图表
                current_tab = self.notebook.index(self.notebook.select())
                
                if current_tab == 0:
                    self.protocol_canvas.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                elif current_tab == 1:
                    self.trend_canvas.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                elif current_tab == 2:
                    self.ip_canvas.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                elif current_tab == 3:
                    self.port_canvas.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                
                tk.messagebox.showinfo("成功", f"图表已导出到: {filepath}")
                
        except Exception as e:
            tk.messagebox.showerror("错误", f"导出图表失败: {e}")

# 如果matplotlib不可用，创建虚拟类
try:
    import matplotlib.pyplot as plt
except ImportError:
    class ChartsPanel(ttk.Frame):
        def __init__(self, parent, statistics):
            super().__init__(parent)
            ttk.Label(self, text="图表功能需要 matplotlib 库", 
                     font=('Arial', 12), foreground='red').pack(expand=True)
            ttk.Label(self, text="请运行: pip install matplotlib", 
                     font=('Arial', 10)).pack(expand=True)