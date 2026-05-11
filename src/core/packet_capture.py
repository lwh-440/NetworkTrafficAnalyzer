"""
网络报文捕获模块
"""
import threading
import time
from scapy.all import *
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import ARP, Ether
import psutil
from collections import defaultdict, deque
from datetime import datetime

class PacketCapture:
    """网络报文捕获类"""
    
    def __init__(self, interface=None):
        self.interface = interface
        self.is_capturing = False
        self.packet_count = 0
        self.start_time = None
        self.capture_thread = None
        self.packet_queue = deque(maxlen=1000)  # 存储最近1000个报文
        self.stats_callback = None
        self.packet_callback = None
        self.filter_rules = ""
        
        # 获取网络接口
        if not interface:
            self.interface = self.get_default_interface()
    
    def get_default_interface(self):
        """获取默认网络接口"""
        try:
            # 获取所有网络接口
            interfaces = psutil.net_io_counters(pernic=True)
            # 选择第一个非lo回环接口
            for iface in interfaces:
                if iface != 'lo' and not iface.startswith('veth'):
                    return iface
            return list(interfaces.keys())[0] if interfaces else 'eth0'
        except:
            return 'eth0'  # 默认值
    
    def get_available_interfaces(self):
        """获取所有可用的网络接口"""
        interfaces = psutil.net_io_counters(pernic=True)
        return list(interfaces.keys())
    
    def packet_handler(self, packet):
        """处理捕获的报文"""
        if not self.is_capturing:
            return
            
        self.packet_count += 1
        packet_info = self.analyze_packet(packet)
        
        # 添加到队列
        self.packet_queue.append(packet_info)
        
        # 回调通知
        if self.stats_callback:
            self.stats_callback(packet_info)
        
        if self.packet_callback:
            self.packet_callback(packet_info)
    
    def analyze_packet(self, packet):
        """分析报文内容"""
        packet_info = {
            'timestamp': datetime.now(),
            'length': len(packet),
            'protocol': 'Unknown',
            'src': '',
            'dst': '',
            'info': '',
            'raw_data': packet
        }
        
        # Ethernet层
        if Ether in packet:
            packet_info['src_mac'] = packet[Ether].src
            packet_info['dst_mac'] = packet[Ether].dst
        
        # IP层
        if IP in packet:
            packet_info['protocol'] = 'IPv4'
            packet_info['src'] = packet[IP].src
            packet_info['dst'] = packet[IP].dst
            packet_info['ttl'] = packet[IP].ttl
            
            if TCP in packet:
                packet_info['protocol'] = 'TCP'
                packet_info['src_port'] = packet[TCP].sport
                packet_info['dst_port'] = packet[TCP].dport
                packet_info['info'] = f"TCP {packet[TCP].sport} → {packet[TCP].dport} " \
                                     f"Flags: {packet[TCP].flags} Seq: {packet[TCP].seq}"
                
            elif UDP in packet:
                packet_info['protocol'] = 'UDP'
                packet_info['src_port'] = packet[UDP].sport
                packet_info['dst_port'] = packet[UDP].dport
                packet_info['info'] = f"UDP {packet[UDP].sport} → {packet[UDP].dport}"
                
            elif ICMP in packet:
                packet_info['protocol'] = 'ICMP'
                packet_info['info'] = f"ICMP Type: {packet[ICMP].type}"
        
        # IPv6层
        elif IPv6 in packet:
            packet_info['protocol'] = 'IPv6'
            packet_info['src'] = packet[IPv6].src
            packet_info['dst'] = packet[IPv6].dst
            
            if TCP in packet:
                packet_info['protocol'] = 'TCPv6'
                packet_info['src_port'] = packet[TCP].sport
                packet_info['dst_port'] = packet[TCP].dport
                
            elif UDP in packet:
                packet_info['protocol'] = 'UDPv6'
                packet_info['src_port'] = packet[UDP].sport
                packet_info['dst_port'] = packet[UDP].dport
        
        # ARP层
        elif ARP in packet:
            packet_info['protocol'] = 'ARP'
            packet_info['src'] = packet[ARP].psrc
            packet_info['dst'] = packet[ARP].pdst
            packet_info['info'] = f"ARP {packet[ARP].op} {packet[ARP].psrc} -> {packet[ARP].pdst}"
        
        # DNS (在UDP或TCP之上)
        if packet_info.get('dst_port') == 53 or packet_info.get('src_port') == 53:
            packet_info['protocol'] = 'DNS'
        
        return packet_info
    
    def start_capture(self, filter_rules=""):
        """开始捕获报文"""
        if self.is_capturing:
            return False
            
        self.filter_rules = filter_rules
        self.is_capturing = True
        self.packet_count = 0
        self.start_time = datetime.now()
        
        def capture_loop():
            try:
                sniff(
                    iface=self.interface,
                    prn=self.packet_handler,
                    filter=filter_rules,
                    store=False,
                    stop_filter=lambda x: not self.is_capturing
                )
            except Exception as e:
                print(f"捕获错误: {e}")
                self.is_capturing = False
        
        self.capture_thread = threading.Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()
        return True
    
    def stop_capture(self):
        """停止捕获报文"""
        self.is_capturing = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
    
    def set_interface(self, interface):
        """设置网络接口"""
        if not self.is_capturing:
            self.interface = interface
    
    def get_capture_stats(self):
        """获取捕获统计"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
        else:
            duration = 0
            
        return {
            'packet_count': self.packet_count,
            'duration': duration,
            'interface': self.interface,
            'is_capturing': self.is_capturing
        }
    
    def get_recent_packets(self, count=100):
        """获取最近的报文"""
        return list(self.packet_queue)[-count:]
    
    def set_stats_callback(self, callback):
        """设置统计回调函数"""
        self.stats_callback = callback
    
    def set_packet_callback(self, callback):
        """设置报文回调函数"""
        self.packet_callback = callback