"""
SciFlow FastAPI后端服务器
提供Web API服务、SSE流式接口和静态文件服务
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ..core.config import Config, get_config
from ..core.database import Database, get_database
from ..core.generator import ResultGenerator, get_result_generator
from ..core.literature import (
    LiteratureManager,
    get_literature_manager,
)
from ..core.models import (
    Conversation,
    Discipline,
    Literature,
    LLMProvider,
    Message,
    MessageRole,
    Project,
    ProjectStatus,
    Theme,
    generate_id,
)
from ..core.workflow import (
    WorkflowEngine,
    WorkflowEvent as CoreWorkflowEvent,
    WorkflowEventType,
    get_workflow_engine,
)
from ..llm.client import LLMClient, get_llm_client


# ==================== 请求/响应模型 ====================


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    active_provider: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream_enabled: Optional[bool] = None
    auto_save: Optional[bool] = None
    providers: Optional[List[Dict[str, Any]]] = None


class TestConnectionRequest(BaseModel):
    """测试连接请求"""
    provider: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None


class ChatRequest(BaseModel):
    """聊天请求"""
    conversation_id: Optional[str] = None
    message: str
    project_id: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    topic: str
    description: str = ""
    author: str = ""
    affiliation: str = ""
    discipline: str = "other"


class ProjectUpdateRequest(BaseModel):
    """更新项目请求"""
    topic: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    affiliation: Optional[str] = None
    discipline: Optional[str] = None
    status: Optional[str] = None


class LiteratureSearchRequest(BaseModel):
    """文献搜索请求"""
    query: str
    limit: int = 10
    discipline: Optional[str] = None


class BibTeXExportRequest(BaseModel):
    """BibTeX导出请求"""
    literature_ids: List[str]


class GBTExportRequest(BaseModel):
    """GB/T导出请求"""
    literature_ids: List[str]


# ==================== 工作流状态存储 ====================

_workflow_states: Dict[str, Dict[str, Any]] = {}
_workflow_queues: Dict[str, asyncio.Queue] = {}
_workflow_tasks: Dict[str, asyncio.Task] = {}


# ==================== FastAPI应用创建 ====================

def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title="SciFlow API",
        description="AI科研助手后端API服务",
        version="1.0.0",
    )

    # CORS中间件配置 - 允许本地开发
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8765",
            "http://127.0.0.1:8765",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 启动和关闭事件
    @app.on_event("startup")
    async def startup_event():
        """启动时初始化配置、数据库"""
        config = get_config()
        db = get_database()
        _ = get_llm_client()
        _ = get_literature_manager()
        _ = get_result_generator()
        _ = get_workflow_engine()
        print(f"[SciFlow] 配置加载完成，数据目录: {config.data_dir}")
        print(f"[SciFlow] 数据库已初始化: {db.db_path}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """关闭时清理资源"""
        for project_id, task in _workflow_tasks.items():
            if not task.done():
                task.cancel()
        db = get_database()
        db.close()
        print("[SciFlow] 服务器已关闭，资源已清理")

    # 挂载静态文件目录
    _mount_static_files(app)

    # ==================== 配置相关API ====================

    @app.get("/api/config")
    async def get_config_api():
        """获取当前配置"""
        config = get_config()
        return JSONResponse(content={
            "success": True,
            "data": _config_to_dict(config)
        })

    @app.put("/api/config")
    async def update_config_api(request: ConfigUpdateRequest):
        """更新配置"""
        config = get_config()
        try:
            update_data = request.model_dump(exclude_unset=True)
            
            if "active_provider" in update_data and update_data["active_provider"]:
                config.active_provider = LLMProvider(update_data["active_provider"])
            
            if "theme" in update_data and update_data["theme"]:
                from ..core.models import Theme
                config.theme = Theme(update_data["theme"])
            
            if "language" in update_data:
                config.language = update_data["language"]
            
            if "max_tokens" in update_data and update_data["max_tokens"]:
                config.max_tokens = update_data["max_tokens"]
            
            if "temperature" in update_data and update_data["temperature"] is not None:
                config.temperature = update_data["temperature"]
            
            if "stream_enabled" in update_data and update_data["stream_enabled"] is not None:
                config.stream_enabled = update_data["stream_enabled"]
            
            if "auto_save" in update_data and update_data["auto_save"] is not None:
                config.auto_save = update_data["auto_save"]
            
            if "providers" in update_data and update_data["providers"]:
                for p_data in update_data["providers"]:
                    if "name" in p_data:
                        provider_name = LLMProvider(p_data["name"])
                        kwargs = {}
                        for key in ["api_key", "api_base", "model", "enabled"]:
                            if key in p_data:
                                kwargs[key] = p_data[key]
                        if kwargs:
                            config.update_provider(provider_name, **kwargs)
            
            config.save()
            _reset_llm_client()
            
            return JSONResponse(content={
                "success": True,
                "message": "配置已更新",
                "data": _config_to_dict(config)
            })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"更新配置失败: {str(e)}")

    @app.get("/api/config/providers")
    async def get_providers_api():
        """获取支持的LLM提供商列表"""
        providers = []
        for provider in get_config().providers:
            p_dict = provider.model_dump()
            if p_dict.get("api_key"):
                p_dict["api_key_configured"] = True
                p_dict["api_key"] = None
            else:
                p_dict["api_key_configured"] = False
            p_dict["configured"] = provider.is_configured()
            providers.append(p_dict)
        
        return JSONResponse(content={
            "success": True,
            "data": providers
        })

    @app.post("/api/config/test")
    async def test_connection_api(request: TestConnectionRequest):
        """测试API连接"""
        try:
            config = get_config()
            temp_config = Config()
            temp_config.providers = list(config.providers)
            
            provider_name = None
            if request.provider:
                provider_name = LLMProvider(request.provider)
                temp_config.active_provider = provider_name
            else:
                provider_name = config.active_provider
            
            test_kwargs = {}
            if request.api_key is not None:
                test_kwargs["api_key"] = request.api_key
            if request.api_base is not None:
                test_kwargs["api_base"] = request.api_base
            if request.model is not None:
                test_kwargs["model"] = request.model
            
            if test_kwargs:
                temp_config.update_provider(provider_name, **test_kwargs)
            
            test_client = LLMClient(temp_config)
            
            test_prompt = "你好，请回复'连接成功'四个字。"
            start_time = datetime.now()
            response = await test_client.achat(
                [{"role": "user", "content": test_prompt}],
                max_tokens=20,
                temperature=0.1
            )
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            
            return JSONResponse(content={
                "success": True,
                "message": "连接成功",
                "data": {
                    "response": response,
                    "elapsed_ms": round(elapsed, 2),
                    "provider": provider_name.value
                }
            })
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"连接失败: {str(e)}"
                }
            )

    # ==================== 对话/聊天API ====================

    @app.get("/api/conversations")
    async def list_conversations_api(project_id: Optional[str] = None, limit: int = 50, offset: int = 0):
        """获取对话列表"""
        db = get_database()
        conversations = db.list_conversations(project_id=project_id, limit=limit, offset=offset)
        return JSONResponse(content={
            "success": True,
            "data": [_conversation_to_dict(c, include_messages=False) for c in conversations]
        })

    @app.post("/api/conversations")
    async def create_conversation_api(project_id: Optional[str] = None, title: str = "新对话"):
        """创建新对话"""
        db = get_database()
        conversation = Conversation(
            title=title,
            project_id=project_id
        )
        
        if project_id:
            project = db.get_project(project_id)
            if project:
                project.add_conversation(conversation.id)
                db.update_project(project)
        
        db.create_conversation(conversation)
        return JSONResponse(content={
            "success": True,
            "data": _conversation_to_dict(conversation)
        })

    @app.get("/api/conversations/{conversation_id}")
    async def get_conversation_api(conversation_id: str):
        """获取对话详情"""
        db = get_database()
        conversation = db.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        return JSONResponse(content={
            "success": True,
            "data": _conversation_to_dict(conversation)
        })

    @app.delete("/api/conversations/{conversation_id}")
    async def delete_conversation_api(conversation_id: str):
        """删除对话"""
        db = get_database()
        conversation = db.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if conversation.project_id:
            project = db.get_project(conversation.project_id)
            if project and conversation_id in project.conversations:
                project.conversations.remove(conversation_id)
                db.update_project(project)
        
        db.delete_conversation(conversation_id)
        return JSONResponse(content={
            "success": True,
            "message": "对话已删除"
        })

    @app.post("/api/chat")
    async def chat_api(request: ChatRequest):
        """发送消息（非流式，返回完整响应）"""
        db = get_database()
        llm = get_llm_client()
        
        conversation = None
        conversation_id = request.conversation_id
        
        if conversation_id:
            conversation = db.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            conversation = Conversation(project_id=request.project_id)
            db.create_conversation(conversation)
            conversation_id = conversation.id
            
            if request.project_id:
                project = db.get_project(request.project_id)
                if project:
                    project.add_conversation(conversation_id)
                    db.update_project(project)
        
        user_message = Message(role=MessageRole.USER, content=request.message)
        db.create_message(conversation_id, user_message)
        conversation.add_message(user_message)
        
        messages_for_llm = []
        for msg in conversation.messages:
            messages_for_llm.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        try:
            response_content = await llm.achat(messages_for_llm, stream=False)
            
            assistant_message = Message(role=MessageRole.ASSISTANT, content=response_content)
            db.create_message(conversation_id, assistant_message)
            
            conversation.title = _generate_conversation_title(request.message)
            db.update_conversation(conversation)
            
            return JSONResponse(content={
                "success": True,
                "data": {
                    "conversation_id": conversation_id,
                    "message": _message_to_dict(assistant_message),
                    "title": conversation.title
                }
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"聊天失败: {str(e)}")

    @app.post("/api/chat/stream")
    async def chat_stream_api(request: ChatRequest):
        """SSE流式聊天"""
        db = get_database()
        llm = get_llm_client()
        
        conversation = None
        conversation_id = request.conversation_id
        
        if conversation_id:
            conversation = db.get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            conversation = Conversation(project_id=request.project_id)
            db.create_conversation(conversation)
            conversation_id = conversation.id
            
            if request.project_id:
                project = db.get_project(request.project_id)
                if project:
                    project.add_conversation(conversation_id)
                    db.update_project(project)
        
        user_message = Message(role=MessageRole.USER, content=request.message)
        db.create_message(conversation_id, user_message)
        conversation.add_message(user_message)
        
        messages_for_llm = []
        for msg in conversation.messages:
            messages_for_llm.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
            full_response = ""
            message_id = generate_id()
            
            try:
                stream = await llm.achat(messages_for_llm, stream=True)
                
                yield {
                    "event": "message",
                    "id": message_id,
                    "data": json.dumps({
                        "type": "start",
                        "conversation_id": conversation_id,
                        "message_id": message_id
                    }, ensure_ascii=False)
                }
                
                async for chunk in stream:
                    if chunk:
                        full_response += chunk
                        yield {
                            "event": "message",
                            "id": message_id,
                            "data": json.dumps({
                                "type": "chunk",
                                "content": chunk
                            }, ensure_ascii=False)
                        }
                
                assistant_message = Message(
                    id=message_id,
                    role=MessageRole.ASSISTANT,
                    content=full_response
                )
                db.create_message(conversation_id, assistant_message)
                
                conversation.title = _generate_conversation_title(request.message)
                db.update_conversation(conversation)
                
                yield {
                    "event": "done",
                    "id": message_id,
                    "data": json.dumps({
                        "type": "end",
                        "conversation_id": conversation_id,
                        "title": conversation.title,
                        "message": _message_to_dict(assistant_message)
                    }, ensure_ascii=False)
                }
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": str(e)
                    }, ensure_ascii=False)
                }
        
        return EventSourceResponse(event_generator())

    # ==================== 项目相关API ====================

    @app.get("/api/projects")
    async def list_projects_api(limit: int = 50, offset: int = 0):
        """获取项目列表"""
        db = get_database()
        projects = db.list_projects(limit=limit, offset=offset)
        return JSONResponse(content={
            "success": True,
            "data": [_project_to_dict(p, include_details=False) for p in projects]
        })

    @app.post("/api/projects")
    async def create_project_api(request: ProjectCreateRequest):
        """创建新项目"""
        db = get_database()
        
        try:
            discipline = Discipline(request.discipline)
        except ValueError:
            discipline = Discipline.OTHER
        
        project = Project(
            topic=request.topic,
            description=request.description,
            author=request.author,
            affiliation=request.affiliation,
            discipline=discipline
        )
        
        db.create_project(project)
        
        config = get_config()
        config.add_recent_project(project.id)
        config.save()
        
        return JSONResponse(content={
            "success": True,
            "data": _project_to_dict(project)
        })

    @app.get("/api/projects/{project_id}")
    async def get_project_api(project_id: str):
        """获取项目详情"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project_dict = _project_to_dict(project)
        
        project_dict["conversations_detail"] = []
        for conv_id in project.conversations:
            conv = db.get_conversation(conv_id)
            if conv:
                project_dict["conversations_detail"].append(
                    _conversation_to_dict(conv, include_messages=False)
                )
        
        lit_manager = get_literature_manager()
        project_literature = lit_manager.get_project_literature(project_id)
        project_dict["literature_detail"] = [
            _literature_to_dict(lit) for lit in project_literature
        ]
        
        return JSONResponse(content={
            "success": True,
            "data": project_dict
        })

    @app.put("/api/projects/{project_id}")
    async def update_project_api(project_id: str, request: ProjectUpdateRequest):
        """更新项目"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        update_data = request.model_dump(exclude_unset=True)
        
        if "topic" in update_data and update_data["topic"]:
            project.topic = update_data["topic"]
        if "description" in update_data:
            project.description = update_data["description"] or ""
        if "author" in update_data:
            project.author = update_data["author"] or ""
        if "affiliation" in update_data:
            project.affiliation = update_data["affiliation"] or ""
        if "discipline" in update_data and update_data["discipline"]:
            try:
                project.discipline = Discipline(update_data["discipline"])
            except ValueError:
                pass
        if "status" in update_data and update_data["status"]:
            try:
                project.status = ProjectStatus(update_data["status"])
            except ValueError:
                pass
        
        db.update_project(project)
        
        return JSONResponse(content={
            "success": True,
            "data": _project_to_dict(project)
        })

    @app.delete("/api/projects/{project_id}")
    async def delete_project_api(project_id: str):
        """删除项目"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project_id in _workflow_tasks:
            task = _workflow_tasks[project_id]
            if not task.done():
                task.cancel()
            del _workflow_tasks[project_id]
        if project_id in _workflow_states:
            del _workflow_states[project_id]
        if project_id in _workflow_queues:
            del _workflow_queues[project_id]
        
        db.delete_project(project_id)
        
        return JSONResponse(content={
            "success": True,
            "message": "项目已删除"
        })

    # ==================== 工作流API ====================

    @app.post("/api/projects/{project_id}/workflow/start")
    async def start_workflow_api(project_id: str):
        """启动工作流"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project_id in _workflow_tasks:
            existing_task = _workflow_tasks[project_id]
            if not existing_task.done():
                raise HTTPException(status_code=400, detail="工作流已在运行中")
        
        workflow_engine = get_workflow_engine()
        
        queue: asyncio.Queue = asyncio.Queue()
        _workflow_queues[project_id] = queue
        
        _workflow_states[project_id] = {
            "status": "running",
            "current_step": 0,
            "started_at": datetime.now().isoformat()
        }
        
        async def workflow_callback(event: CoreWorkflowEvent):
            await queue.put(event)
        
        workflow_engine.add_event_callback(workflow_callback)
        
        async def run_workflow_task():
            try:
                async for event in workflow_engine.run_workflow(project):
                    await queue.put(event)
                    
                    if event.event_type == WorkflowEventType.STEP_STARTED:
                        if project_id in _workflow_states:
                            _workflow_states[project_id]["current_step"] = event.step_index or 0
                    elif event.event_type == WorkflowEventType.WORKFLOW_COMPLETED:
                        if project_id in _workflow_states:
                            _workflow_states[project_id]["status"] = "completed"
                    elif event.event_type == WorkflowEventType.WORKFLOW_CANCELLED:
                        if project_id in _workflow_states:
                            _workflow_states[project_id]["status"] = "cancelled"
                    elif event.event_type == WorkflowEventType.WORKFLOW_PAUSED:
                        if project_id in _workflow_states:
                            _workflow_states[project_id]["status"] = "paused"
                    elif event.event_type == WorkflowEventType.WORKFLOW_RESUMED:
                        if project_id in _workflow_states:
                            _workflow_states[project_id]["status"] = "running"
                
                await queue.put(None)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                error_event = CoreWorkflowEvent(
                    event_type=WorkflowEventType.STEP_ERROR,
                    project_id=project_id,
                    message=f"工作流出错: {str(e)}",
                    data={"error": str(e)}
                )
                await queue.put(error_event)
                await queue.put(None)
                if project_id in _workflow_states:
                    _workflow_states[project_id]["status"] = "error"
                    _workflow_states[project_id]["error"] = str(e)
            finally:
                workflow_engine.remove_event_callback(workflow_callback)
        
        task = asyncio.create_task(run_workflow_task())
        _workflow_tasks[project_id] = task
        
        return JSONResponse(content={
            "success": True,
            "message": "工作流已启动"
        })

    @app.get("/api/projects/{project_id}/workflow/stream")
    async def workflow_stream_api(project_id: str):
        """SSE工作流状态流"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if project_id not in _workflow_queues:
            queue: asyncio.Queue = asyncio.Queue()
            _workflow_queues[project_id] = queue
        else:
            queue = _workflow_queues[project_id]
        
        async def event_generator():
            if project_id in _workflow_states:
                state = _workflow_states[project_id]
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "type": "state",
                        "status": state.get("status"),
                        "current_step": state.get("current_step", 0)
                    }, ensure_ascii=False)
                }
            
            try:
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    except asyncio.TimeoutError:
                        yield {
                            "event": "ping",
                            "data": json.dumps({"type": "ping"}, ensure_ascii=False)
                        }
                        continue
                    
                    if event is None:
                        yield {
                            "event": "done",
                            "data": json.dumps({"type": "completed"}, ensure_ascii=False)
                        }
                        break
                    
                    event_data = event.to_dict()
                    event_type = event.event_type.value
                    
                    if event_type in ("step_started", "step_completed", "step_progress"):
                        sse_event = "step"
                        if event_type == "step_progress":
                            sse_event = "progress"
                        
                        data = {
                            "type": event_type,
                            "step_index": event.step_index,
                            "step_name": event.step_name,
                            "progress": event.progress,
                            "message": event.message
                        }
                        if event.data:
                            data["data"] = event.data
                        
                        yield {
                            "event": sse_event,
                            "data": json.dumps(data, ensure_ascii=False)
                        }
                    elif event_type == "workflow_started":
                        yield {
                            "event": "step",
                            "data": json.dumps({
                                "type": "workflow_started",
                                "message": event.message
                            }, ensure_ascii=False)
                        }
                    elif event_type == "workflow_completed":
                        yield {
                            "event": "done",
                            "data": json.dumps({
                                "type": "completed",
                                "message": event.message,
                                "data": event.data
                            }, ensure_ascii=False)
                        }
                    elif event_type == "workflow_paused":
                        yield {
                            "event": "progress",
                            "data": json.dumps({
                                "type": "paused",
                                "message": event.message
                            }, ensure_ascii=False)
                        }
                    elif event_type == "workflow_resumed":
                        yield {
                            "event": "progress",
                            "data": json.dumps({
                                "type": "resumed",
                                "message": event.message
                            }, ensure_ascii=False)
                        }
                    elif event_type == "workflow_cancelled":
                        yield {
                            "event": "done",
                            "data": json.dumps({
                                "type": "cancelled",
                                "message": event.message
                            }, ensure_ascii=False)
                        }
                        break
                    elif event_type == "step_error":
                        yield {
                            "event": "error",
                            "data": json.dumps({
                                "type": "error",
                                "message": event.message,
                                "error": event.data.get("error") if event.data else None
                            }, ensure_ascii=False)
                        }
                        yield {
                            "event": "done",
                            "data": json.dumps({
                                "type": "error",
                                "message": event.message
                            }, ensure_ascii=False)
                        }
                        break
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": str(e)
                    }, ensure_ascii=False)
                }
        
        return EventSourceResponse(event_generator())

    @app.post("/api/projects/{project_id}/workflow/pause")
    async def pause_workflow_api(project_id: str):
        """暂停工作流"""
        workflow_engine = get_workflow_engine()
        workflow_engine.pause_workflow(project_id)
        return JSONResponse(content={
            "success": True,
            "message": "工作流已暂停"
        })

    @app.post("/api/projects/{project_id}/workflow/resume")
    async def resume_workflow_api(project_id: str):
        """恢复工作流"""
        workflow_engine = get_workflow_engine()
        workflow_engine.resume_workflow(project_id)
        return JSONResponse(content={
            "success": True,
            "message": "工作流已恢复"
        })

    @app.post("/api/projects/{project_id}/workflow/cancel")
    async def cancel_workflow_api(project_id: str):
        """取消工作流"""
        workflow_engine = get_workflow_engine()
        workflow_engine.cancel_workflow(project_id)
        if project_id in _workflow_tasks:
            task = _workflow_tasks[project_id]
            task.cancel()
        return JSONResponse(content={
            "success": True,
            "message": "工作流已取消"
        })

    # ==================== 文献相关API ====================

    @app.get("/api/projects/{project_id}/literature")
    async def get_project_literature_api(project_id: str):
        """获取项目文献"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        lit_manager = get_literature_manager()
        literature = lit_manager.get_project_literature(project_id)
        
        return JSONResponse(content={
            "success": True,
            "data": [_literature_to_dict(lit) for lit in literature]
        })

    @app.post("/api/projects/{project_id}/literature/search")
    async def search_literature_api(project_id: str, request: LiteratureSearchRequest):
        """搜索文献添加到项目"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        lit_manager = get_literature_manager()
        
        discipline = project.discipline
        if request.discipline:
            try:
                discipline = Discipline(request.discipline)
            except ValueError:
                pass
        
        try:
            literature_list = await lit_manager.search(
                request.query,
                limit=request.limit,
                discipline=discipline
            )
            
            saved_literature = []
            for lit in literature_list:
                saved = lit_manager.save_literature(lit)
                lit_manager.add_to_project(project_id, saved.id)
                project.add_literature(saved.id)
                saved_literature.append(saved)
            
            db.update_project(project)
            
            return JSONResponse(content={
                "success": True,
                "message": f"已添加{len(saved_literature)}篇文献",
                "data": [_literature_to_dict(lit) for lit in saved_literature]
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文献搜索失败: {str(e)}")

    @app.post("/api/literature/export/bibtex")
    async def export_bibtex_api(request: BibTeXExportRequest):
        """导出BibTeX"""
        db = get_database()
        lit_manager = get_literature_manager()
        
        literature_list = []
        for lit_id in request.literature_ids:
            lit = db.get_literature(lit_id)
            if lit:
                literature_list.append(lit)
        
        bibtex_content = lit_manager.generate_bibtex(literature_list)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "content": bibtex_content,
                "format": "bibtex",
                "filename": "references.bib"
            }
        })

    @app.post("/api/literature/export/gbt")
    async def export_gbt_api(request: GBTExportRequest):
        """导出GB/T引用"""
        db = get_database()
        lit_manager = get_literature_manager()
        
        literature_list = []
        for lit_id in request.literature_ids:
            lit = db.get_literature(lit_id)
            if lit:
                literature_list.append(lit)
        
        gbt_content = lit_manager.generate_gbt7714(literature_list)
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "content": gbt_content,
                "format": "gbt7714",
                "filename": "references_gbt7714.txt"
            }
        })

    # ==================== 成果导出API ====================

    @app.get("/api/projects/{project_id}/results")
    async def get_results_api(project_id: str):
        """获取成果列表"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        config = get_config()
        exports_dir = config.get_exports_dir()
        project_export_dir = exports_dir / project_id
        
        results = []
        
        if project.report:
            results.append({
                "name": f"{project.topic}_report.md",
                "type": "report",
                "format": "markdown",
                "size": len(project.report.encode("utf-8"))
            })
        
        lit_manager = get_literature_manager()
        project_literature = lit_manager.get_project_literature(project_id)
        if project_literature:
            bibtex = lit_manager.generate_bibtex(project_literature)
            results.append({
                "name": "references.bib",
                "type": "references",
                "format": "bibtex",
                "size": len(bibtex.encode("utf-8"))
            })
            
            gbt = lit_manager.generate_gbt7714(project_literature)
            results.append({
                "name": "references_gbt7714.txt",
                "type": "references",
                "format": "gbt7714",
                "size": len(gbt.encode("utf-8"))
            })
        
        if project.outline:
            results.append({
                "name": "outline.md",
                "type": "outline",
                "format": "markdown",
                "size": len(project.outline.encode("utf-8"))
            })
        
        if project_export_dir.exists():
            for file in project_export_dir.iterdir():
                if file.is_file():
                    results.append({
                        "name": file.name,
                        "type": "file",
                        "path": str(file),
                        "size": file.stat().st_size
                    })
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "project_id": project_id,
                "results": results,
                "has_report": project.report is not None,
                "literature_count": len(project.literature)
            }
        })

    @app.get("/api/projects/{project_id}/results/download")
    async def download_results_zip_api(project_id: str):
        """下载ZIP打包成果"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        generator = get_result_generator()
        zip_content = generator.generate_project_bundle(project)
        
        filename = f"{project.topic}_{project_id}.zip"
        filename = _sanitize_filename(filename)
        
        return StreamingResponse(
            BytesIO(zip_content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            }
        )

    @app.get("/api/projects/{project_id}/results/{filename}")
    async def download_result_file_api(project_id: str, filename: str):
        """下载单个文件"""
        db = get_database()
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        safe_filename = Path(filename).name
        
        config = get_config()
        exports_dir = config.get_exports_dir()
        file_path = exports_dir / project_id / safe_filename
        
        if file_path.exists() and file_path.is_file():
            return FileResponse(
                str(file_path),
                filename=safe_filename
            )
        
        content = None
        media_type = "text/plain"
        
        if safe_filename.endswith("_report.md") and project.report:
            content = project.report
            media_type = "text/markdown"
        elif safe_filename == "references.bib":
            lit_manager = get_literature_manager()
            project_literature = lit_manager.get_project_literature(project_id)
            content = lit_manager.generate_bibtex(project_literature)
        elif safe_filename.startswith("references_gbt"):
            lit_manager = get_literature_manager()
            project_literature = lit_manager.get_project_literature(project_id)
            content = lit_manager.generate_gbt7714(project_literature)
        elif safe_filename == "outline.md" and project.outline:
            content = project.outline
            media_type = "text/markdown"
        
        if content is None:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        content_bytes = content.encode("utf-8")
        return StreamingResponse(
            BytesIO(content_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
            }
        )

    return app


