import re
import random
import logging
from typing import Dict, Any, List, Optional, Tuple

# 配置日志
logger = logging.getLogger(__name__)

class PromptBuilder:
    """提示构造工具，负责将模板和问题组合成完整的提示"""
    
    def __init__(self):
        """初始化提示构造器"""
        pass
    
    def build_prompt(self, template: str, question: str, field: str = "一般知识") -> str:
        """构建完整提示
        
        Args:
            template: 模板内容
            question: 问题内容
            field: 领域信息
            
        Returns:
            str: 构造的提示
        """
        logger.info("开始构建提示")
        
        # 替换模板中的变量
        prompt = template
        
        # 替换{question}
        prompt = prompt.replace("{question}", question)
        
        # 替换{field}
        prompt = prompt.replace("{field}", field)
        
        # 替换其他可能的变量
        variables = {
            "user": "用户",
            "assistant": "助手",
            "current_date": "2023年12月",
            "version": "1.0"
        }
        
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, value)
                logger.debug(f"替换变量 {placeholder} 为 {value}")
        
        logger.info(f"提示构建完成: {prompt[:50]}..." if len(prompt) > 50 else prompt)
        return prompt
    
    def build_conversation_prompt(self, template: str, question: str, 
                                 num_turns: int = 2, field: str = "一般知识") -> str:
        """构建对话形式的提示
        
        Args:
            template: 模板内容
            question: 问题内容
            num_turns: 对话轮次数
            field: 领域信息
            
        Returns:
            str: 对话形式的提示
        """
        logger.info(f"构建{num_turns}轮对话提示")
        
        # 基础提示
        base_prompt = self.build_prompt(template, question, field)
        
        # 构建对话
        conversation = []
        
        # 第一轮：用户提问，助手回答
        conversation.append(f"用户: {base_prompt}")
        
        # 助手的随机回复
        assistant_responses = [
            "我需要更多信息才能回答这个问题。",
            "这是一个有趣的问题，让我思考一下。",
            "我不确定，但我会尝试回答。",
            "我可以从几个角度回答这个问题。"
        ]
        conversation.append(f"助手: {random.choice(assistant_responses)}")
        
        # 额外的对话轮次
        for i in range(1, num_turns):
            # 用户的追问
            follow_up_questions = [
                "请详细说明一下。",
                "你能再解释一下吗？",
                "我想知道更多细节。",
                "为什么这么说？",
                "有什么依据吗？"
            ]
            conversation.append(f"用户: {random.choice(follow_up_questions)}")
            
            # 如果是最后一轮，则包含原始问题
            if i == num_turns - 1:
                conversation.append(f"用户: 回到我的问题，{question}")
        
        # 合并成完整对话
        full_prompt = "\n".join(conversation)
        
        logger.info(f"对话提示构建完成: {full_prompt[:50]}..." if len(full_prompt) > 50 else full_prompt)
        return full_prompt
    
    @staticmethod
    def generate_field_variables(vulnerability_type: str) -> Dict[str, str]:
        """根据脆弱点类型生成相关领域变量
        
        Args:
            vulnerability_type: 脆弱点类型
            
        Returns:
            Dict[str, str]: 变量字典
        """
        # 根据脆弱点类型选择合适的领域
        fields = {
            'hallucination': ['政治学', '历史学', '医学', '气象学', '经济学', '心理学'],
            'safety': ['安全研究', '网络安全', '社会学', '犯罪学', '伦理学'],
            'long_context': ['文学分析', '数据科学', '法律', '哲学', '系统工程'],
            'consistency': ['逻辑学', '物理学', '数学', '哲学', '认知科学'],
            'prompt_injection': ['计算机科学', '信息安全', '软件工程', '人机交互', '系统安全']
        }
        
        # 从对应脆弱点类型的领域列表中随机选择
        if vulnerability_type in fields:
            field = random.choice(fields[vulnerability_type])
        else:
            field = random.choice(fields['hallucination'])
        
        # 构建变量字典
        variables = {
            'field': field,
            'user': '用户',
            'assistant': '助手',
            'current_date': '2023年',
            'version': '1.0'
        }
        
        return variables
