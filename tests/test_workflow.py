"""工作流引擎测试：8步流程、事件回调、暂停/恢复/取消"""

import asyncio

import pytest

from sci_flow.core.database import Database
from sci_flow.core.models import Project, ProjectStatus, WorkflowStatus
from sci_flow.core.workflow import (
    WORKFLOW_STEPS,
    WorkflowEngine,
    WorkflowEventType,
)


@pytest.fixture
def engine():
    return WorkflowEngine(db=Database())


@pytest.fixture
def project(engine):
    return engine.db.create_project(
        Project(topic="大语言模型推理优化", description="测试工作流", author="测试作者")
    )


def test_workflow_steps_definition():
    """工作流应包含 8 个标准步骤"""
    assert len(WORKFLOW_STEPS) == 8
    names = [s["name"] for s in WORKFLOW_STEPS]
    assert names == [
        "需求理解",
        "文献检索",
        "文献分析",
        "思路生成",
        "大纲构建",
        "实验设计",
        "文档撰写",
        "成果导出",
    ]


def test_create_workflow_initializes_steps(engine, project):
    updated = engine.create_workflow(project)
    assert len(updated.workflow_steps) == 8
    assert updated.status == ProjectStatus.IN_PROGRESS
    assert all(s.status == WorkflowStatus.PENDING for s in updated.workflow_steps)


def test_run_single_step(engine, project):
    """单步执行应返回结果并标记完成"""
    project = engine.create_workflow(project)
    result = asyncio.run(engine.run_step(project, 0, {"project_id": project.id}))
    assert "topic_analysis" in result or "analysis" in result
    step = engine.db.get_project(project.id).workflow_steps[0]
    assert step.status == WorkflowStatus.COMPLETED


def test_run_workflow_full(engine, project):
    """完整工作流应跑完 8 步并以 WORKFLOW_COMPLETED 结束"""

    async def run():
        events = []
        async for event in engine.run_workflow(project):
            events.append(event.event_type)
        return events

    events = asyncio.run(run())
    assert WorkflowEventType.WORKFLOW_STARTED in events
    assert WorkflowEventType.WORKFLOW_COMPLETED in events
    completed_steps = sum(1 for e in events if e == WorkflowEventType.STEP_COMPLETED)
    assert completed_steps >= 8

    final_project = engine.db.get_project(project.id)
    assert final_project.status == ProjectStatus.COMPLETED
    assert final_project.outline is not None
    assert final_project.report is not None


def test_event_callback_receives_events(engine, project):
    """事件回调应收到工作流事件"""
    received = []

    def callback(event):
        received.append(event.event_type)

    engine.add_event_callback(callback)

    async def run():
        async for _ in engine.run_workflow(project):
            pass

    asyncio.run(run())
    assert len(received) > 0
    assert WorkflowEventType.WORKFLOW_STARTED in received
    engine.remove_event_callback(callback)


def test_run_workflow_returns_artifacts(engine, project):
    """工作流结束后应产出大纲、实验方案、报告等成果"""

    async def run():
        context = {}
        async for event in engine.run_workflow(project):
            if event.event_type == WorkflowEventType.WORKFLOW_COMPLETED:
                context = event.data or {}
        return context

    context = asyncio.run(run())
    assert "outline" in context or "report" in context or "literature" in context


def test_cancel_workflow(engine, project):
    """取消工作流应终止后续步骤"""

    async def run():
        project_ = engine.create_workflow(project)
        events = []
        agen = engine.run_workflow(project_)
        # 消费第一个事件后再取消（run_workflow 内部会重置 cancelled 标志）
        first = await agen.__anext__()
        events.append(first.event_type)
        engine.cancel_workflow(project_.id)
        async for event in agen:
            events.append(event.event_type)
            if event.event_type == WorkflowEventType.WORKFLOW_CANCELLED:
                break
        return events

    events = asyncio.run(run())
    assert WorkflowEventType.WORKFLOW_CANCELLED in events


def test_get_workflow_status(engine, project):
    project = engine.create_workflow(project)
    steps = engine.get_workflow_status(project.id)
    assert len(steps) == 8
    assert engine.get_workflow_status("not-exist") is None
