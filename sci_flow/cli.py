import click
from sci_flow import __version__
from sci_flow.literature import literature_cli
from sci_flow.zotero import zotero_cli
from sci_flow.lark import lark_cli
from sci_flow.python import python_cli
from sci_flow.word import word_cli
from sci_flow.pipeline import pipeline_cli


@click.group()
@click.version_option(__version__, "--version", "-v")
def cli():
    """SciFlow - 科研全流程 Agent 编排器
    
    用自然语言串联文献管理、技术文档、数据分析、论文撰写，实现科研工作流自动化。
    """
    pass


cli.add_command(literature_cli, name="literature")
cli.add_command(zotero_cli, name="zotero")
cli.add_command(lark_cli, name="lark")
cli.add_command(python_cli, name="python")
cli.add_command(word_cli, name="word")
cli.add_command(pipeline_cli, name="pipeline")


if __name__ == "__main__":
    cli()
