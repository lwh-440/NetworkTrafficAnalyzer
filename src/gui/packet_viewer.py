"""
报文查看器模块
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import json
import csv

class PacketViewer(ttk.Frame):
    """报文查看器面板"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.packets = []
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 配置主框架的网格权重
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # 报文列表区域可扩展
        self.rowconfigure(3, weight=1)  # 详细信息区域可扩展
        
        # 控制按钮框架
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)
        control_frame.columnconfigure(1, weight=1)  # 搜索框区域可扩展
        
        ttk.Button(control_frame, text="清空列表", command=self.clear_packets).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Button(control_frame, text="导出选中", command=self.export_selected).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 搜索框
        search_frame = ttk.Frame(control_frame)
        search_frame.grid(row=0, column=2, sticky=tk.E, padx=5)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # 报文列表
        list_frame = ttk.LabelFrame(self, text="报文列表", padding=5)
        list_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建树形视图
        columns = ('序号', '时间', '源地址', '目标地址', '协议', '长度', '信息')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # 设置列
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, minwidth=50)
        
        # 特别设置信息列的宽度可以更大
        self.tree.column('信息', width=200, minwidth=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_packet_select)
        
        # 详细信息框架
        detail_frame = ttk.LabelFrame(self, text="报文详细信息", padding=5)
        detail_frame.grid(row=2, column=0, sticky=tk.EW, padx=5, pady=5)
        detail_frame.columnconfigure(0, weight=1)
        
        # 详细信息文本框
        self.detail_text = tk.Text(detail_frame, height=8, wrap=tk.WORD)
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)
        
        self.detail_text.grid(row=0, column=0, sticky=tk.EW)
        detail_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        # 十六进制转储框架
        hex_frame = ttk.LabelFrame(self, text="十六进制转储", padding=5)
        hex_frame.grid(row=3, column=0, sticky=tk.NSEW, padx=5, pady=5)
        hex_frame.columnconfigure(0, weight=1)
        hex_frame.rowconfigure(0, weight=1)
        
        self.hex_text = tk.Text(hex_frame, height=6, wrap=tk.WORD, font=('Courier', 10))
        hex_scrollbar = ttk.Scrollbar(hex_frame, orient=tk.VERTICAL, command=self.hex_text.yview)
        self.hex_text.configure(yscrollcommand=hex_scrollbar.set)
        
        self.hex_text.grid(row=0, column=0, sticky=tk.NSEW)
        hex_scrollbar.grid(row=0, column=1, sticky=tk.NS)
    
    def add_packet(self, packet_info):
        """添加报文到列表"""
        packet_id = len(self.packets) + 1
        self.packets.append(packet_info)
        
        # 格式化时间
        time_str = packet_info['timestamp'].strftime("%H:%M:%S.%f")[:-3]
        
        # 获取源和目标地址
        src = packet_info.get('src', packet_info.get('src_mac', ''))
        dst = packet_info.get('dst', packet_info.get('dst_mac', ''))
        
        # 添加端口信息（如果有）
        if 'src_port' in packet_info:
            src += f":{packet_info['src_port']}"
        if 'dst_port' in packet_info:
            dst += f":{packet_info['dst_port']}"
        
        # 插入到树形视图
        values = (
            packet_id,
            time_str,
            src,
            dst,
            packet_info['protocol'],
            packet_info['length'],
            packet_info.get('info', '')
        )
        
        self.tree.insert('', tk.END, values=values, tags=(packet_info['protocol'],))
        
        # 自动滚动到最新
        self.tree.see(self.tree.get_children()[-1])
        
        # 限制显示数量，避免内存问题
        if len(self.tree.get_children()) > 10000:
            self.tree.delete(self.tree.get_children()[0])
    
    def on_packet_select(self, event):
        """报文选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values:
            return
        
        packet_id = int(values[0]) - 1  # 转换为0-based索引
        if 0 <= packet_id < len(self.packets):
            self.show_packet_details(self.packets[packet_id])
    
    def show_packet_details(self, packet_info):
        """显示报文详细信息"""
        # 清空文本框
        self.detail_text.config(state=tk.NORMAL)
        self.hex_text.config(state=tk.NORMAL)
        
        self.detail_text.delete(1.0, tk.END)
        self.hex_text.delete(1.0, tk.END)
        
        # 显示基本信息
        self.detail_text.insert(tk.END, "=== 报文基本信息 ===\n")
        self.detail_text.insert(tk.END, f"时间: {packet_info['timestamp']}\n")
        self.detail_text.insert(tk.END, f"长度: {packet_info['length']} 字节\n")
        self.detail_text.insert(tk.END, f"协议: {packet_info['protocol']}\n")
        
        # 显示各层信息
        for key, value in packet_info.items():
            if key not in ['timestamp', 'length', 'protocol', 'info', 'raw_data']:
                self.detail_text.insert(tk.END, f"{key}: {value}\n")
        
        # 显示十六进制转储
        if 'raw_data' in packet_info:
            try:
                from ...core.protocol_parser import ProtocolParser
                hex_dump = ProtocolParser.get_hex_dump(packet_info['raw_data'])
                self.hex_text.insert(tk.END, hex_dump)
            except ImportError:
                self.hex_text.insert(tk.END, "无法导入协议解析器，无法显示十六进制转储")
        
        # 禁用编辑
        self.detail_text.config(state=tk.DISABLED)
        self.hex_text.config(state=tk.DISABLED)
    
    def clear_packets(self):
        """清空报文列表"""
        self.packets.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.config(state=tk.DISABLED)
        
        self.hex_text.config(state=tk.NORMAL)
        self.hex_text.delete(1.0, tk.END)
        self.hex_text.config(state=tk.DISABLED)
    
    def export_selected(self):
        """导出选中的报文"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要导出的报文")
            return
        
        # 获取选中的报文数据
        selected_packets = []
        for item in selection:
            values = self.tree.item(item, 'values')
            packet_id = int(values[0]) - 1
            if 0 <= packet_id < len(self.packets):
                selected_packets.append(self.packets[packet_id])
        
        if not selected_packets:
            messagebox.showwarning("警告", "未找到选中的报文数据")
            return
        
        # 创建导出选项对话框
        export_window = tk.Toplevel(self)
        export_window.title("导出选中报文")
        export_window.geometry("400x300")
        export_window.transient(self)
        export_window.grab_set()
        
        # 导出格式选择
        format_frame = ttk.LabelFrame(export_window, text="导出格式", padding=10)
        format_frame.pack(fill=tk.X, padx=10, pady=10)
        
        export_format = tk.StringVar(value="pcap")
        formats = [
            ("PCAP格式 (推荐)", "pcap"),
            ("JSON格式", "json"),
            ("CSV格式", "csv"),
            ("文本报告", "txt")
        ]
        
        for text, value in formats:
            ttk.Radiobutton(format_frame, text=text, variable=export_format, 
                           value=value).pack(anchor=tk.W, pady=2)
        
        # 导出选项
        options_frame = ttk.LabelFrame(export_window, text="导出选项", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        include_raw = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="包含原始报文数据", 
                       variable=include_raw).pack(anchor=tk.W, pady=2)
        
        include_hex = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="包含十六进制转储", 
                       variable=include_hex).pack(anchor=tk.W, pady=2)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(export_window, text="统计信息", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        stats_text = (f"选中报文数量: {len(selected_packets)}\n"
                      f"时间范围: {selected_packets[0]['timestamp'].strftime('%H:%M:%S')} - "
                      f"{selected_packets[-1]['timestamp'].strftime('%H:%M:%S')}\n"
                      f"协议分布: {self._get_protocol_distribution(selected_packets)}")
        
        ttk.Label(stats_frame, text=stats_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        def do_export():
            format_choice = export_format.get()
            export_window.destroy()
            self._perform_export(selected_packets, format_choice, include_raw.get(), include_hex.get())
        
        button_frame = ttk.Frame(export_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="导出", command=do_export).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=export_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _get_protocol_distribution(self, packets):
        """获取协议分布信息"""
        protocol_count = {}
        for packet in packets:
            protocol = packet.get('protocol', 'Unknown')
            protocol_count[protocol] = protocol_count.get(protocol, 0) + 1
        
        distribution = []
        for protocol, count in protocol_count.items():
            percentage = (count / len(packets)) * 100
            distribution.append(f"{protocol}: {count}({percentage:.1f}%)")
        
        return ", ".join(distribution)
    
    def _perform_export(self, packets, format_choice, include_raw, include_hex):
        """执行导出操作"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_choice == "pcap":
                # 导出为PCAP格式
                from scapy.all import wrpcap
                filename = f"selected_packets_{timestamp}.pcap"
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".pcap",
                    filetypes=[("PCAP files", "*.pcap"), ("All files", "*.*")],
                    initialfile=filename
                )
                if filepath:
                    raw_packets = [p['raw_data'] for p in packets if 'raw_data' in p]
                    if raw_packets:
                        wrpcap(filepath, raw_packets)
                        messagebox.showinfo("成功", f"已导出 {len(raw_packets)} 个报文到: {filepath}")
                    else:
                        messagebox.showwarning("警告", "选中的报文中没有原始数据，无法导出为PCAP格式")
            
            elif format_choice == "json":
                # 导出为JSON格式
                filename = f"selected_packets_{timestamp}.json"
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    initialfile=filename
                )
                if filepath:
                    export_data = []
                    for packet in packets:
                        packet_data = packet.copy()
                        if not include_raw and 'raw_data' in packet_data:
                            del packet_data['raw_data']
                        if 'timestamp' in packet_data:
                            packet_data['timestamp'] = packet_data['timestamp'].isoformat()
                        export_data.append(packet_data)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                    messagebox.showinfo("成功", f"已导出 {len(export_data)} 个报文到: {filepath}")
            
            elif format_choice == "csv":
                # 导出为CSV格式
                filename = f"selected_packets_{timestamp}.csv"
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    initialfile=filename
                )
                if filepath:
                    with open(filepath, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        # 写入表头
                        headers = ['时间', '协议', '源地址', '目标地址', '长度', '信息']
                        writer.writerow(headers)
                        
                        # 写入数据
                        for packet in packets:
                            row = [
                                packet['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                                packet.get('protocol', ''),
                                packet.get('src', ''),
                                packet.get('dst', ''),
                                packet.get('length', 0),
                                packet.get('info', '')
                            ]
                            writer.writerow(row)
                    
                    messagebox.showinfo("成功", f"已导出 {len(packets)} 个报文到: {filepath}")
            
            elif format_choice == "txt":
                # 导出为文本报告格式
                filename = f"packet_report_{timestamp}.txt"
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                    initialfile=filename
                )
                if filepath:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write("网络报文分析报告\n")
                        f.write("=" * 50 + "\n")
                        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"报文数量: {len(packets)}\n")
                        f.write(f"时间范围: {packets[0]['timestamp'].strftime('%H:%M:%S')} - {packets[-1]['timestamp'].strftime('%H:%M:%S')}\n")
                        f.write(f"协议分布: {self._get_protocol_distribution(packets)}\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for i, packet in enumerate(packets, 1):
                            f.write(f"报文 #{i}\n")
                            f.write(f"  时间: {packet['timestamp'].strftime('%H:%M:%S.%f')[:-3]}\n")
                            f.write(f"  协议: {packet.get('protocol', 'Unknown')}\n")
                            f.write(f"  源地址: {packet.get('src', '')}\n")
                            f.write(f"  目标地址: {packet.get('dst', '')}\n")
                            f.write(f"  长度: {packet.get('length', 0)} 字节\n")
                            if packet.get('info'):
                                f.write(f"  信息: {packet.get('info', '')}\n")
                            f.write("\n")
                    
                    messagebox.showinfo("成功", f"已生成分析报告到: {filepath}")
        
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def on_search(self, event):
        """搜索报文"""
        search_term = self.search_var.get().lower()
        
        # 清空当前选择
        for item in self.tree.selection():
            self.tree.selection_remove(item)
        
        # 搜索匹配的项
        if search_term:
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                if any(search_term in str(value).lower() for value in values):
                    self.tree.selection_add(item)
                    self.tree.see(item)