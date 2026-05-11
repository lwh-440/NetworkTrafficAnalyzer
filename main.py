#!/usr/bin/env python3
"""
网络流量分析器 - 主程序入口
Network Traffic Analyzer - Main Entry Point
"""
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow
import tkinter as tk
from utils.helpers import check_dependencies

def main():
    """主函数"""
    # 检查依赖
    missing_deps = check_dependencies()
    if missing_deps:
        print("缺少必要的依赖包:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行: pip install " + " ".join(missing_deps))
        return
    
    try:
        # 创建主窗口
        root = tk.Tk()
        app = MainWindow(root)
        
        # 设置窗口标题和图标
        root.title("网络流量分析器 v1.0")
        root.geometry("1200x800")
        
        # 启动主循环
        print("网络流量分析器启动成功!")
        print("运行提示: 请确保以管理员/root权限运行以获得完整的网络访问权限")
        root.mainloop()
        
    except Exception as e:
        print(f"程序启动失败: {e}")
        print("请检查是否安装了所有依赖包")
        input("按Enter键退出...")

if __name__ == "__main__":
    main()