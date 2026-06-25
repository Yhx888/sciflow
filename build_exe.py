"""
SciFlow PyInstaller打包脚本
用于将SciFlow桌面应用打包为Windows可执行文件
使用方法: python build_exe.py [--onefile] [--cli] [--spec-only]
"""

from __future__ import annotations

import argparse
import os
import sys
import shutil
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.resolve()


def get_web_dir() -> Path:
    """获取web静态文件目录"""
    return get_project_root() / "sci_flow" / "web"


def find_icon() -> Optional[Path]:
    """查找图标文件"""
    root = get_project_root()
    icon_extensions = [".ico", ".png", ".icns"]
    for ext in icon_extensions:
        for name in ["icon", "sciflow", "SciFlow", "logo"]:
            icon_path = root / f"{name}{ext}"
            if icon_path.exists():
                return icon_path
    assets_dir = root / "assets"
    if assets_dir.exists():
        for ext in icon_extensions:
            for icon_path in assets_dir.glob(f"*{ext}"):
                return icon_path
    return None


def get_hidden_imports() -> list[str]:
    """获取需要的hidden imports列表"""
    return [
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "litellm",
        "sse_starlette",
        "pydantic",
        "pydantic.deprecated.decorator",
        "starlette",
        "anyio",
        "anyio._backends._asyncio",
        "httptools",
        "websockets",
        "click",
        "requests",
        "docx",
        "multipart",
        "aiofiles",
        "pydantic_settings",
    ]


def build_spec_file(
    entry_script: Path,
    app_name: str,
    onefile: bool = False,
    windowed: bool = True,
    icon_path: Optional[Path] = None,
) -> Path:
    """生成PyInstaller spec文件"""
    
    project_root = get_project_root()
    web_dir = get_web_dir()
    
    datas = []
    if web_dir.exists():
        datas.append(f"('{web_dir.as_posix()}', 'sci_flow/web')")
    
    hidden_imports = get_hidden_imports()
    
    icon_line = ""
    if icon_path and icon_path.exists():
        icon_line = f"icon='{icon_path.as_posix().replace(chr(92), '/')}',"
    
    datas_str = ",\n        ".join(datas) if datas else ""
    hidden_imports_str = ",\n        ".join([f"'{imp}'" for imp in hidden_imports])
    
    console_str = "False" if windowed else "True"
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
SciFlow PyInstaller spec文件
自动生成于 build_exe.py
"""

import sys
from pathlib import Path

block_cipher = None

project_root = Path(r'{project_root.as_posix()}')

a = Analysis(
    ['{entry_script.as_posix()}'],
    pathex=[r'{project_root.as_posix()}'],
    binaries=[],
    datas=[
        {datas_str}
    ],
    hiddenimports=[
        {hidden_imports_str}
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

'''

    if onefile:
        spec_content += f'''exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console_str},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_line}
)
'''
    else:
        spec_content += f'''exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={console_str},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_line}
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{app_name}',
)
'''

    spec_path = project_root / f"{app_name}.spec"
    spec_path.write_text(spec_content, encoding="utf-8")
    return spec_path


def run_pyinstaller(spec_path: Path, clean: bool = True):
    """运行PyInstaller打包"""
    try:
        import PyInstaller.__main__
    except ImportError:
        print("[错误] PyInstaller未安装，请运行: pip install pyinstaller", file=sys.stderr)
        print("或者: pip install -e .[dev]", file=sys.stderr)
        sys.exit(1)
    
    args = [str(spec_path)]
    if clean:
        args.append("--clean")
    args.append("--noconfirm")
    
    print(f"[打包] 运行PyInstaller: {' '.join(args)}")
    PyInstaller.__main__.run(args)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SciFlow PyInstaller打包脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python build_exe.py              # 打包桌面版（目录模式，启动更快）
  python build_exe.py --onefile    # 打包为单个exe文件
  python build_exe.py --cli        # 打包CLI版本（带控制台）
  python build_exe.py --spec-only  # 仅生成spec文件，不执行打包
        """
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="打包为单个exe文件（默认: 目录模式）"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="打包CLI版本（显示控制台窗口）"
    )
    parser.add_argument(
        "--spec-only",
        action="store_true",
        help="仅生成spec文件，不执行打包"
    )
    parser.add_argument(
        "--name",
        default="SciFlow",
        help="输出文件名（默认: SciFlow）"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="不清理之前的构建缓存"
    )
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    os.chdir(project_root)
    
    print("=" * 60)
    print("  SciFlow PyInstaller 打包工具")
    print("=" * 60)
    print()
    
    if args.cli:
        entry_script = project_root / "sci_flow" / "cli.py"
        windowed = False
        if args.name == "SciFlow":
            args.name = "SciFlow-CLI"
    else:
        entry_script = project_root / "sci_flow" / "desktop" / "launcher.py"
        windowed = True
    
    if not entry_script.exists():
        print(f"[错误] 入口脚本不存在: {entry_script}", file=sys.stderr)
        sys.exit(1)
    
    print(f"[配置] 入口脚本: {entry_script.name}")
    print(f"[配置] 输出名称: {args.name}")
    print(f"[配置] 打包模式: {'单文件' if args.onefile else '目录模式'}")
    print(f"[配置] 窗口模式: {'GUI（无控制台）' if windowed else 'CLI（带控制台）'}")
    
    icon_path = find_icon()
    if icon_path:
        print(f"[配置] 图标文件: {icon_path.name}")
    else:
        print("[配置] 图标文件: 未找到，使用默认图标")
    
    web_dir = get_web_dir()
    if web_dir.exists():
        web_files = list(web_dir.glob("**/*"))
        print(f"[配置] Web静态文件: {len(web_files)} 个文件")
    else:
        print("[警告] Web静态文件目录不存在: sci_flow/web", file=sys.stderr)
    
    print()
    
    print("[步骤1/3] 生成spec文件...")
    spec_path = build_spec_file(
        entry_script=entry_script,
        app_name=args.name,
        onefile=args.onefile,
        windowed=windowed,
        icon_path=icon_path,
    )
    print(f"[完成] Spec文件已生成: {spec_path.name}")
    
    if args.spec_only:
        print()
        print("[完成] Spec文件已生成，未执行打包")
        print(f"       如需打包，请运行: pyinstaller {spec_path.name}")
        return
    
    print()
    print("[步骤2/3] 清理旧构建...")
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    if not args.no_clean:
        if dist_dir.exists():
            print(f"[清理] 删除 dist/ 目录")
            shutil.rmtree(dist_dir, ignore_errors=True)
        if build_dir.exists():
            print(f"[清理] 删除 build/ 目录")
            shutil.rmtree(build_dir, ignore_errors=True)
    
    print()
    print("[步骤3/3] 开始打包...")
    print("-" * 60)
    
    run_pyinstaller(spec_path, clean=not args.no_clean)
    
    print("-" * 60)
    print()
    print("=" * 60)
    print("  打包完成!")
    print("=" * 60)
    
    output_dir = dist_dir / args.name
    if args.onefile:
        output_file = dist_dir / f"{args.name}.exe"
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"  输出文件: {output_file}")
            print(f"  文件大小: {size_mb:.2f} MB")
    else:
        if output_dir.exists():
            exe_path = output_dir / f"{args.name}.exe"
            if exe_path.exists():
                print(f"  输出目录: {output_dir}")
                print(f"  启动程序: {exe_path}")
    
    print()


if __name__ == "__main__":
    main()