# ==================== 工具函数 ====================


def _mount_static_files(app: FastAPI):
    """挂载静态文件目录"""
    server_dir = Path(__file__).parent
    web_dir = server_dir.parent / "web"
    
    if web_dir.exists() and web_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
        
        @app.get("/")
        async def root_redirect():
            index_file = web_dir / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            return FileResponse(str(web_dir / "index.html"))
    else:
        @app.get("/")
        async def root_info():
            return JSONResponse(content={
                "name": "SciFlow API",
                "version": "1.0.0",
                "status": "running",
                "message": "Web目录不存在，请先构建前端",
                "endpoints": {
                    "config": "/api/config",
                    "projects": "/api/projects",
                    "conversations": "/api/conversations",
                    "docs": "/docs"
                }
            })
    
    @app.get("/index.html")
    async def index_html():
        web_dir = Path(__file__).parent.parent / "web"
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse(content="<html><body><h1>SciFlow</h1><p>前端文件不存在，请先构建web目录</p></body></html>")


def _config_to_dict(config: Config) -> Dict[str, Any]:
    """将配置转换为字典"""
    data = config.model_dump()
    data["data_dir"] = str(config.data_dir)
    data["providers"] = []
    for p in config.providers:
        p_dict = p.model_dump()
        if p_dict.get("api_key"):
            p_dict["api_key_configured"] = True
            p_dict["api_key"] = None
        else:
            p_dict["api_key_configured"] = False
        p_dict["configured"] = p.is_configured()
        data["providers"].append(p_dict)
    data["active_provider"] = config.active_provider.value
    data["theme"] = config.theme.value
    data["mock_mode"] = config.is_mock_mode()
    data["llm_configured"] = config.is_llm_configured()
    return data


