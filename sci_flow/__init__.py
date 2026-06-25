"""
SciFlow - AI驱动的科研工作流助手
"""

__version__ = "1.0.0"
__author__ = "SciFlow Team"
__description__ = "AI驱动的科研工作流助手，助力学术研究全流程"

from .core import (
    ApiProvider,
    Config,
    Conversation,
    Database,
    Discipline,
    ExperimentDesign,
    Literature,
    LiteratureManager,
    Message,
    MessageRole,
    Project,
    ProjectStatus,
    ResultGenerator,
    WorkflowEngine,
    WorkflowEvent,
    WorkflowStatus,
    WorkflowStep,
    get_config,
    get_database,
    get_literature_manager,
    get_result_generator,
    get_workflow_engine,
)
from .llm import LLMClient, get_llm_client

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "ApiProvider",
    "Config",
    "Conversation",
    "Database",
    "Discipline",
    "ExperimentDesign",
    "Literature",
    "LiteratureManager",
    "Message",
    "MessageRole",
    "Project",
    "ProjectStatus",
    "ResultGenerator",
    "WorkflowEngine",
    "WorkflowEvent",
    "WorkflowStatus",
    "WorkflowStep",
    "get_config",
    "get_database",
    "get_literature_manager",
    "get_result_generator",
    "get_workflow_engine",
    "LLMClient",
    "get_llm_client",
]
