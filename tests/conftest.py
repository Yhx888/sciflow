"""
SciFlow 测试公共夹具：隔离用户配置目录，避免污染真实 ~/.sciflow
"""

import sys
from pathlib import Path

import pytest

# 确保项目根目录可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def isolated_config_dir(tmp_path, monkeypatch):
    """每个测试使用独立的临时配置目录，并重置所有单例"""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))

    yield fake_home

    # 重置单例，防止测试间污染
    from sci_flow.core import config as config_mod
    from sci_flow.core import database as db_mod
    from sci_flow.core import generator as gen_mod
    from sci_flow.core import literature as lit_mod
    from sci_flow.core import workflow as wf_mod
    from sci_flow.llm import client as llm_mod

    config_mod.reset_config()
    db_mod.reset_database()
    lit_mod.reset_literature_manager()
    gen_mod.reset_result_generator()
    wf_mod.reset_workflow_engine()
    llm_mod.reset_llm_client()
