"""
数据统计模块
"""
from collections import defaultdict, deque
import time
from datetime import datetime
import pandas as pd

class TrafficStatistics:
    """流量统计类"""
    
    def __init__(self, timeline_size=1000):
        # 基础统计
        self.protocol_stats = defaultdict(int)
        self.ip_stats = defaultdict(int)
        self.port_stats = defaultdict(int)
        
        # 时间序列数据
        self.timeline_data = deque(maxlen=timeline_size)
        self.start_time = None
        
        # 实时速率计算
        self.last_update_time = None
        self.last_packet_count = 0
        self.current_rate = 0
        
        # 历史记录
        self.hourly_stats = defaultdict(lambda: defaultdict(int))
        self.daily_stats = defaultdict(lambda: defaultdict(int))
    
    def update_stats(self, packet_info):
        """更新统计数据"""
        if self.start_time is None:
            self.start_time = datetime.now()
        
        protocol = packet_info['protocol']
        src_ip = packet_info.get('src', '')
        dst_ip = packet_info.get('dst', '')
        
        # 更新协议统计
        self.protocol_stats[protocol] += 1
        self.protocol_stats['total'] += 1
        
        # 更新IP统计
        if src_ip:
            self.ip_stats[src_ip] += 1
        if dst_ip:
            self.ip_stats[dst_ip] += 1
        
        # 更新端口统计
        src_port = packet_info.get('src_port')
        dst_port = packet_info.get('dst_port')
        if src_port:
            self.port_stats[f"src_{src_port}"] += 1
        if dst_port:
            self.port_stats[f"dst_{dst_port}"] += 1
        
        # 更新时间序列数据
        current_time = time.time()
        timeline_point = {
            'timestamp': current_time,
            'protocol': protocol,
            'packet_size': packet_info['length'],
            'src_ip': src_ip,
            'dst_ip': dst_ip
        }
        self.timeline_data.append(timeline_point)
        
        # 计算实时速率
        self._update_packet_rate()
        
        # 更新小时和天统计
        self._update_historical_stats(packet_info)
    
    def _update_packet_rate(self):
        """更新报文速率"""
        current_time = time.time()
        
        if self.last_update_time is None:
            self.last_update_time = current_time
            self.last_packet_count = self.protocol_stats['total']
            return
        
        time_diff = current_time - self.last_update_time
        if time_diff >= 1.0:  # 每秒更新一次
            packet_diff = self.protocol_stats['total'] - self.last_packet_count
            self.current_rate = packet_diff / time_diff
            
            self.last_update_time = current_time
            self.last_packet_count = self.protocol_stats['total']
    
    def _update_historical_stats(self, packet_info):
        """更新历史统计数据"""
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d %H:00")
        day_key = now.strftime("%Y-%m-%d")
        
        protocol = packet_info['protocol']
        
        self.hourly_stats[hour_key][protocol] += 1
        self.hourly_stats[hour_key]['total'] += 1
        
        self.daily_stats[day_key][protocol] += 1
        self.daily_stats[day_key]['total'] += 1
    
    def get_protocol_distribution(self):
        """获取协议分布"""
        total = self.protocol_stats['total']
        if total == 0:
            return {}
        
        distribution = {}
        for protocol, count in self.protocol_stats.items():
            if protocol != 'total':
                distribution[protocol] = {
                    'count': count,
                    'percentage': (count / total) * 100
                }
        
        return distribution
    
    def get_ipv6_ratio(self):
        """获取IPv6流量占比"""
        total = self.protocol_stats['total']
        if total == 0:
            return 0
        
        ipv6_count = (self.protocol_stats.get('IPv6', 0) + 
                     self.protocol_stats.get('TCPv6', 0) + 
                     self.protocol_stats.get('UDPv6', 0))
        
        return (ipv6_count / total) * 100
    
    def get_top_ips(self, top_n=10):
        """获取流量最大的IP地址"""
        return dict(sorted(self.ip_stats.items(), 
                         key=lambda x: x[1], reverse=True)[:top_n])
    
    def get_top_ports(self, top_n=10):
        """获取流量最大的端口"""
        return dict(sorted(self.port_stats.items(), 
                         key=lambda x: x[1], reverse=True)[:top_n])
    
    def get_timeline_summary(self, window_seconds=60):
        """获取时间线摘要"""
        if not self.timeline_data:
            return []
        
        current_time = time.time()
        time_threshold = current_time - window_seconds
        
        # 过滤最近的数据
        recent_data = [point for point in self.timeline_data 
                      if point['timestamp'] >= time_threshold]
        
        if not recent_data:
            return []
        
        # 创建DataFrame进行分析
        df = pd.DataFrame(recent_data)
        
        # 按协议分组统计
        protocol_summary = df.groupby('protocol').agg({
            'packet_size': ['count', 'sum', 'mean']
        }).round(2)
        
        # 格式化结果
        summary = []
        for protocol, stats in protocol_summary.iterrows():
            summary.append({
                'protocol': protocol,
                'packet_count': int(stats[('packet_size', 'count')]),
                'total_bytes': int(stats[('packet_size', 'sum')]),
                'avg_packet_size': float(stats[('packet_size', 'mean')])
            })
        
        return summary
    
    def get_real_time_metrics(self):
        """获取实时指标"""
        duration = 0
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'total_packets': self.protocol_stats['total'],
            'packet_rate': self.current_rate,
            'duration': duration,
            'ipv6_ratio': self.get_ipv6_ratio(),
            'unique_ips': len(self.ip_stats),
            'unique_ports': len(self.port_stats) // 2  # 除以2因为包含源和目标端口
        }
    
    def reset_stats(self):
        """重置统计"""
        self.protocol_stats.clear()
        self.ip_stats.clear()
        self.port_stats.clear()
        self.timeline_data.clear()
        self.start_time = None
        self.last_update_time = None
        self.last_packet_count = 0
        self.current_rate = 0
        self.hourly_stats.clear()
        self.daily_stats.clear()
        
        # 重新初始化total
        self.protocol_stats['total'] = 0