import csv
import json
import os

def load_truthful_qa():
    """将TruthfulQA.csv加载并转换为类似question_pool格式的数据结构"""
    truthful_qa_data = {}
    
    csv_path = os.path.join("data", "TruthfulQA.csv")
    if not os.path.exists(csv_path):
        # 尝试相对当前脚本的路径
        csv_path = "TruthfulQA.csv"
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"无法找到TruthfulQA.csv文件，已尝试路径: data/TruthfulQA.csv 和 ./TruthfulQA.csv")
    
    print(f"正在从 {csv_path} 加载TruthfulQA数据...")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # 获取类别，如果为空则用"Other"
            category = row.get("Category", "Other")
            if not category:
                category = "Other"
            
            # 确保该类别的列表已创建
            if category not in truthful_qa_data:
                truthful_qa_data[category] = []
            
            # 为每个TruthfulQA问题创建一个条目
            entry = {
                "id": f"t{str(i+1).zfill(3)}",  # t001, t002, etc.
                "content": row["Question"],
                "type": row.get("Type", "Unknown"),
                "difficulty": "medium",  # 默认难度
                "fact": row.get("Best Answer", ""),
                "correct_answers": row.get("Correct Answers", ""),
                "incorrect_answers": row.get("Incorrect Answers", ""),
                "source": "TruthfulQA",
                "test_count": 0,
                "success_count": 0
            }
            
            # 添加到相应类别
            truthful_qa_data[category].append(entry)
    
    print(f"成功加载 {sum(len(questions) for questions in truthful_qa_data.values())} 个问题，分布在 {len(truthful_qa_data)} 个类别中")
    return truthful_qa_data

def create_hallucination_dataset():
    """创建专门的幻觉检测数据集"""
    # 确保data目录存在
    if not os.path.exists("data"):
        os.makedirs("data")
        print("已创建data目录")
    
    # 加载并按类别组织数据
    truthful_qa_by_category = load_truthful_qa()
    
    # 统计问题总数
    total_questions = sum(len(questions) for questions in truthful_qa_by_category.values())
    
    # 确定输出路径
    output_path = os.path.join("data", "hallucination_dataset.json")
    
    # 保存为JSON文件
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(truthful_qa_by_category, f, indent=2, ensure_ascii=False)
    
    print(f"成功转换 {total_questions} 个TruthfulQA问题到 {output_path}，按 {len(truthful_qa_by_category)} 个类别组织")
    return output_path

if __name__ == "__main__":
    try:
        output_file = create_hallucination_dataset()
        print(f"转换完成，数据已保存到 {output_file}")
    except Exception as e:
        print(f"转换过程中出错: {e}")
        import traceback
        print(traceback.format_exc()) 