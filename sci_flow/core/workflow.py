"""
SciFlow 工作流引擎模块
实现8步标准科研工作流，支持异步执行、流式状态更新、中断恢复和事件回调
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from ..llm.client import LLMClient, get_llm_client
from .config import Config, get_config
from .database import Database, get_database
from .generator import ResultGenerator, get_result_generator
from .literature import LiteratureManager, get_literature_manager
from .models import (
    Discipline,
    Literature,
    Project,
    ProjectStatus,
    WorkflowStatus,
    WorkflowStep,
)


class WorkflowEventType(str, Enum):
    """工作流事件类型"""
    STEP_STARTED = "step_started"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETED = "step_completed"
    STEP_ERROR = "step_error"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    WORKFLOW_CANCELLED = "workflow_cancelled"


@dataclass
class WorkflowEvent:
    """工作流事件"""
    event_type: WorkflowEventType
    project_id: str
    step_index: Optional[int] = None
    step_name: Optional[str] = None
    progress: float = 0.0
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "project_id": self.project_id,
            "step_index": self.step_index,
            "step_name": self.step_name,
            "progress": self.progress,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_sse(self) -> str:
        """转换为SSE格式"""
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"


WORKFLOW_STEPS = [
    {
        "name": "需求理解",
        "description": "深入理解研究主题，明确研究目标、范围和关键问题",
    },
    {
        "name": "文献检索",
        "description": "根据研究主题检索相关学术文献，建立文献库",
    },
    {
        "name": "文献分析",
        "description": "对检索到的文献进行深度分析，总结研究现状和趋势",
    },
    {
        "name": "思路生成",
        "description": "基于文献分析，生成创新的研究思路和方向",
    },
    {
        "name": "大纲构建",
        "description": "构建详细的论文/报告大纲，明确各章节内容",
    },
    {
        "name": "实验设计",
        "description": "设计科学合理的实验方案，验证研究假设",
    },
    {
        "name": "文档撰写",
        "description": "根据大纲撰写完整的调研报告或论文初稿",
    },
    {
        "name": "成果导出",
        "description": "生成多种格式的最终成果，打包导出",
    },
]


class WorkflowEngine:
    """科研工作流引擎"""

    def __init__(
        self,
        config: Optional[Config] = None,
        db: Optional[Database] = None,
        llm: Optional[LLMClient] = None,
        literature_manager: Optional[LiteratureManager] = None,
        generator: Optional[ResultGenerator] = None,
    ):
        self.config = config or get_config()
        self.db = db or get_database()
        self.llm = llm or get_llm_client()
        self.literature_manager = literature_manager or get_literature_manager()
        self.generator = generator or get_result_generator()
        self._event_callbacks: List[Callable[[WorkflowEvent], None]] = []
        self._running_projects: Dict[str, Dict[str, Any]] = {}

    def add_event_callback(self, callback: Callable[[WorkflowEvent], None]) -> None:
        """添加事件回调函数"""
        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: Callable[[WorkflowEvent], None]) -> None:
        """移除事件回调函数"""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def _emit_event(self, event: WorkflowEvent) -> None:
        """触发事件"""
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def _initialize_steps(self) -> List[WorkflowStep]:
        """初始化工作流步骤"""
        return [
            WorkflowStep(name=step["name"], description=step["description"])
            for step in WORKFLOW_STEPS
        ]

    def create_workflow(self, project: Project) -> Project:
        """为项目创建工作流"""
        project.workflow_steps = self._initialize_steps()
        project.status = ProjectStatus.IN_PROGRESS
        return self.db.update_project(project)

    async def run_step(
        self,
        project: Project,
        step_index: int,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行单个工作流步骤"""
        step = project.workflow_steps[step_index]
        step_name = step.name

        step.start()
        self._emit_event(
            WorkflowEvent(
                event_type=WorkflowEventType.STEP_STARTED,
                project_id=project.id,
                step_index=step_index,
                step_name=step_name,
                message=f"开始执行步骤：{step_name}",
            )
        )

        try:
            result = await self._execute_step(project, step_index, step_name, context)
            step.complete(result)
            self._emit_event(
                WorkflowEvent(
                    event_type=WorkflowEventType.STEP_COMPLETED,
                    project_id=project.id,
                    step_index=step_index,
                    step_name=step_name,
                    progress=1.0,
                    message=f"步骤完成：{step_name}",
                    data=result,
                )
            )
            return result
        except Exception as e:
            step.fail(str(e))
            self._emit_event(
                WorkflowEvent(
                    event_type=WorkflowEventType.STEP_ERROR,
                    project_id=project.id,
                    step_index=step_index,
                    step_name=step_name,
                    message=f"步骤出错：{step_name} - {str(e)}",
                    data={"error": str(e)},
                )
            )
            raise

    async def _execute_step(
        self,
        project: Project,
        step_index: int,
        step_name: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行具体步骤逻辑"""
        topic = project.topic
        discipline = project.discipline

        if step_name == "需求理解":
            return await self._step_requirement_understanding(topic, discipline, context)
        elif step_name == "文献检索":
            return await self._step_literature_search(topic, discipline, context)
        elif step_name == "文献分析":
            return await self._step_literature_analysis(topic, context)
        elif step_name == "思路生成":
            return await self._step_idea_generation(topic, context)
        elif step_name == "大纲构建":
            return await self._step_outline_construction(topic, context)
        elif step_name == "实验设计":
            return await self._step_experiment_design(topic, context)
        elif step_name == "文档撰写":
            return await self._step_document_writing(topic, project, context)
        elif step_name == "成果导出":
            return await self._step_result_export(project, context)
        else:
            raise ValueError(f"未知步骤：{step_name}")

    async def _update_progress(
        self,
        project_id: str,
        step_index: int,
        step_name: str,
        progress: float,
        message: str,
    ) -> None:
        """更新步骤进度"""
        self._emit_event(
            WorkflowEvent(
                event_type=WorkflowEventType.STEP_PROGRESS,
                project_id=project_id,
                step_index=step_index,
                step_name=step_name,
                progress=progress,
                message=message,
            )
        )
        await asyncio.sleep(0.05)

    async def _step_requirement_understanding(
        self, topic: str, discipline: Discipline, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤1：需求理解"""
        await self._update_progress(
            context["project_id"], 0, "需求理解", 0.2, "分析研究主题..."
        )

        analysis_prompt = f"""请对以下研究主题进行深入分析：
主题：{topic}
学科领域：{discipline.value}

请从以下几个方面进行分析：
1. 研究背景与意义
2. 核心研究问题
3. 研究范围界定
4. 预期研究目标
5. 关键技术挑战

请以结构化的方式输出分析结果。"""

        await self._update_progress(
            context["project_id"], 0, "需求理解", 0.6, "生成需求分析报告..."
        )

        analysis = await self.llm.achat_with_system_prompt(
            "你是一位资深的科研导师，擅长帮助研究者明确研究方向和目标。",
            analysis_prompt,
        )

        await self._update_progress(
            context["project_id"], 0, "需求理解", 1.0, "需求理解完成"
        )

        return {
            "topic_analysis": analysis,
            "research_questions": [
                f"{topic}的核心问题是什么？",
                f"现有方法在{topic}上存在哪些局限性？",
                f"如何改进{topic}的现有方法？",
            ],
        }

    async def _step_literature_search(
        self, topic: str, discipline: Discipline, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤2：文献检索"""
        await self._update_progress(
            context["project_id"], 1, "文献检索", 0.2, "正在检索相关文献..."
        )

        literature_list = await self.literature_manager.search(
            topic, limit=10, discipline=discipline
        )

        await self._update_progress(
            context["project_id"], 1, "文献检索", 0.5, f"找到{len(literature_list)}篇相关文献"
        )

        saved_literature = []
        for i, lit in enumerate(literature_list):
            saved = self.literature_manager.save_literature(lit)
            saved_literature.append(saved)
            self.literature_manager.add_to_project(context["project_id"], saved.id)
            progress = 0.5 + (i + 1) / len(literature_list) * 0.4
            await self._update_progress(
                context["project_id"], 1, "文献检索", progress,
                f"已保存{ i + 1 }/{len(literature_list)}篇文献"
            )

        await self._update_progress(
            context["project_id"], 1, "文献检索", 1.0, "文献检索完成"
        )

        return {
            "literature_count": len(saved_literature),
            "literature_ids": [lit.id for lit in saved_literature],
            "literature": saved_literature,
        }

    async def _step_literature_analysis(
        self, topic: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤3：文献分析"""
        await self._update_progress(
            context["project_id"], 2, "文献分析", 0.2, "分析文献数据..."
        )

        project_literature = self.literature_manager.get_project_literature(
            context["project_id"]
        )

        await self._update_progress(
            context["project_id"], 2, "文献分析", 0.4, "生成文献矩阵..."
        )

        literature_matrix = self.literature_manager.generate_literature_matrix(
            project_literature
        )
        trend_summary = self.literature_manager.generate_trend_summary(
            project_literature
        )

        await self._update_progress(
            context["project_id"], 2, "文献分析", 0.7, "生成研究现状综述..."
        )

        analysis_prompt = f"""基于以下{len(project_literature)}篇关于"{topic}"的文献，撰写一份研究现状综述：

{[lit.title + ' (' + str(lit.year) + ')' for lit in project_literature[:5]]}

请包含以下内容：
1. 该领域的发展历程
2. 当前主流方法分类
3. 各类方法的优缺点比较
4. 现有研究的空白和不足
5. 未来可能的研究方向"""

        review = await self.llm.achat_with_system_prompt(
            "你是一位学术综述专家，擅长对研究领域进行系统性总结。",
            analysis_prompt,
        )

        await self._update_progress(
            context["project_id"], 2, "文献分析", 1.0, "文献分析完成"
        )

        return {
            "literature_matrix": literature_matrix,
            "trend_summary": trend_summary,
            "literature_review": review,
            "literature_count": len(project_literature),
        }

    async def _step_idea_generation(
        self, topic: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤4：思路生成"""
        await self._update_progress(
            context["project_id"], 3, "思路生成", 0.2, "构思研究方向..."
        )

        literature_review = context.get("literature_review", "")
        prompt = f"""基于以下研究现状分析，为"{topic}"这个主题提出3-5个创新的研究思路：

研究现状：{literature_review[:1000]}

每个研究思路请包含：
1. 思路名称
2. 核心创新点
3. 技术路线
4. 预期贡献
5. 可行性评估（1-5星）"""

        await self._update_progress(
            context["project_id"], 3, "思路生成", 0.5, "生成研究思路..."
        )

        ideas = await self.llm.achat_with_system_prompt(
            "你是一位富有创造力的科研战略家，擅长提出新颖且可行的研究方向。",
            prompt,
        )

        await self._update_progress(
            context["project_id"], 3, "思路生成", 1.0, "思路生成完成"
        )

        return {
            "research_ideas": ideas,
            "selected_idea": ideas,
        }

    async def _step_outline_construction(
        self, topic: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤5：大纲构建"""
        await self._update_progress(
            context["project_id"], 4, "大纲构建", 0.3, "构建论文大纲..."
        )

        project_literature = self.literature_manager.get_project_literature(
            context["project_id"]
        )

        outline = self.generator.generate_outline(topic, project_literature)

        await self._update_progress(
            context["project_id"], 4, "大纲构建", 0.7, "优化大纲结构..."
        )

        await self._update_progress(
            context["project_id"], 4, "大纲构建", 1.0, "大纲构建完成"
        )

        return {
            "outline": outline,
        }

    async def _step_experiment_design(
        self, topic: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤6：实验设计"""
        await self._update_progress(
            context["project_id"], 5, "实验设计", 0.3, "设计实验方案..."
        )

        project_literature = self.literature_manager.get_project_literature(
            context["project_id"]
        )

        experiments = self.generator.generate_experiment_design(topic, project_literature)

        await self._update_progress(
            context["project_id"], 5, "实验设计", 0.7, "细化实验步骤..."
        )

        await self._update_progress(
            context["project_id"], 5, "实验设计", 1.0, "实验设计完成"
        )

        return {
            "experiments": experiments,
        }

    async def _step_document_writing(
        self, topic: str, project: Project, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤7：文档撰写"""
        await self._update_progress(
            context["project_id"], 6, "文档撰写", 0.2, "准备撰写材料..."
        )

        project_literature = self.literature_manager.get_project_literature(
            context["project_id"]
        )
        outline = context.get("outline", "")
        experiments = context.get("experiments", {})

        await self._update_progress(
            context["project_id"], 6, "文档撰写", 0.4, "撰写调研报告..."
        )

        report = self.generator.generate_report(
            topic, project_literature, outline, experiments
        )

        await self._update_progress(
            context["project_id"], 6, "文档撰写", 0.8, "生成参考文献..."
        )

        bibtex = self.generator.generate_bibtex(project_literature)

        await self._update_progress(
            context["project_id"], 6, "文档撰写", 1.0, "文档撰写完成"
        )

        return {
            "report": report,
            "bibtex": bibtex,
        }

    async def _step_result_export(
        self, project: Project, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """步骤8：成果导出"""
        await self._update_progress(
            context["project_id"], 7, "成果导出", 0.2, "准备导出文件..."
        )

        exports_dir = self.config.get_exports_dir()
        project_export_dir = exports_dir / project.id
        project_export_dir.mkdir(parents=True, exist_ok=True)

        await self._update_progress(
            context["project_id"], 7, "成果导出", 0.4, "生成Markdown报告..."
        )

        report_content = context.get("report", "")
        bibtex_content = context.get("bibtex", "")
        outline_content = context.get("outline", "")

        md_path = project_export_dir / f"{project.topic}_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        await self._update_progress(
            context["project_id"], 7, "成果导出", 0.6, "生成BibTeX文件..."
        )

        bib_path = project_export_dir / "references.bib"
        with open(bib_path, "w", encoding="utf-8") as f:
            f.write(bibtex_content)

        await self._update_progress(
            context["project_id"], 7, "成果导出", 0.8, "打包项目文件..."
        )

        import zipfile
        zip_path = exports_dir / f"{project.topic}_{project.id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if md_path.exists():
                zf.write(md_path, md_path.name)
            if bib_path.exists():
                zf.write(bib_path, bib_path.name)
            outline_path = project_export_dir / "outline.md"
            with open(outline_path, "w", encoding="utf-8") as f:
                f.write(outline_content)
            zf.write(outline_path, outline_path.name)

        await self._update_progress(
            context["project_id"], 7, "成果导出", 1.0, "成果导出完成"
        )

        return {
            "export_dir": str(project_export_dir),
            "zip_path": str(zip_path),
            "files": [str(md_path), str(bib_path)],
        }

    async def run_workflow(
        self,
        project: Project,
        start_step: int = 0,
    ) -> AsyncGenerator[WorkflowEvent, None]:
        """运行完整工作流"""
        project = self.create_workflow(project)
        context: Dict[str, Any] = {"project_id": project.id}

        self._emit_event(
            WorkflowEvent(
                event_type=WorkflowEventType.WORKFLOW_STARTED,
                project_id=project.id,
                message="工作流开始执行",
            )
        )
        yield WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_STARTED,
            project_id=project.id,
            message="工作流开始执行",
        )

        self._running_projects[project.id] = {
            "project": project,
            "context": context,
            "current_step": start_step,
            "paused": False,
            "cancelled": False,
        }

        try:
            for step_index in range(start_step, len(WORKFLOW_STEPS)):
                run_info = self._running_projects.get(project.id)
                if run_info and run_info["cancelled"]:
                    yield WorkflowEvent(
                        event_type=WorkflowEventType.WORKFLOW_CANCELLED,
                        project_id=project.id,
                        message="工作流已取消",
                    )
                    break

                while run_info and run_info["paused"]:
                    yield WorkflowEvent(
                        event_type=WorkflowEventType.WORKFLOW_PAUSED,
                        project_id=project.id,
                        message="工作流已暂停",
                    )
                    await asyncio.sleep(0.5)
                    run_info = self._running_projects.get(project.id)

                step_result = await self.run_step(project, step_index, context)
                context.update(step_result)

                for callback in self._event_callbacks:
                    pass

                project = self.db.get_project(project.id) or project

                yield WorkflowEvent(
                    event_type=WorkflowEventType.STEP_COMPLETED,
                    project_id=project.id,
                    step_index=step_index,
                    step_name=WORKFLOW_STEPS[step_index]["name"],
                    data=step_result,
                )

            project.status = ProjectStatus.COMPLETED
            self.db.update_project(project)

            final_event = WorkflowEvent(
                event_type=WorkflowEventType.WORKFLOW_COMPLETED,
                project_id=project.id,
                message="工作流执行完成",
                data=context,
            )
            self._emit_event(final_event)
            yield final_event

        except Exception as e:
            self._emit_event(
                WorkflowEvent(
                    event_type=WorkflowEventType.STEP_ERROR,
                    project_id=project.id,
                    message=f"工作流出错：{str(e)}",
                    data={"error": str(e)},
                )
            )
            raise
        finally:
            if project.id in self._running_projects:
                del self._running_projects[project.id]

    def pause_workflow(self, project_id: str) -> None:
        """暂停工作流"""
        if project_id in self._running_projects:
            self._running_projects[project_id]["paused"] = True
            self._emit_event(
                WorkflowEvent(
                    event_type=WorkflowEventType.WORKFLOW_PAUSED,
                    project_id=project_id,
                    message="工作流已暂停",
                )
            )

    def resume_workflow(self, project_id: str) -> None:
        """恢复工作流"""
        if project_id in self._running_projects:
            self._running_projects[project_id]["paused"] = False
            self._emit_event(
                WorkflowEvent(
                    event_type=WorkflowEventType.WORKFLOW_RESUMED,
                    project_id=project_id,
                    message="工作流已恢复",
                )
            )

    def cancel_workflow(self, project_id: str) -> None:
        """取消工作流"""
        if project_id in self._running_projects:
            self._running_projects[project_id]["cancelled"] = True
            self._emit_event(
                WorkflowEvent(
                    event_type=WorkflowEventType.WORKFLOW_CANCELLED,
                    project_id=project_id,
                    message="工作流已取消",
                )
            )

    def get_workflow_status(self, project_id: str) -> Optional[List[WorkflowStep]]:
        """获取工作流状态"""
        project = self.db.get_project(project_id)
        if project:
            return project.workflow_steps
        return None


_workflow_engine_instance: Optional[WorkflowEngine] = None


def get_workflow_engine(
    config: Optional[Config] = None,
    db: Optional[Database] = None,
    llm: Optional[LLMClient] = None,
    literature_manager: Optional[LiteratureManager] = None,
    generator: Optional[ResultGenerator] = None,
) -> WorkflowEngine:
    """获取工作流引擎单例"""
    global _workflow_engine_instance
    if _workflow_engine_instance is None:
        _workflow_engine_instance = WorkflowEngine(
            config, db, llm, literature_manager, generator
        )
    return _workflow_engine_instance


def reset_workflow_engine() -> None:
    """重置工作流引擎（主要用于测试）"""
    global _workflow_engine_instance
    _workflow_engine_instance = None
