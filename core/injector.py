import json
import time
import logging
from typing import Dict, Any, Tuple, List, Optional
import os
import random

from utils.file_manager import FileManager
from utils.llm_interface import LLMInterface
from utils.prompt_builder import PromptBuilder
from utils.logger import Logger

# 配置日志
logger = logging.getLogger(__name__)

class Injector:
    """注入模块，将提示发送给目标大模型并获取回应"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化注入器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = Logger()
        self.prompt_builder = PromptBuilder()
        
        # 设置目标模型
        target_config = config.get('models', {}).get('target', {})
        if not target_config:
            logger.warning("配置中未找到目标模型配置，将使用默认值")
            target_config = {
                'type': 'openai',
                'name': 'gpt-4',
                'temperature': 0.7
            }
        self.target_model = LLMInterface(target_config, is_target=True)
        
        # 确保缓存目录存在
        cache_dir = config.get('paths', {}).get('prompts_cache', 'data/prompts_cache')
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_dir = cache_dir
        
    def inject(self, template: Dict[str, Any], question: Dict[str, Any]) -> Tuple[str, str, float]:
        """将问题注入到模板中并发送到目标模型
        
        Args:
            template: 模板数据
            question: 问题数据
            
        Returns:
            Tuple[str, str, float]: (提示文本, 模型响应, 响应延迟)
        """
        self.logger.info("=" * 60)
        self.logger.info("步骤4.1: 将问题注入到模板中")
        self.logger.info("=" * 60)
        
        # 构建提示
        template_content = template.get('content', '')
        question_content = question.get('content', '')
        
        # 处理模板中的字段替换
        field = self._extract_field_from_question(question_content)
        
        # 构建提示
        prompt = self.prompt_builder.build_prompt(template_content, question_content, field)
        
        # 详细记录问题和模板信息
        self.logger.info("问题详情:")
        self.logger.info(f"内容: {question_content}")
        self.logger.info(f"ID: {question.get('id', 'unknown')}")
        if 'fact' in question:
            self.logger.info(f"事实: {question.get('fact', '')}")
            
        self.logger.info("模板详情:")
        self.logger.info(f"ID: {template.get('id', 'unknown')}")
        self.logger.info(f"内容: {template_content}")
        
        self.logger.info("生成的完整提示:")
        self.logger.info("-" * 40)
        self.logger.info(prompt)
        self.logger.info("-" * 40)
        
        # 缓存提示（用于复现和分析）
        self._cache_prompt(prompt, template.get('id', 'unknown'), question.get('id', 'unknown'))
        
        self.logger.info("=" * 60)
        self.logger.info("步骤4.2: 发送提示到目标模型")
        self.logger.info("=" * 60)
        
        # 记录目标模型信息
        model_name = self.target_model.model_name
        model_type = self.target_model.model_type
        self.logger.info(f"目标模型: {model_type}/{model_name}")
        
        # 向模型发送提示，测量响应时间
        start_time = time.time()
        response, _ = self.target_model.generate_response(prompt)
        end_time = time.time()
        
        # 计算延迟
        latency = end_time - start_time
        
        # 完整记录响应
        self.logger.info(f"模型响应 (延迟: {latency:.2f}秒):")
        self.logger.info("-" * 40)
        self.logger.info(response)
        self.logger.info("-" * 40)
        
        # 记录详细测试数据
        test_data = {
            "question_id": question.get('id', 'unknown'),
            "question_content": question_content,
            "template_id": template.get('id', 'unknown'),
            "template_content": template_content,
            "prompt": prompt,
            "response": response,
            "latency": latency,
            "model": f"{model_type}/{model_name}"
        }
        
        if 'fact' in question:
            test_data["fact"] = question.get('fact', '')
            
        # 使用Logger记录详细测试信息
        self.logger.log_detailed_test(test_data)
        
        return prompt, response, latency
    
    def _extract_field_from_question(self, question_content: str) -> str:
        """从问题内容中提取领域信息
        
        简单启发式方法：从问题中推断可能的领域
        
        Args:
            question_content: 问题内容
            
        Returns:
            str: 推断的领域
        """
        # 简单的领域关键词映射
        domain_keywords = {
            '政治': ['总统', '政府', '选举', '民主', '党派', '奥巴马', '特朗普'],
            '技术': ['技术', '计算机', '软件', '编程', '人工智能', 'AI', '算法'],
            '医学': ['医学', '疾病', '治疗', '患者', '医生', '药物', '健康', '癌症'],
            '物理': ['物理', '能量', '质量', '引力', '粒子', '原子'],
            '地理': ['地理', '国家', '城市', '地区', '气候', '山脉'],
            '历史': ['历史', '战争', '王朝', '革命', '时代', '古代'],
            '数学': ['数学', '几何', '代数', '方程', '计算', '数字'],
            '艺术': ['艺术', '绘画', '音乐', '雕塑', '文学', '电影']
        }
        
        # 检查问题是否包含领域关键词
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in question_content:
                    logger.info(f"从问题中提取的领域: {domain}")
                    return domain
        
        # 默认领域
        logger.info("无法从问题中提取领域，使用默认领域: 一般知识")
        return "一般知识"
    
    def _cache_prompt(self, prompt: str, template_id: str, question_id: str) -> None:
        """缓存提示文本，用于未来分析和复现
        
        Args:
            prompt: 提示文本
            template_id: 模板ID
            question_id: 问题ID
        """
        try:
            # 生成缓存文件名
            timestamp = int(time.time())
            filename = f"{template_id}_{question_id}_{timestamp}.txt"
            
            # 缓存到文件
            filepath = os.path.join(self.cache_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)
                
            logger.debug(f"提示已缓存到: {filepath}")
        except Exception as e:
            logger.error(f"缓存提示时出错: {e}")