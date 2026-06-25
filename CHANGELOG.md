# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-25

### Added - 重大新特性
- 🖥️ **全新桌面应用**：基于pywebview的原生桌面体验
- 🌐 **Web UI重写**：ChatGPT/苹果级精致界面设计
- ⚡ **FastAPI后端**：高性能异步API服务器，支持SSE流式响应
- 🔌 **真实LLM接入**：支持OpenAI/Anthropic/DeepSeek/智谱/通义千问/Ollama
- 🔧 **API配置界面**：图形化配置LLM提供商、API Key、模型
- 💾 **数据持久化**：SQLite本地数据库
- 📦 **模块化架构**：core/llm/server/desktop/web清晰分层
- 🎯 **三模式使用**：桌面App / Web界面 / CLI命令行
- 📥 **成果下载**：ZIP打包导出Markdown/Word/BibTeX
- 🌓 **深浅主题切换**：精致的主题系统

### Changed
- 🎨 整体UI重新设计，极简苹果风格
- 🏗️ 项目架构从单体CLI重构为前后端分离
- ⚡ LLM客户端自研，移除litellm依赖（更轻量）
- 📝 CLI命令重构，新增app/config/project/chat命令组

### Fixed
- 🐛 修复pydantic-settings依赖
- 🐛 修复Windows路径兼容性

## [0.2.0] - 2026-06-25

### Added
- ✨ 全新Web Demo：单文件HTML应用，开箱即用
- 💬 AI对话式交互界面，支持自然语言输入
- 🎨 可视化工作流画布：8个节点+动画流转效果
- 📚 智能文献检索：多领域模板，生成8-12篇真实感文献
- 📊 文献矩阵分析：多维度对比表格
- 🧠 研究思路脑图：可交互展开/折叠
- 📋 论文大纲生成：标准学术结构，支持编辑
- 🔬 实验方案建议：完整实验设计卡片
- 📦 成果打包下载：ZIP包含Markdown、BibTeX、大纲、实验方案
- 🌓 深色/浅色主题切换
- 🎬 自动演示模式
- 🎉 工作流完成庆祝动画
- 📱 移动端响应式适配
- 🆕 `sciflow demo` 命令：启动本地Web服务器预览Demo
- 🆕 `sciflow guide` 命令：新手引导
- 🌈 全新sciflow_creative.html展示页面

### Changed
- 🔧 pipeline模块扩展到8步，输出更丰富真实
- 📝 literature模块Mock数据动态生成
- 🎨 整体UI升级科技感设计

### Fixed
- 🐛 添加缺失的pydantic-settings依赖

## [0.1.0] - 2026-06-20

### Added
- 📚 文献调研模块（支持 Mock 模式检索）
- 📦 Zotero 同步模块（支持文献添加和查询）
- 📝 飞书文档模块（支持技术调研文档生成）
- 🐍 Python 数据处理模块（支持脚本执行）
- 📄 Word 文档生成模块（支持论文初稿生成）
- 🔄 全流程编排模块（支持一键执行完整工作流）
- CLI 命令行框架（Click）
- Pydantic Settings 配置管理
