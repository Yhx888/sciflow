<div align="center">

# 🧬 SciFlow

**AI驱动的科研全流程智能工作台**

*从文献调研到论文撰写，让科研回归创新本身*

<p align="center">
  <a href="#核心特性">核心特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#使用指南">使用指南</a> •
  <a href="#api配置">API配置</a> •
  <a href="#开发">开发</a> •
  <a href="https://github.com/Yhx888/sciflow">GitHub</a>
</p>

</div>

## ✨ 核心特性

- 🖥️ **桌面应用 + Web界面 + CLI** 三种使用方式，开箱即用
- 💬 **ChatGPT式对话交互**，自然语言驱动科研工作流
- 🔌 **支持多种LLM**：OpenAI GPT-4o、Anthropic Claude、DeepSeek、智谱GLM、通义千问、Ollama本地模型
- 📚 **智能文献调研**：检索、分析、矩阵对比、自动BibTeX/GB-T 7714/APA引用
- 🧠 **研究辅助**：思路梳理、论文大纲生成、实验方案设计
- 📊 **成果导出**：Markdown报告、Word文档、BibTeX、ZIP打包下载
- 🎨 **精致UI设计**：苹果/Notion/ChatGPT级别的界面体验
- 🔒 **本地优先**：数据存储在本地，隐私安全

## 🚀 快速开始

### 方式零：在线体验（零安装）

打开 **单文件 Web Demo**（`sciflow_demo.html`，纯前端、零依赖）：

- 🖱️ 双击打开即可体验完整 8 步科研工作流，无需安装任何环境
- 🎭 内置演示引擎（Mock）开箱即用；在 ⚙️ 设置中填入 API Key 即可切换为真实 LLM
- 🌐 可部署到任意静态托管（魔搭创空间 / GitHub Pages / Vercel），作为公网访问链接提交参赛

> 部署教程见下方 [📡 部署指南](#-部署指南)

### 方式一：桌面应用（推荐）

下载最新的 `SciFlow-Setup.exe` 安装包，双击安装即可使用。

### 方式二：Python包

```bash
pip install sciflow
sciflow-app        # 启动桌面应用
sciflow server     # 启动Web服务器，访问 http://127.0.0.1:8765
sciflow            # 使用CLI
```

### 方式三：源码运行

```bash
git clone https://github.com/Yhx888/sciflow.git
cd sciflow
pip install -e ".[desktop,dev]"
python run.py
```

## 📖 使用指南

### 第一次使用

1. 启动SciFlow后，点击左下角 ⚙️ 设置按钮
2. 在「AI模型」中选择你使用的提供商（DeepSeek/OpenAI等）
3. 输入API Key（如使用DeepSeek，到 https://platform.deepseek.com/ 获取）
4. 可选：自定义API Base URL（如使用代理或本地Ollama）
5. 点击「测试连接」确认配置正确
6. 保存配置，开始使用！

未配置API Key时，SciFlow将使用Mock模式演示功能。

### 工作流步骤

SciFlow将科研流程自动化为8个步骤：

1. 🎯 **需求理解** - 分析你的研究主题
2. 🔍 **文献检索** - 搜索相关领域文献
3. 📊 **文献分析** - 总结研究趋势
4. 💡 **思路生成** - 探索创新研究点
5. 📋 **大纲构建** - 生成论文框架
6. 🧪 **实验设计** - 制定实验方案
7. ✍️ **文档撰写** - 辅助撰写报告
8. 📦 **成果导出** - 打包下载所有成果

### 支持的LLM提供商

| 提供商 | 默认模型 | 获取API Key |
|--------|---------|------------|
| OpenAI | gpt-4o-mini | https://platform.openai.com/ |
| Anthropic | claude-3-haiku | https://console.anthropic.com/ |
| DeepSeek | deepseek-chat | https://platform.deepseek.com/ |
| 智谱AI | glm-4-flash | https://open.bigmodel.cn/ |
| 通义千问 | qwen-turbo | https://dashscope.aliyun.com/ |
| Ollama | llama3 | http://localhost:11434（本地） |

## 🔧 API配置

### 配置文件位置

配置文件存储在 `~/.sciflow/config.json`

### 通过环境变量配置

也可以通过环境变量配置：

```bash
# OpenAI
export OPENAI_API_KEY="sk-xxx"

# DeepSeek（推荐国内用户使用）
export DEEPSEEK_API_KEY="sk-xxx"
```

## 📡 部署指南

### 方案一：魔搭创空间（推荐，公网可访问）

1. 注册登录 [魔搭创空间](https://modelscope.cn/studios)（阿里云，国内访问快）
2. 点击「创建空间」，空间类型选择 **静态页面**
3. 将仓库中的 `sciflow_demo.html` 重命名为 `index.html` 上传（或用 git 推送到空间仓库）
4. 等待部署完成，即可获得公网链接：`https://modelscope.cn/studios/<你的用户名>/<空间名>`

### 方案二：GitHub Pages（免费）

1. 在 GitHub 仓库 `Settings → Pages` 中启用 Pages，分支选 `main`，目录选 `/`
2. 访问 `https://<你的用户名>.github.io/sciflow/` 即可
3. 如目录下还有其他文件，可直接访问 `/sciflow_demo.html`

### 方案三：Vercel / Netlify / 任意静态托管

将 `sciflow_demo.html` 拖入即可，其他无需配置。

## 🏗️ 技术栈

- **后端**：Python 3.10+、FastAPI、Pydantic v2、httpx
- **前端**：原生HTML/CSS/JS、Marked.js、Highlight.js
- **桌面**：pywebview（轻量WebView）
- **LLM**：统一OpenAI兼容API接口
- **CLI**：Click
- **文档**：python-docx

## 📁 项目结构

```
├── sci_flow/                    # 核心代码目录
│   ├── core/           # 核心业务逻辑
│   │   ├── config.py   # 配置管理
│   │   ├── database.py # 数据持久化
│   │   ├── models.py   # 数据模型
│   │   ├── literature.py # 文献管理（arXiv/Semantic Scholar 真实检索）
│   │   ├── workflow.py # 工作流引擎
│   │   └── generator.py # 成果生成
│   ├── llm/            # LLM客户端
│   │   └── client.py   # 多提供商支持
│   ├── server/         # FastAPI服务器
│   │   └── app.py      # API路由
│   ├── desktop/        # 桌面应用
│   │   └── launcher.py # pywebview启动器
│   ├── web/            # Web前端
│   │   └── index.html  # 单页应用（渐进增强：有后端走真实API）
│   └── cli.py          # 命令行入口
├── sciflow_demo.html       # ★ 单文件参赛 Demo（零依赖，可静态部署）
├── tests/                  # pytest 测试（48 个用例）
├── build_exe.py        # 打包脚本
├── run.py              # 开发启动器
└── pyproject.toml
```

## 🧪 测试

```bash
pip install -e ".[dev]"
pytest           # 运行全部 48 个测试用例
pytest -x        # 遇到第一个失败即停止
```

覆盖：配置管理、数据库 CRUD、文献生成/引用格式/arXiv 解析、8 步工作流、成果导出（Word/ZIP）。

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

<div align="center">
Made with ❤️ for researchers
</div>
