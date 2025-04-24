import json
from core import mutator, injector, evaluator, feedback
from utils import prompt_builder, file_manager
import os
import random
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from utils.file_manager import FileManager
from utils.logger import Logger
from core.mutator import Mutator
from core.injector import Injector
from core.evaluator import Evaluator
from core.feedback import Feedback

# 配置日志
logger = logging.getLogger(__name__)

CONFIG = FileManager.load_yaml("config/config.yaml")

FAIL_COUNT = {}

class Runner:
    """主控制流模块，负责加载任务、控制模糊测试流程、管理状态"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化运行器
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = FileManager.load_yaml(config_path)
        if not self.config:
            logger.error(f"无法加载配置文件: {config_path}")
            raise ValueError(f"配置文件加载失败: {config_path}")
            
        # 设置日志
        self.logger = Logger(self.config.get('system', {}).get('log_level'))
        self.logger.info("初始化模糊测试运行器")
        
        # 加载问题池
        self.question_pool = FileManager.load_json(self.config['paths']['question_pool'])
        if not self.question_pool:
            logger.error("无法加载问题池")
            raise ValueError("问题池加载失败")
            
        # 初始化组件
        self.mutator = Mutator(self.config)
        self.injector = Injector(self.config)
        self.evaluator = Evaluator(self.config)
        self.feedback = Feedback(self.config)
        
        # 运行计数器
        self.total_runs = 0
        self.successful_runs = 0
        
        # 记录当前任务状态
        self.current_task = {
            "template_id": None,
            "question_id": None,
            "vulnerability_type": None,
            "retry_count": 0
        }
    
    def run_once(self, vulnerability_type: Optional[str] = None, 
                question_id: Optional[str] = None, 
                template_id: Optional[str] = None) -> bool:
        """运行一次模糊测试
        
        Args:
            vulnerability_type: 指定脆弱点类型，为None时随机选择
            question_id: 指定问题ID，为None时随机选择
            template_id: 指定模板ID，为None时随机选择
            
        Returns:
            bool: 测试是否成功
        """
        self.logger.info("=" * 50)
        self.logger.info("步骤1: 初始化测试任务")
        self.logger.info("=" * 50)
        
        # 重置当前任务
        self.current_task = {
            "template_id": template_id,
            "question_id": question_id,
            "vulnerability_type": vulnerability_type,
            "retry_count": 0
        }
        
        self.logger.info(f"初始任务参数 - 脆弱点类型: {vulnerability_type}, 问题ID: {question_id}, 模板ID: {template_id}")
        
        # 选择脆弱点类型（如果未指定）
        if not vulnerability_type:
            vulnerability_type = self._select_vulnerability_type()
            self.current_task["vulnerability_type"] = vulnerability_type
            self.logger.info(f"脆弱点类型未指定，随机选择: {vulnerability_type}")
        
        self.logger.info("=" * 50)
        self.logger.info("步骤2: 选择测试问题")
        self.logger.info("=" * 50)
        
        # 选择问题（如果未指定）
        question = None
        if question_id:
            question = self._find_question_by_id(question_id)
            if not question:
                self.logger.warning(f"未找到指定问题 ID: {question_id}，将随机选择")
        
        if not question:
            question = self._select_question(vulnerability_type)
            self.logger.info(f"随机选择问题: ID={question.get('id')}, 内容={question.get('content')}")
        else:
            self.logger.info(f"使用指定问题: ID={question.get('id')}, 内容={question.get('content')}")
        
        self.logger.info("=" * 50)
        self.logger.info("步骤3: 选择或变异攻击模板")
        self.logger.info("=" * 50)
        
        # 选择或变异模板
        template = None
        if template_id:
            template = self._find_template_by_id(template_id)
            if not template:
                self.logger.warning(f"未找到指定模板 ID: {template_id}，将随机选择")
        
        if not template:
            # 有一定概率选择现有模板，否则变异现有模板
            if random.random() < 0.7:  # 70%概率使用现有模板
                template = self.mutator.select_template(vulnerability_type)
                self.logger.info(f"选择现有模板: ID={template.get('id')}, 内容={template.get('content')}")
            else:  # 30%概率变异模板
                base_template = self.mutator.select_template(vulnerability_type)
                self.logger.info(f"选择基础模板进行变异: ID={base_template.get('id')}")
                template = self.mutator.mutate_template(base_template, vulnerability_type)
                self.logger.info(f"变异后的新模板: ID={template.get('id')}, 内容={template.get('content')}")
                # 保存新模板
                self.mutator.save_new_template(template, vulnerability_type)
                self.logger.info(f"新模板已保存到模板池")
        else:
            self.logger.info(f"使用指定模板: ID={template.get('id')}, 内容={template.get('content')}")
        
        # 更新当前任务
        self.current_task["template_id"] = template.get("id")
        self.current_task["question_id"] = question.get("id")
        
        self.logger.info("=" * 50)
        self.logger.info("步骤4: 构造提示并注入到目标模型")
        self.logger.info("=" * 50)
        
        # 执行注入
        self.logger.info(f"开始注入 - 脆弱点: {vulnerability_type}, 问题ID: {question.get('id')}, 模板ID: {template.get('id')}")
        prompt, response, latency = self.injector.inject(template, question)
        
        self.logger.info(f"构造的提示: {prompt}")
        self.logger.info(f"模型响应(延迟: {latency:.2f}s): {response[:100]}..." if len(response) > 100 else response)
        
        self.logger.info("=" * 50)
        self.logger.info("步骤5: 评估模型响应")
        self.logger.info("=" * 50)
        
        # 评估结果
        is_success, reason, confidence = self.evaluator.evaluate(response, question, template)
        
        self.logger.info(f"评估结果: {'成功' if is_success else '失败'}")
        self.logger.info(f"评估原因: {reason}")
        self.logger.info(f"评估置信度: {confidence:.2f}")
        
        self.logger.info("=" * 50)
        self.logger.info("步骤6: 记录反馈并更新统计")
        self.logger.info("=" * 50)
        
        # 记录结果
        feedback_result = self.feedback.record_attack_result(is_success, template, question, 
                                         prompt, response, reason, confidence)
        self.logger.info(f"反馈记录结果: {'成功' if feedback_result else '失败'}")
        
        # 更新计数器
        self.total_runs += 1
        if is_success:
            self.successful_runs += 1
            self.logger.info(f"攻击成功 - 原因: {reason}, 置信度: {confidence:.2f}")
        else:
            self.logger.info(f"攻击失败 - 置信度: {confidence:.2f}")
        
        self.logger.info(f"当前总测试数: {self.total_runs}, 成功测试数: {self.successful_runs}")
        self.logger.info("=" * 50)
        
        return is_success
    
    def run_batch(self, batch_size: Optional[int] = None, 
                vulnerability_type: Optional[str] = None) -> Dict[str, Any]:
        """运行一批模糊测试
        
        Args:
            batch_size: 批量大小，为None时使用配置中的值
            vulnerability_type: 指定脆弱点类型，为None时随机选择
            
        Returns:
            Dict[str, Any]: 批量测试结果统计
        """
        # 使用配置中的批量大小（如果未指定）
        if batch_size is None:
            batch_size = self.config.get('system', {}).get('batch_size', 10)
            
        start_time = time.time()
        
        # 批量测试结果
        results = {
            "total": batch_size,
            "successful": 0,
            "success_rate": 0.0,
            "total_time": 0.0,
            "vulnerable_types": {}
        }
        
        # 按脆弱点类型进行统计
        for i in range(batch_size):
            # 随机选择脆弱点类型（如果未指定）
            type_for_run = vulnerability_type
            if not type_for_run:
                type_for_run = self._select_vulnerability_type()
                
            # 确保统计字典中有该类型
            if type_for_run not in results["vulnerable_types"]:
                results["vulnerable_types"][type_for_run] = {
                    "total": 0,
                    "successful": 0,
                    "success_rate": 0.0
                }
                
            # 执行一次测试
            success = self.run_once(type_for_run)
            
            # 更新统计
            results["vulnerable_types"][type_for_run]["total"] += 1
            if success:
                results["successful"] += 1
                results["vulnerable_types"][type_for_run]["successful"] += 1
            
            # 计算成功率
            for type_name, stats in results["vulnerable_types"].items():
                if stats["total"] > 0:
                    stats["success_rate"] = stats["successful"] / stats["total"]
        
        # 计算总成功率
        if results["total"] > 0:
            results["success_rate"] = results["successful"] / results["total"]
            
        # 计算总时间
        end_time = time.time()
        results["total_time"] = end_time - start_time
        
        # 输出批量测试结果
        self.logger.info(f"批量测试完成 - 总数: {batch_size}, 成功: {results['successful']}, " +
                   f"成功率: {results['success_rate']:.2f}, 总时间: {results['total_time']:.2f}秒")
        
        return results
    
    def run_with_retry(self, vulnerability_type: Optional[str] = None, 
                     max_retries: Optional[int] = None) -> bool:
        """运行测试并在失败时重试
        
        Args:
            vulnerability_type: 指定脆弱点类型，为None时随机选择
            max_retries: 最大重试次数，为None时使用配置中的值
            
        Returns:
            bool: 是否最终成功
        """
        # 使用配置中的最大重试次数（如果未指定）
        if max_retries is None:
            max_retries = self.config.get('system', {}).get('max_retries', 3)
            
        # 选择脆弱点类型（如果未指定）
        if not vulnerability_type:
            vulnerability_type = self._select_vulnerability_type()
            
        self.logger.info(f"开始测试（带重试） - 脆弱点类型: {vulnerability_type}, 最大重试次数: {max_retries}")
        
        # 运行测试
        success = self.run_once(vulnerability_type)
        retry_count = 0
        
        # 如果失败则重试
        while not success and retry_count < max_retries:
            retry_count += 1
            self.current_task["retry_count"] = retry_count
            
            self.logger.info(f"第 {retry_count} 次重试...")
            
            # 尝试使用变异的模板
            base_template = self.mutator.select_template(vulnerability_type)
            template = self.mutator.mutate_template(base_template, vulnerability_type)
            # 保存新模板
            self.mutator.save_new_template(template, vulnerability_type)
            
            # 重新运行
            success = self.run_once(vulnerability_type, template_id=template.get("id"))
            
        if success:
            self.logger.info(f"在第 {retry_count} 次重试后成功")
        else:
            self.logger.info(f"在 {max_retries} 次重试后仍然失败")
            
        return success
    
    def _select_vulnerability_type(self) -> str:
        """选择脆弱点类型
        
        根据配置的权重随机选择脆弱点类型
        
        Returns:
            str: 选中的脆弱点类型
        """
        # 从配置中获取脆弱点权重
        weights = self.config.get('strategies', {}).get('vulnerabilities', {})
        
        # 构建权重数组
        types = list(weights.keys())
        if not types:
            # 默认使用平均权重
            types = ['hallucination', 'safety', 'long_context', 'consistency', 'prompt_injection']
            weights = {t: 1.0 for t in types}
        
        # 获取权重值
        weight_values = [weights.get(t, 1.0) for t in types]
        
        # 归一化权重
        total_weight = sum(weight_values)
        if total_weight <= 0:
            # 如果总权重不正，使用平均权重
            weight_values = [1.0] * len(types)
            
        # 随机选择
        selected_type = random.choices(types, weights=weight_values, k=1)[0]
        
        return selected_type
    
    def _select_question(self, vulnerability_type: str) -> Dict[str, Any]:
        """选择问题
        
        从问题池中选择指定类型的问题
        
        Args:
            vulnerability_type: 脆弱点类型
            
        Returns:
            Dict[str, Any]: 选中的问题
        """
        # 从问题池中获取指定类型的问题列表
        questions = self.question_pool.get(vulnerability_type, [])
        if not questions:
            self.logger.warning(f"未找到类型为 {vulnerability_type} 的问题，将随机选择任意类型")
            # 随机选择一个非空类型
            for vul_type, type_questions in self.question_pool.items():
                if type_questions:
                    questions = type_questions
                    break
        
        # 确保有问题可选
        if not questions:
            self.logger.error("问题池为空")
            raise ValueError("问题池为空")
            
        # 随机选择一个问题
        selected_question = random.choice(questions)
        
        return selected_question
    
    def _find_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找问题
        
        Args:
            question_id: 问题ID
            
        Returns:
            Optional[Dict[str, Any]]: 找到的问题，未找到则返回None
        """
        for vul_type, questions in self.question_pool.items():
            for question in questions:
                if question.get('id') == question_id:
                    return question
        return None
    
    def _find_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            Optional[Dict[str, Any]]: 找到的模板，未找到则返回None
        """
        for vul_type, templates in self.mutator.template_pool.items():
            for template in templates:
                if template.get('id') == template_id:
                    return template
        return None

def run_one_test():
    """运行单次测试的快捷函数，用于简单测试"""
    
    # 从配置加载路径
    config = FileManager.load_yaml("config/config.yaml")
    if not config:
        logger.error("无法加载配置文件")
        return
    
    # 加载测试数据
    questions = FileManager.load_json(config.get("paths", {}).get("question_pool"))
    templates = FileManager.load_json(config.get("paths", {}).get("template_pool"))
    
    if not questions or not templates:
        logger.error("无法加载问题池或模板池")
        return
    
    # 选择一个问题和模板
    if "hallucination" in questions and questions["hallucination"]:
        question = questions["hallucination"][0]
    else:
        logger.error("没有可用的幻觉类问题")
        return
        
    if "hallucination" in templates and templates["hallucination"]:
        template = templates["hallucination"][0]
    else:
        logger.error("没有可用的幻觉类模板")
        return
    
    # 初始化组件
    from core.mutator import Mutator
    from core.injector import Injector
    from core.evaluator import Evaluator
    from core.feedback import Feedback
    
    mutator = Mutator(config)
    injector = Injector(config)
    evaluator = Evaluator(config)
    feedback = Feedback(config)
    
    # 执行测试
    for retry in range(config.get("system", {}).get("max_retries", 3)):
        logger.info(f"开始第 {retry+1} 次测试...")
        
        # 变异模板
        mutated_template = mutator.mutate_template(template, "hallucination")
        logger.info(f"变异模板: {mutated_template.get('content')}")
        
        # 注入并获取响应
        prompt, response, latency = injector.inject(mutated_template, question)
        logger.info(f"模型响应(延迟: {latency:.2f}s): {response[:100]}..." if len(response) > 100 else response)
        
        # 评估结果
        is_success, reason, confidence = evaluator.evaluate(response, question, mutated_template)
        logger.info(f"评估结果: {'成功' if is_success else '失败'}, 原因: {reason}, 置信度: {confidence:.2f}")
        
        # 记录结果
        if is_success:
            feedback.record_attack_result(True, mutated_template, question, prompt, response, reason, confidence)
            logger.info("攻击成功，测试结束")
            return
        else:
            logger.info("攻击失败，继续尝试")
    
    logger.info(f"在 {config.get('system', {}).get('max_retries', 3)} 次尝试后仍然失败")
