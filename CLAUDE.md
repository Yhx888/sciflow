# CLAUDE.md - SciFlow 项目上下文

> 本文件为 AI 助手提供项目关键信息，确保每次新对话都能快速理解项目背景。

---

## 项目概述

**SciFlow** 是一个科研全流程 Agent 编排器，用自然语言串联文献管理、技术文档、数据分析、论文撰写，实现科研工作流自动化。

- **目标用户**: 理工科研究生、科研工作者
- **核心价值**: 让研究者专注于创新本身，而非重复性劳动
- **技术形态**: Python CLI 工具，支持 MCP/Skill 协议串联工具生态

---

## 项目结构

```
c:\HOME\Project\Trae创意大赛/
├── sci_flow/                    # 核心代码目录
│   ├── cli.py                   # CLI 入口（Click 框架）
│   ├── config.py                # 配置管理（Pydantic Settings）
│   ├── literature.py            # 文献调研模块
│   ├── zotero.py                # Zotero 同步模块
│   ├── lark.py                  # 飞书文档模块
│   ├── python.py                # Python 数据处理模块
│   ├── word.py                  # Word 文档生成模块
│   └── pipeline.py              # 全流程编排模块
│   ├── __init__.py              # 版本信息
│   └── __main__.py              # Python 模块入口
│
├── pyproject.toml               # 项目配置（setuptools）
├── README.md                    # 使用说明（小白友好）
├── LICENSE                      # MIT 许可证
├── CONTRIBUTING.md              # 贡献指南
├── CHANGELOG.md                 # 变更日志
├── .gitignore                   # Git 忽略规则
├── sciflow_creative.html        # 创意展示页面
│
└── .trae/specs/sciflow/         # 项目规划文档
    ├── spec.md                  # 产品需求文档
    ├── tasks.md                 # 实现计划
    └── checklist.md             # 验证清单
```

---

## 技术栈

| 技术 | 用途 | 版本要求 |
|------|------|---------|
| Python | 编程语言 | 3.10+ |
| Click | CLI 框架 | 8.0+ |
| Pydantic | 数据验证 | 2.0+ |
| python-docx | Word 文档处理 | 1.1+ |
| requests | HTTP 请求 | 2.31+ |

---

## 核心命令

### 安装
```bash
pip install -e .
```

### 基本使用
```bash
sciflow --version              # 查看版本
sciflow --help                 # 查看帮助
```

### 模块命令
```bash
# 文献调研
sciflow literature search "topic" --mock

# Zotero 同步
sciflow zotero add --title "论文标题" --authors "作者" --year 2025
sciflow zotero list

# 飞书文档
sciflow lark create --title "技术调研文档" --from-zotero

# Python 数据处理
sciflow python create-template --name "analysis"
sciflow python run --script "analysis.py"

# Word 论文生成
sciflow word create --title "论文" --author "作者" --affiliation "单位"

# 全流程编排（推荐）
sciflow pipeline run --topic "研究主题" --author "作者" --affiliation "单位"
```

---

## 开发指南

### 代码风格
- 使用 Black 格式化
- 遵循 PEP 8 规范
- 函数注释使用中文（与用户语言一致）

### 模块设计原则
1. 每个模块独立可测试
2. 支持 Mock 模式演示
3. 错误信息友好清晰
4. 配置通过 Pydantic Settings 管理

### 添加新模块
1. 在 `sci_flow/` 目录创建新模块文件
2. 在 `cli.py` 中注册新命令
3. 更新 README.md 和 CHANGELOG.md

---

## 关键文件说明

### [cli.py](file:///C:/HOME/Project/Trae创意大赛/sci_flow/cli.py)
CLI 入口文件，使用 Click 框架构建命令组。所有子模块命令在此注册。

### [config.py](file:///C:/HOME/Project/Trae创意大赛/sci_flow/config.py)
配置管理，使用 Pydantic Settings 支持环境变量和 .env 文件。

### [pipeline.py](file:///C:/HOME/Project/Trae创意大赛/sci_flow/pipeline.py)
全流程编排模块，串联所有环节形成完整工作流。

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
2. **Mock 模式**: 当前所有模块支持 Mock 模式演示，真实 API 接入需要用户配置
3. **输出目录**: `data/` 和 `output/` 目录在运行时自动创建，已在 .gitignore 中排除
4. **中文支持**: 项目面向中文用户，所有输出和注释使用中文

---

## 快速诊断

如果遇到问题，按以下顺序检查：

1. `sciflow --version` 是否正常返回版本
2. `pip list | findstr sciflow` 确认安装状态
3. 检查 Python 版本是否 >= 3.10
4. 检查依赖是否完整安装

---

> 💡 **提示**: 本文件应在每次新对话开始时被读取，确保 AI 助手了解项目上下文。