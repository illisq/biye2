import argparse
import logging
import sys
import os
import time
from typing import Optional, Dict, Any

from core.runner import Runner
from utils.logger import Logger
from utils.file_manager import FileManager

# 配置根日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='大语言模型模糊测试框架')
    
    # 基本参数
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='配置文件路径')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    
    # 运行模式
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--single', action='store_true',
                           help='运行单次测试')
    mode_group.add_argument('--batch', type=int,
                           help='批量运行指定次数的测试')
    mode_group.add_argument('--retry', action='store_true',
                           help='带重试的测试模式')
    
    # 脆弱点类型
    parser.add_argument('--type', type=str, 
                       choices=['hallucination', 'safety', 'long_context', 
                               'consistency', 'prompt_injection'],
                       help='指定脆弱点类型')
    
    # 高级选项
    parser.add_argument('--question-id', type=str,
                       help='指定问题ID')
    parser.add_argument('--template-id', type=str,
                       help='指定模板ID')
    parser.add_argument('--max-retries', type=int,
                       help='最大重试次数，仅在retry模式下有效')
    
    return parser.parse_args()

def setup_environment(config_path: str) -> Dict[str, Any]:
    """设置运行环境
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    # 确保目录结构
    dirs_to_create = [
        'logs',
        'data/history',
        'data/prompts_cache'
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
    
    # 加载配置
    config = FileManager.load_yaml(config_path)
    if not config:
        logger.error(f"无法加载配置文件: {config_path}")
        sys.exit(1)
        
    return config

def run_test(args):
    """运行测试
    
    Args:
        args: 命令行参数
    """
    # 设置环境
    config = setup_environment(args.config)
    
    # 更新日志级别
    if args.log_level:
        config['system']['log_level'] = args.log_level
    
    # 初始化全局日志
    logger_instance = Logger(config['system']['log_level'])
    logger_instance.info("初始化模糊测试框架")
    
    # 创建运行器
    try:
        runner = Runner(args.config)
    except Exception as e:
        logger.error(f"初始化运行器失败: {e}")
        sys.exit(1)
    
    # 根据模式运行测试
    try:
        if args.single:
            # 单次测试
            logger.info("开始单次测试")
            success = runner.run_once(args.type, args.question_id, args.template_id)
            logger.info(f"测试结果: {'成功' if success else '失败'}")
            
        elif args.batch:
            # 批量测试
            batch_size = args.batch
            logger.info(f"开始批量测试，数量: {batch_size}")
            results = runner.run_batch(batch_size, args.type)
            
            # 输出详细结果
            logger.info(f"批量测试完成: 成功率 {results['success_rate']:.2f}, " +
                       f"耗时 {results['total_time']:.2f} 秒")
            
            for vul_type, stats in results['vulnerable_types'].items():
                logger.info(f"  类型 {vul_type}: " +
                           f"成功 {stats['successful']}/{stats['total']}, " +
                           f"成功率 {stats['success_rate']:.2f}")
                
        elif args.retry:
            # 带重试的测试
            max_retries = args.max_retries
            logger.info(f"开始带重试的测试，最大重试次数: {max_retries if max_retries else '默认值'}")
            success = runner.run_with_retry(args.type, max_retries)
            logger.info(f"测试结果: {'成功' if success else '失败'}")
            
        else:
            # 默认运行模式：批量测试10次
            logger.info("使用默认模式：批量测试10次")
            results = runner.run_batch(10, args.type)
            
            # 输出详细结果
            logger.info(f"批量测试完成: 成功率 {results['success_rate']:.2f}, " +
                       f"耗时 {results['total_time']:.2f} 秒")
            
    except KeyboardInterrupt:
        logger.info("用户中断测试")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 记录启动信息
    logger.info("启动大语言模型模糊测试框架")
    
    # 记录启动参数
    if args.single:
        mode = "单次测试"
    elif args.batch:
        mode = f"批量测试 ({args.batch}次)"
    elif args.retry:
        mode = f"带重试测试 (最大{args.max_retries if args.max_retries else '默认'}次)"
    else:
        mode = "默认模式"
        
    logger.info(f"运行模式: {mode}")
    if args.type:
        logger.info(f"脆弱点类型: {args.type}")
    
    # 运行测试
    start_time = time.time()
    run_test(args)
    end_time = time.time()
    
    # 输出总运行时间
    total_time = end_time - start_time
    logger.info(f"模糊测试完成，总耗时: {total_time:.2f} 秒")

if __name__ == "__main__":
    main() 