"""
SciFlow CLI - 科研全流程Agent编排器命令行工具
基于Click框架，使用colorama实现彩色输出，支持新的核心模块架构
"""

import asyncio
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

import click
from colorama import Fore, Style, init as colorama_init

from sci_flow import __version__

# 初始化colorama，Windows兼容
colorama_init(autoreset=True)

# 尝试导入rich，如果不可用则降级
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# ==================== 核心模块导入（带降级处理）====================
_CONFIG = None
_DB = None
_LLM_CLIENT = None
_LIT_MANAGER = None
_RESULT_GENERATOR = None
_WORKFLOW_ENGINE = None

def _lazy_import_core():
    """延迟导入核心模块，避免启动时失败"""
    global _CONFIG, _DB, _LLM_CLIENT, _LIT_MANAGER, _WORKFLOW_ENGINE, _RESULT_GENERATOR
    try:
        from sci_flow.core.config import get_config
        _CONFIG = get_config()
    except Exception as e:
        click.echo(f"{Fore.YELLOW}⚠  配置模块加载失败: {e}{Style.RESET_ALL}")
    
    try:
        from sci_flow.core.database import get_database
        _DB = get_database()
    except Exception as e:
        click.echo(f"{Fore.YELLOW}⚠  数据库模块加载失败: {e}{Style.RESET_ALL}")
    
    try:
        from sci_flow.llm.client import get_llm_client
        _LLM_CLIENT = get_llm_client(_CONFIG)
    except Exception as e:
        click.echo(f"{Fore.YELLOW}⚠  LLM客户端加载失败: {e}{Style.RESET_ALL}")
    
    try:
        from sci_flow.core.literature import get_literature_manager
        _LIT_MANAGER = get_literature_manager(_CONFIG, _DB, _LLM_CLIENT)
    except Exception as e:
        click.echo(f"{Fore.YELLOW}⚠  文献管理模块加载失败: {e}{Style.RESET_ALL}")
    
    try:
        from sci_flow.core.generator import get_result_generator
        _RESULT_GENERATOR = get_result_generator(_CONFIG, _LLM_CLIENT, _LIT_MANAGER)
    except Exception as e:
        click.echo(f"{Fore.YELLOW}⚠  成果生成模块加载失败: {e}{Style.RESET_ALL}")
    
    try:
        from sci_flow.core.workflow import get_workflow_engine
        _WORKFLOW_ENGINE = get_workflow_engine(_CONFIG, _DB, _LLM_CLIENT, _LIT_MANAGER, _RESULT_GENERATOR)
    except Exception as e:
        click.echo(f"{Fore.YELLOW}⚠  工作流引擎加载失败: {e}{Style.RESET_ALL}")


# ==================== 输出美化工具函数 ====================

def print_header(title: str):
    """打印带装饰线的标题"""
    line = "═" * 60
    click.echo(f"{Fore.CYAN}{line}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{line}{Style.RESET_ALL}")
    click.echo()

def print_step(step_num: int, total: int, name: str, status: str = "pending"):
    """打印步骤指示器"""
    icons = {
        "pending": "⏳",
        "running": "▶",
        "completed": "✓",
        "error": "✗"
    }
    colors = {
        "pending": Fore.YELLOW,
        "running": Fore.BLUE,
        "completed": Fore.GREEN,
        "error": Fore.RED
    }
    icon = icons.get(status, "•")
    color = colors.get(status, Fore.WHITE)
    prefix = f"[{step_num}/{total}]"
    click.echo(f"  {color}{icon}{Style.RESET_ALL} {Fore.WHITE}{prefix}{Style.RESET_ALL} {name}")

def print_success(message: str):
    """打印成功消息"""
    click.echo(f"{Fore.GREEN}✓{Style.RESET_ALL} {message}")

def print_error(message: str):
    """打印错误消息"""
    click.echo(f"{Fore.RED}✗{Style.RESET_ALL} {message}")

