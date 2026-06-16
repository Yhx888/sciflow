import click
import json
from pathlib import Path
from sci_flow.config import get_settings, get_data_dir, ensure_directories


@click.group()
def zotero_cli():
    """Zotero 同步模块
    
    用于管理 Zotero 文献库，支持文献添加和查询。
    """
    ensure_directories()


@zotero_cli.command()
@click.option("--api-key", help="Zotero API Key")
@click.option("--user-id", help="Zotero User ID")
def config(api_key, user_id):
    """配置 Zotero 连接参数"""
    settings = get_settings()
    
    if api_key:
        settings.zotero_api_key = api_key
    if user_id:
        settings.zotero_user_id = user_id
    
    config_path = get_data_dir() / "zotero_config.json"
    config_data = {
        "api_key": settings.zotero_api_key or "",
        "user_id": settings.zotero_user_id or ""
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    
    click.echo(f"✅ Zotero 配置已保存至 {config_path}")


@zotero_cli.command()
@click.option("--title", help="文献标题")
@click.option("--authors", help="作者列表，逗号分隔")
@click.option("--year", type=int, help="发表年份")
@click.option("--venue", help="期刊/会议名称")
@click.option("--link", help="论文链接")
def add(title, authors, year, venue, link):
    """添加文献到 Zotero (Mock)"""
    if not title:
        click.echo("❌ 请提供文献标题 (--title)")
        return
    
    config_path = get_data_dir() / "zotero_config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        if config_data.get("api_key") and config_data.get("user_id"):
            click.echo("🔐 使用已配置的 Zotero API")
        else:
            click.echo("⚠️  未配置 Zotero API，使用 Mock 模式")
    else:
        click.echo("⚠️  未找到配置文件，使用 Mock 模式")
    
    paper_data = {
        "title": title,
        "authors": authors.split(",") if authors else [],
        "year": year,
        "venue": venue,
        "link": link,
        "added_at": "2025-01-15"
    }
    
    library_path = get_data_dir() / "zotero_library.json"
    if library_path.exists():
        with open(library_path, "r", encoding="utf-8") as f:
            library = json.load(f)
    else:
        library = []
    
    library.append(paper_data)
    
    with open(library_path, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2, ensure_ascii=False)
    
    click.echo(f"\n✅ 文献已添加到 Zotero (Mock):")
    click.echo(f"   标题: {title}")
    if authors:
        click.echo(f"   作者: {authors}")
    if year:
        click.echo(f"   年份: {year}")
    if venue:
        click.echo(f"   期刊: {venue}")
    if link:
        click.echo(f"   链接: {link}")


@zotero_cli.command()
def list():
    """列出 Zotero 文献库中的文献 (Mock)"""
    library_path = get_data_dir() / "zotero_library.json"
    
    if not library_path.exists():
        click.echo("📭 Zotero 文献库为空，请先添加文献")
        return
    
    with open(library_path, "r", encoding="utf-8") as f:
        library = json.load(f)
    
    click.echo(f"\n📚 Zotero 文献库 ({len(library)} 篇):")
    for i, paper in enumerate(library, 1):
        click.echo(f"\n{i}. {paper['title']}")
        if paper.get("authors"):
            click.echo(f"   作者: {', '.join(paper['authors'])}")
        if paper.get("year"):
            click.echo(f"   年份: {paper['year']}")
        if paper.get("venue"):
            click.echo(f"   期刊: {paper['venue']}")
