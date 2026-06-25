"""
LLM客户端模块 - 支持多种LLM提供商的统一接口
支持OpenAI兼容API格式，可配置不同提供商
"""

import json
import asyncio
from typing import AsyncGenerator, List, Dict, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """支持的LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    QWEN = "qwen"
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass
class ProviderConfig:
    """提供商配置"""
    name: str
    display_name: str
    api_base: str
    model: str
    api_key_env: Optional[str] = None


PROVIDER_CONFIGS: Dict[str, ProviderConfig] = {
    LLMProvider.OPENAI: ProviderConfig(
        name="openai",
        display_name="OpenAI",
        api_base="https://api.openai.com/v1",
        model="gpt-4o-mini",
    ),
    LLMProvider.ANTHROPIC: ProviderConfig(
        name="anthropic",
        display_name="Anthropic",
        api_base="https://api.anthropic.com/v1",
        model="claude-3-haiku-20240307",
    ),
    LLMProvider.DEEPSEEK: ProviderConfig(
        name="deepseek",
        display_name="DeepSeek",
        api_base="https://api.deepseek.com/v1",
        model="deepseek-chat",
    ),
    LLMProvider.ZHIPU: ProviderConfig(
        name="zhipu",
        display_name="智谱AI",
        api_base="https://open.bigmodel.cn/api/paas/v4",
        model="glm-4-flash",
    ),
    LLMProvider.QWEN: ProviderConfig(
        name="qwen",
        display_name="通义千问",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-turbo",
    ),
    LLMProvider.OLLAMA: ProviderConfig(
        name="ollama",
        display_name="Ollama (本地)",
        api_base="http://localhost:11434/v1",
        model="llama3",
    ),
}


SYSTEM_PROMPT = """你是SciFlow，一位专业的AI科研助手。你擅长：
1. 文献调研：帮助用户搜索、分析、整理学术文献
2. 研究思路：协助用户梳理研究方向、提出创新点
3. 论文写作：生成论文大纲、协助撰写各章节内容
4. 实验设计：帮助设计实验方案、选择评测指标
5. 数据分析：指导数据分析方法和可视化

