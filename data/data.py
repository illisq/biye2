import csv
import json
import os

def load_question_pool():
    """Load the existing question pool JSON file."""
    with open("data/question_pool.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_question_pool(question_pool):
    """Save the updated question pool to the JSON file."""
    with open("data/question_pool.json", "w", encoding="utf-8") as f:
        json.dump(question_pool, indent=2, ensure_ascii=False)

def load_truthful_qa():
    """Load the TruthfulQA dataset from CSV."""
    truthful_qa_data = []
    with open("data/TruthfulQA.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Create an entry for each TruthfulQA question
            entry = {
                "id": f"t{str(i+1).zfill(3)}",  # t001, t002, etc.
                "content": row["Question"],
                "source": row["Category"] if "Category" in row else "Unknown",
                "difficulty": "medium",  # Default difficulty
                "fact": row["Best Answer"] if "Best Answer" in row else "",
                "correct_answers": row["Correct Answers"] if "Correct Answers" in row else "",
                "incorrect_answers": row["Incorrect Answers"] if "Incorrect Answers" in row else "",
                "test_count": 0,
                "success_count": 0
            }
            truthful_qa_data.append(entry)
    return truthful_qa_data

def main():
    """Main function to update the question pool with TruthfulQA data."""
    # Load the existing question pool
    question_pool = load_question_pool()
    
    # Load TruthfulQA data
    truthful_qa_data = load_truthful_qa()
    
    # Add TruthfulQA category to the question pool if it doesn't exist
    if "truthful_qa" not in question_pool:
        question_pool["truthful_qa"] = []
    
    # Add TruthfulQA data to the question pool
    question_pool["truthful_qa"] = truthful_qa_data
    
    # Save the updated question pool
    save_question_pool(question_pool)
    
    print(f"Successfully added {len(truthful_qa_data)} TruthfulQA questions to the question pool.")

if __name__ == "__main__":
    main()
