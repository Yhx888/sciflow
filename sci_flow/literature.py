import click
from sci_flow.config import ensure_directories


@click.group()
def literature_cli():
    """文献调研模块
    
    用于检索和整理学术文献，支持同步至 Zotero。
    """
    ensure_directories()


@literature_cli.command()
@click.argument("query")
@click.option("--mock", is_flag=True, help="使用 Mock 数据进行演示")
def search(query, mock):
    """检索文献
    
    在学术数据库中检索与 QUERY 相关的文献。
    """
    click.echo(f"🔍 正在检索文献: {query}")
    
    if mock:
        mock_papers = [
            {
                "title": "ROS2 Navigation System with Deep Reinforcement Learning",
                "authors": ["Li, Wei", "Zhang, Ming", "Wang, Fang"],
                "year": 2025,
                "venue": "IEEE Robotics and Automation Letters",
                "abstract": "This paper presents a novel navigation system for mobile robots using ROS2 and deep reinforcement learning...",
                "link": "https://arxiv.org/abs/2501.00123"
            },
            {
                "title": "Multi-Robot Collaborative Exploration in Unknown Environments",
                "authors": ["Chen, Jie", "Liu, Yang", "Xu, Hao"],
                "year": 2024,
                "venue": "International Conference on Robotics and Automation",
                "abstract": "We propose a decentralized framework for multi-robot collaborative exploration...",
                "link": "https://arxiv.org/abs/2405.06789"
            },
            {
                "title": "Real-Time SLAM with LiDAR and Camera Fusion",
                "authors": ["Wang, Lei", "Zhao, Qian"],
                "year": 2024,
                "venue": "Journal of Field Robotics",
                "abstract": "This work introduces a robust SLAM system that fuses LiDAR and camera data in real-time...",
                "link": "https://arxiv.org/abs/2403.09876"
            }
        ]
        
        click.echo("\n📚 检索结果:")
        for i, paper in enumerate(mock_papers, 1):
            click.echo(f"\n{i}. {paper['title']}")
            click.echo(f"   作者: {', '.join(paper['authors'])}")
            click.echo(f"   年份: {paper['year']}")
            click.echo(f"   期刊: {paper['venue']}")
            click.echo(f"   链接: {paper['link']}")
            click.echo(f"   摘要: {paper['abstract'][:100]}...")
        
        click.echo("\n✅ Mock 文献检索完成！")
        click.echo("💡 提示: 使用 `sciflow zotero sync` 将文献同步至 Zotero")
    else:
        click.echo("⚠️  真实检索功能正在开发中，请使用 --mock 进行演示")


@literature_cli.command()
@click.argument("keywords", nargs=-1)
def summarize(keywords):
    """总结文献
    
    根据关键词总结相关文献的研究趋势和热点。
    """
    click.echo(f"📊 正在分析文献趋势: {' '.join(keywords)}")
    click.echo("\n📈 研究趋势分析 (Mock):")
    click.echo("  - ROS2 导航算法: 持续增长，2024-2025年发表量翻倍")
    click.echo("  - 强化学习应用: 成为热点，多篇顶会论文采用")
    click.echo("  - 多传感器融合: 技术成熟，工程化应用增多")
    click.echo("  - 多机器人协作: 新兴方向，值得深入研究")
    click.echo("\n✅ 文献趋势分析完成！")
