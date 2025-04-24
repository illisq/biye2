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
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 如果已经有处理器，则不重复添加
        if self.logger.handlers:
            return
            
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        
        # 创建文件处理器
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
        self.logger.debug(message)
    
    def info(self, message):
        """记录一般信息
        
        Args:
            message: 日志消息
        """
        self.logger.info(message)
    
    def warning(self, message):
        """记录警告信息
        
        Args:
            message: 日志消息
        """
        self.logger.warning(message)
    
    def error(self, message):
        """记录错误信息
        
        Args:
            message: 日志消息
        """
        self.logger.error(message)
    
    def critical(self, message):
        """记录严重错误信息
        
        Args:
            message: 日志消息
        """
        self.logger.critical(message)
        
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
        self.logger.debug(f"攻击提示: {prompt}")
        
    def log_model_response(self, response, latency):
        """记录模型响应
        
        Args:
            response: 模型响应文本
            latency: 响应延迟（秒）
        """
        # 截断过长的响应
        if len(response) > 500:
            response_text = response[:500] + "... [截断]"
        else:
            response_text = response
            
        self.logger.debug(f"模型响应 (延迟: {latency:.2f}s): {response_text}")
        
    def log_mutation(self, original_template_id, new_template_id, strategies):
        """记录模板变异信息
        
        Args:
            original_template_id: 原始模板ID
            new_template_id: 新模板ID
            strategies: 使用的变异策略列表
        """
        self.logger.info(f"模板变异: {original_template_id} → {new_template_id}, 策略: {', '.join(strategies)}")
