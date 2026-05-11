"""
网络流量分析器 - 核心模块
"""

__version__ = "1.0.0"
__author__ = "网络流量分析器开发团队"

from .core.packet_capture import PacketCapture
from .core.protocol_parser import ProtocolParser
from .core.statistics import TrafficStatistics
from .core.file_manager import FileManager

from .utils.filters import PacketFilter
from .utils.resource_monitor import ResourceMonitor
from .utils.helpers import *

# 导出主要类
__all__ = [
    'PacketCapture',
    'ProtocolParser', 
    'TrafficStatistics',
    'FileManager',
    'PacketFilter',
    'ResourceMonitor'
]