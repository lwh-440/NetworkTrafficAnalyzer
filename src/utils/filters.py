"""
过滤器工具模块
"""
import re
from scapy.all import *

class PacketFilter:
    """报文过滤器"""
    
    def __init__(self):
        self.filters = []
        self.custom_filters = []
    
    def add_basic_filter(self, filter_type, value=None):
        """添加基础过滤器"""
        filter_map = {
            'ipv4': 'ip',
            'ipv6': 'ip6',
            'tcp': 'tcp',
            'udp': 'udp',
            'arp': 'arp',
            'dns': 'port 53',
            'icmp': 'icmp'
        }
        
        if filter_type in filter_map:
            self.filters.append(filter_map[filter_type])
            return True
        return False
    
    def add_custom_filter(self, filter_expression):
        """添加自定义过滤器表达式"""
        try:
            # 验证过滤器表达式
            if self._validate_filter(filter_expression):
                self.custom_filters.append(filter_expression)
                return True
        except:
            pass
        return False
    
    def _validate_filter(self, filter_expression):
        """验证过滤器表达式（基础验证）"""
        # 这里可以添加更复杂的验证逻辑
        if not filter_expression or len(filter_expression) > 100:
            return False
        
        # 简单的关键字检查
        allowed_keywords = ['ip', 'tcp', 'udp', 'arp', 'icmp', 'host', 'net', 
                           'port', 'src', 'dst', 'and', 'or', 'not']
        
        words = re.findall(r'[a-zA-Z0-9.]+', filter_expression)
        for word in words:
            if word not in allowed_keywords and not self._is_ip_or_port(word):
                return False
        
        return True
    
    def _is_ip_or_port(self, text):
        """检查是否为IP地址或端口"""
        # 检查IP地址
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if re.match(ip_pattern, text):
            return all(0 <= int(part) <= 255 for part in text.split('.'))
        
        # 检查端口
        if text.isdigit():
            return 0 <= int(text) <= 65535
        
        return False
    
    def add_ip_filter(self, ip_address, direction='both'):
        """添加IP过滤器"""
        if direction in ['src', 'both']:
            self.filters.append(f"src host {ip_address}")
        if direction in ['dst', 'both']:
            self.filters.append(f"dst host {ip_address}")
    
    def add_port_filter(self, port, direction='both'):
        """添加端口过滤器"""
        if direction in ['src', 'both']:
            self.filters.append(f"src port {port}")
        if direction in ['dst', 'both']:
            self.filters.append(f"dst port {port}")
    
    def add_protocol_filter(self, protocol):
        """添加协议过滤器"""
        protocol = protocol.lower()
        if protocol in ['tcp', 'udp', 'arp', 'icmp']:
            self.filters.append(protocol)
        elif protocol == 'dns':
            self.filters.append('port 53')
    
    def clear_filters(self):
        """清除所有过滤器"""
        self.filters.clear()
        self.custom_filters.clear()
    
    def get_bpf_filter(self):
        """生成BPF过滤器表达式"""
        all_filters = self.filters + self.custom_filters
        
        if not all_filters:
            return ""
        
        # 合并过滤器，使用OR关系
        return " or ".join(f"({f})" for f in all_filters)
    
    def get_filter_description(self):
        """获取过滤器描述"""
        descriptions = []
        
        for filter_expr in self.filters:
            if filter_expr == 'ip':
                descriptions.append("IPv4流量")
            elif filter_expr == 'ip6':
                descriptions.append("IPv6流量")
            elif filter_expr == 'tcp':
                descriptions.append("TCP流量")
            elif filter_expr == 'udp':
                descriptions.append("UDP流量")
            elif filter_expr == 'arp':
                descriptions.append("ARP流量")
            elif filter_expr == 'icmp':
                descriptions.append("ICMP流量")
            elif filter_expr == 'port 53':
                descriptions.append("DNS流量")
            elif filter_expr.startswith('src host'):
                descriptions.append(f"源IP: {filter_expr.split()[-1]}")
            elif filter_expr.startswith('dst host'):
                descriptions.append(f"目标IP: {filter_expr.split()[-1]}")
            elif filter_expr.startswith('src port'):
                descriptions.append(f"源端口: {filter_expr.split()[-1]}")
            elif filter_expr.startswith('dst port'):
                descriptions.append(f"目标端口: {filter_expr.split()[-1]}")
        
        for custom_filter in self.custom_filters:
            descriptions.append(f"自定义: {custom_filter}")
        
        return " | ".join(descriptions) if descriptions else "无过滤器"