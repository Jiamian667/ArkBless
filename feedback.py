# feedback.py
import datetime
import requests
import streamlit as st

try:
    WEBHOOK_URL = st.secrets["WEBHOOK_URL"]
except KeyError:
    # 作为一个保险，如果没配密钥就置空，防止程序崩溃
    WEBHOOK_URL = ""

def save_feedback(query, meta, feedback_type, all_op_names=None):
    """发送匹配反馈到机器人"""
    fb_text = "✅ 准确" if feedback_type == "correct" else "❌ 不准确"
    
    content = f"""【玄学匹配反馈】
🔍 搜索词：{query}
👤 匹配干员：{meta.get("operator_name", "未知")}
🏷️ 标签：{meta.get("trait_tag", "")}
💡 用户评价：{fb_text}
🕒 时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

    _send_to_bot(content)

def save_supplement_feedback(query, op_name, trait, source, pass_box):
    """发送补充档案到机器人"""
    content = f"""【新增干员档案补充】
🔍 原搜索词：{query}
👤 提交干员：{op_name}
✨ 特殊才能：{trait}
📚 出处：{source or "未提供"}
📦 分盒：{pass_box or "未提供"}
🕒 时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

    _send_to_bot(content)

def _send_to_bot(text_content):
    """钉钉机器人专用发送方法"""
    if not WEBHOOK_URL or not WEBHOOK_URL.startswith("http"):
        print("Webhook URL 未配置或格式错误，跳过发送")
        return
        
    # 钉钉 API 规定的格式
    payload = {
        "msgtype": "text",
        "text": {
            "content": text_content
        }
    }
    
    try:
        # 发送 POST 请求
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        # 将钉钉服务器的返回结果打印在终端里，方便排错
        print(f"钉钉推送结果: {response.text}")
    except Exception as e:
        print(f"推送过程发生网络错误: {e}")