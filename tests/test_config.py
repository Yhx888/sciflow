"""配置模块测试"""

from pathlib import Path

from sci_flow.core.config import Config, get_config, reset_config
from sci_flow.core.models import ApiProvider, LLMProvider, Theme


def test_default_config():
    """默认配置应包含全部 6 家提供商"""
    cfg = Config()
    assert len(cfg.providers) == 6
    assert cfg.active_provider == LLMProvider.OPENAI
    assert cfg.theme == Theme.SYSTEM
    assert cfg.first_run is True
    assert cfg.temperature == 0.7


def test_default_providers_names():
    """默认提供商名称覆盖主流 LLM 服务"""
    cfg = Config()
    names = {p.name for p in cfg.providers}
    assert names == {
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.DEEPSEEK,
        LLMProvider.ZHIPU,
        LLMProvider.QWEN,
        LLMProvider.OLLAMA,
    }


def test_provider_get_set():
    cfg = Config()
    assert cfg.get_active_provider() is not None
    cfg.set_active_provider(LLMProvider.DEEPSEEK)
    assert cfg.active_provider == LLMProvider.DEEPSEEK
    assert cfg.get_provider(LLMProvider.DEEPSEEK).display_name == "DeepSeek"
    assert cfg.get_provider(LLMProvider.OLLAMA).model == "llama3"


def test_provider_update_keeps_other_fields():
    cfg = Config()
    cfg.update_provider(LLMProvider.DEEPSEEK, api_key="sk-test", model="deepseek-chat")
    provider = cfg.get_provider(LLMProvider.DEEPSEEK)
    assert provider.api_key == "sk-test"
    assert provider.model == "deepseek-chat"
    # 其他字段不受影响
    assert provider.api_base == "https://api.deepseek.com/v1"


def test_mock_mode_detection():
    cfg = Config()
    # 默认无 API Key → Mock 模式
    assert cfg.is_mock_mode() is True
    assert cfg.is_llm_configured() is False
    cfg.update_provider(cfg.active_provider, api_key="sk-real-key")
    assert cfg.is_llm_configured() is True
    assert cfg.is_mock_mode() is False


def test_recent_projects_dedup_and_cap():
    cfg = Config()
    for i in range(15):
        cfg.add_recent_project(f"p{i}")
    assert len(cfg.recent_projects) <= 10
    assert cfg.recent_projects[0] == "p14"
    # 重复添加会移到最前
    cfg.add_recent_project("p10")
    assert cfg.recent_projects[0] == "p10"
    assert cfg.recent_projects.count("p10") == 1


def test_save_load_roundtrip():
    cfg = Config()
    cfg.update_provider(LLMProvider.DEEPSEEK, api_key="sk-roundtrip")
    cfg.set_active_provider(LLMProvider.ZHIPU)
    cfg.theme = Theme.DARK
    cfg.add_recent_project("proj-1")
    cfg.save()

    loaded = Config.load()
    assert loaded.get_provider(LLMProvider.DEEPSEEK).api_key == "sk-roundtrip"
    assert loaded.active_provider == LLMProvider.ZHIPU
    assert loaded.theme == Theme.DARK
    assert loaded.recent_projects == ["proj-1"]


def test_get_config_singleton_and_reset():
    reset_config()
    first = get_config()
    second = get_config()
    assert first is second
    reset_config()
    third = get_config()
    assert third is not first


def test_data_dirs_created():
    cfg = Config()
    assert cfg.get_projects_dir().exists()
    assert cfg.get_exports_dir().exists()
    assert cfg.get_temp_dir().exists()
    assert isinstance(cfg.get_database_path(), Path)


def test_complete_first_run():
    cfg = Config()
    assert cfg.first_run is True
    cfg.complete_first_run()
    assert cfg.first_run is False
    # 持久化后再次加载也是已完成状态
    assert Config.load().first_run is False
