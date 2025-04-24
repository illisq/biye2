import json
from utils import file_manager
import logging
from typing import Dict, Any, List, Optional, Tuple

from utils.file_manager import FileManager
from utils.logger import Logger

# 配置日志
logger = logging.getLogger(__name__)

def record_success(template, question, response):
    entry = {
        "template_id": template["id"],
        "question_id": question["id"],
        "response": response
    }
    file_manager.append_json("data/history/success_logs.json", entry)
    file_manager.update_template_pool(template)

def discard_template(template):
    file_manager.remove_template(template["id"])

class Feedback:
    """反馈模块，负责模板池更新与失败模板处理"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化反馈模块
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = Logger()
        
        # 加载模板池
        self.template_pool = FileManager.load_json(config['paths']['template_pool'])
        if not self.template_pool:
            logger.error("无法加载模板池")
            raise ValueError("模板池加载失败")
            
        # 加载失败日志
        self.failure_logs = FileManager.load_json(config['paths']['failure_logs'])
        if self.failure_logs is None:
            self.failure_logs = []
            
        # 加载成功日志
        self.success_logs = FileManager.load_json(config['paths']['success_logs'])
        if self.success_logs is None:
            self.success_logs = []
    
    def record_attack_result(self, is_success: bool, template: Dict[str, Any], question: Dict[str, Any], 
                            prompt: str, response: str, success_reason: str = "", confidence: float = 0.0) -> bool:
        """记录攻击结果
        
        Args:
            is_success: 攻击是否成功
            template: 使用的模板
            question: 使用的问题
            prompt: 构造的提示
            response: 模型响应
            success_reason: 成功原因（如果成功）
            confidence: 置信度
            
        Returns:
            bool: 记录是否成功
        """
        # 构建日志数据
        log_data = {
            "template_id": template.get("id", "unknown"),
            "question_id": question.get("id", "unknown"),
            "vulnerability_type": self._get_vulnerability_type(question, template),
            "prompt": prompt,
            "response": response,
            "confidence": confidence
        }
        
        if is_success:
            log_data["success_reason"] = success_reason
            
            # 更新问题成功计数
            if 'id' in question:
                self._update_question_stats(question['id'], True)
                
            # 记录到成功日志
            result = FileManager.append_log(log_data, is_success=True)
            if result:
                logger.info(f"已记录成功攻击，模板ID: {template.get('id')}, 问题ID: {question.get('id')}")
            else:
                logger.error("记录成功攻击失败")
        else:
            # 更新问题失败计数
            if 'id' in question:
                self._update_question_stats(question['id'], False)
                
            # 记录到失败日志
            result = FileManager.append_log(log_data, is_success=False)
            if result:
                logger.info(f"已记录失败攻击，模板ID: {template.get('id')}, 问题ID: {question.get('id')}")
            else:
                logger.error("记录失败攻击失败")
                
        # 更新模板统计信息
        if 'id' in template:
            self._update_template_stats(template['id'], self._get_vulnerability_type(question, template), is_success)
            
        return result
    
    def _update_template_stats(self, template_id: str, vulnerability_type: str, is_success: bool) -> bool:
        """更新模板统计信息
        
        Args:
            template_id: 模板ID
            vulnerability_type: 脆弱点类型
            is_success: 攻击是否成功
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 在模板池中查找模板
            found = False
            for template in self.template_pool.get(vulnerability_type, []):
                if template['id'] == template_id:
                    # 更新使用计数
                    template['usage_count'] = template.get('usage_count', 0) + 1
                    
                    # 更新成功率
                    success_count = template.get('success_count', 0)
                    if is_success:
                        success_count += 1
                        template['success_count'] = success_count
                    
                    usage = template['usage_count']
                    template['success_rate'] = success_count / usage if usage > 0 else 0
                    
                    found = True
                    break
            
            if not found:
                logger.warning(f"未找到模板 ID: {template_id}")
                return False
                
            # 保存更新后的模板池
            result = FileManager.save_json(self.template_pool, self.config['paths']['template_pool'])
            
            if result:
                logger.debug(f"已更新模板统计信息，ID: {template_id}, 成功: {is_success}")
            else:
                logger.error(f"更新模板统计信息失败，ID: {template_id}")
                
            return result
        except Exception as e:
            logger.error(f"更新模板统计信息时发生错误: {e}")
            return False
    
    def _update_question_stats(self, question_id: str, is_success: bool) -> bool:
        """更新问题统计信息
        
        Args:
            question_id: 问题ID
            is_success: 攻击是否成功
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 加载问题池
            question_pool = FileManager.load_json(self.config['paths']['question_pool'])
            if not question_pool:
                logger.error("无法加载问题池")
                return False
                
            # 在问题池中查找问题
            found = False
            for category in question_pool:
                for question in question_pool[category]:
                    if question.get('id') == question_id:
                        # 更新测试计数
                        question['test_count'] = question.get('test_count', 0) + 1
                        
                        # 更新成功计数
                        if is_success:
                            question['success_count'] = question.get('success_count', 0) + 1
                        
                        found = True
                        break
                        
                if found:
                    break
            
            if not found:
                logger.warning(f"未找到问题 ID: {question_id}")
                return False
                
            # 保存更新后的问题池
            result = FileManager.save_json(question_pool, self.config['paths']['question_pool'])
            
            if result:
                logger.debug(f"已更新问题统计信息，ID: {question_id}, 成功: {is_success}")
            else:
                logger.error(f"更新问题统计信息失败，ID: {question_id}")
                
            return result
        except Exception as e:
            logger.error(f"更新问题统计信息时发生错误: {e}")
            return False
    
    def get_template_failure_count(self, template_id: str) -> int:
        """获取模板的失败次数
        
        Args:
            template_id: 模板ID
            
        Returns:
            int: 失败次数
        """
        # 遍历失败日志，统计该模板的失败次数
        failure_count = 0
        
        for log in self.failure_logs:
            if log.get('template_id') == template_id:
                failure_count += 1
                
        return failure_count
    
    def should_drop_template(self, template_id: str) -> bool:
        """判断是否应该丢弃模板
        
        如果模板连续失败次数过多，或者成功率过低，则考虑丢弃
        
        Args:
            template_id: 模板ID
            
        Returns:
            bool: 是否应该丢弃
        """
        # 获取最大失败次数
        max_failures = self.config.get('system', {}).get('max_failures', 5)
        
        # 获取模板的失败次数
        failure_count = self.get_template_failure_count(template_id)
        
        # 查找模板
        template = None
        for category in self.template_pool:
            for t in self.template_pool[category]:
                if t.get('id') == template_id:
                    template = t
                    break
            if template:
                break
                
        if not template:
            logger.warning(f"未找到模板 ID: {template_id}")
            return False
            
        # 检查使用次数和成功率
        usage_count = template.get('usage_count', 0)
        success_rate = template.get('success_rate', 0.0)
        
        # 判断是否应该丢弃
        # 1. 如果连续失败次数超过阈值
        if failure_count >= max_failures:
            return True
            
        # 2. 如果使用次数足够多，但成功率很低
        if usage_count >= 10 and success_rate < 0.1:
            return True
            
        return False
    
    def get_successful_templates(self, vulnerability_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取指定脆弱点类型的成功模板
        
        Args:
            vulnerability_type: 脆弱点类型
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 成功模板列表
        """
        # 提取所有成功日志中的模板ID
        successful_templates = {}
        
        for log in self.success_logs:
            if log.get('vulnerability_type') == vulnerability_type:
                template_id = log.get('template_id')
                if template_id:
                    successful_templates[template_id] = successful_templates.get(template_id, 0) + 1
        
        # 按成功次数排序
        sorted_templates = sorted(successful_templates.items(), key=lambda x: x[1], reverse=True)
        
        # 获取前N个模板的详细信息
        result = []
        for template_id, count in sorted_templates[:limit]:
            # 查找模板详情
            for template in self.template_pool.get(vulnerability_type, []):
                if template.get('id') == template_id:
                    result.append(template)
                    break
        
        return result
    
    def _get_vulnerability_type(self, question: Dict[str, Any], template: Dict[str, Any]) -> str:
        """确定脆弱点类型
        
        Args:
            question: 问题数据
            template: 模板数据
            
        Returns:
            str: 脆弱点类型
        """
        # 从问题ID推断类型
        question_id = question.get('id', '')
        if question_id.startswith('h'):
            return 'hallucination'
        elif question_id.startswith('s'):
            return 'safety'
        elif question_id.startswith('l'):
            return 'long_context'
        elif question_id.startswith('c'):
            return 'consistency'
        elif question_id.startswith('p'):
            return 'prompt_injection'
            
        # 从模板ID推断类型
        template_id = template.get('id', '')
        if template_id.startswith('ht'):
            return 'hallucination'
        elif template_id.startswith('st'):
            return 'safety'
        elif template_id.startswith('lt'):
            return 'long_context'
        elif template_id.startswith('ct'):
            return 'consistency'
        elif template_id.startswith('pt'):
            return 'prompt_injection'
            
        # 无法确定，返回默认值
        return 'hallucination'
