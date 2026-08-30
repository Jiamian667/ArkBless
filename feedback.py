# feedback.py
import json
import os
import datetime

FEEDBACK_FILE = "feedback.json"

def save_feedback(query, meta, feedback_type, all_op_names=None):
    """保存搜索词、本次搜索结果及对错反馈到 JSON 文件中"""
    record = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "match_feedback",
        "search_query": query,
        "feedback_item": {
            "operator_name": meta.get("operator_name", "未知"),
            "trait_tag": meta.get("trait_tag", ""),
            "trait_content": meta.get("trait_content", ""),
            "source_type": meta.get("source_type", ""),
        },
        "feedback": feedback_type,
        "all_returned_operators": all_op_names or []
    }
    _write_to_json(record)

def save_supplement_feedback(query, op_name, trait, source, pass_box):
    """保存用户主动补充的干员档案数据"""
    record = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "supplement_archive",
        "search_query": query,
        "supplement_data": {
            "operator_name": op_name,
            "special_talent": trait,
            "source": source or "未知",
            "pass_box": pass_box or "未提供"
        }
    }
    _write_to_json(record)

def _write_to_json(record):
    """内部通用写入 JSON 方法"""
    existing_data = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = []
            
    existing_data.append(record)
    
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)