import sys
import os
import json
import random
from typing import Dict, Any, Tuple, List, Optional

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.file_manager import FileManager
from core.template_mutator import TemplateMutator
from utils.llm_interface import LLMInterface

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return None

def load_template_pool():
    """加载模板池"""
    config = load_config()
    if not config:
        print("无法加载配置文件，测试终止")
        return None
        
    template_pool_path = os.path.join(config['paths']['data_dir'], 'template_pool.json')
    try:
        with open(template_pool_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载模板池失败: {str(e)}")
        return None

def test_template_mutation():
    """测试模板变异功能"""
    print("=== 模板变异测试 ===")
    
    # 加载配置
    config = load_config()
    if not config:
        print("无法加载配置文件，测试终止")
        return
        
    # 加载模板池
    template_pool = load_template_pool()
    if not template_pool:
        print("无法加载模板池，测试终止")
        return
    
    # 初始化模板变异器
    mutator = TemplateMutator(config)
    
    # 从模板池中选择一个模板
    hallucination_templates = template_pool.get('hallucination', [])
    if not hallucination_templates:
        print("未找到幻觉类型的模板，测试终止")
        return
        
    # 选择一个有内容的模板
    template = None
    for t in hallucination_templates:
        if t.get('content'):
            template = t
            break
            
    if not template:
        print("未找到有效模板，测试终止")
        return
        
    print(f"选择模板 ID: {template.get('id')}")
    print(f"模板内容: {template.get('content')}")
    print(f"模板类型: {template.get('applicable_types', [])}")
    print(f"使用次数: {template.get('usage_count', 0)}")
    print(f"成功次数: {template.get('success_count', 0)}")
    print(f"成功率: {template.get('success_rate', 0):.2f}")
    print("\n")
    
    # 测试模板变异
    print("生成变异模板...")
    
    # 模拟测试函数
    def test_mutated_template(mutated_template):
        print(f"测试变异模板: {mutated_template.get('id')}")
        print(f"变异内容: {mutated_template.get('content')}")
        print(f"使用的策略: {mutated_template.get('strategies', [])}")
        
        # 50%的概率返回成功
        success = random.random() < 0.5
        print(f"测试结果: {'成功' if success else '失败'}")
        return success, {"result": "测试结果信息"}
    
    # 执行变异和测试
    print("\n执行变异和测试...")
    success, new_template = mutator.mutate_and_test(template, test_mutated_template)
    
    print(f"\n变异测试总结: {'成功' if success else '失败'}")
    if success and new_template:
        print(f"新模板 ID: {new_template.get('id')}")
        print(f"新模板内容: {new_template.get('content')}")
    
    # 检查模板池是否已更新
    print("\n检查模板池更新...")
    updated_template_pool = load_template_pool()
    if updated_template_pool:
        # 查找新模板
        found = False
        for category, templates in updated_template_pool.items():
            for t in templates:
                if new_template and t.get('id') == new_template.get('id'):
                    found = True
                    print(f"在模板池中找到新模板 {t.get('id')}")
                    print(f"使用次数: {t.get('usage_count', 0)}")
                    print(f"成功次数: {t.get('success_count', 0)}")
                    print(f"成功率: {t.get('success_rate', 0):.2f}")
                    break
            if found:
                break
                
        if not found and success:
            print("警告: 新模板未能保存到模板池")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_template_mutation() 