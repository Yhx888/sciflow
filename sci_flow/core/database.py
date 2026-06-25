"""
SciFlow 数据持久化模块
使用SQLite进行数据存储，提供Repository模式接口
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

from .config import get_config
from .models import (
    Conversation,
    Discipline,
    ExperimentDesign,
    Literature,
    Message,
    MessageRole,
    Project,
    ProjectStatus,
    WorkflowStatus,
    WorkflowStep,
    generate_id,
)

T = TypeVar("T")


class Database:
    """SQLite数据库管理类"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = self._get_default_db_path()
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize()

    def _get_default_db_path(self) -> Path:
        """获取默认数据库路径，如果用户目录不可用则回退到临时目录"""
        import tempfile
        paths_to_try = []

        try:
            from .config import get_user_config_dir
            config_dir = get_user_config_dir()
            paths_to_try.append(config_dir / "sciflow.db")
        except Exception:
            pass

        cwd = Path.cwd()
        paths_to_try.append(cwd / ".sciflow" / "sciflow.db")

        temp_dir = Path(tempfile.gettempdir())
        paths_to_try.append(temp_dir / "sciflow" / "sciflow.db")

        for path in paths_to_try:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                test_conn = sqlite3.connect(str(path))
                test_conn.close()
                return path
            except Exception:
                continue

        return cwd / "sciflow.db"

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _initialize(self) -> None:
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                description TEXT DEFAULT '',
                author TEXT DEFAULT '',
                affiliation TEXT DEFAULT '',
                discipline TEXT DEFAULT 'other',
                status TEXT DEFAULT 'draft',
                conversations TEXT DEFAULT '[]',
                literature TEXT DEFAULT '[]',
                outline TEXT,
                experiments TEXT,
                report TEXT,
                workflow_steps TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '新对话',
                project_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS literature (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT DEFAULT '[]',
                year INTEGER,
                venue TEXT,
                abstract TEXT,
                citations INTEGER DEFAULT 0,
                url TEXT,
                doi TEXT,
                tags TEXT DEFAULT '[]',
                added_at TEXT NOT NULL,
                bibtex TEXT,
                notes TEXT,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS project_literature (
                project_id TEXT NOT NULL,
                literature_id TEXT NOT NULL,
                added_at TEXT NOT NULL,
                PRIMARY KEY (project_id, literature_id),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (literature_id) REFERENCES literature(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_project ON conversations(project_id);
            CREATE INDEX IF NOT EXISTS idx_literature_title ON literature(title);
            CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
            CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at DESC);
            """
        )
        conn.commit()

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        return {key: row[key] for key in row.keys()}

    def _parse_datetime(self, value: str) -> datetime:
        """解析日期时间字符串"""
        return datetime.fromisoformat(value)

    def _format_datetime(self, dt: datetime) -> str:
        """格式化日期时间"""
        return dt.isoformat()

    def _serialize_json(self, obj: Any) -> str:
        """序列化为JSON字符串"""
        return json.dumps(obj, ensure_ascii=False, default=str)

    def _deserialize_json(self, value: Optional[str]) -> Any:
        """反序列化JSON字符串"""
        if value is None or value == "":
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    # ==================== 项目操作 ====================

    def create_project(self, project: Project) -> Project:
        """创建项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (
                id, topic, description, author, affiliation, discipline, status,
                conversations, literature, outline, experiments, report,
                workflow_steps, tags, created_at, updated_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project.id,
                project.topic,
                project.description,
                project.author,
                project.affiliation,
                project.discipline.value,
                project.status.value,
                self._serialize_json(project.conversations),
                self._serialize_json(project.literature),
                project.outline,
                self._serialize_json(project.experiments.model_dump() if project.experiments else None),
                project.report,
                self._serialize_json([step.model_dump() for step in project.workflow_steps]),
                self._serialize_json(project.tags),
                self._format_datetime(project.created_at),
                self._format_datetime(project.updated_at),
                self._serialize_json(project.metadata),
            ),
        )
        conn.commit()
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_project(row)

    def list_projects(self, limit: int = 50, offset: int = 0) -> List[Project]:
        """列出项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cursor.fetchall()
        return [self._row_to_project(row) for row in rows]

    def update_project(self, project: Project) -> Project:
        """更新项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        project.updated_at = datetime.now()
        cursor.execute(
            """
            UPDATE projects SET
                topic = ?, description = ?, author = ?, affiliation = ?,
                discipline = ?, status = ?, conversations = ?, literature = ?,
                outline = ?, experiments = ?, report = ?, workflow_steps = ?,
                tags = ?, updated_at = ?, metadata = ?
            WHERE id = ?
            """,
            (
                project.topic,
                project.description,
                project.author,
                project.affiliation,
                project.discipline.value,
                project.status.value,
                self._serialize_json(project.conversations),
                self._serialize_json(project.literature),
                project.outline,
                self._serialize_json(project.experiments.model_dump() if project.experiments else None),
                project.report,
                self._serialize_json([step.model_dump() for step in project.workflow_steps]),
                self._serialize_json(project.tags),
                self._format_datetime(project.updated_at),
                self._serialize_json(project.metadata),
                project.id,
            ),
        )
        conn.commit()
        return project

    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        """将行数据转换为Project对象"""
        data = self._row_to_dict(row)
        data["discipline"] = Discipline(data["discipline"])
        data["status"] = ProjectStatus(data["status"])
        data["conversations"] = self._deserialize_json(data["conversations"]) or []
        data["literature"] = self._deserialize_json(data["literature"]) or []
        experiments_data = self._deserialize_json(data["experiments"])
        data["experiments"] = ExperimentDesign(**experiments_data) if experiments_data else None
        workflow_steps_data = self._deserialize_json(data["workflow_steps"]) or []
        data["workflow_steps"] = []
        for step_data in workflow_steps_data:
            if "status" in step_data:
                step_data["status"] = WorkflowStatus(step_data["status"])
            data["workflow_steps"].append(WorkflowStep(**step_data))
        data["tags"] = self._deserialize_json(data["tags"]) or []
        data["created_at"] = self._parse_datetime(data["created_at"])
        data["updated_at"] = self._parse_datetime(data["updated_at"])
        data["metadata"] = self._deserialize_json(data["metadata"]) or {}
        return Project(**data)

    # ==================== 对话操作 ====================

    def create_conversation(self, conversation: Conversation) -> Conversation:
        """创建对话"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations (id, title, project_id, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                conversation.id,
                conversation.title,
                conversation.project_id,
                self._format_datetime(conversation.created_at),
                self._format_datetime(conversation.updated_at),
                self._serialize_json(conversation.metadata),
            ),
        )
        conn.commit()
        for message in conversation.messages:
            self.create_message(conversation.id, message)
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话（包含消息）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        conversation = self._row_to_conversation(row)
        conversation.messages = self.get_messages(conversation_id)
        return conversation

    def list_conversations(
        self, project_id: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """列出对话"""
        conn = self._get_connection()
        cursor = conn.cursor()
        if project_id:
            cursor.execute(
                "SELECT * FROM conversations WHERE project_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (project_id, limit, offset),
            )
        else:
            cursor.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        rows = cursor.fetchall()
        return [self._row_to_conversation(row) for row in rows]

    def update_conversation(self, conversation: Conversation) -> Conversation:
        """更新对话"""
        conn = self._get_connection()
        cursor = conn.cursor()
        conversation.updated_at = datetime.now()
        cursor.execute(
            """
            UPDATE conversations SET title = ?, project_id = ?, updated_at = ?, metadata = ?
            WHERE id = ?
            """,
            (
                conversation.title,
                conversation.project_id,
                self._format_datetime(conversation.updated_at),
                self._serialize_json(conversation.metadata),
                conversation.id,
            ),
        )
        conn.commit()
        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        return cursor.rowcount > 0

    def _row_to_conversation(self, row: sqlite3.Row) -> Conversation:
        """将行数据转换为Conversation对象"""
        data = self._row_to_dict(row)
        data["created_at"] = self._parse_datetime(data["created_at"])
        data["updated_at"] = self._parse_datetime(data["updated_at"])
        data["metadata"] = self._deserialize_json(data["metadata"]) or {}
        data["messages"] = []
        return Conversation(**data)

    # ==================== 消息操作 ====================

    def create_message(self, conversation_id: str, message: Message) -> Message:
        """创建消息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message.id,
                conversation_id,
                message.role.value,
                message.content,
                self._format_datetime(message.timestamp),
                self._serialize_json(message.metadata),
            ),
        )
        conn.commit()
        return message

    def get_messages(self, conversation_id: str, limit: int = 100, offset: int = 0) -> List[Message]:
        """获取对话的消息列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ? OFFSET ?",
            (conversation_id, limit, offset),
        )
        rows = cursor.fetchall()
        return [self._row_to_message(row) for row in rows]

    def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        """添加消息便捷方法"""
        message = Message(role=role, content=content)
        return self.create_message(conversation_id, message)

    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """将行数据转换为Message对象"""
        data = self._row_to_dict(row)
        data["role"] = MessageRole(data["role"])
        data["timestamp"] = self._parse_datetime(data["timestamp"])
        data["metadata"] = self._deserialize_json(data["metadata"]) or {}
        return Message(**data)

    # ==================== 文献操作 ====================

    def create_literature(self, literature: Literature) -> Literature:
        """创建文献"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO literature (
                id, title, authors, year, venue, abstract, citations, url, doi,
                tags, added_at, bibtex, notes, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                literature.id,
                literature.title,
                self._serialize_json(literature.authors),
                literature.year,
                literature.venue,
                literature.abstract,
                literature.citations,
                literature.url,
                literature.doi,
                self._serialize_json(literature.tags),
                self._format_datetime(literature.added_at),
                literature.bibtex,
                literature.notes,
                self._serialize_json(literature.metadata),
            ),
        )
        conn.commit()
        return literature

    def get_literature(self, literature_id: str) -> Optional[Literature]:
        """获取文献"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM literature WHERE id = ?", (literature_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_literature(row)

    def list_literature(self, limit: int = 100, offset: int = 0) -> List[Literature]:
        """列出文献"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM literature ORDER BY added_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cursor.fetchall()
        return [self._row_to_literature(row) for row in rows]

    def search_literature(self, query: str, limit: int = 20) -> List[Literature]:
        """搜索文献"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM literature
            WHERE title LIKE ? OR abstract LIKE ? OR authors LIKE ?
            ORDER BY citations DESC LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        )
        rows = cursor.fetchall()
        return [self._row_to_literature(row) for row in rows]

    def update_literature(self, literature: Literature) -> Literature:
        """更新文献"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE literature SET
                title = ?, authors = ?, year = ?, venue = ?, abstract = ?,
                citations = ?, url = ?, doi = ?, tags = ?, bibtex = ?,
                notes = ?, metadata = ?
            WHERE id = ?
            """,
            (
                literature.title,
                self._serialize_json(literature.authors),
                literature.year,
                literature.venue,
                literature.abstract,
                literature.citations,
                literature.url,
                literature.doi,
                self._serialize_json(literature.tags),
                literature.bibtex,
                literature.notes,
                self._serialize_json(literature.metadata),
                literature.id,
            ),
        )
        conn.commit()
        return literature

    def delete_literature(self, literature_id: str) -> bool:
        """删除文献"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM literature WHERE id = ?", (literature_id,))
        conn.commit()
        return cursor.rowcount > 0

    def _row_to_literature(self, row: sqlite3.Row) -> Literature:
        """将行数据转换为Literature对象"""
        data = self._row_to_dict(row)
        data["authors"] = self._deserialize_json(data["authors"]) or []
        data["tags"] = self._deserialize_json(data["tags"]) or []
        data["added_at"] = self._parse_datetime(data["added_at"])
        data["metadata"] = self._deserialize_json(data["metadata"]) or {}
        return Literature(**data)

    # ==================== 项目-文献关联 ====================

    def add_literature_to_project(self, project_id: str, literature_id: str) -> None:
        """添加文献到项目"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO project_literature (project_id, literature_id, added_at)
            VALUES (?, ?, ?)
            """,
            (project_id, literature_id, self._format_datetime(datetime.now())),
        )
        conn.commit()

    def remove_literature_from_project(self, project_id: str, literature_id: str) -> None:
        """从项目移除文献"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM project_literature WHERE project_id = ? AND literature_id = ?",
            (project_id, literature_id),
        )
        conn.commit()

    def get_project_literature(self, project_id: str) -> List[Literature]:
        """获取项目的文献列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT l.* FROM literature l
            JOIN project_literature pl ON l.id = pl.literature_id
            WHERE pl.project_id = ?
            ORDER BY pl.added_at DESC
            """,
            (project_id,),
        )
        rows = cursor.fetchall()
        return [self._row_to_literature(row) for row in rows]


_db_instance: Optional[Database] = None


def get_database() -> Database:
    """获取数据库单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def reset_database() -> None:
    """重置数据库实例（主要用于测试）"""
    global _db_instance
    if _db_instance is not None:
        _db_instance.close()
        _db_instance = None
