"""
SciFlow 配置管理模块
使用Pydantic Settings管理应用配置，支持配置文件持久化
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .models import ApiProvider, LLMProvider, Theme


def get_user_config_dir() -> Path:
    """获取用户配置目录"""
    home = Path.home()
    config_dir = home / ".sciflow"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_default_data_dir() -> Path:
    """获取默认数据目录"""
    data_dir = get_user_config_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_default_providers() -> List[ApiProvider]:
    """获取默认的API提供商配置"""
    return [
        ApiProvider(
            name=LLMProvider.OPENAI,
            display_name="OpenAI",
            api_base="https://api.openai.com/v1",
            model="gpt-4o",
            enabled=True,
        ),
        ApiProvider(
            name=LLMProvider.ANTHROPIC,
            display_name="Anthropic",
            api_base="https://api.anthropic.com",
            model="claude-3-5-sonnet-20241022",
            enabled=False,
        ),
        ApiProvider(
            name=LLMProvider.DEEPSEEK,
            display_name="DeepSeek",
            api_base="https://api.deepseek.com/v1",
            model="deepseek-chat",
            enabled=False,
        ),
        ApiProvider(
            name=LLMProvider.ZHIPU,
            display_name="智谱AI",
            api_base="https://open.bigmodel.cn/api/paas/v4",
            model="glm-4",
            enabled=False,
        ),
        ApiProvider(
            name=LLMProvider.QWEN,
            display_name="通义千问",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            enabled=False,
        ),
        ApiProvider(
            name=LLMProvider.OLLAMA,
            display_name="Ollama (本地)",
            api_base="http://localhost:11434",
            model="llama3",
            enabled=False,
        ),
    ]


class Config(BaseModel):
    """SciFlow应用配置"""
    version: str = "1.0.0"
    active_provider: LLMProvider = LLMProvider.OPENAI
    providers: List[ApiProvider] = Field(default_factory=get_default_providers)
    theme: Theme = Theme.SYSTEM
    data_dir: Path = Field(default_factory=get_default_data_dir)
    first_run: bool = True
    language: str = "zh-CN"
    max_tokens: int = 4096
    temperature: float = 0.7
    stream_enabled: bool = True
    auto_save: bool = True
    auto_save_interval: int = 300
    recent_projects: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            Path: lambda v: str(v),
        }

    def get_active_provider(self) -> Optional[ApiProvider]:
        """获取当前激活的API提供商"""
        for provider in self.providers:
            if provider.name == self.active_provider:
                return provider
        return None

    def get_provider(self, name: LLMProvider) -> Optional[ApiProvider]:
        """根据名称获取API提供商"""
        for provider in self.providers:
            if provider.name == name:
                return provider
        return None

    def set_active_provider(self, name: LLMProvider) -> None:
        """设置当前激活的API提供商"""
        self.active_provider = name

    def update_provider(self, name: LLMProvider, **kwargs) -> None:
        """更新API提供商配置"""
        for i, provider in enumerate(self.providers):
            if provider.name == name:
                provider_data = provider.model_dump()
                provider_data.update(kwargs)
                self.providers[i] = ApiProvider(**provider_data)
                return

    def is_llm_configured(self) -> bool:
        """检查是否有可用的LLM配置"""
        active = self.get_active_provider()
        if active is None:
            return False
        return active.is_configured()

    def is_mock_mode(self) -> bool:
        """检查是否使用Mock模式（无API配置时）"""
        return not self.is_llm_configured()

    def add_recent_project(self, project_id: str) -> None:
        """添加最近项目"""
        if project_id in self.recent_projects:
            self.recent_projects.remove(project_id)
        self.recent_projects.insert(0, project_id)
        if len(self.recent_projects) > 10:
            self.recent_projects = self.recent_projects[:10]

    @classmethod
    def get_config_path(cls) -> Path:
        """获取配置文件路径"""
        return get_user_config_dir() / "config.json"

    @classmethod
    def load(cls) -> "Config":
        """从配置文件加载配置"""
        config_path = cls.get_config_path()
        if not config_path.exists():
            config = cls()
            config.save()
            return config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "data_dir" in data:
                data["data_dir"] = Path(data["data_dir"])
            if "providers" in data:
                providers = []
                for p_data in data["providers"]:
                    if "name" in p_data:
                        p_data["name"] = LLMProvider(p_data["name"])
                    providers.append(ApiProvider(**p_data))
                data["providers"] = providers
            if "active_provider" in data:
                data["active_provider"] = LLMProvider(data["active_provider"])
            if "theme" in data:
                data["theme"] = Theme(data["theme"])
            return cls(**data)
        except Exception as e:
            print(f"加载配置文件失败，使用默认配置: {e}")
            return cls()

    def save(self) -> None:
        """保存配置到文件"""
        config_path = self.get_config_path()
        data = self.model_dump()
        data["data_dir"] = str(data["data_dir"])
        for i, provider in enumerate(data["providers"]):
            data["providers"][i] = provider
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def get_database_path(self) -> Path:
        """获取数据库文件路径"""
        return get_user_config_dir() / "sciflow.db"

    def get_projects_dir(self) -> Path:
        """获取项目存储目录"""
        projects_dir = self.data_dir / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        return projects_dir

    def get_exports_dir(self) -> Path:
        """获取导出目录"""
        exports_dir = self.data_dir / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        return exports_dir

    def get_temp_dir(self) -> Path:
        """获取临时目录"""
        temp_dir = self.data_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    def complete_first_run(self) -> None:
        """完成首次运行配置"""
        self.first_run = False
        self.save()


_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取配置单例实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.load()
    return _config_instance


def reset_config() -> None:
    """重置配置（主要用于测试）"""
    global _config_instance
    _config_instance = None
