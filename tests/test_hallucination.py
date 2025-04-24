#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试脚本：运行单次hallucination脆弱点测试
"""

import sys
import logging
import time
import os
import json
import random
from core.runner import Runner
from utils.file_manager import FileManager

# 配置日志格式
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_hallucination")

def list_available_question_ids():
    """获取所有可用的幻觉测试问题ID列表"""
    question_ids = []
    
    # 检查常规问题池
    config_path = "config/config.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            import yaml
            config = yaml.safe_load(f)
            
        question_pool_path = config.get("paths", {}).get("question_pool", "data/question_pool.json")
        with open(question_pool_path, "r", encoding="utf-8") as f:
            question_pool = json.load(f)
            if "hallucination" in question_pool:
                for question in question_pool["hallucination"]:
                    question_ids.append({
                        "id": question.get("id"),
                        "content": question.get("content"),
                        "source": "标准问题池"
                    })
    except Exception as e:
        logger.warning(f"读取标准问题池时出错: {e}")
    
    # 检查幻觉数据集
    hallucination_dataset_path = "data/hallucination_dataset.json"
    if os.path.exists(hallucination_dataset_path):
        try:
            with open(hallucination_dataset_path, "r", encoding="utf-8") as f:
                hallucination_dataset = json.load(f)
                
            for category, questions in hallucination_dataset.items():
                for question in questions:
                    question_ids.append({
                        "id": question.get("id"),
                        "content": question.get("content"),
                        "source": f"幻觉数据集-{category}"
                    })
        except Exception as e:
            logger.warning(f"读取幻觉数据集时出错: {e}")
    
    return question_ids

def format_box(title, content, width=80):
    """格式化内容为带边框的文本框"""
    lines = []
    lines.append("+" + "-" * (width - 2) + "+")
    title_line = "| " + title.center(width - 4) + " |"
    lines.append(title_line)
    lines.append("|" + "-" * (width - 2) + "|")
    
    # 处理多行内容
    content_lines = content.split('\n')
    for line in content_lines:
        # 处理长行
        while len(line) > width - 4:
            lines.append("| " + line[:width-4] + " |")
            line = line[width-4:]
        lines.append("| " + line.ljust(width - 4) + " |")
    
    lines.append("+" + "-" * (width - 2) + "+")
    return "\n".join(lines)

def run_single_hallucination_test(question_id=None):
    """
    运行单次hallucination脆弱点测试，详细记录每个步骤
    
    Args:
        question_id: 可选，指定要测试的问题ID
    """
    print("\n" + "=" * 80)
    print("步骤1: 初始化测试环境".center(80))
    print("=" * 80 + "\n")
    
    # 创建Runner实例
    runner = Runner("config/config.yaml")
    logger.info("测试环境初始化完成")
    
    print("\n" + "=" * 80)
    print("步骤2: 选择测试问题".center(80))
    print("=" * 80 + "\n")
    
    # 指定hallucination类型
    vulnerability_type = "hallucination"
    
    # 如果没有指定问题ID，显示可选的幻觉测试问题
    if not question_id:
        available_questions = list_available_question_ids()
        if available_questions:
            print("可选的幻觉测试问题:")
            print("-" * 80)
            print(f"{'序号':<5}{'ID':<10}{'来源':<20}{'问题内容':<45}")
            print("-" * 80)
            for i, q in enumerate(available_questions, 1):
                # 截断过长的问题内容
                content = q['content']
                if len(content) > 40:
                    content = content[:40] + "..."
                print(f"{i:<5}{q['id']:<10}{q['source']:<20}{content:<45}")
            
            # 随机选择一个问题ID
            selected_question = random.choice(available_questions)
            question_id = selected_question["id"]
            print(f"\n随机选择问题: {question_id}")
            print(f"问题内容: {selected_question['content']}")
        else:
            question_id = "h001"  # 默认使用h001
            print(f"\n没有找到可用的幻觉测试问题，使用默认问题ID: {question_id}")
    
    logger.info(f"已选择脆弱点类型: {vulnerability_type}")
    logger.info(f"已选择问题ID: {question_id}")
    
    print("\n" + "=" * 80)
    print("步骤3: 执行测试".center(80))
    print("=" * 80 + "\n")
    print("正在向模型注入提示并等待响应...")
    
    # 记录开始时间
    start_time = time.time()
    
    # 运行单次测试，不指定模板以触发变异
    success = runner.run_once(vulnerability_type, question_id)
    
    # 记录结束时间并计算总耗时
    end_time = time.time()
    total_time = end_time - start_time
    
    # 获取测试结果详情
    current_task = runner.current_task
    
    # 获取使用的问题
    question = runner._find_question_by_id(question_id)
    
    # 获取使用的模板
    template_id = current_task.get('template_id')
    template = runner._find_template_by_id(template_id)
    
    print("\n" + "=" * 80)
    print("步骤4: 测试结果".center(80))
    print("=" * 80 + "\n")
    
    # 输出测试结果
    if success:
        print(format_box("✅ 测试结果: 成功", "模型产生了幻觉或不准确的信息"))
    else:
        print(format_box("❌ 测试结果: 失败", "模型正确回答了问题，没有产生幻觉"))
    
    print("\n问题信息:")
    print("-" * 80)
    print(f"问题ID: {question_id}")
    print(f"问题内容: {question.get('content', 'unknown')}")
    if 'fact' in question:
        print(f"正确事实: {question.get('fact', 'unknown')}")
    if 'correct_answers' in question:
        print(f"正确答案: {question.get('correct_answers', 'unknown')}")
    print("-" * 80)
    
    print("\n模板信息:")
    print("-" * 80)
    print(f"模板ID: {template_id}")
    print(f"模板内容: {template.get('content', 'unknown')}")
    print("-" * 80)
    
    # 尝试从日志文件中获取最近的提示和响应
    # 因为我们无法直接从runner对象获取这些信息
    try:
        log_dir = "logs"
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if log_files:
            latest_log = os.path.join(log_dir, sorted(log_files)[-1])
            with open(latest_log, 'r', encoding='utf-8') as f:
                log_content = f.read()
                
                # 尝试提取最近的提示和响应
                prompt_start = log_content.rfind("构造的完整提示:")
                if prompt_start > 0:
                    prompt_content = log_content[prompt_start:].split("\n", 2)[2].split("-" * 40, 1)[0].strip()
                    print("\n注入的提示:")
                    print("-" * 80)
                    print(prompt_content)
                    print("-" * 80)
                
                response_start = log_content.rfind("模型完整响应:")
                if response_start > 0:
                    response_content = log_content[response_start:].split("\n", 2)[2].split("-" * 40, 1)[0].strip()
                    print("\n模型响应:")
                    print("-" * 80)
                    print(response_content)
                    print("-" * 80)
    except Exception as e:
        logger.warning(f"无法从日志文件中提取提示和响应: {e}")
    
    logger.info(f"测试总耗时: {total_time:.2f}秒")
    logger.info(f"使用的问题ID: {question_id}")
    logger.info(f"使用的模板ID: {template_id}")
    
    print(f"\n测试总耗时: {total_time:.2f}秒")
    
    return success

if __name__ == "__main__":
    print("\n🔍 开始执行单次hallucination脆弱点测试 🔍\n")
    try:
        # 检查是否传入了问题ID参数
        if len(sys.argv) > 1:
            question_id = sys.argv[1]
            success = run_single_hallucination_test(question_id)
        else:
            success = run_single_hallucination_test()
            
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("用户中断测试")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1) 