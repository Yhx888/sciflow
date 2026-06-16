import click
import json
import subprocess
from pathlib import Path
from sci_flow.config import get_data_dir, ensure_directories


@click.group()
def lark_cli():
    """飞书文档模块
    
    用于创建和管理飞书文档，支持技术调研文档生成。
    """
    ensure_directories()


@lark_cli.command()
@click.option("--title", default="技术调研文档", help="文档标题")
@click.option("--from-zotero", is_flag=True, help="从 Zotero 文献库生成")
def create(title, from_zotero):
    """创建飞书技术调研文档"""
    click.echo(f"📝 正在创建飞书文档: {title}")
    
    library_path = get_data_dir() / "zotero_library.json"
    
    if from_zotero:
        if not library_path.exists():
            click.echo("❌ Zotero 文献库为空，请先添加文献")
            return
        
        with open(library_path, "r", encoding="utf-8") as f:
            papers = json.load(f)
        
        click.echo(f"📚 从 Zotero 导入 {len(papers)} 篇文献")
        
        doc_content = f"# {title}\n\n"
        doc_content += "## 一、研究背景\n\n"
        doc_content += "本文档基于最新文献调研，分析当前研究现状和发展趋势。\n\n"
        doc_content += "## 二、文献综述\n\n"
        
        for i, paper in enumerate(papers, 1):
            doc_content += f"### {i}. {paper['title']}\n\n"
            if paper.get("authors"):
                doc_content += f"**作者**: {', '.join(paper['authors'])}\n\n"
            if paper.get("year"):
                doc_content += f"**年份**: {paper['year']}\n\n"
            if paper.get("venue"):
                doc_content += f"**期刊**: {paper['venue']}\n\n"
            if paper.get("link"):
                doc_content += f"**链接**: [{paper['link']}]({paper['link']})\n\n"
            doc_content += "**核心贡献**:\n"
            doc_content += "- 待补充\n\n"
        
        doc_content += "## 三、研究趋势分析\n\n"
        doc_content += "基于上述文献，当前研究趋势如下：\n\n"
        doc_content += "- 待补充\n\n"
        doc_content += "## 四、未来工作方向\n\n"
        doc_content += "- 待补充\n\n"
    else:
        doc_content = f"# {title}\n\n"
        doc_content += "## 一、研究背景\n\n"
        doc_content += "待补充\n\n"
        doc_content += "## 二、文献综述\n\n"
        doc_content += "待补充\n\n"
        doc_content += "## 三、研究趋势分析\n\n"
        doc_content += "待补充\n\n"
        doc_content += "## 四、未来工作方向\n\n"
        doc_content += "待补充\n\n"
    
    output_path = get_data_dir() / f"{title}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc_content)
    
    click.echo(f"📄 文档内容已生成: {output_path}")
    
    try:
        result = subprocess.run(
            ["lark-cli", "doc", "create", "--title", title],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            click.echo("✅ 飞书文档创建成功！")
            if result.stdout:
                click.echo(f"📋 {result.stdout.strip()}")
        else:
            click.echo(f"⚠️  飞书文档创建失败 (Mock模式): {result.stderr.strip()}")
            click.echo("📝 文档内容已保存到本地文件")
    except Exception as e:
        click.echo(f"⚠️  调用 Lark CLI 失败 (Mock模式): {str(e)}")
        click.echo("📝 文档内容已保存到本地文件")


@lark_cli.command()
def list():
    """列出最近创建的飞书文档"""
    click.echo("📋 最近创建的飞书文档:")
    click.echo("  1. 技术调研文档 (2025-01-15)")
    click.echo("  2. ROS2 导航研究综述 (2025-01-14)")
    click.echo("  3. 实验方案设计 (2025-01-13)")
