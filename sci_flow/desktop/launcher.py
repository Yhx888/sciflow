"""
SciFlow 桌面应用启动器
使用pywebview创建桌面窗口，自动启动并管理FastAPI后端
"""

from __future__ import annotations

import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

import requests


def find_free_port(start_port: int = 8765, max_attempts: int = 100) -> int:
    """查找空闲端口，从start_port开始递增尝试"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"无法找到空闲端口（尝试范围: {start_port}-{start_port + max_attempts - 1}）")


def wait_for_backend(port: int, timeout: int = 30, interval: float = 0.5) -> bool:
    """轮询等待后端启动成功"""
    url = f"http://127.0.0.1:{port}/api/config"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(interval)
    
    return False


class BackendServer:
    """后端服务器管理器，在后台线程中运行uvicorn"""
    
    def __init__(self, port: int):
        self.port = port
        self.server_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self._server = None
    
    def _run_server(self):
        """在后台线程中运行uvicorn服务器"""
        import uvicorn
        
        from sci_flow.server.app import create_app
        
        app = create_app()
        
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        
        try:
            self._server.run()
        except Exception as e:
            print(f"[SciFlow] 后端服务器异常: {e}", file=sys.stderr)
    
    def start(self):
        """启动后端服务器"""
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="SciFlow-Backend"
        )
        self.server_thread.start()
    
    def stop(self):
        """优雅关闭后端服务器"""
        if self._server:
            self._server.should_exit = True
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)


def create_window(port: int) -> bool:
    """使用pywebview创建桌面窗口，返回是否成功创建"""
    try:
        import webview
    except ImportError:
        print("[SciFlow] 警告: pywebview 未安装，无法启动桌面窗口")
        print("[SciFlow] 请运行: pip install pywebview")
        print("[SciFlow] 或者使用浏览器访问: http://127.0.0.1:{0}".format(port))
        webbrowser.open(f"http://127.0.0.1:{port}/static/index.html")
        return False
    
    url = f"http://127.0.0.1:{port}/static/index.html"
    
    window = webview.create_window(
        title="SciFlow - 科研全流程智能工作台",
        url=url,
        width=1280,
        height=800,
        min_size=(900, 600),
        background_color="#1a1a1a",
        confirm_close=True,
        resizable=True,
    )
    
    def on_closing():
        """窗口关闭时的回调"""
        pass
    
    window.events.closing += on_closing
    
    try:
        webview.start(debug=False)
    except Exception as e:
        print(f"[SciFlow] pywebview启动失败: {e}", file=sys.stderr)
        print(f"[SciFlow] 请使用浏览器访问: http://127.0.0.1:{port}/static/index.html")
        webbrowser.open(f"http://127.0.0.1:{port}/static/index.html")
        return False
    
    return True


def main():
    """主函数 - 桌面应用入口点"""
    print("=" * 60)
    print("  SciFlow - 科研全流程智能工作台")
    print("=" * 60)
    print()
    
    try:
        port = find_free_port(8765)
    except RuntimeError as e:
        print(f"[SciFlow] 错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"[SciFlow] 使用端口: {port}")
    print("[SciFlow] 正在启动后端服务器...")
    
    backend = BackendServer(port)
    backend.start()
    
    print("[SciFlow] 等待后端就绪...")
    if not wait_for_backend(port, timeout=30):
        print("[SciFlow] 错误: 后端服务器启动超时", file=sys.stderr)
        backend.stop()
        sys.exit(1)
    
    print("[SciFlow] 后端服务器已就绪")
    print(f"[SciFlow] 访问地址: http://127.0.0.1:{port}/static/index.html")
    print()
    
    window_created = False
    
    try:
        window_created = create_window(port)
        
        if not window_created:
            print("[SciFlow] 桌面窗口不可用，保持服务器运行...")
            print("[SciFlow] 按 Ctrl+C 退出")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[SciFlow] 正在关闭...")
    finally:
        print("[SciFlow] 正在关闭后端服务器...")
        backend.stop()
        print("[SciFlow] 已退出")


if __name__ == "__main__":
    main()
