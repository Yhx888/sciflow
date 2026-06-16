# Contributing to SciFlow

欢迎贡献代码！以下是参与项目的指南。

## 环境要求

- Python 3.10+
- Git

## 开发流程

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature-name`
3. 提交代码：`git commit -m "feat: add your feature"`
4. 推送到远程：`git push origin feature/your-feature-name`
5. 创建 Pull Request

## 代码风格

- 使用 Black 格式化代码
- 使用 Flake8 检查代码
- 保持代码简洁，遵循 PEP 8

## 提交规范

请使用 Conventional Commits：

- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档更新
- `refactor`: 代码重构
- `test`: 测试更新
- `chore`: 构建/工具更新

## 测试

```bash
# 运行测试
python -m pytest

# 检查代码风格
flake8 sci_flow/
black sci_flow/
```

## 问题反馈

在 GitHub Issues 中提交问题，请提供：
- 问题描述
- 复现步骤
- 预期结果
- 实际结果
- 环境信息

谢谢参与！🚀
