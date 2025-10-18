import os
import sys
import subprocess
from pathlib import Path

def main():
    # 获取脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    
    # 找到邀请码管理工具文件
    ui_dir = script_dir 
    manager_file = ui_dir / "invitation_manager_tool.py"
    
    # 检查文件是否存在
    if not manager_file.exists():
        print(f"错误：找不到邀请码管理工具文件")
        print(f"期望位置：{manager_file}")
        return 1
    
    # 切换到UI目录
    os.chdir(ui_dir)
    
    print("启动 Qrent AI Agent - 邀请码管理系统...")
    print("浏览器将自动打开 http://localhost:8501")
    print("按 Ctrl+C 停止应用")
    print("-" * 40)
    
    # 启动streamlit
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "invitation_manager_tool.py"])
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败：{e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())