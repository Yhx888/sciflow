"""数据库模块测试：项目/对话/消息/文献 CRUD"""

from sci_flow.core.database import Database, get_database, reset_database
from sci_flow.core.models import (
    Conversation,
    Literature,
    Message,
    MessageRole,
    Project,
    ProjectStatus,
    generate_id,
)


def test_db_created_in_isolated_dir(tmp_path):
    db = Database()
    assert db.db_path.parent == tmp_path / "home" / ".sciflow"


def test_project_crud():
    db = Database()
    project = Project(topic="测试项目", description="用于测试")
    created = db.create_project(project)
    assert created.id is not None

    fetched = db.get_project(created.id)
    assert fetched.topic == "测试项目"
    assert fetched.status == ProjectStatus.DRAFT

    created.topic = "改名后的项目"
    updated = db.update_project(created)
    assert updated.topic == "改名后的项目"

    assert db.delete_project(created.id) is True
    assert db.get_project(created.id) is None
    assert db.delete_project("not-exist") is False


def test_list_projects_pagination():
    db = Database()
    for i in range(5):
        db.create_project(Project(topic=f"项目{i}"))
    projects = db.list_projects(limit=3, offset=1)
    assert len(projects) == 3
    # 列表按创建时间倒序（新项目在前）
    assert [p.topic for p in projects] == ["项目3", "项目2", "项目1"]


def test_conversation_and_messages():
    db = Database()
    project = db.create_project(Project(topic="对话测试"))
    conv = db.create_conversation(Conversation(project_id=project.id, title="研究讨论"))
    assert conv.id is not None

    msg = db.add_message(conv.id, role="user", content="帮我调研强化学习")
    assert msg.role == MessageRole.USER
    db.add_message(conv.id, role="assistant", content="好的，正在检索文献……")

    messages = db.get_messages(conv.id)
    assert len(messages) == 2
    assert messages[0].content == "帮我调研强化学习"

    convs = db.list_conversations(project_id=project.id)
    assert len(convs) == 1
    assert db.delete_conversation(conv.id) is True
    assert db.get_messages(conv.id) == []


def test_literature_crud_and_search():
    db = Database()
    lit = Literature(
        title="Attention Is All You Need",
        authors=["Vaswani", "Shazeer"],
        year=2017,
        venue="NeurIPS",
        abstract="Transformer 架构论文",
        citations=100000,
        doi="10.5555/3295222",
    )
    created = db.create_literature(lit)
    assert created.id is not None

    results = db.search_literature("attention", limit=10)
    assert len(results) == 1
    assert results[0].title == "Attention Is All You Need"

    # 无匹配查询
    assert db.search_literature("不存在的关键词xyz") == []

    # 项目关联：写入关联表后 project.literature 列表由上层管理，此处验证不报错且可移除
    project = db.create_project(Project(topic="文献项目"))
    db.add_literature_to_project(project.id, created.id)
    db.remove_literature_from_project(project.id, created.id)

    assert db.delete_literature(created.id) is True


def test_get_database_singleton():
    reset_database()
    assert get_database() is get_database()
    reset_database()
    assert get_database() is not None


def test_db_path_from_config():
    """数据库路径应来自隔离后的配置目录"""
    db = Database()
    assert str(db.db_path).endswith("sciflow.db")
    assert ".sciflow" in str(db.db_path)


def test_generate_id_unique():
    ids = {generate_id() for _ in range(1000)}
    assert len(ids) == 1000
