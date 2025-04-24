import logging
import os
from datetime import datetime

class Logger:
    """日志工具类，用于记录系统运行日志"""
    
    def __init__(self, log_level=None, log_dir="logs"):
        """初始化日志工具
        
        Args:
            log_level: 日志级别，默认为None，会从配置文件读取
            log_dir: 日志文件目录
        """
        self.logger = logging.getLogger("fuzz_framework")
        
        # 如果未指定日志级别，从配置文件读取
        if log_level is None:
            try:
                from utils.file_manager import FileManager
                config = FileManager.load_yaml("config/config.yaml")
                log_level = config.get('system', {}).get('log_level', 'INFO')
            except Exception:
                log_level = 'INFO'  # 默认使用INFO级别
        
        # 设置日志级别
        level = getattr(logging, log_level.upper(), logging.DEBUG)
        self.logger.setLevel(level)
        
        # 如果已经有处理器，则不重复添加
        if self.logger.handlers:
            return
            
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建控制台处理器 - 简洁格式，适合快速浏览
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        
        # 创建详细文件处理器 - 详细格式，记录完整信息
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"fuzz_{timestamp}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        
        # 添加处理器到logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"日志系统初始化完成，日志级别: {log_level}, 日志文件: {log_file}")
    
    def debug(self, message):
        """记录调试信息
        
        Args:
            message: 日志消息
        """
        # 支持多行内容
        self._log_multiline(self.logger.debug, message)
    
    def info(self, message):
        """记录一般信息
        
        Args:
            message: 日志消息
        """
        # 支持多行内容
        self._log_multiline(self.logger.info, message)
    
    def warning(self, message):
        """记录警告信息
        
        Args:
            message: 日志消息
        """
        # 支持多行内容
        self._log_multiline(self.logger.warning, message)
    
    def error(self, message):
        """记录错误信息
        
        Args:
            message: 日志消息
        """
        # 支持多行内容
        self._log_multiline(self.logger.error, message)
    
    def critical(self, message):
        """记录严重错误信息
        
        Args:
            message: 日志消息
        """
        # 支持多行内容
        self._log_multiline(self.logger.critical, message)
    
    def _log_multiline(self, log_func, message):
        """处理多行日志内容
        
        对多行内容进行逐行记录，保持正确的缩进和格式
        
        Args:
            log_func: 日志函数 (debug, info, etc.)
            message: 日志消息
        """
        if not message:
            return
            
        # 检查是否为多行内容
        if '\n' in str(message):
            lines = str(message).split('\n')
            # 记录第一行
            log_func(lines[0])
            # 后续行添加缩进以保持格式
            for line in lines[1:]:
                if line.strip():  # 只记录非空行
                    log_func(f"    {line}")
        else:
            # 单行内容直接记录
            log_func(message)
        
    def log_attack_attempt(self, template_id, question_id, prompt, is_success=False):
        """记录攻击尝试
        
        Args:
            template_id: 使用的模板ID
            question_id: 问题ID
            prompt: 构造的提示文本
            is_success: 攻击是否成功
        """
        status = "成功" if is_success else "失败"
        self.logger.info(f"攻击尝试 [{status}] - 模板ID: {template_id}, 问题ID: {question_id}")
        self.info("提示内容:")
        self.info("=" * 40)
        self.info(prompt)
        self.info("=" * 40)
        
    def log_model_response(self, response, latency):
        """记录模型响应
        
        Args:
            response: 模型响应文本
            latency: 响应延迟（秒）
        """
        self.info(f"模型响应 (延迟: {latency:.2f}秒):")
        self.info("=" * 40)
        self.info(response)
        self.info("=" * 40)
        
    def log_mutation(self, original_template_id, new_template_id, strategies):
        """记录模板变异信息
        
        Args:
            original_template_id: 原始模板ID
            new_template_id: 新模板ID
            strategies: 使用的变异策略列表
        """
        self.logger.info(f"模板变异: {original_template_id} → {new_template_id}, 策略: {', '.join(strategies)}")
    
    def log_detailed_test(self, test_data):
        """记录详细测试结果
        
        Args:
            test_data: 包含测试详情的字典
        """
        self.info("=" * 80)
        self.info("详细测试信息")
        self.info("=" * 80)
        
        # 记录问题信息
        self.info("问题信息:")
        self.info(f"ID: {test_data.get('question_id', 'unknown')}")
        self.info(f"内容: {test_data.get('question_content', 'unknown')}")
        if 'fact' in test_data:
            self.info(f"事实: {test_data.get('fact', 'unknown')}")
            
        # 记录模板信息
        self.info("\n模板信息:")
        self.info(f"ID: {test_data.get('template_id', 'unknown')}")
        self.info(f"内容: {test_data.get('template_content', 'unknown')}")
        
        # 记录完整提示
        self.info("\n完整提示:")
        self.info(test_data.get('prompt', 'unknown'))
        
        # 记录完整响应
        self.info("\n完整响应:")
        self.info(test_data.get('response', 'unknown'))
        
        # 记录评估结果
        self.info("\n评估结果:")
        self.info(f"成功: {test_data.get('success', False)}")
        self.info(f"原因: {test_data.get('reason', 'unknown')}")
        self.info(f"置信度: {test_data.get('confidence', 0):.2f}")
        
        self.info("=" * 80)