def print_warning(message: str):
    """打印警告消息"""
    click.echo(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {message}")

def print_info(message: str):
    """打印信息消息"""
    click.echo(f"{Fore.BLUE}ℹ{Style.RESET_ALL} {message}")

def print_divider(char: str = "─", length: int = 60):
    """打印分隔线"""
    click.echo(f"{Fore.CYAN}{char * length}{Style.RESET_ALL}")


# ==================== 异步工具 ====================

def run_async(coro):
    """在同步上下文中运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ==================== 主CLI入口 ====================

@click.group(invoke_without_command=True)
@click.version_option(__version__, "--version", "-v", message=f"SciFlow v{__version__}")
@click.pass_context
def cli(ctx):
    """SciFlow - 科研全流程Agent编排器
    
    用自然语言串联文献管理、技术文档、数据分析、论文撰写，实现科研工作流自动化。
    
    使用 sciflow guide 查看新手引导。
    """
    _lazy_import_core()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        if _CONFIG and _CONFIG.first_run:
            click.echo()
            print_warning("看起来是首次使用，建议运行 sciflow guide 查看新手引导")
            print_warning("或者运行 sciflow config init 进行初始配置")


# ==================== app 命令组 - 桌面应用 ====================

@cli.group()
def app():
    """桌面应用和API服务器管理"""
    pass

@app.command("start")
def app_start():
    """启动桌面应用（包含API服务器和GUI窗口）"""
    print_header("🚀 SciFlow 桌面应用")
    try:
        from sci_flow.desktop.launcher import main as launcher_main
        launcher_main()
    except ImportError as e:
        print_error(f"桌面应用模块不可用: {e}")
        print_info("尝试使用 sciflow app serve 启动API服务器")
    except Exception as e:
        print_error(f"启动桌面应用失败: {e}")

@app.command("serve")
@click.option("--host", default="127.0.0.1", help="监听地址")
@click.option("--port", default=8765, help="监听端口")
@click.option("--no-browser", is_flag=True, help="不自动打开浏览器")
def app_serve(host, port, no_browser):
    """仅启动API服务器（不启动桌面窗口）"""
    print_header("🌐 SciFlow API 服务器")
    
    try:
        import uvicorn
        from sci_flow.server.app import create_app
        
        app_instance = create_app()
        url = f"http://{host}:{port}"
        
        click.echo(f"  {Fore.GREEN}服务器地址:{Style.RESET_ALL} {url}")
        click.echo(f"  {Fore.GREEN}API文档:{Style.RESET_ALL} {url}/docs")
        click.echo(f"  {Fore.GREEN}Web界面:{Style.RESET_ALL} {url}/static/index.html")
        print_divider()
        click.echo()
        
        if not no_browser:
            print_info("正在打开浏览器...")
            threading.Timer(1.5, lambda: webbrowser.open(f"{url}/static/index.html")).start()
        
        print_info("按 Ctrl+C 停止服务器")
        click.echo()
        
        uvicorn.run(
            app_instance,
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
        )
    except ImportError as e:
        print_error(f"服务器依赖缺失: {e}")
        print_info("请确保已安装 fastapi 和 uvicorn: pip install fastapi uvicorn")
    except Exception as e:
        if "Address already in use" in str(e):
            print_error(f"端口 {port} 已被占用")
            print_info(f"尝试其他端口: sciflow app serve --port {port + 1}")
        else:
            print_error(f"启动服务器失败: {e}")


# ==================== config 命令组 - 配置管理 ====================

@cli.group()
def config():
    """配置管理 - 设置LLM提供商、API Key等"""
    pass

@config.command("show")
def config_show():
    """显示当前配置"""
    print_header("⚙️  SciFlow 配置信息")
    
    if not _CONFIG:
        print_error("配置模块未加载")
        return
    
    click.echo(f"  {Fore.CYAN}版本:{Style.RESET_ALL} {_CONFIG.version}")
    click.echo(f"  {Fore.CYAN}数据目录:{Style.RESET_ALL} {_CONFIG.data_dir}")
    click.echo(f"  {Fore.CYAN}当前提供商:{Style.RESET_ALL} {_CONFIG.active_provider.value}")
    click.echo(f"  {Fore.CYAN}Mock模式:{Style.RESET_ALL} {'是' if _CONFIG.is_mock_mode() else '否'}")
    click.echo(f"  {Fore.CYAN}流式输出:{Style.RESET_ALL} {'开启' if _CONFIG.stream_enabled else '关闭'}")
    click.echo(f"  {Fore.CYAN}主题:{Style.RESET_ALL} {_CONFIG.theme.value}")
    click.echo(f"  {Fore.CYAN}语言:{Style.RESET_ALL} {_CONFIG.language}")
    print_divider()
    click.echo()
    
    click.echo(f"{Fore.CYAN}已配置的LLM提供商:{Style.RESET_ALL}")
    click.echo()
    for provider in _CONFIG.providers:
        status_icon = f"{Fore.GREEN}✓{Style.RESET_ALL}" if provider.is_configured() else f"{Fore.YELLOW}○{Style.RESET_ALL}"
        active_icon = f"{Fore.BLUE}●{Style.RESET_ALL}" if provider.name == _CONFIG.active_provider else " "
        click.echo(f"  {active_icon} {status_icon} {provider.display_name} ({provider.name.value})")
        if provider.api_base:
            click.echo(f"      API地址: {provider.api_base}")
        if provider.model:
            click.echo(f"      模型: {provider.model}")
        if provider.api_key:
            click.echo(f"      API Key: ******{provider.api_key[-4:] if len(provider.api_key) > 4 else ''}")
        click.echo()

@config.command("set-provider")
@click.option("--name", help="提供商名称 (openai/anthropic/deepseek/zhipu/qwen/ollama)")
def config_set_provider(name):
    """设置当前使用的LLM提供商（交互式引导）"""
    print_header("🔧 设置LLM提供商")
    
    if not _CONFIG:
        print_error("配置模块未加载")
        return
    
    providers = [p for p in _CONFIG.providers if p.enabled]
    
    if not name:
        click.echo(f"{Fore.CYAN}可用的LLM提供商:{Style.RESET_ALL}")
        click.echo()
        for i, provider in enumerate(providers, 1):
            configured = f" {Fore.GREEN}(已配置){Style.RESET_ALL}" if provider.is_configured() else ""
            click.echo(f"  {i}. {provider.display_name} ({provider.name.value}){configured}")
        click.echo()
        
        choice = click.prompt("请选择提供商编号", type=int)
        if choice < 1 or choice > len(providers):
            print_error("无效的选择")
            return
        selected = providers[choice - 1]
    else:
        from sci_flow.core.models import LLMProvider
        try:
            provider_name = LLMProvider(name)
            selected = next((p for p in providers if p.name == provider_name), None)
            if not selected:
                print_error(f"未找到提供商: {name}")
                return
        except ValueError:
            print_error(f"无效的提供商名称: {name}")
            return
    
    _CONFIG.set_active_provider(selected.name)
    _CONFIG.save()
    print_success(f"已设置当前提供商为: {selected.display_name}")
    
    if not selected.is_configured():
        print_warning("该提供商尚未配置API Key，请运行 sciflow config set-key 进行配置")

@config.command("set-key")
@click.option("--provider", help="提供商名称")
@click.option("--key", help="API Key")
@click.option("--api-base", help="自定义API基础URL")
@click.option("--model", help="模型名称")
def config_set_key(provider, key, api_base, model):
    """设置API Key和相关配置"""
    print_header("🔑 配置API Key")
    
    if not _CONFIG:
        print_error("配置模块未加载")
        return
    
    from sci_flow.core.models import LLMProvider
    
    if not provider:
        active = _CONFIG.get_active_provider()
        if active:
            provider = active.name.value
            print_info(f"当前提供商: {active.display_name}")
        else:
            provider = click.prompt("请输入提供商名称 (openai/anthropic/deepseek/zhipu/qwen/ollama)")
    
    try:
        provider_name = LLMProvider(provider)
    except ValueError:
        print_error(f"无效的提供商名称: {provider}")
        return
    
    target_provider = _CONFIG.get_provider(provider_name)
    if not target_provider:
        print_error(f"未找到提供商: {provider}")
        return
    
    click.echo(f"正在配置 {target_provider.display_name}...")
    click.echo()
    
    if not key and provider_name != LLMProvider.OLLAMA:
        key = click.prompt("请输入API Key", hide_input=True)
    
    if not api_base:
        custom_base = click.confirm("是否使用自定义API地址?", default=False)
        if custom_base:
            api_base = click.prompt("请输入API基础URL", default=target_provider.api_base or "")
    
    if not model:
        default_model = target_provider.model or ""
        model_input = click.prompt("请输入模型名称", default=default_model)
        if model_input:
            model = model_input
    
    kwargs = {}
    if key:
        kwargs["api_key"] = key
    if api_base:
        kwargs["api_base"] = api_base
    if model:
        kwargs["model"] = model
    
    _CONFIG.update_provider(provider_name, **kwargs)
    _CONFIG.save()
    
    print_success("配置已保存")
    
    if click.confirm("是否测试连接?"):
        ctx = click.get_current_context()
        ctx.invoke(config_test, provider=provider_name.value)

@config.command("test")
@click.option("--provider", help="指定测试的提供商")
def config_test(provider):
    """测试API连接是否正常"""
    print_header("🔍 测试API连接")
    
    if not _CONFIG or not _LLM_CLIENT:
        print_error("核心模块未加载，请先运行 sciflow config init 完成初始化")
        return
    
    from sci_flow.core.models import LLMProvider
    import time
    
    test_provider = None
    if provider:
        try:
            test_provider = LLMProvider(provider)
        except ValueError:
            print_error(f"无效的提供商名称: {provider}")
            return
    
    if test_provider:
        target = _CONFIG.get_provider(test_provider)
        if not target:
            print_error(f"未找到提供商: {provider}")
            return
        if not target.is_configured():
            print_warning(f"{target.display_name} 尚未配置API Key")
            if click.confirm("是否先进行配置?"):
                ctx = click.get_current_context()
                ctx.invoke(config_set_key, provider=provider)
                return
    
    print_info("正在测试连接...")
    start_time = time.time()
    
    try:
        async def test_conn():
            test_prompt = "你好，请回复'连接成功'四个字。"
            return await _LLM_CLIENT.achat(
                [{"role": "user", "content": test_prompt}],
                max_tokens=20,
                temperature=0.1
            )
        
        response = run_async(test_conn())
        elapsed = (time.time() - start_time) * 1000
        
        print_success(f"连接成功! (耗时 {elapsed:.0f}ms)")
        print_divider()
        click.echo(f"  响应: {Fore.GREEN}{response}{Style.RESET_ALL}")
        click.echo()
        
        if _CONFIG.is_mock_mode():
            print_warning("注意: 当前使用Mock模式，未真实连接API")
            print_info("配置真实API Key后可使用完整功能")
    except Exception as e:
        print_error(f"连接失败: {e}")
        print_info("请检查API Key和网络连接，或稍后重试")

@config.command("init")
def config_init():
    """初始化配置 - 引导式设置"""
    print_header("🎉 欢迎使用 SciFlow!")
    click.echo("  接下来将引导您完成初始配置。")
    click.echo()
    
    if not _CONFIG:
        print_error("配置模块未加载")
        return
    
    click.echo(f"{Fore.CYAN}步骤 1/3: 选择LLM提供商{Style.RESET_ALL}")
    print_divider("-", 40)
    click.echo()
    
    providers = [p for p in _CONFIG.providers if p.enabled]
    for i, provider in enumerate(providers, 1):
        ollama_note = " (本地部署，无需API Key)" if provider.name.value == "ollama" else ""
        click.echo(f"  {i}. {provider.display_name}{ollama_note}")
    click.echo()
    
    choice = click.prompt("请选择提供商编号", type=int, default=1)
    if choice < 1 or choice > len(providers):
        print_warning("无效选择，使用默认值 OpenAI")
        choice = 1
    
    selected = providers[choice - 1]
    _CONFIG.set_active_provider(selected.name)
    
    click.echo()
    click.echo(f"{Fore.CYAN}步骤 2/3: 配置API参数{Style.RESET_ALL}")
    print_divider("-", 40)
    click.echo()
    
    from sci_flow.core.models import LLMProvider
    if selected.name != LLMProvider.OLLAMA:
        api_key = click.prompt(f"请输入 {selected.display_name} 的API Key", hide_input=True, default="")
        if api_key:
            kwargs = {"api_key": api_key}
            
            use_custom_base = click.confirm("是否使用自定义API地址?", default=False)
            if use_custom_base:
                api_base = click.prompt("请输入API基础URL", default=selected.api_base or "")
                if api_base:
                    kwargs["api_base"] = api_base
            
            model = click.prompt("请输入模型名称", default=selected.model or "")
            if model:
                kwargs["model"] = model
            
            _CONFIG.update_provider(selected.name, **kwargs)
    else:
        model = click.prompt("请输入Ollama模型名称", default=selected.model or "llama3")
        api_base = click.prompt("请输入Ollama地址", default=selected.api_base or "http://localhost:11434")
        _CONFIG.update_provider(selected.name, model=model, api_base=api_base, enabled=True)
    
    click.echo()
    click.echo(f"{Fore.CYAN}步骤 3/3: 保存配置{Style.RESET_ALL}")
    print_divider("-", 40)
    click.echo()
    
    _CONFIG.complete_first_run()
    print_success("配置已保存!")
    click.echo()
    
    print_info(f"数据目录: {_CONFIG.data_dir}")
    print_info(f"配置文件: {_CONFIG.get_config_path()}")
    click.echo()
    
    if selected.is_configured():
        if click.confirm("是否立即测试API连接?"):
            ctx = click.get_current_context()
            ctx.invoke(config_test)
    else:
        print_warning("您可以稍后随时运行 sciflow config set-key 来配置API Key")
        print_info("现在可以使用Mock模式体验所有功能!")
    
    click.echo()
    print_success("初始化完成! 运行 sciflow guide 查看使用指南")


# ==================== literature 命令组 - 文献调研 ====================

@cli.group()
def literature():
    """文献调研 - 搜索、分析和管理学术文献"""
    pass

@literature.command("search")
@click.argument("topic")
@click.option("--limit", "-n", default=10, help="返回文献数量")
@click.option("--mock", is_flag=True, help="强制使用Mock模式")
@click.option("--discipline", "-d", default="computer_science", 
              type=click.Choice(["computer_science", "biology", "physics", "chemistry", 
                                  "materials_science", "mathematics", "medicine", "other"]),
              help="学科领域")
def literature_search(topic, limit, mock, discipline):
    """搜索相关文献
    
    TOPIC 是要搜索的研究主题
    """
    print_header(f"📚 文献搜索: {topic}")
    
    if not _LIT_MANAGER:
        print_error("文献管理模块未加载")
        return
    
    from sci_flow.core.models import Discipline
    try:
        disc = Discipline(discipline)
    except ValueError:
        disc = Discipline.COMPUTER_SCIENCE
    
    use_mock = mock or (_CONFIG.is_mock_mode() if _CONFIG else True)
    
    if use_mock:
        print_info("使用Mock模式 (演示数据)")
    click.echo()
    
    with console.status(f"{Fore.BLUE}正在搜索文献...{Style.RESET_ALL}") if RICH_AVAILABLE else click.progressbar(length=1, label="搜索中"):
        try:
            lit_list = run_async(_LIT_MANAGER.search(topic, limit=limit, discipline=disc, use_mock=use_mock))
        except Exception as e:
            print_error(f"搜索失败: {e}")
            print_info("尝试使用Mock模式...")
            lit_list = _LIT_MANAGER.generate_mock_literature(topic, limit, disc)
    
    print_success(f"找到 {len(lit_list)} 篇相关文献")
    print_divider()
    click.echo()
    
    for i, lit in enumerate(lit_list, 1):
        authors_str = ", ".join(lit.authors[:3])
        if len(lit.authors) > 3:
            authors_str += " 等"
        
        click.echo(f"{Fore.CYAN}[{i}]{Style.RESET_ALL} {Fore.WHITE}{lit.title}{Style.RESET_ALL}")
        click.echo(f"    {Fore.YELLOW}{authors_str}{Style.RESET_ALL}")
        meta_parts = []
        if lit.year:
            meta_parts.append(str(lit.year))
        if lit.venue:
            meta_parts.append(lit.venue)
        meta_parts.append(f"引用: {lit.citations}")
        click.echo(f"    {Fore.GREEN}{' | '.join(meta_parts)}{Style.RESET_ALL}")
        if lit.abstract:
            abstract_short = lit.abstract[:100] + "..." if len(lit.abstract) > 100 else lit.abstract
            click.echo(f"    {Style.DIM}{abstract_short}{Style.RESET_ALL}")
        click.echo()
    
    if lit_list and click.confirm("是否保存这些文献到本地数据库?"):
        saved_count = 0
        for lit in lit_list:
            try:
                _LIT_MANAGER.save_literature(lit)
                saved_count += 1
            except Exception:
                pass
        print_success(f"已保存 {saved_count} 篇文献到本地数据库")

@literature.command("bibtex")
@click.option("--output", "-o", type=click.Path(), help="输出到文件")
@click.option("--query", "-q", help="搜索关键词筛选文献")
def literature_bibtex(output, query):
    """导出文献为BibTeX格式"""
    print_header("📄 BibTeX 导出")
    
    if not _LIT_MANAGER or not _DB:
        print_error("文献管理模块未加载")
        return
    
    if query:
        lit_list = _LIT_MANAGER.search_local(query)
    else:
        lit_list = _LIT_MANAGER.list_literature()
    
    if not lit_list:
        print_warning("没有找到文献")
        print_info("请先使用 sciflow literature search <topic> 搜索文献")
        return
    
    bibtex_content = _LIT_MANAGER.generate_bibtex(lit_list)
    
    if output:
        output_path = Path(output)
        output_path.write_text(bibtex_content, encoding="utf-8")
        print_success(f"BibTeX已导出到: {output_path}")
    else:
        print_divider()
        click.echo(bibtex_content)
        print_divider()
        click.echo()
        print_info(f"共 {len(lit_list)} 条文献记录")

@literature.command("matrix")
@click.option("--query", "-q", help="搜索关键词筛选文献")
def literature_matrix(query):
    """生成文献对比分析矩阵"""
    print_header("📊 文献矩阵分析")
    
    if not _LIT_MANAGER or not _DB:
        print_error("文献管理模块未加载")
        return
    
    if query:
        lit_list = _LIT_MANAGER.search_local(query)
    else:
        lit_list = _LIT_MANAGER.list_literature(limit=20)
    
    if not lit_list:
        print_warning("没有找到文献")
        return
    
    matrix = _LIT_MANAGER.generate_literature_matrix(lit_list)
    click.echo(matrix)
    click.echo()
    print_success(f"分析完成，共 {len(lit_list)} 篇文献")

@literature.command("trend")
@click.option("--query", "-q", help="搜索关键词筛选文献")
def literature_trend(query):
    """研究趋势分析"""
    print_header("📈 研究趋势分析")
    
    if not _LIT_MANAGER or not _DB:
        print_error("文献管理模块未加载")
        return
    
    if query:
        lit_list = _LIT_MANAGER.search_local(query)
    else:
        lit_list = _LIT_MANAGER.list_literature()
    
    if not lit_list:
        print_warning("没有找到文献")
        print_info("请先搜索文献或使用Mock模式体验")
        return
    
    trend = _LIT_MANAGER.generate_trend_summary(lit_list)
    click.echo(trend)
    click.echo()


# ==================== project 命令组 - 项目管理 ====================

@cli.group()
def project():
    """项目管理 - 创建、运行和管理科研项目"""
    pass

@project.command("list")
@click.option("--limit", "-n", default=20, help="显示项目数量")
def project_list(limit):
    """列出所有项目"""
    print_header("📋 项目列表")
    
    if not _DB:
        print_error("数据库模块未加载")
        return
    
    projects = _DB.list_projects(limit=limit)
    
    if not projects:
        print_warning("暂无项目")
        print_info("使用 sciflow project create 创建第一个项目")
        return
    
    click.echo(f"  {Fore.CYAN}{'ID':<10} {'主题':<30} {'作者':<12} {'状态':<12} {'更新时间'}{Style.RESET_ALL}")
    print_divider("-", 80)
    
    status_colors = {
        "draft": Fore.YELLOW,
        "in_progress": Fore.BLUE,
        "completed": Fore.GREEN,
        "archived": Style.DIM,
        "error": Fore.RED,
    }
    
    for p in projects:
        status_color = status_colors.get(p.status.value, Fore.WHITE)
        topic_short = p.topic[:28] + "..." if len(p.topic) > 30 else p.topic
        author_short = p.author[:10] + "..." if len(p.author) > 12 else p.author
        updated_str = p.updated_at.strftime("%Y-%m-%d %H:%M")
        
        click.echo(
            f"  {p.id[:8]:<10} "
            f"{topic_short:<30} "
            f"{author_short:<12} "
            f"{status_color}{p.status.value:<12}{Style.RESET_ALL} "
            f"{updated_str}"
        )
    click.echo()
    print_info(f"共 {len(projects)} 个项目")

@project.command("create")
@click.option("--topic", "-t", required=True, help="研究主题")
@click.option("--author", "-a", default="", help="作者姓名")
@click.option("--affiliation", default="", help="作者单位")
@click.option("--description", "-d", default="", help="项目描述")
@click.option("--discipline", default="computer_science",
              type=click.Choice(["computer_science", "biology", "physics", "chemistry", 
                                  "materials_science", "mathematics", "medicine", "other"]),
              help="学科领域")
def project_create(topic, author, affiliation, description, discipline):
    """创建新项目"""
    print_header("🆕 创建新项目")
    
    if not _DB:
        print_error("数据库模块未加载")
        return
    
    from sci_flow.core.models import Project, Discipline
    try:
        disc = Discipline(discipline)
    except ValueError:
        disc = Discipline.COMPUTER_SCIENCE
    
    new_project = Project(
        topic=topic,
        author=author,
        affiliation=affiliation,
        description=description,
        discipline=disc,
    )
    
    created = _DB.create_project(new_project)
    
    if _CONFIG:
        _CONFIG.add_recent_project(created.id)
        _CONFIG.save()
    
    print_success("项目创建成功!")
    print_divider("-", 50)
    click.echo(f"  项目ID: {Fore.CYAN}{created.id}{Style.RESET_ALL}")
    click.echo(f"  研究主题: {topic}")
    click.echo(f"  作者: {author or '(未设置)'}")
    click.echo(f"  单位: {affiliation or '(未设置)'}")
    click.echo()
    print_info(f"运行 sciflow project run {created.id[:8]}... 启动工作流")

@project.command("run")
@click.argument("project_id")
def project_run(project_id):
    """运行项目工作流
    
    PROJECT_ID 是项目ID（可输入前8位）
    """
    print_header("⚡ 运行工作流")
    
    if not _DB or not _WORKFLOW_ENGINE:
        print_error("核心模块未加载")
        return
    
    proj = _find_project(project_id)
    if not proj:
        return
    
    print_info(f"项目: {proj.topic}")
    print_info(f"作者: {proj.author or '(未设置)'}")
    click.echo()
    
    click.echo(f"{Fore.CYAN}工作流步骤:{Style.RESET_ALL}")
    from sci_flow.core.workflow import WORKFLOW_STEPS
    for i, step in enumerate(WORKFLOW_STEPS, 1):
        print_step(i, len(WORKFLOW_STEPS), step["name"], "pending")
    click.echo()
    
    if not click.confirm("确认开始运行工作流?"):
        print_info("已取消")
        return
    
    click.echo()
    _run_workflow_cli(proj)

@project.command("delete")
@click.argument("project_id")
@click.confirmation_option(prompt="确定要删除该项目吗? 此操作不可撤销!")
def project_delete(project_id):
    """删除项目
    
    PROJECT_ID 是项目ID
    """
    print_header("🗑️  删除项目")
    
    if not _DB:
        print_error("数据库模块未加载")
        return
    
    proj = _find_project(project_id)
    if not proj:
        return
    
    _DB.delete_project(proj.id)
    print_success(f"项目已删除: {proj.topic}")

@project.command("export")
@click.argument("project_id")
@click.option("--output", "-o", type=click.Path(), help="输出目录")
def project_export(project_id, output):
    """导出项目成果
    
    PROJECT_ID 是项目ID
    """
    print_header("📦 导出项目成果")
    
    if not _DB:
        print_error("数据库模块未加载")
        return
    
    proj = _find_project(project_id)
    if not proj:
        return
    
    if not proj.report:
        print_warning("该项目尚未生成报告")
        print_info("请先运行 sciflow project run <project_id>")
        return
    
    if output:
        export_dir = Path(output)
    else:
        export_dir = Path.cwd() / f"export_{proj.id[:8]}"
    
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # 导出报告
    report_path = export_dir / f"{proj.topic}_report.md"
    report_path.write_text(proj.report, encoding="utf-8")
    print_success(f"报告: {report_path}")
    
    # 导出大纲
    if proj.outline:
        outline_path = export_dir / "outline.md"
        outline_path.write_text(proj.outline, encoding="utf-8")
        print_success(f"大纲: {outline_path}")
    
    # 导出文献
    if _LIT_MANAGER:
        project_lit = _LIT_MANAGER.get_project_literature(proj.id)
        if project_lit:
            bib_path = export_dir / "references.bib"
            bib_path.write_text(_LIT_MANAGER.generate_bibtex(project_lit), encoding="utf-8")
            print_success(f"参考文献(BibTeX): {bib_path}")
            
            gbt_path = export_dir / "references_gbt7714.txt"
            gbt_path.write_text(_LIT_MANAGER.generate_gbt7714(project_lit), encoding="utf-8")
            print_success(f"参考文献(GB/T 7714): {gbt_path}")
    
    # 打包ZIP
    import zipfile
    zip_path = export_dir.parent / f"{proj.topic}_{proj.id[:8]}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in export_dir.iterdir():
            if f.is_file():
                zf.write(f, f.name)
    
    print_divider()
    print_success(f"导出完成!")
    print_info(f"导出目录: {export_dir}")
    print_info(f"打包文件: {zip_path}")

def _find_project(project_id: str):
    """查找项目（支持模糊匹配ID前缀）"""
    if not _DB:
        return None
    
    proj = _DB.get_project(project_id)
    if proj:
        return proj
    
    projects = _DB.list_projects(limit=100)
    matches = [p for p in projects if p.id.startswith(project_id)]
    
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print_warning(f"找到多个匹配的项目，请使用完整ID:")
        for m in matches:
            click.echo(f"  {m.id} - {m.topic}")
        return None
    else:
        print_error(f"未找到项目: {project_id}")
        print_info("使用 sciflow project list 查看所有项目")
        return None

def _run_workflow_cli(project):
    """在CLI中运行工作流"""
    from sci_flow.core.workflow import WORKFLOW_STEPS, WorkflowEventType
    
    step_results = {}
    current_step = 0
    has_error = False
    
    async def workflow_runner():
        nonlocal current_step, has_error
        try:
            async for event in _WORKFLOW_ENGINE.run_workflow(project):
                if event.event_type == WorkflowEventType.STEP_STARTED:
                    current_step = event.step_index or 0
                    for i in range(len(WORKFLOW_STEPS)):
                        if i < current_step:
                            print_step(i+1, len(WORKFLOW_STEPS), WORKFLOW_STEPS[i]["name"], "completed")
                        elif i == current_step:
                            print_step(i+1, len(WORKFLOW_STEPS), WORKFLOW_STEPS[i]["name"], "running")
                        else:
                            pass
                    if event.message:
                        click.echo(f"      {Fore.BLUE}→{Style.RESET_ALL} {event.message}")
                elif event.event_type == WorkflowEventType.STEP_PROGRESS:
                    msg = event.message or f"进度: {int(event.progress * 100)}%"
                    click.echo(f"      {Fore.BLUE}→{Style.RESET_ALL} {msg}")
                elif event.event_type == WorkflowEventType.STEP_COMPLETED:
                    if event.data:
                        step_results[current_step] = event.data
                elif event.event_type == WorkflowEventType.STEP_ERROR:
                    has_error = True
                    click.echo(f"      {Fore.RED}✗{Style.RESET_ALL} {event.message}")
                elif event.event_type == WorkflowEventType.WORKFLOW_COMPLETED:
                    for i in range(len(WORKFLOW_STEPS)):
                        print_step(i+1, len(WORKFLOW_STEPS), WORKFLOW_STEPS[i]["name"], "completed")
        except Exception as e:
            has_error = True
            print_error(f"工作流执行出错: {e}")
    
    run_async(workflow_runner())
    
    click.echo()
    print_divider()
    if has_error:
        print_error("工作流执行过程中出现错误")
    else:
        print_success("工作流执行完成! 🎉")
        click.echo()
        print_info(f"项目ID: {project.id}")
        print_info(f"运行 sciflow project export {project.id[:8]}... 导出成果")


# ==================== chat 命令组 - 交互式对话 ====================

@cli.command()
@click.option("--project", "-p", help="关联的项目ID")
def chat(project):
    """进入交互式对话模式（类似ChatGPT CLI）
    
    支持多行输入，流式输出。
    命令:
      /exit    退出对话
      /new     开始新对话
      /help    显示帮助
    """
    print_header("💬 SciFlow 对话助手")
    
    if not _DB or not _LLM_CLIENT:
        print_error("核心模块未加载，请先完成配置")
        return
    
    from sci_flow.core.models import Conversation, Message, MessageRole
    
    project_obj = None
    if project:
        project_obj = _find_project(project)
        if not project_obj:
            return
    
    conversation = Conversation(project_id=project_obj.id if project_obj else None)
    _DB.create_conversation(conversation)
    
    if project_obj:
        project_obj.add_conversation(conversation.id)
        _DB.update_project(project_obj)
        print_info(f"已关联到项目: {project_obj.topic}")
    
    print_info("输入您的问题开始对话，/help 查看命令，/exit 退出")
    print_divider()
    click.echo()
    
    while True:
        try:
            user_input_lines = []
            
            while True:
                prompt = f"{Fore.GREEN}You{Style.RESET_ALL}: " if not user_input_lines else "... "
                line = click.prompt(prompt, default="", show_default=False)
                
                if not line and user_input_lines:
                    break
                if line:
                    if line.startswith("/"):
                        break
                    user_input_lines.append(line)
                    break
                elif not user_input_lines:
                    continue
            
            full_input = "\n".join(user_input_lines)
            
            if line.startswith("/"):
                cmd = line.strip().lower()
                if cmd in ("/exit", "/quit", "/q"):
                    print_info("再见!")
                    break
                elif cmd in ("/new", "/reset"):
                    conversation = Conversation(project_id=project_obj.id if project_obj else None)
                    _DB.create_conversation(conversation)
                    if project_obj:
                        project_obj.add_conversation(conversation.id)
                        _DB.update_project(project_obj)
                    print_success("已开始新对话")
                    print_divider()
                    continue
                elif cmd in ("/help", "/?"):
                    _chat_help()
                    continue
                else:
                    print_warning(f"未知命令: {cmd}")
                    _chat_help()
                    continue
            
            if not full_input.strip():
                continue
            
            user_msg = Message(role=MessageRole.USER, content=full_input)
            _DB.create_message(conversation.id, user_msg)
            conversation.add_message(user_msg)
            
            messages_for_llm = []
            for msg in conversation.messages:
                messages_for_llm.append({"role": msg.role.value, "content": msg.content})
            
            click.echo(f"{Fore.BLUE}SciFlow{Style.RESET_ALL}: ", nl=False)
            
            full_response = ""
            use_stream = _CONFIG.stream_enabled if _CONFIG else True
            
            try:
                if use_stream:
                    stream = run_async(_LLM_CLIENT.achat(messages_for_llm, stream=True))
                    for chunk in stream:
                        if chunk:
                            full_response += chunk
                            click.echo(chunk, nl=False)
                    click.echo()
                else:
                    response = run_async(_LLM_CLIENT.achat(messages_for_llm, stream=False))
                    full_response = response
                    click.echo(response)
            except Exception as e:
                error_msg = f"生成响应时出错: {e}"
                print_error(error_msg)
                full_response = error_msg
            
            click.echo()
            
            assistant_msg = Message(role=MessageRole.ASSISTANT, content=full_response)
            _DB.create_message(conversation.id, assistant_msg)
            conversation.add_message(assistant_msg)
            
            if conversation.title == "新对话" and len(full_input) > 5:
                conversation.title = full_input[:30] + ("..." if len(full_input) > 30 else "")
                _DB.update_conversation(conversation)
        
        except KeyboardInterrupt:
            click.echo()
            print_info("输入 /exit 退出")
            continue
        except EOFError:
            click.echo()
            break
        except Exception as e:
            print_error(f"发生错误: {e}")
            continue

def _chat_help():
    """显示对话帮助"""
    click.echo()
    print_divider("-", 40)
    click.echo(f"{Fore.CYAN}可用命令:{Style.RESET_ALL}")
    click.echo("  /exit    退出对话")
    click.echo("  /new     开始新对话")
    click.echo("  /help    显示此帮助")
    print_divider("-", 40)
    click.echo()


# ==================== pipeline 命令组 - 全流程编排 ====================

@cli.group()
def pipeline():
    """全流程编排 - 一键运行完整科研工作流"""
    pass

@pipeline.command("run")
@click.option("--topic", "-t", required=True, help="研究主题")
@click.option("--author", "-a", default="", help="作者姓名")
@click.option("--affiliation", default="", help="作者单位")
@click.option("--mock/--no-mock", default=None, help="是否使用Mock模式")
@click.option("--discipline", "-d", default="computer_science",
              type=click.Choice(["computer_science", "biology", "physics", "chemistry", 
                                  "materials_science", "mathematics", "medicine", "other"]),
              help="学科领域")
def pipeline_run(topic, author, affiliation, mock, discipline):
    """一键运行完整8步科研工作流
    
    包括: 需求理解 → 文献检索 → 文献分析 → 思路生成 → 大纲构建 → 实验设计 → 文档撰写 → 成果导出
    """
    print_header("🚀 SciFlow 科研全流程")
    
    if not _DB or not _WORKFLOW_ENGINE:
        print_error("核心模块未加载")
        return
    
    from sci_flow.core.models import Project, Discipline
    
    if mock is None:
        mock = _CONFIG.is_mock_mode() if _CONFIG else True
    
    if mock:
        print_warning("当前使用Mock模式 (演示数据，无需API配置)")
        print_info("配置真实API Key后可获得真实LLM输出")
        click.echo()
    
    try:
        disc = Discipline(discipline)
    except ValueError:
        disc = Discipline.COMPUTER_SCIENCE
    
    new_project = Project(
        topic=topic,
        author=author,
        affiliation=affiliation,
        discipline=disc,
    )
    created = _DB.create_project(new_project)
    
    if _CONFIG:
        _CONFIG.add_recent_project(created.id)
        _CONFIG.save()
    
    print_info(f"项目ID: {created.id}")
    print_info(f"研究主题: {topic}")
    click.echo()
    
    _run_workflow_cli(created)


# ==================== guide 命令 - 新手引导 ====================

@cli.command()
def guide():
    """新手引导 - 快速开始使用SciFlow"""
    print_header(f"📚 SciFlow v{__version__} 新手引导")
    
    click.echo()
    click.echo(f"{Fore.CYAN}🎯 什么是 SciFlow?{Style.RESET_ALL}")
    print_divider("-", 40)
    click.echo("SciFlow 是一个科研全流程 Agent 编排器，用自然语言串联")
    click.echo("文献管理、技术文档、数据分析、论文撰写，实现科研工作流自动化。")
    click.echo()
    
    click.echo(f"{Fore.CYAN}🚀 快速开始 (3步体验完整流程){Style.RESET_ALL}")
    print_divider("-", 40)
    click.echo()
    
    click.echo(f"  {Fore.GREEN}步骤 1:{Style.RESET_ALL} 初始化配置（可选）")
    click.echo("    sciflow config init")
    click.echo("    （不配置也可以用Mock模式体验）")
    click.echo()
    
    click.echo(f"  {Fore.GREEN}步骤 2:{Style.RESET_ALL} 运行一键全流程演示 (Mock模式)")
    click.echo(f'    sciflow pipeline run --topic "你的研究主题" --author "你的名字"')
    click.echo()
    click.echo("    示例:")
    click.echo(f'    sciflow pipeline run --topic "大语言模型推理优化" --author "张三"')
    click.echo()
    
    click.echo(f"  {Fore.GREEN}步骤 3:{Style.RESET_ALL} 启动Web界面体验可视化操作")
    click.echo("    sciflow app serve")
    click.echo("    或启动桌面应用: sciflow app start")
    click.echo()
    
    click.echo(f"{Fore.CYAN}📋 所有命令概览{Style.RESET_ALL}")
    print_divider("-", 40)
    click.echo()
    
    commands_info = [
        ("config", "配置管理", "show/set-key/set-provider/test/init", "管理LLM配置和API Key"),
        ("app start", "桌面应用", "", "启动桌面应用（GUI窗口）"),
        ("app serve", "API服务器", "--port <port>", "仅启动API服务器"),
        ("literature search", "文献搜索", "<topic> --mock", "搜索相关学术文献"),
        ("literature bibtex", "BibTeX导出", "", "导出文献引用格式"),
        ("literature matrix", "文献矩阵", "", "生成文献对比分析矩阵"),
        ("literature trend", "趋势分析", "", "研究趋势可视化分析"),
        ("project list", "项目列表", "", "查看所有项目"),
        ("project create", "创建项目", "--topic <topic>", "创建新科研项目"),
        ("project run", "运行工作流", "<project_id>", "执行项目的科研工作流"),
        ("project export", "导出成果", "<project_id>", "导出生成的报告等文件"),
        ("chat", "对话助手", "", "进入交互式AI对话模式"),
        ("pipeline run", "一键全流程", "--topic <topic>", "从主题到报告一步完成"),
        ("guide", "新手引导", "", "显示本帮助信息"),
    ]
    
    for cmd_path, name, subcmd, desc in commands_info:
        click.echo(f"  {Fore.CYAN}📌 sciflow {cmd_path:18}{Style.RESET_ALL}")
        click.echo(f"     {Fore.WHITE}{name}{Style.RESET_ALL} - {desc}")
        if subcmd:
            click.echo(f"     用法: sciflow {cmd_path} {subcmd}")
        click.echo()
    
    click.echo(f"{Fore.CYAN}💡 使用技巧{Style.RESET_ALL}")
    print_divider("-", 40)
    click.echo(f"  • 所有模块都支持 {Fore.YELLOW}--mock{Style.RESET_ALL} 参数进行演示，无需配置API")
    click.echo(f"  • 使用 {Fore.YELLOW}--help{Style.RESET_ALL} 查看任意命令的详细帮助")
    click.echo(f"  • 数据存储在用户目录: {Fore.CYAN}~/.sciflow/{Style.RESET_ALL}")
    click.echo(f"  • 建议先使用Mock模式熟悉流程，再配置真实API")
    click.echo()
    
    print_divider("═", 60)
    click.echo(f"  🎉 {Fore.GREEN}开始你的科研自动化之旅吧！{Style.RESET_ALL}")
    print_divider("═", 60)
    click.echo()


# ==================== demo 命令 - 启动Web演示 ====================

@cli.command()
@click.option("--port", default=8765, help="HTTP服务器端口")
@click.option("--no-browser", is_flag=True, help="不自动打开浏览器")
def demo(port, no_browser):
    """启动Web演示 - 启动API服务器并打开浏览器
    
    这是 sciflow app serve 的快捷方式
    """
    ctx = click.get_current_context()
    ctx.invoke(app_serve, host="127.0.0.1", port=port, no_browser=no_browser)


# ==================== 入口点 ====================

def main():
    """CLI主入口"""
    try:
        cli(standalone_mode=False)
    except click.exceptions.Abort:
        click.echo()
        print_info("操作已取消")
        sys.exit(1)
    except click.exceptions.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        click.echo()
        print_info("再见!")
        sys.exit(0)
    except Exception as e:
        print_error(f"发生未预期的错误: {e}")
        if os.environ.get("SCIFLOW_DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