def _message_to_dict(msg: Message) -> Dict[str, Any]:
    """将消息转换为字典"""
    data = msg.model_dump()
    data["timestamp"] = msg.timestamp.isoformat()
    data["role"] = msg.role.value
    return data


def _conversation_to_dict(conv: Conversation, include_messages: bool = True) -> Dict[str, Any]:
    """将对话转换为字典"""
    data = conv.model_dump()
    data["created_at"] = conv.created_at.isoformat()
    data["updated_at"] = conv.updated_at.isoformat()
    data["messages"] = []
    if include_messages:
        for msg in conv.messages:
            data["messages"].append(_message_to_dict(msg))
    return data


def _project_to_dict(project: Project, include_details: bool = True) -> Dict[str, Any]:
    """将项目转换为字典"""
    data = project.model_dump()
    data["created_at"] = project.created_at.isoformat()
    data["updated_at"] = project.updated_at.isoformat()
    data["discipline"] = project.discipline.value
    data["status"] = project.status.value
    data["workflow_steps"] = []
    for step in project.workflow_steps:
        step_dict = step.model_dump()
        step_dict["status"] = step.status.value
        if step.started_at:
            step_dict["started_at"] = step.started_at.isoformat()
        if step.completed_at:
            step_dict["completed_at"] = step.completed_at.isoformat()
        data["workflow_steps"].append(step_dict)
    
    if not include_details:
        data.pop("outline", None)
        data.pop("report", None)
        data.pop("experiments", None)
    
    return data


