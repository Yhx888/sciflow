import click
import subprocess
import sys
from pathlib import Path
from sci_flow.config import get_data_dir, get_output_dir, ensure_directories


@click.group()
def python_cli():
    """Python 数据处理模块
    
    用于执行 Python 数据分析脚本，支持参数传递和结果收集。
    """
    ensure_directories()


@python_cli.command()
@click.option("--script", help="要执行的 Python 脚本路径")
@click.option("--input", "input_file", help="输入数据文件")
@click.option("--output", "output_file", help="输出文件路径")
def run(script, input_file, output_file):
    """执行 Python 数据处理脚本"""
    if not script:
        click.echo("❌ 请提供要执行的脚本路径 (--script)")
        return
    
    script_path = Path(script)
    if not script_path.is_absolute():
        script_path = get_data_dir() / script
    
    if not script_path.exists():
        click.echo(f"❌ 脚本文件不存在: {script_path}")
        return
    
    click.echo(f"🐍 正在执行脚本: {script_path}")
    
    cmd = [sys.executable, str(script_path)]
    
    if input_file:
        cmd.extend(["--input", input_file])
    if output_file:
        cmd.extend(["--output", output_file])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=get_output_dir(),
            timeout=120
        )
        
        if result.returncode == 0:
            click.echo("✅ 脚本执行成功！")
            if result.stdout:
                click.echo(f"📊 输出结果:\n{result.stdout.strip()}")
        else:
            click.echo(f"❌ 脚本执行失败:")
            click.echo(f"   错误: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        click.echo("⏰ 脚本执行超时")
    except Exception as e:
        click.echo(f"⚠️  执行脚本时出错: {str(e)}")


@python_cli.command()
@click.option("--name", default="data_analysis", help="示例脚本名称")
def create_template(name):
    """创建数据分析示例脚本"""
    template = f'''import argparse

def main():
    parser = argparse.ArgumentParser(description='数据分析脚本')
    parser.add_argument('--input', help='输入数据文件')
    parser.add_argument('--output', help='输出文件路径')
    args = parser.parse_args()
    
    print("=== 数据分析脚本 ===")
    print(f"输入文件: {{args.input}}")
    print(f"输出文件: {{args.output}}")
    
    mock_data = [12.5, 15.3, 18.7, 14.2, 16.8, 19.1, 13.4, 17.6]
    
    print(f"\\n📈 数据统计:")
    print(f"数据点数: {{len(mock_data)}}")
    print(f"平均值: {{sum(mock_data)/len(mock_data):.2f}}")
    print(f"最大值: {{max(mock_data)}}")
    print(f"最小值: {{min(mock_data)}}")
    
    print(f"\\n✅ 数据分析完成！")

if __name__ == "__main__":
    main()
'''
    
    script_path = get_data_dir() / f"{name}.py"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(template)
    
    click.echo(f"📄 示例脚本已创建: {script_path}")
    click.echo(f"💡 运行: sciflow python run --script {script_path}")
