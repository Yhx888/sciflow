# SciFlow 项目规则

## 项目上下文

每次开启新对话时，**必须首先读取**以下文件了解项目背景：

1. **CLAUDE.md** - 项目核心信息、技术栈、命令指南
2. **README.md** - 用户使用说明
3. **pyproject.toml** - 项目配置和依赖

## 开发规范

### 代码风格
- 使用 Black 格式化代码
- 遵循 PEP 8 规范
- 函数和模块注释使用中文

### 命令执行
- Windows 环境，使用 PowerShell 命令
- 避免使用 `&&` 串联命令（PowerShell 不支持）
- 使用绝对路径引用文件

### 测试验证
- 每次修改后运行 `sciflow --version` 验证安装
- 使用 `--mock` 参数测试各模块功能
- 清理测试数据后再提交

## 核心命令

```bash
# 安装
pip install -e .

# 验证
sciflow --version
sciflow --help

# 全流程测试
sciflow pipeline run --topic "测试主题" --author "测试" --affiliation "测试单位"
```

## 文件引用

关键文件位置：
- 核心代码: `sci_flow/`
- 配置文件: `pyproject.toml`
- 项目文档: `CLAUDE.md`, `README.md`
- 规划文档: `.trae/specs/sciflow/`

## 注意事项

1. 项目面向中文用户，输出和注释使用中文
2. 支持 Mock 模式演示，真实 API 需用户配置
3. `data/` 和 `output/` 目录运行时自动创建
4. GitHub 仓库: https://github.com/Yhx888/sciflow