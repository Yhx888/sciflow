"""文献模块测试：Mock 生成、引用格式、矩阵分析、真实 API 降级"""

import asyncio

import pytest

from sci_flow.core.database import Database
from sci_flow.core.literature import CitationFormatter, LiteratureManager
from sci_flow.core.models import Discipline, Literature


@pytest.fixture
def manager(tmp_path):
    return LiteratureManager(db=Database())


def test_mock_literature_generation(manager):
    """Mock 文献应生成合理数量的真实感条目"""
    lits = manager.generate_mock_literature("大语言模型推理优化", count=10)
    assert len(lits) == 10
    for lit in lits:
        assert lit.title
        assert lit.authors
        assert lit.year and 2017 <= lit.year <= 2026
        assert lit.venue
        assert lit.abstract
        assert lit.doi
        assert lit.bibtex


def test_mock_literature_sorted_by_citations(manager):
    lits = manager.generate_mock_literature("机器人控制", count=12)
    citations = [l.citations for l in lits]
    assert citations == sorted(citations, reverse=True)


def test_mock_literature_disciplines(manager):
    for discipline in Discipline:
        lits = manager.generate_mock_literature("测试主题", count=5, discipline=discipline)
        assert len(lits) == 5


def test_citation_bibtex_format():
    lit = Literature(
        title="Deep Learning",
        authors=["LeCun", "Bengio", "Hinton"],
        year=2015,
        venue="Nature",
        volume="521",
        pages="436-444",
    )
    bibtex = CitationFormatter.generate_bibtex(lit)
    assert bibtex.startswith("@article{")
    assert "Deep Learning" in bibtex
    assert "LeCun" in bibtex
    assert "2015" in bibtex
    assert "Nature" in bibtex


def test_citation_gbt7714_format():
    lit = Literature(
        title="强化学习综述",
        authors=["张三", "李四"],
        year=2020,
        venue="计算机学报",
    )
    gbt = CitationFormatter.generate_gbt7714(lit)
    assert "张三" in gbt
    assert "2020" in gbt


def test_citation_apa_format():
    lit = Literature(title="RLHF", authors=["Ouyang"], year=2022, venue="NeurIPS")
    apa = CitationFormatter.generate_apa(lit)
    assert "Ouyang" in apa
    assert "(2022)" in apa


def test_generate_all_citation_styles(manager):
    lits = manager.generate_mock_literature("AI Agent", count=5)
    assert "@article" in manager.generate_bibtex(lits)
    assert "[" in manager.generate_gbt7714(lits)
    assert "(20" in manager.generate_apa(lits)


def test_literature_matrix(manager):
    lits = manager.generate_mock_literature("多模态学习", count=6)
    matrix = manager.generate_literature_matrix(lits)
    assert "文献" in matrix and "方法" in matrix and "年份" in matrix


def test_trend_summary(manager):
    lits = manager.generate_mock_literature("具身智能", count=8)
    summary = manager.generate_trend_summary(lits)
    assert "篇" in summary or "趋势" in summary


def test_search_mock_mode(manager):
    """Mock 模式下 search 应返回生成的模拟文献"""
    lits = asyncio.run(manager.search("量子计算", limit=8, use_mock=True))
    assert len(lits) == 8


def test_search_mock_fallback_on_network_error(manager, monkeypatch):
    """真实 API 失败时应自动降级为 Mock"""

    async def fake_fail(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(manager, "_search_semantic_scholar", fake_fail)
    monkeypatch.setattr(manager, "_search_arxiv", fake_fail)
    lits = asyncio.run(manager.search("网络故障主题", limit=5, use_mock=False))
    assert len(lits) == 5


def test_search_arxiv_source(manager, monkeypatch):
    """指定 arxiv 数据源时只走 arXiv；失败时降级 Mock"""

    async def fake_success(topic, limit):
        return manager.generate_mock_literature(topic, limit)

    async def fake_fail(*args, **kwargs):
        raise RuntimeError("arxiv down")

    monkeypatch.setattr(manager, "_search_arxiv", fake_success)
    lits = asyncio.run(manager.search("arxiv主题", limit=3, use_mock=False, source="arxiv"))
    assert len(lits) == 3

    monkeypatch.setattr(manager, "_search_arxiv", fake_fail)
    lits = asyncio.run(manager.search("arxiv失败", limit=4, use_mock=False, source="arxiv"))
    assert len(lits) == 4  # 降级 Mock


def test_search_arxiv_parsing(manager, monkeypatch):
    """arXiv Atom XML 解析应正确提取标题/作者/年份/摘要"""
    xml_sample = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2301.00001v1</id>
        <title>  Attention Is All You Need  </title>
        <published>2023-01-01T00:00:00Z</published>
        <author><name>Vaswani</name></author>
        <author><name>Shazeer</name></author>
        <summary>  A transformer architecture paper.  </summary>
      </entry>
    </feed>"""

    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return self._data

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=15: FakeResponse(xml_sample))
    lits = asyncio.run(manager._search_arxiv("transformer", 5))
    assert len(lits) == 1
    assert lits[0].title == "Attention Is All You Need"
    assert lits[0].authors == ["Vaswani", "Shazeer"]
    assert lits[0].year == 2023
    assert lits[0].venue == "arXiv"
    assert lits[0].url == "http://arxiv.org/abs/2301.00001v1"
    assert lits[0].bibtex is not None


def test_save_and_get_literature(manager):
    lits = manager.generate_mock_literature("保存测试", count=3)
    saved = manager.save_literature(lits[0])
    assert manager.get_literature(saved.id) is not None


def test_project_literature_binding(manager):
    from sci_flow.core.models import Project

    project = manager.db.create_project(Project(topic="绑定测试"))
    lits = manager.generate_mock_literature("绑定", count=2)
    for lit in lits:
        manager.save_literature(lit)
        manager.add_to_project(project.id, lit.id)
    bound = manager.get_project_literature(project.id)
    assert len(bound) == 2