请用中文回答，风格专业、简洁、有深度。当用户提出科研相关问题时，给出有见地的分析和建议。
如果涉及文献引用，请标注[1][2]等引用标记。"""


class LLMClient:
    """LLM客户端 - 统一接口支持多种提供商"""

    def __init__(
        self,
        config_or_provider: Any = None,
        api_key: str = "",
        api_base: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = "mock"
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.use_mock = True

        if config_or_provider is not None:
            if isinstance(config_or_provider, str):
                self.provider = config_or_provider
                self.api_base = api_base or self._get_default_api_base(self.provider)
                self.model = model or self._get_default_model(self.provider)
                self.use_mock = not api_key or self.provider == "mock"
            elif hasattr(config_or_provider, 'active_provider'):
                self._init_from_config(config_or_provider)
            else:
                self.provider = "mock"
                self.use_mock = True
        else:
            self.provider = "mock"
            self.use_mock = True

    def _init_from_config(self, config: Any) -> None:
        """从Config对象初始化"""
        active_provider = config.active_provider
        if hasattr(active_provider, 'value'):
            provider_name = active_provider.value
        else:
            provider_name = str(active_provider)
        
        self.provider = provider_name
        provider_config = config.get_active_provider()
        
        if provider_config:
            self.api_key = getattr(provider_config, 'api_key', '') or ""
            self.api_base = getattr(provider_config, 'api_base', None) or self._get_default_api_base(self.provider)
            self.model = getattr(provider_config, 'model', None) or self._get_default_model(self.provider)
            is_configured_method = getattr(provider_config, 'is_configured', None)
            if callable(is_configured_method):
                self.use_mock = not is_configured_method()
            else:
                self.use_mock = not self.api_key
        else:
            self.use_mock = True

    def _get_default_api_base(self, provider: str) -> str:
        """获取默认API地址"""
        config = PROVIDER_CONFIGS.get(provider)
        if config:
            return config.api_base
        return "https://api.openai.com/v1"

    def _get_default_model(self, provider: str) -> str:
        """获取默认模型"""
        config = PROVIDER_CONFIGS.get(provider)
        if config:
            return config.model
        return "gpt-4o-mini"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs,
    ) -> AsyncGenerator[str, None] | str:
        """
        聊天接口

        Args:
            messages: 消息列表，格式 [{"role": "user/assistant/system", "content": "..."}]
            stream: 是否流式输出
            **kwargs: 其他参数（temperature, max_tokens等）

        Returns:
            流式模式返回AsyncGenerator，非流式返回完整字符串
        """
        if self.use_mock:
            if stream:
                return self._mock_stream_chat(messages)
            else:
                return await self._mock_chat(messages)

        if stream:
            return self._stream_chat(messages, **kwargs)
        else:
            return await self._non_stream_chat(messages, **kwargs)

    async def achat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs,
    ) -> Union[AsyncGenerator[str, None], str]:
        """
        异步聊天接口（chat方法的别名，保持API兼容）

        Args:
            messages: 消息列表
            stream: 是否流式输出
            **kwargs: 其他参数

        Returns:
            流式模式返回AsyncGenerator，非流式返回完整字符串
        """
        result = self.chat(messages, stream=stream, **kwargs)
        if stream:
            return result
        else:
            return await result

    async def achat_with_system_prompt(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs,
    ) -> str:
        """
        使用系统提示词进行聊天

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            **kwargs: 其他参数

        Returns:
            完整响应字符串
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.chat(messages, stream=False, **kwargs)

    async def _non_stream_chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """非流式聊天"""
        import httpx

        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                return f"⚠️ API调用失败: {str(e)}\n\n请检查您的API配置是否正确，或使用Mock模式体验功能。"

    async def _stream_chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        import httpx

        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if data.get("choices") and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                yield f"\n\n⚠️ API调用失败: {str(e)}\n请检查API配置或使用Mock模式。"

    async def _mock_chat(self, messages: List[Dict[str, str]]) -> str:
        """Mock模式聊天 - 生成真实感的响应"""
        user_msg = messages[-1]["content"] if messages else ""

        responses = self._generate_mock_response(user_msg)
        return responses

    async def _mock_stream_chat(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Mock模式流式聊天"""
        response = await self._mock_chat(messages)
        for char in response:
            yield char
            await asyncio.sleep(0.01)

    def _generate_mock_response(self, user_msg: str) -> str:
        """根据用户输入生成Mock响应"""
        msg_lower = user_msg.lower()

        if any(kw in msg_lower for kw in ["文献", "搜索", "检索", "paper", "literature"]):
            return self._mock_literature_response(user_msg)
        elif any(kw in msg_lower for kw in ["大纲", "outline", "写作", "论文结构"]):
            return self._mock_outline_response(user_msg)
        elif any(kw in msg_lower for kw in ["实验", "experiment", "设计", "评估"]):
            return self._mock_experiment_response(user_msg)
        elif any(kw in msg_lower for kw in ["趋势", "trend", "热点", "方向"]):
            return self._mock_trend_response(user_msg)
        elif any(kw in msg_lower for kw in ["调研", "survey", "综述", "了解"]):
            return self._mock_survey_response(user_msg)
        else:
            return self._mock_general_response(user_msg)

    def _mock_literature_response(self, topic: str) -> str:
        return f"""关于「{topic}」的文献调研，我为你整理了以下关键信息：

## 📚 核心文献推荐

根据检索，该领域近年的代表性工作包括：

**1. 奠基性工作**
- 早期研究者提出了基础框架，为后续发展奠定了理论基础
- 主要贡献在于问题形式化和初步解决方案

**2. 近期突破**
- 2024年以来，深度学习方法带来了显著性能提升
- 代表性模型在多个基准测试上取得SOTA结果

**3. 前沿方向**
- 当前研究热点集中在效率优化和多模态扩展
- 开源社区贡献了多个高质量实现

## 🔍 检索建议

建议你可以从以下关键词组合进行更精确的检索：
- `{topic} + survey` 找综述论文
- `{topic} + benchmark` 找评测数据集
- `{topic} + transformer/deep learning` 找最新方法

需要我帮你：
1. 生成具体的文献列表？
2. 做文献矩阵对比分析？
3. 梳理研究时间线？"""

    def _mock_outline_response(self, topic: str) -> str:
        return f"""我为你整理了「{topic}」的标准学术论文大纲：

## 📋 论文大纲

### 摘要 (Abstract)
- 研究背景与问题（1-2句）
- 现有方法局限性（1句）
- 本文核心方法/贡献（2-3句）
- 主要实验结果（1-2句）
- 结论与意义（1句）

### 1. 引言 (Introduction)
- 1.1 研究背景与意义
- 1.2 问题定义与挑战
- 1.3 现有方法局限性分析
- 1.4 本文主要贡献（3-4点）
- 1.5 论文组织结构

### 2. 相关工作 (Related Work)
- 2.1 基础理论与背景知识
- 2.2 传统方法回顾
- 2.3 深度学习方法
- 2.4 与本文方法的对比分析

### 3. 方法 (Methodology)
- 3.1 问题形式化
- 3.2 整体框架设计
- 3.3 核心算法/模型
  - 3.3.1 模块A设计
  - 3.3.2 模块B设计
- 3.4 训练/优化策略
- 3.5 理论分析（可选）

### 4. 实验 (Experiments)
- 4.1 实验设置
  - 4.1.1 数据集
  - 4.1.2 评价指标
  - 4.1.3 实现细节
- 4.2 主实验结果
- 4.3 消融实验
- 4.4 可视化分析
- 4.5 案例分析

### 5. 讨论 (Discussion)
- 5.1 方法局限性分析
- 5.2 伦理与社会影响
- 5.3 未来工作方向

### 6. 结论 (Conclusion)

### 参考文献 (References)

需要我展开某个章节的具体内容吗？"""

    def _mock_experiment_response(self, topic: str) -> str:
        return f"""针对「{topic}」，我建议以下实验设计方案：

## 🔬 实验设计方案

### 基准模型 (Baselines)
- **经典方法**：选择2-3个传统方法作为基准
- **近期SOTA**：选择2-3个最新的代表性模型
- **消融变体**：设计3-4个模型变体验证各模块贡献

### 评测数据集
- **通用基准**：选择领域内标准数据集
- **自建数据集**：如需验证特定场景，建议构建小规模评测集
- **数据规模**：建议训练集/验证集/测试集比例 7:1:2

### 评价指标
| 指标类型 | 具体指标 | 说明 |
|---------|---------|------|
| 效果指标 | Accuracy/F1/BLEU等 | 根据任务选择主要指标 |
| 效率指标 | 推理速度、显存占用 | 实际部署必须关注 |
| 鲁棒性 | 扰动测试、OOD测试 | 验证泛化能力 |

### 硬件配置建议
- **开发阶段**：RTX 4090 (24GB) 或 A100 (40GB)
- **大规模实验**：建议使用8×A100集群
- **消融实验**：单卡即可完成

### 关键实验清单
1. ✅ 主结果对比表（和SOTA比）
2. ✅ 消融实验表（每个模块的贡献）
3. ✅ 超参数敏感性分析
4. ✅ 效率对比（速度/显存）
5. ✅ 可视化分析
6. ✅ 错误案例分析

需要我详细展开某个部分吗？"""

    def _mock_trend_response(self, topic: str) -> str:
        return f"""关于「{topic}」领域的研究趋势分析：

## 📈 研究趋势总结

### 技术演进路线
```
2020年以前 → 传统方法主导，基于规则和统计
2020-2022  → Transformer架构引入，预训练范式兴起
2023年     → 大模型时代，端到端方法成为主流
2024年至今 → 高效推理、多模态、Agent化是热点
```

### 当前热点方向 🔥
1. **效率优化**：模型量化、剪枝、蒸馏、投机解码
2. **长上下文**：扩展上下文窗口至100K+ tokens
3. **多模态融合**：文本+图像+代码+结构化数据
4. **Agent框架**：工具使用、规划、记忆、自主决策
5. **可信AI**：可解释性、安全性、对齐研究

### 主要挑战 ⚠️
- 计算成本过高，中小团队难以复现
- 评测标准不统一，结果可比性差
- 理论解释薄弱，偏经验主义
- 落地应用存在安全和伦理风险

### 推荐投稿方向
- **顶会**：NeurIPS, ICML, ICLR, ACL, CVPR（根据领域选择）
- **期刊**：Nature子刊, JMLR, TPAMI等
- 建议关注 workshop 和挑战赛道"""

    def _mock_survey_response(self, topic: str) -> str:
        return f"""好的！让我为你梳理「{topic}」的整体研究图景：

## 🗺️ {topic} - 研究全景

### 一句话概括
这是一个快速发展的研究方向，旨在解决传统方法在复杂场景下的局限性，近年来受到学术界和工业界的广泛关注。

### 核心问题
该领域主要解决以下关键问题：
1. 如何有效建模复杂依赖关系？
2. 如何提升计算和数据效率？
3. 如何保证输出的可靠性和可控性？
4. 如何实现跨领域泛化？

### 方法分类

| 方法类别 | 代表工作 | 优点 | 缺点 |
|---------|---------|------|------|
| 基于规则 | 早期系统 | 可解释、可控 | 泛化差、维护成本高 |
| 统计学习 | 经典ML方法 | 理论成熟 | 特征工程依赖强 |
| 深度学习 | Transformer系列 | 端到端、性能强 | 数据/算力需求大 |
| 大模型方法 | GPT/LLM for X | 少样本/零样本 | 成本高、可控性弱 |

### 应用场景
- 📚 学术研究：论文写作、文献分析、实验设计
- 🏢 工业界：智能客服、内容生成、决策支持
- 🔬 交叉领域：生物信息、材料科学、医疗健康

### 入门建议
1. **先读综述**：找近2年的Survey论文建立全局认知
2. **复现经典**：选1-2篇代表性工作动手复现
3. **关注开源**：跟踪GitHub热门项目
4. **动手实践**：在小数据集上验证想法

需要我深入哪个方面？"""

    def _mock_general_response(self, topic: str) -> str:
        return f"""你好！我是SciFlow，你的AI科研助手 🧪

关于「{topic}」，我可以帮你做很多事情：

## 🛠️ 我能帮你做什么？

### 📚 文献调研
- 搜索相关领域的学术论文
- 整理文献综述和研究趋势
- 生成文献矩阵对比表
- 导出BibTeX/GB/T引用格式

### 💡 研究辅助
- 梳理研究思路和创新点
- 分析相关工作的优缺点
- 提供研究方向建议
- 协助设计技术方案

### ✍️ 论文写作
- 生成论文大纲
- 协助撰写各章节内容
- 润色和优化表达
- 生成图表建议

### 🔬 实验支持
- 设计实验方案
- 推荐基准模型和数据集
- 建议评价指标
- 分析实验结果

### 📊 数据分析
- 生成数据分析脚本
- 建议可视化方案
- 统计方法选择建议

---

**💡 提示**：你可以点击左侧「新建项目」开始一个完整的科研工作流，或者在对话框中告诉我你具体想做什么。

如果你配置了自己的API Key（OpenAI/DeepSeek/智谱等），我会使用真实的大模型为你服务；未配置时我将使用Mock模式演示功能。"""


# 全局客户端实例
_client: Optional[LLMClient] = None


def get_llm_client(
    config_or_provider: Any = None,
    api_key: str = "",
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMClient:
    """获取LLM客户端单例"""
    global _client
    if _client is None:
        _client = LLMClient(config_or_provider, api_key, api_base, model)
    return _client


def reset_llm_client():
    """重置LLM客户端（配置变更时调用）"""
    global _client
    _client = None
