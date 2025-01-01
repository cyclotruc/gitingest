import os
import subprocess
import json
import argparse
from typing import List, Tuple, Dict
from gitingest.ingest import ingest
from config_manager import ConfigManager

# 加载配置
config = ConfigManager()

def generate_tree(directory: str, max_depth: int = None) -> str:
    """
    生成目录树结构
    :param directory: 要分析的目录路径
    :param max_depth: 树的最大深度
    :return: 目录树的字符串表示
    """
    if max_depth is None:
        max_depth = config.tree_max_depth
        
    try:
        result = subprocess.run(
            ['tree', '-L', str(max_depth)],
            cwd=directory,
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"生成目录树时出错: {str(e)}"

def analyze_tree_and_suggest_patterns(tree_output: str) -> Tuple[List[str], List[str]]:
    """
    分析目录树并建议包含和排除模式
    :param tree_output: 目录树字符串
    :return: (包含模式列表, 排除模式列表)
    """
    # 针对markdown文档的包含模式
    include_patterns = [
        # 核心源代码
        "**/*.py",           # Python源代码
        
        # 文档和配置
        "README.md",         # 主要文档
        "CHANGELOG.md",      # 变更日志
        "LICENSE",           # 许可证
        "requirements.txt",  # Python依赖
        "pyproject.toml",    # Python项目配置
        "setup.py",         # 安装配置
        "setup.cfg",        # 安装配置
        "MANIFEST.in",      # 打包配置
        
        # 核心文档（选择性包含）
        "docs/**/*.md",     # 文档目录下的markdown文件
    ]
    
    # 排除模式 - 更细致的控制
    exclude_patterns = [
        # 二进制和生成文件
        "**/*.pyc",          # Python编译文件
        "**/__pycache__/**", # Python缓存
        "**/*.so",           # 编译的扩展模块
        "**/*.pyd",          # Windows下的Python扩展模块
        "**/*.dll",          # Windows动态链接库
        "**/*.dylib",        # Mac动态链接库
        "**/*.egg",          # Python打包文件
        "**/*.whl",          # Python wheel包
        "**/*.exe",          # 可执行文件
        
        # 媒体文件
        "**/*.png",          # PNG图片
        "**/*.jpg",          # JPG图片
        "**/*.jpeg",         # JPEG图片
        "**/*.gif",          # GIF图片
        "**/*.ico",          # 图标文件
        "**/*.svg",          # SVG图片
        "**/*.mp4",          # 视频文件
        "**/*.mov",          # 视频文件
        "**/*.avi",          # 视频文件
        "**/*.mp3",          # 音频文件
        "**/*.wav",          # 音频文件
        
        # 开发工具和临时文件
        "**/.git/**",        # Git目录
        "**/.idea/**",       # PyCharm配置
        "**/.vscode/**",     # VSCode配置
        "**/.env",           # 环境变量
        "**/.env.*",         # 环境变量文件
        "**/node_modules/**", # Node.js模块
        "**/venv/**",        # Python虚拟环境
        "**/env/**",         # Python虚拟环境
        "**/build/**",       # 构建目录
        "**/dist/**",        # 分发目录
        "**/.pytest_cache/**", # Pytest缓存
        "**/.coverage",      # 测试覆盖率文件
        "**/htmlcov/**",     # 测试覆盖率报告
        
        # 编译和打包相关
        "**/*.min.js",       # 压缩的JS文件
        "**/*.min.css",      # 压缩的CSS文件
        "**/*.map",          # Source map文件
        "**/webpack.stats.json", # Webpack统计文件
        
        # UI构建文件
        "**/ui/**/*.js",     # UI JavaScript文件
        "**/ui/**/*.css",    # UI样式文件
        "**/ui/build/**",    # UI构建输出
        "**/ui/dist/**",     # UI分发文件
        
        # 测试文件（可选，取决于是否需要包含测试文档）
        "**/tests/**",       # 测试目录
        "**/test_*.py",      # 测试文件
        "**/*_test.py",      # 测试文件
        
        # Jupyter notebooks（可选）
        "**/*.ipynb",        # Jupyter笔记本
        "**/.ipynb_checkpoints/**", # Jupyter检查点
    ]
    
    return include_patterns, exclude_patterns

def smart_ingest(directory: str, max_file_size: int = None, output_format: str = None) -> Dict:
    """
    智能分析目录并生成报告
    :param directory: 要分析的目录路径
    :param max_file_size: 最大文件大小限制
    :param output_format: 输出格式（md/json/txt）
    :return: 分析报告字典
    """
    if max_file_size is None:
        max_file_size = config.max_file_size
    if output_format is None:
        output_format = config.default_format
        
    if not config.validate_format(output_format):
        raise ValueError(f"不支持的输出格式: {output_format}")
    
    # 步骤1：生成目录树
    print("步骤1: 生成目录树...")
    tree_output = generate_tree(directory)
    print(tree_output)
    
    # 保存目录树
    tree_file = config.get_output_path(config.get_output_file('tree'), 'trees')
    with open(tree_file, 'w', encoding=config.file_encoding) as f:
        f.write(tree_output)
    
    # 步骤2：分析树结构并建议过滤模式
    print("\n步骤2: 分析目录结构并生成建议...")
    include_patterns, exclude_patterns = analyze_tree_and_suggest_patterns(tree_output)
    
    print("建议的包含模式:")
    for pattern in include_patterns:
        print(f"  - {pattern}")
    
    print("\n建议的排除模式:")
    for pattern in exclude_patterns:
        print(f"  - {pattern}")
    
    # 步骤3：执行ingest
    print("\n步骤3: 执行文件分析...")
    try:
        summary, tree, content = ingest(
            source=directory,
            max_file_size=max_file_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            output=config.get_output_path(config.get_output_file(output_format), 'reports')
        )
        
        # 返回完整报告
        report = {
            "directory_tree": tree_output,
            "suggested_patterns": {
                "include": include_patterns,
                "exclude": exclude_patterns
            },
            "analysis_result": {
                "summary": summary,
                "tree": tree,
                "content": content[:config.content_preview_length] + "..." 
                          if len(content) > config.content_preview_length else content
            }
        }
        
        # 保存JSON报告
        json_file = config.get_output_path(config.get_output_file('json'), 'reports')
        with open(json_file, "w", encoding=config.file_encoding) as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        return report
        
    except Exception as e:
        return {
            "error": f"分析过程中出错: {str(e)}",
            "directory_tree": tree_output,
            "suggested_patterns": {
                "include": include_patterns,
                "exclude": exclude_patterns
            }
        }

if __name__ == "__main__":
    # 配置命令行参数
    parser = argparse.ArgumentParser(description="智能代码仓库分析工具")
    parser.add_argument("--source", "-s", type=str, 
                      default=config.input_base_dir,
                      help="要分析的源目录路径")
    parser.add_argument("--source-type", "-t", type=str,
                      choices=config.supported_sources,
                      default=config.default_source,
                      help="输入源类型")
    parser.add_argument("--max-depth", "-d", type=int, 
                      default=config.tree_max_depth,
                      help="目录树最大深度")
    parser.add_argument("--max-size", "-m", type=int, 
                      default=config.max_file_size,
                      help="最大文件大小(bytes)")
    parser.add_argument("--output-dir", "-o", type=str, 
                      default=config.output_base_dir,
                      help="输出基础目录")
    parser.add_argument("--format", "-f", type=str,
                      choices=config.supported_formats,
                      default=config.default_format,
                      help="输出格式")
    
    args = parser.parse_args()
    
    print(f"开始分析目录: {args.source}")
    print(f"配置信息:")
    print(f"- 输入源类型: {args.source_type}")
    print(f"- 目录树深度: {args.max_depth}")
    print(f"- 最大文件大小: {args.max_size / 1024 / 1024:.2f}MB")
    print(f"- 输出基础目录: {args.output_dir}")
    print(f"- 输出格式: {args.format}")
    
    # 执行分析
    result = smart_ingest(
        directory=args.source,
        max_file_size=args.max_size,
        output_format=args.format
    )
    
    print(f"\n分析完成！输出文件：")
    print(f"1. 目录树: {config.get_output_path(config.get_output_file('tree'), 'trees')}")
    print(f"2. 分析报告: {config.get_output_path(config.get_output_file(args.format), 'reports')}")
    print(f"3. JSON报告: {config.get_output_path(config.get_output_file('json'), 'reports')}")
