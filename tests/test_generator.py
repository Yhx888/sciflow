"""成果生成器测试：大纲、实验方案、报告、Word、ZIP 打包"""

import zipfile

import pytest

from sci_flow.core.database import Database
from sci_flow.core.generator import ResultGenerator
from sci_flow.core.literature import LiteratureManager
from sci_flow.core.models import Project


@pytest.fixture
def generator():
    db = Database()
    return ResultGenerator(literature_manager=LiteratureManager(db=db))


@pytest.fixture
def literature(generator):
    return generator.literature_manager.generate_mock_literature("具身智能", count=6)


def test_generate_outline(generator, literature):
    outline = generator.generate_outline("具身智能抓取", literature)
    assert "# " in outline
    for section in ["摘要", "引言", "文献综述", "结论"]:
        assert section in outline


def test_generate_experiment_design(generator, literature):
    design = generator.generate_experiment_design("端到端机器人控制", literature)
    assert design["title"]
    assert "hypothesis" in design
    assert design["metrics"]
    assert design["controls"]
    assert len(design["methodology"]) > 0


def test_generate_report(generator, literature):
    report = generator.generate_report(
        topic="机器人操作学习",
        literature=literature,
        outline="# 大纲\n\n## 引言",
    )
    assert "机器人操作学习" in report
    assert "#" in report  # Markdown 标题
    assert "参考文献" in report


def test_generate_bibtex(generator, literature):
    bibtex = generator.generate_bibtex(literature)
    assert bibtex.count("@article") == len(literature)


def test_generate_word(generator, literature):
    """Word 文档应生成有效 docx 文件（内部是 zip 格式）"""
    word_path = generator.generate_word(
        report_content="# 测试\n\n这是内容。",
        metadata={"title": "测试报告", "author": "测试"},
    )
    assert word_path.endswith(".docx")
    from pathlib import Path

    assert Path(word_path).exists()
    with open(word_path, "rb") as f:
        assert f.read(2) == b"PK"  # ZIP 魔数


def test_generate_project_bundle(literature):
    """项目 ZIP 包应包含报告、BibTeX、大纲等成果文件"""
    db = Database()
    gen = ResultGenerator(literature_manager=LiteratureManager(db=db))
    project = db.create_project(
        Project(
            topic="多模态大模型",
            author="测试",
            affiliation="测试大学",
            outline="# 大纲\n\n正文",
            report="# 报告\n\n正文",
        )
    )
    for lit in literature:
        db.create_literature(lit)
        db.add_literature_to_project(project.id, lit.id)

    bundle = gen.generate_project_bundle(project)
    assert bundle[:2] == b"PK"
    import io

    with zipfile.ZipFile(io.BytesIO(bundle)) as zf:
        names = zf.namelist()
        assert any("report" in n and n.endswith(".md") for n in names)
        assert any(n.endswith(".bib") for n in names)
        assert any("outline" in n.lower() for n in names)


def test_generate_project_bundle_without_literature():
    """无文献时打包不应报错"""
    db = Database()
    gen = ResultGenerator(literature_manager=LiteratureManager(db=db))
    project = db.create_project(Project(topic="空项目"))
    bundle = gen.generate_project_bundle(project)
    assert bundle[:2] == b"PK"
