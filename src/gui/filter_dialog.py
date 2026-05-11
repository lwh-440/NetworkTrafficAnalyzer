"""
过滤器对话框模块
"""
import tkinter as tk
from tkinter import ttk

class FilterDialog(tk.Toplevel):
    """过滤器设置对话框"""
    
    def __init__(self, parent, packet_filter, callback):
        super().__init__(parent)
        self.packet_filter = packet_filter
        self.callback = callback
        
        self.setup_dialog()
        self.load_current_filters()
    
    def setup_dialog(self):
        """设置对话框"""
        self.title("过滤器设置")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # 设置模态对话框
        self.transient(self.master)
        self.grab_set()
        
        # 协议过滤器框架
        protocol_frame = ttk.LabelFrame(self, text="协议过滤器", padding=10)
        protocol_frame.pack(fill=tk.X, padx=10, pady=5)
        
        protocols = [
            ("IPv4", "ipv4"),
            ("IPv6", "ipv6"), 
            ("TCP", "tcp"),
            ("UDP", "udp"),
            ("ARP", "arp"),
            ("DNS", "dns"),
            ("ICMP", "icmp")
        ]
        
        self.protocol_vars = {}
        for i, (text, key) in enumerate(protocols):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(protocol_frame, text=text, variable=var)
            cb.grid(row=i//4, column=i%4, sticky=tk.W, padx=5, pady=2)
            self.protocol_vars[key] = var
        
        # IP过滤器框架
        ip_frame = ttk.LabelFrame(self, text="IP过滤器", padding=10)
        ip_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ip_frame, text="IP地址:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ip_entry = ttk.Entry(ip_frame, width=15)
        self.ip_entry.grid(row=0, column=1, padx=5)
        
        self.ip_direction_var = tk.StringVar(value="both")
        ttk.Radiobutton(ip_frame, text="源IP", variable=self.ip_direction_var, 
                       value="src").grid(row=0, column=2, padx=5)
        ttk.Radiobutton(ip_frame, text="目标IP", variable=self.ip_direction_var, 
                       value="dst").grid(row=0, column=3, padx=5)
        ttk.Radiobutton(ip_frame, text="两者", variable=self.ip_direction_var, 
                       value="both").grid(row=0, column=4, padx=5)
        
        ttk.Button(ip_frame, text="添加IP过滤器", 
                  command=self.add_ip_filter).grid(row=0, column=5, padx=10)
        
        # 端口过滤器框架
        port_frame = ttk.LabelFrame(self, text="端口过滤器", padding=10)
        port_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(port_frame, text="端口号:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.port_entry = ttk.Entry(port_frame, width=10)
        self.port_entry.grid(row=0, column=1, padx=5)
        
        self.port_direction_var = tk.StringVar(value="both")
        ttk.Radiobutton(port_frame, text="源端口", variable=self.port_direction_var, 
                       value="src").grid(row=0, column=2, padx=5)
        ttk.Radiobutton(port_frame, text="目标端口", variable=self.port_direction_var, 
                       value="dst").grid(row=0, column=3, padx=5)
        ttk.Radiobutton(port_frame, text="两者", variable=self.port_direction_var, 
                       value="both").grid(row=0, column=4, padx=5)
        
        ttk.Button(port_frame, text="添加端口过滤器", 
                  command=self.add_port_filter).grid(row=0, column=5, padx=10)
        
        # 自定义过滤器框架
        custom_frame = ttk.LabelFrame(self, text="自定义BPF过滤器", padding=10)
        custom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(custom_frame, text="BPF表达式:").pack(anchor=tk.W)
        self.custom_filter_entry = ttk.Entry(custom_frame, width=50)
        self.custom_filter_entry.pack(fill=tk.X, pady=5)
        
        ttk.Button(custom_frame, text="添加自定义过滤器", 
                  command=self.add_custom_filter).pack(anchor=tk.E)
        
        # 当前过滤器框架
        current_frame = ttk.LabelFrame(self, text="当前活动的过滤器", padding=10)
        current_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.filters_text = tk.Text(current_frame, height=6, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(current_frame, orient=tk.VERTICAL, command=self.filters_text.yview)
        self.filters_text.configure(yscrollcommand=scrollbar.set)
        
        self.filters_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="清除所有过滤器", 
                  command=self.clear_filters).pack(side=tk.LEFT)
        
        ttk.Button(button_frame, text="应用", 
                  command=self.apply_filters).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", 
                  command=self.destroy).pack(side=tk.RIGHT)
    
    def load_current_filters(self):
        """加载当前过滤器状态"""
        # 更新过滤器描述
        self.update_filters_display()
    
    def add_ip_filter(self):
        """添加IP过滤器"""
        ip_address = self.ip_entry.get().strip()
        if not ip_address:
            tk.messagebox.showwarning("警告", "请输入IP地址")
            return
        
        from ...utils.helpers import validate_ip_address
        if not validate_ip_address(ip_address):
            tk.messagebox.showwarning("警告", "请输入有效的IP地址")
            return
        
        direction = self.ip_direction_var.get()
        self.packet_filter.add_ip_filter(ip_address, direction)
        self.update_filters_display()
        self.ip_entry.delete(0, tk.END)
    
    def add_port_filter(self):
        """添加端口过滤器"""
        port_str = self.port_entry.get().strip()
        if not port_str:
            tk.messagebox.showwarning("警告", "请输入端口号")
            return
        
        from ...utils.helpers import validate_port
        if not validate_port(port_str):
            tk.messagebox.showwarning("警告", "请输入有效的端口号 (1-65535)")
            return
        
        direction = self.port_direction_var.get()
        self.packet_filter.add_port_filter(int(port_str), direction)
        self.update_filters_display()
        self.port_entry.delete(0, tk.END)
    
    def add_custom_filter(self):
        """添加自定义过滤器"""
        filter_expr = self.custom_filter_entry.get().strip()
        if not filter_expr:
            tk.messagebox.showwarning("警告", "请输入BPF过滤器表达式")
            return
        
        if self.packet_filter.add_custom_filter(filter_expr):
            self.update_filters_display()
            self.custom_filter_entry.delete(0, tk.END)
        else:
            tk.messagebox.showerror("错误", "无效的BPF过滤器表达式")
    
    def clear_filters(self):
        """清除所有过滤器"""
        self.packet_filter.clear_filters()
        self.update_filters_display()
    
    def update_filters_display(self):
        """更新过滤器显示"""
        self.filters_text.config(state=tk.NORMAL)
        self.filters_text.delete(1.0, tk.END)
        
        filter_desc = self.packet_filter.get_filter_description()
        bpf_expr = self.packet_filter.get_bpf_filter()
        
        self.filters_text.insert(tk.END, "过滤器描述:\n")
        self.filters_text.insert(tk.END, f"  {filter_desc}\n\n")
        self.filters_text.insert(tk.END, "BPF表达式:\n")
        self.filters_text.insert(tk.END, f"  {bpf_expr if bpf_expr else '无'}")
        
        self.filters_text.config(state=tk.DISABLED)
    
    def apply_filters(self):
        """应用过滤器"""
        # 添加协议过滤器
        for protocol, var in self.protocol_vars.items():
            if var.get():
                self.packet_filter.add_basic_filter(protocol)
        
        if self.callback:
            self.callback()
        
        self.destroy()