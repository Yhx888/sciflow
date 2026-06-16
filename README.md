# SciFlow - 科研全流程 Agent 编排器

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-blue.svg)](https://black.readthedocs.io)

用自然语言串联文献管理、技术文档、数据分析、论文撰写，实现科研工作流自动化。

## 🌟 功能特性

- 📚 **文献调研** - 检索学术文献，支持 Mock 和真实检索
- 📦 **Zotero 同步** - 管理文献库，支持文献添加和查询
- 📝 **飞书文档** - 创建技术调研文档，支持从 Zotero 导入
- 🐍 **Python 处理** - 执行数据分析脚本，支持参数传递
- 📄 **Word 生成** - 创建论文初稿，支持模板填充
- 🔄 **全流程编排** - 串联所有环节，一键完成科研工作流

## 🚀 快速开始

### 安装

```bash
# 从 PyPI 安装
pip install sciflow

# 或从源码安装
git clone https://github.com/your-username/sciflow.git
cd sciflow
pip install -e .
```

### 查看版本和帮助

```bash
sciflow --version
sciflow --help
```

## 📖 使用示例

### 1. 文献调研

```bash
# 检索文献（Mock 模式）
sciflow literature search "ROS2 navigation" --mock

# 分析文献趋势
sciflow literature summarize "ROS2 navigation"
```

### 2. Zotero 同步

```bash
# 添加文献
sciflow zotero add --title "论文标题" --authors "作者1,作者2" --year 2025

# 列出文献库
sciflow zotero list
```

### 3. 飞书文档生成

```bash
# 创建技术调研文档
sciflow lark create --title "技术调研文档"

# 从 Zotero 导入文献生成文档
sciflow lark create --title "技术调研文档" --from-zotero
```

### 4. Python 数据处理

```bash
# 创建示例脚本
sciflow python create-template --name "data_analysis"

# 执行脚本
sciflow python run --script "data_analysis.py"
```

### 5. Word 论文生成

```bash
# 创建论文文档
sciflow word create --title "学术论文" --author "张三" --affiliation "清华大学"
```

### 6. 全流程编排

```bash
# 一键执行完整工作流
sciflow pipeline run --topic "ROS2 自主导航" --author "张三" --affiliation "清华大学"
```

## 📁 项目结构

```
sci_flow/
├── __init__.py
├── __main__.py
├── cli.py              # CLI 入口
├── config.py           # 配置管理
├── literature.py       # 文献调研模块
├── zotero.py           # Zotero 同步模块
├── lark.py             # 飞书文档模块
├── python.py           # Python 数据处理模块
├── word.py             # Word 文档生成模块
└── pipeline.py         # 全流程编排模块
```

## 🛠️ 技术栈

- Python 3.10+
- Click CLI
- Pydantic
- python-docx
- requests

## ⚙️ 配置

支持通过 `.env` 文件配置：

```
ZOTERO_API_KEY=your_api_key
ZOTERO_USER_ID=your_user_id
LARK_DOC_TEMPLATE=template_path
```

## 🤝 贡献

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献流程。

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 📞 问题反馈

如有问题或建议，请在 GitHub Issues 中提交。
