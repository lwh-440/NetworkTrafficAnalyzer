#!/usr/bin/env python3
"""
网络流量分析器 - 启动脚本
"""
import sys
import os

# 将项目根目录添加到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """主函数"""
    try:
        # 现在可以正常导入
        from src.gui.main_window import MainWindow
        from src.utils.helpers import check_dependencies
        import tkinter as tk
        
        # 检查依赖
        missing_deps = check_dependencies()
        if missing_deps:
            print("缺少必要的依赖包:")
            for dep in missing_deps:
                print(f"  - {dep}")
            print("\n请运行: pip install " + " ".join(missing_deps))
            input("按Enter键退出...")
            return
        
        # 创建主窗口
        root = tk.Tk()
        app = MainWindow(root)
        
        # 设置窗口
        root.title("网络流量分析器 v1.0")
        root.geometry("1200x800")
        
        # 设置关闭事件
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("网络流量分析器启动成功!")
        print("运行提示: 请确保以管理员权限运行")
        root.mainloop()
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")

if __name__ == "__main__":
    main()