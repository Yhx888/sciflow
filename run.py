"""
SciFlow 开发启动器
方便开发时快速启动服务器和打开浏览器
使用方法: python run.py [--port PORT] [--no-browser] [--desktop]
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def find_free_port(start_port: int = 8765, max_attempts: int = 100) -> int:
    """查找空闲端口"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"无法找到空闲端口（尝试范围: {start_port}-{start_port + max_attempts - 1}）")


def wait_for_server(port: int, timeout: int = 30, interval: float = 0.5) -> bool:
    """等待服务器启动"""
    import requests
    
    url = f"http://127.0.0.1:{port}/api/config"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(interval)
    
    return False


def open_browser_delayed(port: int, delay: float = 2.0):
    """延迟打开浏览器，等待服务器启动"""
    time.sleep(delay)
    url = f"http://127.0.0.1:{port}/static/index.html"
    print(f"[开发] 打开浏览器: {url}")
    webbrowser.open(url)


def run_desktop(port: int):
    """启动桌面版本"""
    try:
        from sci_flow.desktop.launcher import BackendServer, create_window, wait_for_backend
    except ImportError as e:
        print(f"[错误] 无法导入桌面模块: {e}", file=sys.stderr)
        print("[提示] 请确保已安装 pywebview: pip install pywebview", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 60)
    print("  SciFlow 桌面模式")
    print("=" * 60)
    print()
    
    print(f"[启动] 使用端口: {port}")
    print("[启动] 正在启动后端服务器...")
    
    backend = BackendServer(port)
    backend.start()
    
    print("[启动] 等待后端就绪...")
    if not wait_for_backend(port, timeout=30):
        print("[错误] 后端服务器启动超时", file=sys.stderr)
        backend.stop()
        sys.exit(1)
    
    print("[启动] 后端已就绪")
    print()
    
    try:
        create_window(port)
    finally:
        print("[关闭] 正在停止后端服务器...")
        backend.stop()
        print("[关闭] 已退出")


def run_server(port: int, open_browser: bool = True):
    """启动开发服务器"""
    import uvicorn
    
    print("=" * 60)
    print("  SciFlow 开发服务器")
    print("=" * 60)
    print()
    print(f"[配置] 端口: {port}")
    print(f"[配置] 访问地址: http://127.0.0.1:{port}/static/index.html")
    print(f"[配置] API文档: http://127.0.0.1:{port}/docs")
    print()
    
    if open_browser:
        browser_thread = threading.Thread(
            target=open_browser_delayed,
            args=(port, 2.0),
            daemon=True,
            name="BrowserOpener"
        )
        browser_thread.start()
    
    print("[启动] 正在启动服务器...")
    print("-" * 60)
    
    from sci_flow.server.app import create_app
    app = create_app()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        reload=False,
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SciFlow 开发启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py                  # 启动服务器并自动打开浏览器
  python run.py --port 9000      # 指定端口启动
  python run.py --no-browser     # 不自动打开浏览器
  python run.py --desktop        # 尝试启动桌面版本
        """
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="指定端口号（默认: 自动查找8765或下一个空闲端口）"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动打开浏览器"
    )
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="启动桌面版本（需要pywebview）"
    )
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.resolve()
    sys.path.insert(0, str(project_root))
    
    if args.port:
        port = args.port
    else:
        try:
            port = find_free_port(8765)
        except RuntimeError as e:
            print(f"[错误] {e}", file=sys.stderr)
            sys.exit(1)
    
    os.chdir(project_root)
    
    if args.desktop:
        run_desktop(port)
    else:
        run_server(port, open_browser=not args.no_browser)


if __name__ == "__main__":
    import os
    main()
