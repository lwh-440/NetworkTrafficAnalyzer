"""
资源监控模块
"""
import psutil
import time
import threading
from datetime import datetime

class ResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self, update_interval=2.0):
        self.update_interval = update_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.update_callback = None
        
        # 监控数据
        self.cpu_percent = 0
        self.memory_usage = 0
        self.memory_total = 0
        self.network_io = {'bytes_sent': 0, 'bytes_recv': 0}
        self.disk_io = {'read_bytes': 0, 'write_bytes': 0}
        self.start_time = None
        
        # 历史数据
        self.history = {
            'timestamps': [],
            'cpu': [],
            'memory': [],
            'network_sent': [],
            'network_recv': []
        }
        self.max_history_points = 100
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.start_time = datetime.now()
        
        # 获取初始网络和磁盘IO计数
        self._update_io_counters()
        
        def monitor_loop():
            while self.is_monitoring:
                self._update_metrics()
                if self.update_callback:
                    self.update_callback(self.get_current_stats())
                time.sleep(self.update_interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
    
    def _update_metrics(self):
        """更新监控指标"""
        # CPU使用率
        self.cpu_percent = psutil.cpu_percent(interval=None)
        
        # 内存使用
        memory = psutil.virtual_memory()
        self.memory_usage = memory.percent
        self.memory_total = memory.total / (1024 ** 3)  # 转换为GB
        
        # 网络IO
        self._update_network_io()
        
        # 磁盘IO
        self._update_disk_io()
        
        # 更新历史数据
        self._update_history()
    
    def _update_io_counters(self):
        """更新IO计数器基准"""
        net_io = psutil.net_io_counters()
        disk_io = psutil.disk_io_counters()
        
        self.last_net_io = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv
        }
        
        self.last_disk_io = {
            'read_bytes': disk_io.read_bytes if disk_io else 0,
            'write_bytes': disk_io.write_bytes if disk_io else 0
        }
    
    def _update_network_io(self):
        """更新网络IO统计"""
        current_net_io = psutil.net_io_counters()
        
        if hasattr(self, 'last_net_io'):
            time_diff = self.update_interval
            self.network_io = {
                'bytes_sent': (current_net_io.bytes_sent - self.last_net_io['bytes_sent']) / time_diff,
                'bytes_recv': (current_net_io.bytes_recv - self.last_net_io['bytes_recv']) / time_diff
            }
        
        self.last_net_io = {
            'bytes_sent': current_net_io.bytes_sent,
            'bytes_recv': current_net_io.bytes_recv
        }
    
    def _update_disk_io(self):
        """更新磁盘IO统计"""
        current_disk_io = psutil.disk_io_counters()
        
        if current_disk_io and hasattr(self, 'last_disk_io'):
            time_diff = self.update_interval
            self.disk_io = {
                'read_bytes': (current_disk_io.read_bytes - self.last_disk_io['read_bytes']) / time_diff,
                'write_bytes': (current_disk_io.write_bytes - self.last_disk_io['write_bytes']) / time_diff
            }
        
        if current_disk_io:
            self.last_disk_io = {
                'read_bytes': current_disk_io.read_bytes,
                'write_bytes': current_disk_io.write_bytes
            }
    
    def _update_history(self):
        """更新历史数据"""
        current_time = time.time()
        
        # 添加新数据点
        self.history['timestamps'].append(current_time)
        self.history['cpu'].append(self.cpu_percent)
        self.history['memory'].append(self.memory_usage)
        self.history['network_sent'].append(self.network_io['bytes_sent'])
        self.history['network_recv'].append(self.network_io['bytes_recv'])
        
        # 限制历史数据点数
        if len(self.history['timestamps']) > self.max_history_points:
            for key in self.history:
                self.history[key] = self.history[key][-self.max_history_points:]
    
    def get_current_stats(self):
        """获取当前统计信息"""
        uptime = 0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'cpu_percent': self.cpu_percent,
            'memory_usage': self.memory_usage,
            'memory_total_gb': round(self.memory_total, 2),
            'network_sent_bps': self.network_io['bytes_sent'],
            'network_recv_bps': self.network_io['bytes_recv'],
            'disk_read_bps': self.disk_io['read_bytes'],
            'disk_write_bps': self.disk_io['write_bytes'],
            'uptime_seconds': uptime,
            'history': self.history.copy()
        }
    
    def get_process_stats(self):
        """获取当前进程的统计信息"""
        try:
            process = psutil.Process()
            with process.oneshot():
                return {
                    'process_cpu_percent': process.cpu_percent(),
                    'process_memory_mb': process.memory_info().rss / 1024 / 1024,
                    'process_threads': process.num_threads(),
                    'process_open_files': len(process.open_files()),
                    'process_status': process.status()
                }
        except:
            return {}
    
    def set_update_callback(self, callback):
        """设置更新回调函数"""
        self.update_callback = callback