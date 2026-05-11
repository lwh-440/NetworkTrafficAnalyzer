"""
统计面板模块
"""
import tkinter as tk
import time
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import pandas as pd

class StatisticsPanel(ttk.Frame):
    """统计分析面板"""
    
    def __init__(self, parent, statistics, file_manager):
        super().__init__(parent)
        self.statistics = statistics
        self.file_manager = file_manager
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
        
        ttk.Button(control_frame, text="刷新统计", 
                  command=self.update_display).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出报告", 
                  command=self.export_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="保存数据", 
                  command=self.save_data).pack(side=tk.LEFT, padx=5)
        
        # 创建笔记本(标签页)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)
        
        # 协议分布标签页
        self.setup_protocol_tab()
        
        # IP统计标签页
        self.setup_ip_tab()
        
        # 端口统计标签页
        self.setup_port_tab()
        
        # 实时指标标签页
        self.setup_metrics_tab()
    
    def setup_protocol_tab(self):
        """设置协议分布标签页"""
        protocol_frame = ttk.Frame(self.notebook)
        self.notebook.add(protocol_frame, text="协议分布")
        
        # 配置协议框架的网格权重
        protocol_frame.columnconfigure(0, weight=1)
        protocol_frame.columnconfigure(1, weight=1)  # 图表区域可扩展
        protocol_frame.rowconfigure(0, weight=1)
        
        # 协议统计表格框架
        table_frame = ttk.LabelFrame(protocol_frame, text="协议统计", padding=5)
        table_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # 协议统计表格
        columns = ('协议', '数量', '百分比')
        self.protocol_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.protocol_tree.heading(col, text=col)
            self.protocol_tree.column(col, width=100, minwidth=80)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.protocol_tree.yview)
        self.protocol_tree.configure(yscrollcommand=scrollbar.set)
        
        self.protocol_tree.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        # 协议分布图框架
        chart_frame = ttk.LabelFrame(protocol_frame, text="协议分布图", padding=5)
        chart_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=5)
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)
        
        # 创建饼图
        self.setup_protocol_chart(chart_frame)
    
    def setup_protocol_chart(self, parent):
        """设置协议分布图"""
        self.protocol_fig, self.protocol_ax = plt.subplots(figsize=(6, 4))
        self.protocol_canvas = FigureCanvasTkAgg(self.protocol_fig, parent)
        self.protocol_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_ip_tab(self):
        """设置IP统计标签页"""
        ip_frame = ttk.Frame(self.notebook)
        self.notebook.add(ip_frame, text="IP统计")
        
        # 配置IP框架的网格权重
        ip_frame.columnconfigure(0, weight=1)
        ip_frame.rowconfigure(0, weight=1)
        
        # IP统计表格
        columns = ('IP地址', '报文数量', '占比')
        self.ip_tree = ttk.Treeview(ip_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.ip_tree.heading(col, text=col)
            self.ip_tree.column(col, width=150, minwidth=100)
        
        scrollbar = ttk.Scrollbar(ip_frame, orient=tk.VERTICAL, command=self.ip_tree.yview)
        self.ip_tree.configure(yscrollcommand=scrollbar.set)
        
        self.ip_tree.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
    
    def setup_port_tab(self):
        """设置端口统计标签页"""
        port_frame = ttk.Frame(self.notebook)
        self.notebook.add(port_frame, text="端口统计")
        
        # 配置端口框架的网格权重
        port_frame.columnconfigure(0, weight=1)
        port_frame.rowconfigure(0, weight=1)
        
        # 端口统计表格
        columns = ('端口', '类型', '报文数量', '占比')
        self.port_tree = ttk.Treeview(port_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.port_tree.heading(col, text=col)
            self.port_tree.column(col, width=100, minwidth=80)
        
        scrollbar = ttk.Scrollbar(port_frame, orient=tk.VERTICAL, command=self.port_tree.yview)
        self.port_tree.configure(yscrollcommand=scrollbar.set)
        
        self.port_tree.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
    
    def setup_metrics_tab(self):
        """设置实时指标标签页"""
        metrics_frame = ttk.Frame(self.notebook)
        self.notebook.add(metrics_frame, text="实时指标")
        
        # 配置指标框架的网格权重
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.rowconfigure(1, weight=1)  # 图表区域可扩展
        
        # 创建指标显示框架
        self.metrics_vars = {}
        
        metrics = [
            ('总报文数', 'total_packets'),
            ('报文速率', 'packet_rate'),
            ('IPv6占比', 'ipv6_ratio'),
            ('运行时间', 'duration'),
            ('唯一IP数', 'unique_ips'),
            ('唯一端口数', 'unique_ports')
        ]
        
        metrics_container = ttk.Frame(metrics_frame)
        metrics_container.grid(row=0, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=10)
        
        for i in range(6):  # 3列布局
            metrics_container.columnconfigure(i, weight=1, uniform="metrics")
        
        for i, (label, key) in enumerate(metrics):
            row = i // 3
            col = (i % 3) * 2
            
            # 创建指标卡片
            card_frame = ttk.Frame(metrics_container, relief="solid", borderwidth=1)
            card_frame.grid(row=row, column=col, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
            card_frame.columnconfigure(0, weight=1)
            
            ttk.Label(card_frame, text=label + ":", font=('Arial', 9)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=(5, 2))
            var = tk.StringVar(value="--")
            value_label = ttk.Label(card_frame, textvariable=var, font=('Arial', 12, 'bold'), foreground='blue')
            value_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
            
            self.metrics_vars[key] = var
        
        # 时间序列图表
        chart_frame = ttk.LabelFrame(metrics_frame, text="IPv6占比变化趋势", padding=10)
        chart_frame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, padx=10, pady=10)
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)
        
        self.metrics_fig, self.metrics_ax = plt.subplots(figsize=(8, 4))
        self.metrics_canvas = FigureCanvasTkAgg(self.metrics_fig, chart_frame)
        self.metrics_canvas.get_tk_widget().grid(row=0, column=0, sticky=tk.NSEW)
    
    def update_display(self):
        """更新显示"""
        self.update_protocol_stats()
        self.update_ip_stats()
        self.update_port_stats()
        self.update_metrics()
        self.update_charts()
    
    def update_protocol_stats(self):
        """更新协议统计"""
        # 清空表格
        for item in self.protocol_tree.get_children():
            self.protocol_tree.delete(item)
        
        distribution = self.statistics.get_protocol_distribution()
        total = self.statistics.protocol_stats.get('total', 1)
        
        for protocol, data in distribution.items():
            percentage = data['percentage']
            self.protocol_tree.insert('', tk.END, values=(
                protocol, data['count'], f"{percentage:.2f}%"
            ))
        
        # 更新饼图
        self.update_protocol_chart(distribution)
    
    def update_protocol_chart(self, distribution):
        """更新协议分布图"""
        self.protocol_ax.clear()
        
        if not distribution:
            self.protocol_ax.text(0.5, 0.5, '无数据', ha='center', va='center', transform=self.protocol_ax.transAxes)
            self.protocol_canvas.draw()
            return
        
        labels = list(distribution.keys())
        sizes = [data['count'] for data in distribution.values()]
        
        # 使用 seaborn 颜色方案
        colors = sns.color_palette("husl", len(labels))
        
        self.protocol_ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        self.protocol_ax.set_title('协议分布')
        
        self.protocol_canvas.draw()
    
    def update_ip_stats(self):
        """更新IP统计"""
        for item in self.ip_tree.get_children():
            self.ip_tree.delete(item)
        
        top_ips = self.statistics.get_top_ips(20)
        total = self.statistics.protocol_stats.get('total', 1)
        
        for ip, count in top_ips.items():
            percentage = (count / total) * 100
            self.ip_tree.insert('', tk.END, values=(
                ip, count, f"{percentage:.2f}%"
            ))
    
    def update_port_stats(self):
        """更新端口统计"""
        for item in self.port_tree.get_children():
            self.port_tree.delete(item)
        
        top_ports = self.statistics.get_top_ports(20)
        total = self.statistics.protocol_stats.get('total', 1)
        
        for port, count in top_ports.items():
            percentage = (count / total) * 100
            port_type = "源端口" if port.startswith('src_') else "目标端口"
            port_num = port.replace('src_', '').replace('dst_', '')
            
            self.port_tree.insert('', tk.END, values=(
                port_num, port_type, count, f"{percentage:.2f}%"
            ))
    
    def update_metrics(self):
        """更新实时指标"""
        metrics = self.statistics.get_real_time_metrics()
        
        for key, var in self.metrics_vars.items():
            value = metrics.get(key, 0)
            if key == 'packet_rate':
                var.set(f"{value:.1f} pkt/s")
            elif key == 'ipv6_ratio':
                var.set(f"{value:.2f}%")
            elif key == 'duration':
                # 格式化时间为 HH:MM:SS
                hours = int(value // 3600)
                minutes = int((value % 3600) // 60)
                seconds = int(value % 60)
                var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            else:
                var.set(str(int(value)))
    
    def update_charts(self):
        """更新图表"""
        # 这里可以添加时间序列图表的更新逻辑
        pass
    
    def export_report(self):
        """导出统计报告"""
        filename = self.file_manager.save_statistics_report(self.statistics)
        if filename:
            tk.messagebox.showinfo("成功", f"统计报告已导出到: {filename}")
        else:
            tk.messagebox.showerror("错误", "导出统计报告失败")
    
    def save_data(self):
        """保存数据"""
        # 提供多种保存选项
        save_options = {
            "Excel文件 (.xlsx)": "excel",
            "JSON报告 (.json)": "json", 
            "CSV数据 (.csv)": "csv",
            "所有格式": "all"
        }
        
        # 创建选择对话框
        choice_window = tk.Toplevel(self)
        choice_window.title("保存数据")
        choice_window.geometry("300x200")
        choice_window.transient(self)
        choice_window.grab_set()
        
        ttk.Label(choice_window, text="选择保存格式:", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        selected_format = tk.StringVar(value="excel")
        
        for text, value in save_options.items():
            ttk.Radiobutton(choice_window, text=text, variable=selected_format, 
                           value=value).pack(anchor=tk.W, padx=20, pady=2)
        
        def do_save():
            format_choice = selected_format.get()
            choice_window.destroy()
            
            if format_choice == "excel":
                self.export_to_excel()
            elif format_choice == "json":
                self.export_to_json()
            elif format_choice == "csv":
                self.export_to_csv()
            elif format_choice == "all":
                self.export_all_formats()
        
        ttk.Button(choice_window, text="保存", command=do_save).pack(pady=10)
        ttk.Button(choice_window, text="取消", command=choice_window.destroy).pack(pady=5)
    
    def export_to_excel(self):
        """导出到Excel文件"""
        filename = self.file_manager.export_to_excel(self.statistics)
        if filename:
            tk.messagebox.showinfo("成功", f"Excel文件已保存到: {filename}")
        else:
            tk.messagebox.showerror("错误", "导出Excel文件失败")
    
    def export_to_json(self):
        """导出到JSON报告"""
        filename = self.file_manager.save_statistics_report(self.statistics)
        if filename:
            tk.messagebox.showinfo("成功", f"JSON报告已保存到: {filename}")
        else:
            tk.messagebox.showerror("错误", "导出JSON报告失败")
    
    def export_to_csv(self):
        """导出到CSV文件"""
        try:
            from datetime import datetime
            
            # 准备数据
            data = {
                '统计时间': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '总报文数': [self.statistics.protocol_stats.get('total', 0)],
                'IPv4报文': [self.statistics.protocol_stats.get('IPv4', 0)],
                'IPv6报文': [self.statistics.protocol_stats.get('IPv6', 0)],
                'TCP报文': [self.statistics.protocol_stats.get('TCP', 0)],
                'UDP报文': [self.statistics.protocol_stats.get('UDP', 0)],
                'ARP报文': [self.statistics.protocol_stats.get('ARP', 0)],
                'DNS报文': [self.statistics.protocol_stats.get('DNS', 0)],
                'IPv6占比': [f"{self.statistics.get_ipv6_ratio():.2f}%"]
            }
            
            df = pd.DataFrame(data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.file_manager.export_to_excel(self.statistics).replace('.xlsx', '.csv')
            
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            tk.messagebox.showinfo("成功", f"CSV文件已保存到: {filepath}")
            
        except Exception as e:
            tk.messagebox.showerror("错误", f"导出CSV文件失败: {e}")
    
    def export_all_formats(self):
        """导出所有格式"""
        excel_file = self.file_manager.export_to_excel(self.statistics)
        json_file = self.file_manager.save_statistics_report(self.statistics)
        
        success_files = []
        if excel_file:
            success_files.append(f"Excel: {excel_file}")
        if json_file:
            success_files.append(f"JSON: {json_file}")
        
        if success_files:
            message = "以下文件已保存:\n" + "\n".join(success_files)
            tk.messagebox.showinfo("成功", message)
        else:
            tk.messagebox.showerror("错误", "导出文件失败")