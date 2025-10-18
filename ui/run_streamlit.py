
import os
import sys
import subprocess
from pathlib import Path
import socket
import time

def check_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def find_available_port(start_port=8501, max_ports=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_ports):
        if not check_port_in_use(port):
            return port
    return None

def main():
    # 获取脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    
    # 找到主应用文件 app.py
    ui_dir = script_dir 
    streamlit_file = ui_dir / "app.py"
    
    # 检查文件是否存在
    if not streamlit_file.exists():
        print(f"错误：找不到app.py文件")
        print(f"期望位置：{streamlit_file}")
        return 1
    
    # 切换到UI目录
    os.chdir(ui_dir)
    
    # 检查环境
    is_deployed = os.environ.get("STREAMLIT_RUNTIME_ENV", "").lower() == "cloud"
    
    # 部署环境提示
    if is_deployed:
        print("在部署环境中运行 Qrent AI Agent...")
    else:
        print("启动 Qrent AI Agent...")
        print("本地开发模式：浏览器将自动打开 http://localhost:8501")
        print("按 Ctrl+C 停止应用")
    
    print("-" * 40)
    print("请使用邀请码登录系统")
    print("测试邀请码: TEST01, TEST02, TEST03")
    print("-" * 40)
    
    # 启动streamlit
    try:
        # 查找可用端口
        port = find_available_port()
        if port:
            # 本地环境使用找到的端口
            if not is_deployed:
                print(f"使用端口 {port}")
                subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port)])
            else:
                # 部署环境让streamlit自动分配端口
                subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
        else:
            print("错误：找不到可用端口")
            return 1
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

# 创建一个主入口文件，以便Streamlit Cloud可以直接识别
if __name__ == "__main__":
    sys.exit(main())
else:
    # 当作为模块导入时（可能在Streamlit Cloud中），提供一个简单的导入点
    pass