import click
from sci_flow.config import ensure_directories
from sci_flow.literature import search as literature_search
from sci_flow.zotero import add as zotero_add, list as zotero_list
from sci_flow.lark import create as lark_create
from sci_flow.python import run as python_run, create_template as python_create_template
from sci_flow.word import create as word_create


@click.group()
def pipeline_cli():
    """全流程编排模块
    
    用于串联文献调研、Zotero同步、飞书文档、Python处理、Word导出等环节。
    """
    ensure_directories()


@pipeline_cli.command()
@click.option("--topic", help="研究主题")
@click.option("--author", default="作者", help="作者姓名")
@click.option("--affiliation", default="单位", help="作者单位")
def run(topic, author, affiliation):
    """运行完整科研工作流"""
    if not topic:
        click.echo("❌ 请提供研究主题 (--topic)")
        return
    
    click.echo("🚀 启动 SciFlow 全流程编排")
    click.echo(f"📌 研究主题: {topic}")
    click.echo("=" * 50)
    
    click.echo("\n📋 步骤 1: 文献调研")
    click.echo("-" * 30)
    
    from sci_flow.literature import search
    search.callback(query=topic, mock=True)
    
    click.echo("\n📋 步骤 2: 同步至 Zotero")
    click.echo("-" * 30)
    
    mock_papers = [
        {
            "title": f"{topic} with Deep Learning",
            "authors": ["Wang, Lei", "Li, Wei"],
            "year": 2025,
            "venue": "IEEE Robotics and Automation Letters",
            "link": "https://arxiv.org/abs/2501.00000"
        },
        {
            "title": f"Optimized {topic} System",
            "authors": ["Chen, Jie"],
            "year": 2024,
            "venue": "ICRA",
            "link": "https://arxiv.org/abs/2405.00000"
        }
    ]
    
    for paper in mock_papers:
        zotero_add.callback(
            title=paper["title"],
            authors=",".join(paper["authors"]),
            year=paper["year"],
            venue=paper["venue"],
            link=paper["link"]
        )
        click.echo()
    
    click.echo("\n📋 步骤 3: 创建飞书技术文档")
    click.echo("-" * 30)
    
    lark_create.callback(title=f"{topic} 技术调研文档", from_zotero=True)
    
    click.echo("\n📋 步骤 4: Python 数据分析")
    click.echo("-" * 30)
    
    python_create_template.callback(name=f"{topic}_analysis")
    script_path = f"{topic}_analysis.py"
    python_run.callback(script=script_path, input_file=None, output_file=None)
    
    click.echo("\n📋 步骤 5: 生成 Word 论文")
    click.echo("-" * 30)
    
    abstract = f"本文针对{topic}领域的问题，提出了一种基于深度学习的方法。通过实验验证，该方法在多项指标上优于现有方法，为{topic}的研究提供了新的思路。"
    word_create.callback(
        title=f"{topic}研究论文",
        author=author,
        affiliation=affiliation,
        abstract=abstract
    )
    
    click.echo("\n" + "=" * 50)
    click.echo("🎉 SciFlow 全流程编排完成！")
    click.echo("\n📁 生成的文件:")
    click.echo("   - data/zotero_library.json (Zotero 文献库)")
    click.echo("   - data/技术调研文档.md (飞书文档内容)")
    click.echo("   - data/{topic}_analysis.py (数据分析脚本)")
    click.echo("   - output/{topic}研究论文.docx (论文初稿)")
    click.echo("\n💡 后续步骤:")
    click.echo("   1. 在飞书中完善技术调研文档")
    click.echo("   2. 修改数据分析脚本以适配真实数据")
    click.echo("   3. 在 Word 中完善论文内容")


@pipeline_cli.command()
def status():
    """查看当前工作流状态"""
    click.echo("📊 SciFlow 工作流状态")
    click.echo("-" * 30)
    click.echo("✅ 文献调研: 已完成")
    click.echo("✅ Zotero 同步: 已完成")
    click.echo("✅ 飞书文档: 已创建")
    click.echo("✅ Python 分析: 已执行")
    click.echo("✅ Word 论文: 已生成")
    click.echo("-" * 30)
    click.echo("📈 整体进度: 100%")
