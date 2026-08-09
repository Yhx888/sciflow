"""
魔搭创空间入口（Gradio 应用类型专用）

用途：魔搭创空间若选择「Gradio 应用」类型，会执行 python3 app.py。
本文件以 Gradio 应用形式托管 SciFlow 单文件 Demo（index.html）。

注意：
- 部署时需同时上传 index.html（由 sciflow_demo.html 改名而来）与本文件
- 若空间类型选择「静态页面」，则无需本文件，直接上传 index.html 即可
"""

import gradio as gr

with open("index.html", encoding="utf-8") as f:
    DEMO_HTML = f.read()

with gr.Blocks(title="SciFlow — AI 科研全流程智能工作台") as demo:
    gr.HTML(DEMO_HTML)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
