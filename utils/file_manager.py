import os
import json
import yaml
import logging
import time
from typing import Dict, Any, List, Optional, Union

# 配置日志
logger = logging.getLogger(__name__)

class FileManager:
    """文件管理工具，负责加载与保存配置、问题池和模板池等文件"""
    
    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """加载YAML配置文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 配置字典，加载失败则返回空字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.debug(f"已加载YAML配置文件: {file_path}")
            return config or {}
        except Exception as e:
            logger.error(f"加载YAML文件失败 {file_path}: {e}")
            return {}
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: str) -> bool:
        """保存数据到YAML文件
        
        Args:
            data: 要保存的数据
            file_path: 保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.debug(f"已保存YAML文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存YAML文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def load_json(file_path: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """加载JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Union[Dict[str, Any], List[Any]]]: 加载的数据，加载失败则返回None
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"JSON文件不存在: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"已加载JSON文件: {file_path}")
            return data
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}")
            return None
    
    @staticmethod
    def save_json(data: Union[Dict[str, Any], List[Any]], file_path: str) -> bool:
        """保存数据到JSON文件
        
        Args:
            data: 要保存的数据
            file_path: 保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"已保存JSON文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存JSON文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def append_json(file_path: str, new_data: Dict[str, Any]) -> bool:
        """向JSON文件追加数据
        
        Args:
            file_path: 文件路径
            new_data: 要追加的数据
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 读取现有数据
            current_data = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        current_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning(f"解析JSON文件失败，将覆盖: {file_path}")
            
            # 追加数据
            if isinstance(current_data, list):
                current_data.append(new_data)
            else:
                current_data = [new_data]
                
            # 保存回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"已追加数据到JSON文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"追加JSON数据失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def append_log(log_data: Dict[str, Any], is_success: bool = False) -> bool:
        """记录攻击日志
        
        Args:
            log_data: 日志数据
            is_success: 是否成功日志
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确定日志文件路径
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_dir = "data/history"
            os.makedirs(log_dir, exist_ok=True)
            
            file_name = f"success_logs.json" if is_success else f"failure_logs.json"
            file_path = os.path.join(log_dir, file_name)
            
            # 追加日志
            return FileManager.append_json(file_path, log_data)
        except Exception as e:
            logger.error(f"记录攻击日志失败: {e}")
            return False
    
    @staticmethod
    def save_prompt_cache(prompt: str, response: str, template_id: str, question_id: str) -> Optional[str]:
        """保存提示和响应缓存
        
        Args:
            prompt: 提示文本
            response: 响应文本
            template_id: 模板ID
            question_id: 问题ID
            
        Returns:
            Optional[str]: 缓存文件路径，失败则返回None
        """
        try:
            # 生成缓存文件名和路径
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            cache_dir = "data/prompts_cache"
            os.makedirs(cache_dir, exist_ok=True)
            
            file_name = f"{template_id}_{question_id}_{timestamp}.json"
            file_path = os.path.join(cache_dir, file_name)
            
            # 准备缓存数据
            cache_data = {
                "template_id": template_id,
                "question_id": question_id,
                "prompt": prompt,
                "response": response,
                "timestamp": timestamp
            }
            
            # 保存缓存
            if FileManager.save_json(cache_data, file_path):
                return file_path
            return None
        except Exception as e:
            logger.error(f"保存提示缓存失败: {e}")
            return None 