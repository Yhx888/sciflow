"""
SciFlow 数据模型定义
使用Pydantic进行数据验证和序列化
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class WorkflowStatus(str, Enum):
    """工作流步骤状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class Theme(str, Enum):
    """界面主题枚举"""
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    QWEN = "qwen"
    OLLAMA = "ollama"


class Discipline(str, Enum):
    """学科领域枚举"""
    COMPUTER_SCIENCE = "computer_science"
    BIOLOGY = "biology"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    MATERIALS_SCIENCE = "materials_science"
    MATHEMATICS = "mathematics"
    MEDICINE = "medicine"
    ECONOMICS = "economics"
    PSYCHOLOGY = "psychology"
    OTHER = "other"


def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())


def now() -> datetime:
    """获取当前时间"""
    return datetime.now()


class Message(BaseModel):
    """聊天消息模型"""
    id: str = Field(default_factory=generate_id)
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class Conversation(BaseModel):
    """对话模型"""
    id: str = Field(default_factory=generate_id)
    title: str = "新对话"
    messages: List[Message] = Field(default_factory=list)
    project_id: Optional[str] = None
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """添加消息并更新时间"""
        self.messages.append(message)
        self.updated_at = now()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class Literature(BaseModel):
    """文献模型"""
    id: str = Field(default_factory=generate_id)
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    abstract: Optional[str] = None
    citations: int = 0
    url: Optional[str] = None
    doi: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    added_at: datetime = Field(default_factory=now)
    bibtex: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_authors_str(self, separator: str = ", ") -> str:
        """获取作者字符串"""
        return separator.join(self.authors)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ApiProvider(BaseModel):
    """API提供商配置模型"""
    name: LLMProvider
    display_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None
    enabled: bool = True

    def is_configured(self) -> bool:
        """检查是否已配置（本地模型如ollama不需要api_key）"""
        if self.name == LLMProvider.OLLAMA:
            return self.model is not None
        return self.api_key is not None and self.model is not None


class WorkflowStep(BaseModel):
    """工作流步骤模型"""
    name: str
    description: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def start(self) -> None:
        """标记步骤开始"""
        self.status = WorkflowStatus.RUNNING
        self.started_at = now()
        self.progress = 0.0
        self.error = None

    def update_progress(self, progress: float, message: Optional[str] = None) -> None:
        """更新进度"""
        self.progress = min(max(progress, 0.0), 1.0)
        if message:
            if self.result is None:
                self.result = {}
            self.result["progress_message"] = message

    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """标记步骤完成"""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = now()
        self.progress = 1.0
        if result:
            self.result = result

    def fail(self, error: str) -> None:
        """标记步骤失败"""
        self.status = WorkflowStatus.ERROR
        self.completed_at = now()
        self.error = error


class ExperimentDesign(BaseModel):
    """实验设计模型"""
    title: str
    hypothesis: str
    variables: Dict[str, List[str]] = Field(default_factory=dict)
    methodology: List[str] = Field(default_factory=list)
    expected_results: str
    metrics: List[str] = Field(default_factory=list)
    controls: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    timeline: Optional[str] = None


class Project(BaseModel):
    """科研项目模型"""
    id: str = Field(default_factory=generate_id)
    topic: str
    description: str = ""
    author: str = ""
    affiliation: str = ""
    discipline: Discipline = Discipline.OTHER
    status: ProjectStatus = ProjectStatus.DRAFT
    conversations: List[str] = Field(default_factory=list)
    literature: List[str] = Field(default_factory=list)
    outline: Optional[str] = None
    experiments: Optional[ExperimentDesign] = None
    report: Optional[str] = None
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_conversation(self, conversation_id: str) -> None:
        """添加对话"""
        if conversation_id not in self.conversations:
            self.conversations.append(conversation_id)
            self.updated_at = now()

    def add_literature(self, literature_id: str) -> None:
        """添加文献"""
        if literature_id not in self.literature:
            self.literature.append(literature_id)
            self.updated_at = now()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
