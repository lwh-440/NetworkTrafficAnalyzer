"""
文件管理模块 - 处理数据的保存和读取
"""
import json
import csv
import pickle
from datetime import datetime
import os
from scapy.all import *
import pandas as pd

class FileManager:
    """文件管理类"""
    
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self.captures_dir = os.path.join(base_dir, "captures")
        self.config_dir = os.path.join(base_dir, "config")
        self.reports_dir = os.path.join(base_dir, "reports")
        
        # 创建目录
        self._create_directories()
    
    def _create_directories(self):
        """创建必要的目录"""
        directories = [self.base_dir, self.captures_dir, self.config_dir, self.reports_dir]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def save_packets(self, packets, filename=None, format='pcap'):
        """保存报文数据"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}"
        
        filepath = os.path.join(self.captures_dir, filename)
        
        try:
            if format == 'pcap':
                # 保存为pcap格式
                filepath += '.pcap'
                wrpcap(filepath, [p['raw_data'] for p in packets if 'raw_data' in p])
                
            elif format == 'json':
                # 保存为JSON格式
                filepath += '.json'
                # 转换不可序列化的对象
                serializable_packets = []
                for packet in packets:
                    serializable_packet = packet.copy()
                    if 'raw_data' in serializable_packet:
                        del serializable_packet['raw_data']  # 移除原始数据
                    # 转换datetime对象为字符串
                    if 'timestamp' in serializable_packet:
                        serializable_packet['timestamp'] = serializable_packet['timestamp'].isoformat()
                    serializable_packets.append(serializable_packet)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(serializable_packets, f, indent=2, ensure_ascii=False)
                    
            elif format == 'csv':
                # 保存为CSV格式
                filepath += '.csv'
                if packets:
                    # 提取所有可能的字段
                    all_fields = set()
                    for packet in packets:
                        all_fields.update(packet.keys())
                    
                    # 移除不可序列化的字段
                    all_fields.discard('raw_data')
                    
                    with open(filepath, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=list(all_fields))
                        writer.writeheader()
                        for packet in packets:
                            row = packet.copy()
                            if 'raw_data' in row:
                                del row['raw_data']
                            if 'timestamp' in row:
                                row['timestamp'] = row['timestamp'].isoformat()
                            writer.writerow(row)
            
            return filepath
            
        except Exception as e:
            print(f"保存文件失败: {e}")
            return None
    
    def load_packets(self, filepath):
        """加载报文数据"""
        if not os.path.exists(filepath):
            return None
        
        try:
            if filepath.endswith('.pcap'):
                # 加载pcap文件
                packets_data = []
                scapy_packets = rdpcap(filepath)
                
                from .packet_capture import PacketCapture
                capture = PacketCapture()
                
                for packet in scapy_packets:
                    packet_info = capture.analyze_packet(packet)
                    packets_data.append(packet_info)
                
                return packets_data
                
            elif filepath.endswith('.json'):
                # 加载JSON文件
                with open(filepath, 'r', encoding='utf-8') as f:
                    packets_data = json.load(f)
                
                # 转换时间字符串回datetime对象
                for packet in packets_data:
                    if 'timestamp' in packet:
                        packet['timestamp'] = datetime.fromisoformat(packet['timestamp'])
                
                return packets_data
                
            elif filepath.endswith('.csv'):
                # 加载CSV文件
                packets_data = []
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 转换时间字符串
                        if 'timestamp' in row:
                            row['timestamp'] = datetime.fromisoformat(row['timestamp'])
                        packets_data.append(row)
                
                return packets_data
            
            else:
                print(f"不支持的文件格式: {filepath}")
                return None
                
        except Exception as e:
            print(f"加载文件失败: {e}")
            return None
    
    def save_statistics_report(self, statistics, filename=None):
        """保存统计报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"statistics_report_{timestamp}.json"
        
        filepath = os.path.join(self.reports_dir, filename)
        
        try:
            # 准备可序列化的统计数据
            report = {
                'generated_at': datetime.now().isoformat(),
                'real_time_metrics': statistics.get_real_time_metrics(),
                'protocol_distribution': statistics.get_protocol_distribution(),
                'top_ips': statistics.get_top_ips(20),
                'top_ports': statistics.get_top_ports(20),
                'timeline_summary': statistics.get_timeline_summary(300)  # 5分钟摘要
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            print(f"保存统计报告失败: {e}")
            return None
    
    def save_config(self, config_data, filename='app_config.json'):
        """保存配置"""
        filepath = os.path.join(self.config_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def load_config(self, filename='app_config.json'):
        """加载配置"""
        filepath = os.path.join(self.config_dir, filename)
        
        if not os.path.exists(filepath):
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {}
    
    def get_saved_captures(self):
        """获取所有保存的捕获文件"""
        captures = []
        
        for filename in os.listdir(self.captures_dir):
            filepath = os.path.join(self.captures_dir, filename)
            if os.path.isfile(filepath):
                file_info = {
                    'filename': filename,
                    'filepath': filepath,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath))
                }
                captures.append(file_info)
        
        # 按修改时间排序，最新的在前
        captures.sort(key=lambda x: x['modified'], reverse=True)
        return captures
    
    def export_to_excel(self, statistics, filename=None):
        """导出统计到Excel文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"traffic_analysis_{timestamp}.xlsx"
        
        filepath = os.path.join(self.reports_dir, filename)
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 协议分布
                protocol_dist = statistics.get_protocol_distribution()
                protocol_df = pd.DataFrame([
                    {
                        'Protocol': proto,
                        'Count': data['count'],
                        'Percentage': f"{data['percentage']:.2f}%"
                    }
                    for proto, data in protocol_dist.items()
                ])
                protocol_df.to_excel(writer, sheet_name='Protocol Distribution', index=False)
                
                # Top IPs
                top_ips = statistics.get_top_ips(20)
                ips_df = pd.DataFrame([
                    {'IP Address': ip, 'Packet Count': count}
                    for ip, count in top_ips.items()
                ])
                ips_df.to_excel(writer, sheet_name='Top IP Addresses', index=False)
                
                # Top Ports
                top_ports = statistics.get_top_ports(20)
                ports_df = pd.DataFrame([
                    {'Port': port, 'Packet Count': count}
                    for port, count in top_ports.items()
                ])
                ports_df.to_excel(writer, sheet_name='Top Ports', index=False)
                
                # 实时指标
                metrics = statistics.get_real_time_metrics()
                metrics_df = pd.DataFrame([metrics])
                metrics_df.to_excel(writer, sheet_name='Real-time Metrics', index=False)
            
            return filepath
            
        except Exception as e:
            print(f"导出Excel失败: {e}")
            return None