# CLAUDE.md - SciFlow 项目上下文

> 本文件为 AI 助手提供项目关键信息，确保每次新对话都能快速理解项目背景。

---

## 项目概述

**SciFlow** 是一个AI驱动的科研全流程智能工作台，支持桌面应用、Web界面、CLI三种使用方式。从文献调研到论文撰写，用自然语言驱动科研工作流，让科研回归创新本身。

- **版本**: v1.0.0（商业级正式版）
- **目标用户**: 理工科研究生、科研工作者
- **核心价值**: 让研究者专注于创新本身，而非重复性劳动
- **技术形态**: 桌面App (pywebview) + Web UI (FastAPI) + CLI (Click)
- **数据存储**: 本地SQLite数据库，隐私优先

---

## 项目结构

```
c:\HOME\Project\Trae创意大赛/
├── sci_flow/                    # 核心代码目录
│   ├── core/                    # 核心业务逻辑
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # SQLite数据持久化
│   │   ├── models.py            # Pydantic数据模型
│   │   ├── literature.py        # 文献管理模块
│   │   ├── workflow.py          # 工作流引擎（8步科研流程）
│   │   └── generator.py         # 成果生成（Markdown/Word/BibTeX）
│   ├── llm/                     # LLM客户端
│   │   └── client.py            # 多提供商支持（OpenAI/DeepSeek/Claude等）
│   ├── server/                  # FastAPI后端服务器
│   │   └── app.py               # API路由 + SSE流式响应
│   ├── desktop/                 # 桌面应用
│   │   └── launcher.py          # pywebview启动器
│   ├── web/                     # Web前端
│   │   └── index.html           # 单页应用（ChatGPT风格UI）
│   ├── cli.py                   # CLI命令行入口
│   ├── __init__.py              # 版本信息
│   └── __main__.py              # Python模块入口
│
├── build_exe.py                 # 桌面应用打包脚本
├── run.py                       # 开发启动器
├── pyproject.toml               # 项目配置
├── README.md                    # 项目说明（商业级）
├── LICENSE                      # MIT 许可证
├── CONTRIBUTING.md              # 贡献指南
├── CHANGELOG.md                 # 变更日志
└── .gitignore                   # Git 忽略规则
```

---

## 技术栈

| 技术 | 用途 | 版本要求 |
|------|------|---------|
| Python | 编程语言 | 3.10+ |
| FastAPI | 后端API服务器 | 最新 |
| Pydantic v2 | 数据验证 | 2.0+ |
| httpx | 异步HTTP客户端 | 最新 |
| pywebview | 桌面应用WebView | 最新 |
| Click | CLI框架 | 8.0+ |
| python-docx | Word文档生成 | 1.1+ |
| SQLite | 本地数据库 | 内置 |

### 前端技术
- 原生HTML/CSS/JavaScript
- Marked.js（Markdown渲染）
- Highlight.js（代码高亮）
- 苹果/Notion/ChatGPT风格UI设计
- 深浅主题切换

---

## 核心命令

### 三种启动方式
```bash
sciflow-app        # 启动桌面应用（推荐）
sciflow server     # 启动Web服务器，访问 http://127.0.0.1:8765
sciflow            # 使用CLI命令行
```

### 开发模式
```bash
python run.py      # 从源码启动开发服务器
```

### 主要CLI命令组
```bash
sciflow app        # 桌面应用相关
sciflow server     # Web服务器相关
sciflow config     # 配置管理（LLM提供商、API Key等）
sciflow project    # 项目管理
sciflow chat       # 对话交互
```

---

## LLM支持

### 支持的提供商
- OpenAI (gpt-4o-mini)
- Anthropic (claude-3-haiku)
- DeepSeek (deepseek-chat，推荐国内用户)
- 智谱AI (glm-4-flash)
- 通义千问 (qwen-turbo)
- Ollama本地模型 (llama3)

### 配置方式
1. 图形界面：应用内设置面板
2. 配置文件：`~/.sciflow/config.json`
3. 环境变量：`OPENAI_API_KEY`、`DEEPSEEK_API_KEY`等

未配置API Key时使用Mock模式演示功能。

---

## 工作流步骤

SciFlow将科研流程自动化为8个步骤：

1. 🎯 **需求理解** - 分析研究主题
2. 🔍 **文献检索** - 搜索相关领域文献
3. 📊 **文献分析** - 总结研究趋势
4. 💡 **思路生成** - 探索创新研究点
5. 📋 **大纲构建** - 生成论文框架
6. 🧪 **实验设计** - 制定实验方案
7. ✍️ **文档撰写** - 辅助撰写报告
8. 📦 **成果导出** - ZIP打包下载所有成果（Markdown/Word/BibTeX）

---

## 开发指南

### 代码风格
- 使用 Black 格式化
- 遵循 PEP 8 规范
- 函数注释使用中文（与用户语言一致）
- 不添加多余注释，代码自解释

### 模块设计原则
1. 前后端分离架构
2. 每个模块独立可测试
3. 支持Mock模式演示
4. 错误信息友好清晰
5. 配置通过core/config.py管理
6. 数据持久化使用SQLite

---

## 关键文件说明

### [sci_flow/core/config.py](file:///C:/HOME/Project/Trae创意大赛/sci_flow/core/config.py)
配置管理，支持图形界面、配置文件、环境变量三种方式。

### [sci_flow/core/workflow.py](file:///C:/HOME/Project/Trae创意大赛/sci_flow/core/workflow.py)
8步科研工作流引擎，串联所有业务环节。

### [sci_flow/llm/client.py](file:///C:/HOME/Project/Trae创意大赛/sci_flow/llm/client.py)
统一LLM客户端，自研多提供商适配（OpenAI兼容接口）。

### [sci_flow/server/app.py](file:///C:/HOME/Project/Trae创意大赛/sci_flow/server/app.py)
FastAPI后端，提供REST API和SSE流式响应。

### [sci_flow/desktop/launcher.py](file:///C:/HOME/Project/Trae创意大赛/sci_flow/desktop/launcher.py)
pywebview桌面应用启动器，原生窗口体验。

### [sci_flow/web/index.html](file:///C:/HOME/Project/Trae创意大赛/sci_flow/web/index.html)
单页Web前端，ChatGPT/苹果级精致UI。

### [pyproject.toml](file:///C:/HOME/Project/Trae创意大赛/pyproject.toml)
项目配置文件，定义依赖、入口点、构建方式。

---

## GitHub 仓库

- **地址**: https://github.com/Yhx888/sciflow
- **状态**: 公开仓库（Public）
- **许可证**: MIT License

---

## 注意事项

1. **Windows 环境**: 项目在 Windows 上开发，注意路径分隔符和 PowerShell 命令语法
2. **Mock 模式**: 未配置API Key时自动使用Mock模式演示
3. **配置目录**: 用户配置存储在 `~/.sciflow/` 目录
4. **本地优先**: 所有数据存储在本地，保护隐私安全
5. **中文支持**: 项目面向中文用户，所有输出和注释使用中文

---

## 快速诊断

如果遇到问题，按以下顺序检查：

1. `sciflow --version` 是否正常返回版本
2. `pip list | findstr sciflow` 确认安装状态
3. 检查 Python 版本是否 >= 3.10
4. 检查依赖是否完整安装
5. 检查 `~/.sciflow/config.json` 配置是否正确
6. 如使用LLM，确认API Key和网络连接

---

> 💡 **提示**: 本文件应在每次新对话开始时被读取，确保 AI 助手了解项目上下文。
