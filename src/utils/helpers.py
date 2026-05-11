"""
辅助函数模块
"""
import sys
import platform
import subprocess
from datetime import datetime, timedelta

def check_dependencies():
    """检查必要的依赖包"""
    required_packages = [
        'scapy', 'matplotlib', 'pandas', 'numpy', 'psutil', 'seaborn'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def get_system_info():
    """获取系统信息"""
    system_info = {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.architecture()[0],
        'processor': platform.processor(),
        'python_version': platform.python_version()
    }
    return system_info

def format_bytes(size):
    """格式化字节大小"""
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power and n < len(power_labels) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"

def format_duration(seconds):
    """格式化时间间隔"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        if platform.system() == 'Windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False

def get_timestamp():
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_time_range(time_str):
    """解析时间范围字符串"""
    now = datetime.now()
    
    if time_str == '1h':
        return now - timedelta(hours=1)
    elif time_str == '6h':
        return now - timedelta(hours=6)
    elif time_str == '24h':
        return now - timedelta(hours=24)
    elif time_str == '7d':
        return now - timedelta(days=7)
    else:
        return now - timedelta(hours=1)  # 默认1小时

def validate_ip_address(ip):
    """验证IP地址格式"""
    import re
    pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    if re.match(pattern, ip):
        parts = ip.split('.')
        if all(0 <= int(part) <= 255 for part in parts):
            return True
    return False

def validate_port(port):
    """验证端口号"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except:
        return False

def safe_execute(func, default_return=None, *args, **kwargs):
    """安全执行函数，捕获异常"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"函数执行失败: {func.__name__}, 错误: {e}")
        return default_return

class RateCalculator:
    """速率计算器"""
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.timestamps = []
        self.values = []
    
    def update(self, value):
        """更新数值"""
        current_time = datetime.now()
        self.timestamps.append(current_time)
        self.values.append(value)
        
        # 移除旧数据
        cutoff_time = current_time - timedelta(seconds=self.window_size)
        while self.timestamps and self.timestamps[0] < cutoff_time:
            self.timestamps.pop(0)
            self.values.pop(0)
    
    def get_rate(self):
        """计算速率"""
        if len(self.timestamps) < 2:
            return 0
        
        time_span = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
        if time_span == 0:
            return 0
        
        value_span = self.values[-1] - self.values[0]
        return value_span / time_span