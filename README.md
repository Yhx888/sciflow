# SciFlow - 科研全流程 Agent 编排器

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-blue.svg)](https://black.readthedocs.io)

> 💡 **一句话介绍**：用自然语言告诉 SciFlow 你要做什么，它帮你自动完成从文献调研到论文撰写的全部工作。

---

## 🤔 什么是 SciFlow？

SciFlow 是一个 **AI 驱动的科研工作流助手**。你只需要用自然语言描述你的研究需求，它就能：

1. 📚 **帮你找文献** — 自动检索相关学术论文
2. 📦 **帮你管理文献** — 同步到 Zotero 文献库
3. 📝 **帮你写文档** — 自动生成技术调研文档
4. 🐍 **帮你分析数据** — 执行数据分析脚本
5. 📄 **帮你写论文** — 生成论文初稿

**无需编程基础**，用自然语言就能操作！

---

## 🚀 小白快速上手

### 步骤 1：安装

打开电脑的"命令提示符"或"终端"，输入以下命令：

```bash
# 安装 SciFlow
pip install sciflow
```

如果是从 GitHub 获取最新版本：

```bash
git clone https://github.com/Yhx888/sciflow.git
cd sciflow
pip install -e .
```

### 步骤 2：启动 SciFlow

安装完成后，在终端输入：

```bash
sciflow
```

你会看到欢迎界面和可用的功能选项。

### 步骤 3：一键完成科研工作流（推荐）

这是最简单的方式！只需一行命令，SciFlow 会自动帮你完成所有工作：

```bash
# 告诉 SciFlow 你的研究主题
sciflow pipeline run --topic "ROS2 自主导航" --author "张三" --affiliation "清华大学"
```

执行后，SciFlow 会自动：
1. 检索相关文献
2. 保存到文献库
3. 生成技术调研文档
4. 创建数据分析脚本
5. 生成论文初稿

---

## 🗣️ 自然语言交互指南

你可以用自然语言的方式告诉 SciFlow 你想做什么：

### 📚 "帮我找一些关于 ROS2 导航的论文"

```bash
sciflow literature search "ROS2 navigation" --mock
```

### 📦 "把这篇论文保存到我的文献库"

```bash
sciflow zotero add --title "论文标题" --authors "作者1,作者2" --year 2025
```

### 📝 "帮我生成一份技术调研文档"

```bash
sciflow lark create --title "技术调研文档" --from-zotero
```

### 🐍 "帮我处理一下实验数据"

```bash
# 先创建一个数据分析模板
sciflow python create-template --name "data_analysis"

# 执行数据分析
sciflow python run --script "data_analysis.py"
```

### 📄 "帮我生成一篇论文初稿"

```bash
sciflow word create --title "学术论文" --author "张三" --affiliation "清华大学"
```

---

## 📋 功能说明（通俗版）

| 功能 | 你可以说 | SciFlow 会做 |
|------|---------|-------------|
| 文献调研 | "帮我搜论文" | 自动检索学术数据库 |
| 文献管理 | "保存到文献库" | 同步到 Zotero |
| 文档生成 | "写技术文档" | 创建飞书文档 |
| 数据分析 | "处理数据" | 执行 Python 脚本 |
| 论文生成 | "写论文" | 生成 Word 文档 |
| 全流程 | "帮我做科研" | 一键完成所有工作 |

---

## 🔧 技术细节（进阶用户）

如果你对技术感兴趣，可以了解一下 SciFlow 的内部结构：

### 项目结构

```
sci_flow/
├── cli.py              # 命令行入口
├── config.py           # 配置管理
├── literature.py       # 文献调研模块
├── zotero.py           # Zotero 同步模块
├── lark.py             # 飞书文档模块
├── python.py           # Python 数据处理模块
├── word.py             # Word 文档生成模块
└── pipeline.py         # 全流程编排模块
```

### 技术栈

- **Python 3.10+** — 编程语言
- **Click CLI** — 命令行框架
- **Pydantic** — 数据验证
- **python-docx** — Word 文档处理
- **requests** — HTTP 请求

### 配置文件

可以创建 `.env` 文件自定义配置：

```
ZOTERO_API_KEY=your_api_key
ZOTERO_USER_ID=your_user_id
LARK_DOC_TEMPLATE=template_path
```

---

## 🤝 贡献

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献流程。

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 📞 问题反馈

如有问题或建议，请在 GitHub Issues 中提交。

---

> 💡 **小贴士**：如果你是科研小白，建议直接使用 `sciflow pipeline run` 命令，一键体验完整的科研工作流！
