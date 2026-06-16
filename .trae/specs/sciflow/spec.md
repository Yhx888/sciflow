# SciFlow - Product Requirement Document

## Overview
- **Summary**: SciFlow 是一款基于 MCP 协议的科研工作流编排 CLI 工具，通过自然语言指令无缝串联文献管理（Zotero）、技术文档（飞书）、数据分析（Python）、论文撰写（Word）等工具，实现科研全流程自动化。
- **Purpose**: 解决科研实验中工具割裂、手动操作繁琐、效率低下的问题，让研究者专注于创新本身而非重复劳动。
- **Target Users**: 理工科研究生、博士、科研工作者，尤其适合机器人/AI 领域研究者。

## Goals
- 实现从文献调研到论文撰写的全流程自动化编排
- 通过 MCP/Skill 协议串联现有工具生态（Zotero、Lark、Python、Word）
- 提供自然语言接口，降低使用门槛
- 保证各环节数据格式统一，减少手动转换

## Non-Goals (Out of Scope)
- 不替代现有工具（Zotero、飞书等），而是作为编排层
- 不实现文献检索引擎，复用现有检索能力
- 不涉及底层算法实现，专注于工作流编排

## Background & Context
- 用户现有工作流：Trae Skill 文献调研 → Zotero 存储 → 飞书技术文档 → Python 数据处理 → Word 论文撰写
- 各工具间切换需要手动操作，数据格式不统一
- MCP 协议为工具串联提供标准化接口

## Functional Requirements
- **FR-1**: 通过自然语言指令进行文献调研，并自动同步至 Zotero
- **FR-2**: 基于 Zotero 文献库自动生成飞书技术文档
- **FR-3**: 读取技术文档，生成实验方案建议
- **FR-4**: 执行 Python 数据处理脚本，生成图表
- **FR-5**: 将处理结果自动填充至 Word 文档模板
- **FR-6**: 提供命令行接口，支持各环节独立调用和全流程编排

## Non-Functional Requirements
- **NFR-1**: CLI 命令响应时间 < 3 秒（不含外部工具执行时间）
- **NFR-2**: 支持 Windows/macOS/Linux 跨平台
- **NFR-3**: 错误处理友好，提供清晰的错误信息和恢复建议
- **NFR-4**: 支持配置文件自定义工具路径和参数

## Constraints
- **Technical**: Python 3.10+, Click CLI, Pydantic, python-docx
- **Dependencies**: Zotero API, Lark CLI, Python 环境
- **Business**: 开源免费，非商业化

## Assumptions
- 用户已安装并配置 Zotero，启用 BetterBibTeX 插件
- 用户已安装 Lark CLI 并完成认证
- 用户已配置 Python 环境和常用数据分析库

## Acceptance Criteria

### AC-1: 文献调研命令
- **Given**: 用户执行 `sciflow literature search "ROS2 navigation"`
- **When**: 系统调用外部检索能力并解析结果
- **Then**: 返回文献列表，并提示同步至 Zotero
- **Verification**: `programmatic`

### AC-2: Zotero 同步命令
- **Given**: 用户执行 `sciflow zotero sync --title "论文标题"`
- **When**: 系统调用 Zotero API
- **Then**: 文献成功添加到 Zotero 库
- **Verification**: `programmatic`

### AC-3: 飞书文档生成命令
- **Given**: 用户执行 `sciflow lark create --title "技术调研"`
- **When**: 系统调用 Lark CLI
- **Then**: 飞书云文档创建成功并包含文献信息
- **Verification**: `programmatic`

### AC-4: Python 数据处理命令
- **Given**: 用户执行 `sciflow python run --script data_analysis.py`
- **When**: 系统执行 Python 脚本
- **Then**: 脚本成功执行，生成输出文件
- **Verification**: `programmatic`

### AC-5: Word 文档生成命令
- **Given**: 用户执行 `sciflow word create --template template.docx`
- **When**: 系统调用 python-docx
- **Then**: Word 文档创建成功，内容已填充
- **Verification**: `programmatic`

### AC-6: 全流程编排命令
- **Given**: 用户执行 `sciflow pipeline run --topic "ROS2 navigation"`
- **When**: 系统依次执行各环节
- **Then**: 完成文献调研→Zotero同步→文档生成→数据处理→Word导出
- **Verification**: `human-judgment`

## Open Questions
- [ ] Zotero API 认证方式（API key vs OAuth）
- [ ] 飞书文档模板格式约定
- [ ] Python 脚本执行环境隔离方案