def _literature_to_dict(lit: Literature) -> Dict[str, Any]:
    """将文献转换为字典"""
    data = lit.model_dump()
    data["added_at"] = lit.added_at.isoformat()
    return data


def _generate_conversation_title(first_message: str) -> str:
    """根据首条消息生成对话标题"""
    title = first_message.strip()[:30]
    if len(first_message) > 30:
        title += "..."
    return title


def _sanitize_filename(filename: str) -> str:
    """清理文件名中的非法字符（Windows兼容）"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def _reset_llm_client():
    """重置LLM客户端"""
    from ..llm.client import reset_llm_client as _reset
    _reset()


# ==================== 主函数 ====================


def main():
    """主函数，支持命令行参数"""
    parser = argparse.ArgumentParser(description="SciFlow API服务器")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="监听端口 (默认: 8765)")
    parser.add_argument("--reload", action="store_true", help="启用自动重载（开发模式）")
    
    args = parser.parse_args()
    
    import uvicorn
    
    print("=" * 60)
    print("  SciFlow API 服务器")
    print("=" * 60)
    print(f"  访问地址: http://{args.host}:{args.port}")
    print(f"  API文档: http://{args.host}:{args.port}/docs")
    print(f"  ReDoc文档: http://{args.host}:{args.port}/redoc")
    if args.reload:
        print("  模式: 开发模式 (自动重载已启用)")
    else:
        print("  模式: 生产模式")
    print("=" * 60)
    print()
    
    if args.reload:
        uvicorn.run(
            "sci_flow.server.app:create_app",
            host=args.host,
            port=args.port,
            reload=True,
            factory=True,
            log_level="info"
        )
    else:
        app = create_app()
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )


# 创建应用实例供uvicorn直接导入
app = create_app()


if __name__ == "__main__":
    main()
