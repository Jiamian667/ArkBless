__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import base64
import json
import os
import datetime
import chromadb
from chromadb.utils import embedding_functions
import streamlit as st
import streamlit.components.v1 as components

# ================= 0. 反馈数据保存函数 =================
FEEDBACK_FILE = "feedback.json"

def save_feedback(query, meta, feedback_type, all_op_names=None):
    """保存搜索词、本次搜索结果及对错反馈到 JSON 文件中"""
    record = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "match_feedback",
        "search_query": query,  # 用户本次搜索的内容/关键词
        "feedback_item": {      # 被评价的干员项
            "operator_name": meta.get("operator_name", "未知"),
            "trait_tag": meta.get("trait_tag", ""),
            "trait_content": meta.get("trait_content", ""),
            "source_type": meta.get("source_type", ""),
        },
        "feedback": feedback_type,  # 'correct' (正确) 或 'incorrect' (不准确)
        "all_returned_operators": all_op_names or []  # 本次搜索出的全部前置候选干员
    }
    
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

# ================= 1. 页面配置 =================
st.set_page_config(
    page_title="通行证玄学查询终端",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================= 2. 读取本地背景图片 =================
BG_IMAGE_PATH = "bg.jpg"

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

bg_b64 = get_base64_image(BG_IMAGE_PATH)

bg_style_rule = (
    f'background-image: url("data:image/jpeg;base64,{bg_b64}");'
    if bg_b64
    else "background-color: #121212;"
)

# ================= 3. Session State 初始化 =================
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""

if "feedback_records" not in st.session_state:
    st.session_state["feedback_records"] = {}

if "show_supplement_form" not in st.session_state:
    st.session_state["show_supplement_form"] = False

has_searched = bool(st.session_state["search_query"])

# ================= 4. 注入 CSS 样式 =================
overflow_rule = "overflow-y: auto !important;" if has_searched else "overflow: hidden !important; height: 100vh !important;"

custom_css = f"""
<style>
/* 隐藏 Streamlit 默认 Header 与 页脚 */
header, [data-testid="stHeader"], footer {{
    display: none !important;
}}

/* 未搜索时锁定第一屏，搜索后解锁垂直滚动 */
html, body, .stApp {{
    {overflow_rule}
}}

/* 背景图与全屏半透明黑色遮罩 */
.stApp {{
    {bg_style_rule}
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

.stApp::before {{
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.60);
    z-index: 0;
    pointer-events: none;
}}

/* Streamlit 主容器设置 */
.block-container {{
    position: relative !important;
    z-index: 1;
    max-width: 1200px !important;
    padding-top: 0rem !important;
    padding-bottom: 4rem !important;
    margin: 0 auto !important;
}}

/* 通用白色文字发光阴影 */
.glow-text {{
    color: #FFFFFF !important;
    text-shadow: 
        0 0 8px #000000,
        0 0 16px #000000,
        0 0 24px #000000,
        0 0 32px #000000;
}}

/* ================= Screen 1 (第一屏) ================= */
.screen1-container {{
    position: relative;
    width: 100%;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
}}

.center-title {{
    text-align: center;
    margin-bottom: 60px;
}}
.main-title {{
    font-size: 3.8rem;
    font-weight: 900;
    letter-spacing: 6px;
    line-height: 1.1;
}}
.sub-title {{
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: 3px;
    margin-top: 6px;
    opacity: 0.95;
}}

.bottom-left-box {{
    position: absolute;
    bottom: 40px;
    left: 0px;
    text-align: left;
    pointer-events: none;
}}
.bottom-left-title {{
    font-size: 2rem;
    font-weight: 900;
    line-height: 1.2;
}}
.bottom-left-sub {{
    font-size: 1.1rem;
    font-weight: 600;
    margin-top: 4px;
    opacity: 0.9;
}}

/* 仅针对“寻访”搜索表单应用右下角绝对定位，避免影响其他表单 */
[data-testid="stForm"]:has(input[aria-label="需求"]) {{
    position: absolute !important;
    top: calc(100vh - 95px) !important;
    right: 0px !important;
    left: auto !important;
    bottom: auto !important;
    z-index: 10 !important;
    width: 380px !important;
    max-width: calc(100vw - 60px) !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    pointer-events: none !important;
}}

[data-testid="stForm"]:has(input[aria-label="需求"]) input,
[data-testid="stForm"]:has(input[aria-label="需求"]) button[type="submit"] {{
    pointer-events: auto !important;
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #FFFFFF !important;
    font-weight: bold !important;
    transition: all 0.2s ease;
}}
[data-testid="stForm"]:has(input[aria-label="需求"]) button[type="submit"]:hover {{
    background-color: #E0E0E0 !important;
    color: #000000 !important;
    border-color: #E0E0E0 !important;
}}

/* ================= Screen 2 (重构后的深灰直角卡片容器) ================= */
#results-anchor {{
    padding-top: 60px;
    margin-bottom: 20px;
}}

[data-testid="stVerticalBlockBorderWrapper"] {{
    position: relative !important;
    z-index: 200 !important;
    background: rgba(26, 26, 26, 0.92) !important;
    border: 1px solid #3d3d3d !important;
    border-top: 3px solid #FFFFFF !important;
    border-radius: 0px !important;
    padding: 18px !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8) !important;
    margin-bottom: 20px !important;
}}

.op-name {{
    font-size: 1.8rem;
    font-weight: 900;
    color: #FFFFFF !important;
    margin-bottom: 6px;
    letter-spacing: 1px;
    line-height: 1.2;
}}

.op-tag {{
    font-size: 1.05rem;
    font-weight: 700;
    color: #CCCCCC !important;
    margin-bottom: 14px;
}}

.op-content {{
    background-color: #242424;
    border-left: 3px solid #FFFFFF;
    padding: 12px 14px;
    border-radius: 0px !important;
    color: #E0E0E0 !important;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 14px;
}}

.op-info {{
    font-size: 0.9rem;
    color: #AAAAAA !important;
    margin-top: 6px;
}}

.op-info b {{
    color: #FFFFFF !important;
    font-weight: bold;
}}

/* ================= 右上角反馈按钮样式定制 ================= */
div[data-testid="stButton"] > button {{
    border-radius: 0px !important;
    font-weight: bold !important;
    padding: 2px 0px !important;
    width: 100% !important;
    min-height: 32px !important;
    height: 32px !important;
}}

/* 选中的状态（primary）：变成橙色 */
div[data-testid="stButton"] > button[kind="primary"] {{
    background-color: #FF8C00 !important;
    color: #FFFFFF !important;
    border: 1px solid #FF8C00 !important;
}}

/* 未选中的状态（secondary）：半透明灰色 */
div[data-testid="stButton"] > button[kind="secondary"] {{
    background-color: rgba(255, 255, 255, 0.08) !important;
    color: #CCCCCC !important;
    border: 1px solid #444444 !important;
}}
div[data-testid="stButton"] > button[kind="secondary"]:hover {{
    background-color: rgba(255, 255, 255, 0.25) !important;
    color: #FFFFFF !important;
    border-color: #888888 !important;
}}

/* 特殊定制：橙色“点击这里”纯文字按钮 */
button[aria-label="点击这里"] {{
    background: transparent !important;
    color: #FF8C00 !important;
    border: none !important;
    font-weight: bold !important;
    font-size: 0.88rem !important;
    padding: 0px !important;
    margin: 0px !important;
    height: auto !important;
    min-height: auto !important;
    text-decoration: underline !important;
    box-shadow: none !important;
    cursor: pointer !important;
}}
button[aria-label="点击这里"]:hover {{
    color: #FFA500 !important;
    background: transparent !important;
}}

@media (max-width: 768px) {{
    .main-title {{ font-size: 2.5rem; }}
    .sub-title {{ font-size: 1.3rem; }}
    .screen1-container {{
        height: auto;
        min-height: 100vh;
        padding-bottom: 20px;
    }}
    .bottom-left-box {{
        position: static;
        text-align: center;
        margin-top: 2rem;
    }}
    [data-testid="stForm"]:has(input[aria-label="需求"]) {{
        position: static !important;
        width: 100% !important;
        margin-top: 1rem;
    }}
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ================= 5. 加载 ChromaDB 数据库 =================
@st.cache_resource
def load_database():
    client = chromadb.PersistentClient(path="./ark_chroma_db")
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="shibing624/text2vec-base-chinese"
    )
    collection = client.get_collection(
        name="arkbless_traits", embedding_function=emb_fn
    )
    return collection

try:
    collection = load_database()
except Exception as e:
    st.error(f"数据库加载失败，请检查模型或数据库文件路径：{e}")
    st.stop()

# ================= 6. 渲染 Screen 1 (第一屏) =================
st.markdown("""
<div class="screen1-container">
    <div class="center-title glow-text">
        <div class="main-title">特殊寻访</div>
        <div class="sub-title">Arkblessing</div>
    </div>
    <div class="bottom-left-box glow-text">
        <div class="bottom-left-title">特殊干员定向寻访</div>
        <div class="bottom-left-sub">适合保佑特定属性的强力干员</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ================= 7. 右下角搜索表单 =================
with st.form(key="search_form", clear_on_submit=False):
    col_input, col_btn = st.columns([3, 1.5], gap="small")
    with col_input:
        user_input = st.text_input(
            "需求",
            placeholder="例如：逢考必过...",
            label_visibility="collapsed"
        )
    with col_btn:
        search_submitted = st.form_submit_button("寻访一次", use_container_width=True)

if search_submitted and user_input:
    st.session_state["search_query"] = user_input
    st.session_state["show_supplement_form"] = False  # 重新搜索时收起补充表单

query = st.session_state["search_query"]

# ================= 8. 渲染 Screen 2 (结果展示) =================
if query:
    st.markdown('<div id="results-anchor"></div>', unsafe_allow_html=True)

    components.html("""
    <script>
        setTimeout(function() {
            var el = window.parent.document.getElementById('results-anchor');
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    </script>
    """, height=0)

    with st.spinner("正在连接干员档案库，进行向量匹配..."):
        results = collection.query(query_texts=[query], n_results=15)

        if results["metadatas"] and len(results["metadatas"][0]) > 0:
            st.markdown("<h2 class='glow-text' style='margin-bottom: 25px;'>招募结果</h2>", unsafe_allow_html=True)

            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            candidates = []
            for meta, dist in zip(metadatas, distances):
                weight = float(meta.get("weight", 1.0))
                final_distance = dist / max(weight, 0.1)

                candidates.append({
                    "meta": meta,
                    "final_dist": final_distance,
                })

            candidates.sort(key=lambda x: x["final_dist"])
            top_candidates = candidates[:3]

            # 获取本次搜索出来的所有干员名称列表
            all_op_names = [c["meta"].get("operator_name", "未知") for c in top_candidates]

            result_cols = st.columns(3, gap="medium")

            for i, cand in enumerate(top_candidates):
                meta = cand["meta"]

                try:
                    pass_info = json.loads(meta.get("pass_info", "[]"))
                except Exception:
                    pass_info = meta.get("pass_info", "暂无分盒信息")

                if isinstance(pass_info, list):
                    pass_info_str = ", ".join([str(p) for p in pass_info]) if pass_info else "暂无"
                else:
                    pass_info_str = str(pass_info)

                with result_cols[i]:
                    with st.container(border=True):
                        card_key = f"{query}_{meta.get('operator_name', 'unk')}_{i}"
                        current_fb = st.session_state["feedback_records"].get(card_key, None)

                        c_title, c_btn1, c_btn2 = st.columns([4.5, 1.2, 1.2], gap="small")

                        with c_title:
                            st.markdown(f"<div class='op-name'>{meta.get('operator_name', '未知干员')}</div>", unsafe_allow_html=True)

                        with c_btn1:
                            btn_v = st.button(
                                "✓",
                                key=f"v_{card_key}",
                                type="primary" if current_fb == "correct" else "secondary"
                            )

                        with c_btn2:
                            btn_x = st.button(
                                "✕",
                                key=f"x_{card_key}",
                                type="primary" if current_fb == "incorrect" else "secondary"
                            )

                        # 处理点击逻辑
                        if btn_v:
                            new_fb = "correct" if current_fb != "correct" else None
                            st.session_state["feedback_records"][card_key] = new_fb
                            if new_fb:
                                save_feedback(query, meta, "correct", all_op_names)
                            st.rerun()

                        if btn_x:
                            new_fb = "incorrect" if current_fb != "incorrect" else None
                            st.session_state["feedback_records"][card_key] = new_fb
                            if new_fb:
                                save_feedback(query, meta, "incorrect", all_op_names)
                            st.rerun()

                        card_body_html = f"""
                        <div class="op-tag">{meta.get('trait_tag', '')}</div>
                        <div class="op-content">{meta.get('trait_content', '')}</div>
                        <div class="op-info"><b>出处：</b>{meta.get('source_type', '档案')}</div>
                        <div class="op-info"><b>分盒：</b>{pass_info_str}</div>
                        """
                        st.markdown(card_body_html, unsafe_allow_html=True)

            # ================= 9. 底部小字提示与档案补充入口 =================
            st.markdown("""
            <div style="margin-top: 35px; border-top: 1px solid rgba(255, 255, 255, 0.12); padding-top: 18px; color: #CCCCCC; font-size: 0.88rem; line-height: 1.8;">
                <div>帮助人事部补充档案：</div>
                <div>点击右上角可反馈匹配程度</div>
            </div>
            """, unsafe_allow_html=True)

            col_btn_inline, col_txt_inline = st.columns([0.1, 0.9], gap="small")
            with col_btn_inline:
                if st.button("点击这里", key="btn_toggle_supplement"):
                    st.session_state["show_supplement_form"] = not st.session_state["show_supplement_form"]
                    st.rerun()
            with col_txt_inline:
                st.markdown("<div style='color: #CCCCCC; font-size: 0.88rem; line-height: 1.8; margin-left: -12px;'>反馈想补充的信息</div>", unsafe_allow_html=True)

            # ================= 10. 档案补充填空表单 =================
            if st.session_state["show_supplement_form"]:
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("<h3 style='color: #FFFFFF; margin-bottom: 15px; font-weight: 700; font-size: 1.15rem;'>补充干员档案信息</h3>", unsafe_allow_html=True)
                    
                    with st.form(key="supplement_form", clear_on_submit=True):
                        supp_op_name = st.text_input("干员代号", placeholder="例如：银灰")
                        supp_trait = st.text_input("特殊才能", placeholder="例如：逢考必过、能力卓著...")
                        supp_source = st.text_input("出处（选填）", placeholder="例如：干员档案3 / 语音记录")
                        supp_pass_box = st.text_input("通行证分盒（选填）", placeholder="例如：A盒")

                        col_sub, _ = st.columns([1.2, 3.8])
                        with col_sub:
                            submit_supp = st.form_submit_button("提交补充档案", use_container_width=True)

                        if submit_supp:
                            if not supp_op_name.strip() or not supp_trait.strip():
                                st.error("请填写“干员代号”和“特殊才能”！")
                            else:
                                save_supplement_feedback(
                                    query=query,
                                    op_name=supp_op_name.strip(),
                                    trait=supp_trait.strip(),
                                    source=supp_source.strip(),
                                    pass_box=supp_pass_box.strip()
                                )
                                st.toast("反馈成功！感谢您协助罗德岛人事部")
                                st.session_state["show_supplement_form"] = False
                                st.rerun()

        else:
            st.warning("未能寻访到合适干员，在罗德岛直聘碰碰运气吧")