import os
import yaml
from typing import Dict, List, Optional

class ConfigManager:
    """配置管理器：负责加载和管理配置"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self._init_directories()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return {}
    
    def _init_directories(self):
        """初始化所有必要的目录"""
        # 创建输出基础目录
        os.makedirs(self.output_base_dir, exist_ok=True)
        # 创建报告目录
        os.makedirs(self.reports_dir, exist_ok=True)
        # 创建树文件目录
        os.makedirs(self.trees_dir, exist_ok=True)
        # 创建临时文件目录
        os.makedirs(self.temp_dir, exist_ok=True)
    
    @property
    def tree_max_depth(self) -> int:
        """获取目录树最大深度"""
        return self.config.get('tree', {}).get('max_depth', 4)
    
    @property
    def max_file_size(self) -> int:
        """获取最大文件大小"""
        return self.config.get('file', {}).get('max_size', 10 * 1024 * 1024)
    
    @property
    def file_encoding(self) -> str:
        """获取文件编码"""
        return self.config.get('file', {}).get('encoding', 'utf-8')
    
    # 输入路径相关
    @property
    def input_base_dir(self) -> str:
        """获取输入基础目录"""
        return self.config.get('paths', {}).get('input', {}).get('base_dir', os.getcwd())
    
    @property
    def github_repo(self) -> str:
        """获取默认GitHub仓库地址"""
        return self.config.get('paths', {}).get('input', {}).get('github', '')
    
    @property
    def gitlab_repo(self) -> str:
        """获取默认GitLab仓库地址"""
        return self.config.get('paths', {}).get('input', {}).get('gitlab', '')
    
    # 输出路径相关
    @property
    def output_base_dir(self) -> str:
        """获取输出基础目录"""
        return self.config.get('paths', {}).get('output', {}).get('base_dir', 'output')
    
    @property
    def reports_dir(self) -> str:
        """获取报告目录"""
        reports = self.config.get('paths', {}).get('output', {}).get('reports', 'reports')
        return os.path.join(self.output_base_dir, reports)
    
    @property
    def trees_dir(self) -> str:
        """获取树文件目录"""
        trees = self.config.get('paths', {}).get('output', {}).get('trees', 'trees')
        return os.path.join(self.output_base_dir, trees)
    
    @property
    def temp_dir(self) -> str:
        """获取临时文件目录"""
        temp = self.config.get('paths', {}).get('output', {}).get('temp', 'temp')
        return os.path.join(self.output_base_dir, temp)
    
    @property
    def supported_formats(self) -> List[str]:
        """获取支持的输出格式"""
        return self.config.get('output', {}).get('formats', ['md'])
    
    @property
    def default_format(self) -> str:
        """获取默认输出格式"""
        return self.config.get('output', {}).get('default_format', 'md')
    
    def get_output_file(self, format_type: str) -> str:
        """获取指定格式的输出文件名"""
        files = self.config.get('output', {}).get('files', {})
        return files.get(format_type, f'analysis_result.{format_type}')
    
    def get_output_path(self, filename: str, output_type: str = 'reports') -> str:
        """
        获取输出文件的完整路径
        :param filename: 文件名
        :param output_type: 输出类型（reports/trees/temp）
        :return: 完整路径
        """
        if output_type == 'reports':
            base_dir = self.reports_dir
        elif output_type == 'trees':
            base_dir = self.trees_dir
        elif output_type == 'temp':
            base_dir = self.temp_dir
        else:
            base_dir = self.output_base_dir
            
        return os.path.join(base_dir, filename)
    
    @property
    def content_preview_length(self) -> int:
        """获取内容预览长度"""
        return self.config.get('content', {}).get('preview_length', 1000)
    
    @property
    def supported_sources(self) -> List[str]:
        """获取支持的输入源类型"""
        return self.config.get('input', {}).get('supported_sources', ['local'])
    
    @property
    def default_source(self) -> str:
        """获取默认输入源类型"""
        return self.config.get('input', {}).get('default_source', 'local')
    
    def validate_format(self, format_type: str) -> bool:
        """验证输出格式是否支持"""
        return format_type in self.supported_formats
    
    def validate_source(self, source_type: str) -> bool:
        """验证输入源类型是否支持"""
        return source_type in self.supported_sources
