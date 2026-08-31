# app.py
import streamlit as st
import streamlit.components.v1 as components
import json

# ================= 导入拆分的模块 =================
from db import load_database
from feedback import save_feedback, save_supplement_feedback
from style import get_base64_image, get_custom_css
from config import OPERATOR_NAMES

# ================= 1. 页面配置 =================
st.set_page_config(
    page_title="通行证玄学查询终端",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================= 2. Session State 初始化 =================
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "feedback_records" not in st.session_state:
    st.session_state["feedback_records"] = {}
if "show_supplement_form" not in st.session_state:
    st.session_state["show_supplement_form"] = False

# 新增：记录是否已看过介绍弹窗
if "intro_seen" not in st.session_state:
    st.session_state["intro_seen"] = False

has_searched = bool(st.session_state["search_query"])

# ================= 3. 注入动态 CSS 样式 =================
bg_b64 = get_base64_image("bg.jpg")
custom_css = get_custom_css(has_searched, bg_b64)
st.markdown(custom_css, unsafe_allow_html=True)

# ================= 4. 首次加载弹出介绍页 =================
if not st.session_state["intro_seen"]:
    st.markdown("""
    <div class="intro-box">
        <div class="intro-title">明日方舟通行证玄学查询终端</div>
        <div class="intro-text-line">致力于帮助解决“挂哪个干员的通行证”问题</div>
        <div class="intro-text-line">首次打开需要1-2分钟与prts建立链接</div>
        <div class="intro-text-line">输入愿望，搜索相近干员或搜索干员名称获取通行证分盒信息</div>
        <div class="intro-text-line">玄学查询仅供讨个彩头，无真实含义</div>
        <div class="intro-text-line">暂不支持如“克上司老板”等负面词条</div>
        <div class="intro-text-line">通行证分盒信息暂不完整</div>
        <div class="intro-text-line">如果搜索结果不匹配，可点击右上角反馈</div>
        <div class="intro-text-line">如果愿意帮助完善信息，可在查询结果页面填写补充信息</div>
        <div class="intro-text-line">人事部需要博士的好心助力</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_left, col_mid, col_right = st.columns([1, 1, 1])
    with col_mid:
        if st.button("进入终端", use_container_width=True, type="primary"):
            st.session_state["intro_seen"] = True
            st.rerun()  # 用户点击后刷新页面，即可跳过此判定
            
    # 【关键拦截】：在用户未点击“进入终端”之前，停止渲染下方的所有组件与模型加载
    st.stop()

# ================= 5. 加载 ChromaDB 数据库 =================
# （此时页面才真正开始加载数据库，所以首屏弹出极快）
try:
    collection = load_database()
except Exception as e:
    st.error(f"数据库加载失败，请检查模型或数据库文件路径：{e}")
    st.stop()

# ================= 6. 渲染第一屏 (Hero Section) =================
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
            "需求", placeholder="例如：逢考必过...", label_visibility="collapsed"
        )
    with col_btn:
        search_submitted = st.form_submit_button("寻访一次", use_container_width=True)

if search_submitted and user_input:
    st.session_state["search_query"] = user_input
    st.session_state["show_supplement_form"] = False  
    st.rerun()

query = st.session_state["search_query"]

# ================= 8. 渲染结果展示屏 =================
if query:
    st.markdown('<div id="results-anchor"></div>', unsafe_allow_html=True)

    components.html("""
    <script>
        setTimeout(function() {
            var el = window.parent.document.getElementById('results-anchor');
            if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
        }, 100);
    </script>
    """, height=0)

    with st.spinner("正在连接干员档案库，进行数据检索..."):
        # 1. 尝试按干员名称精确查找
        try:
            exact_results = collection.get(where={"operator_name": query})
        except Exception:
            exact_results = {"metadatas": []}

        # ================== 核心分流逻辑 ==================
        
        # 分支 A：只要输入的名字在 OPERATOR_NAMES 列表中，就严格判定为干员名字查询
        if query in OPERATOR_NAMES:
            # 尝试从向量数据库中获取该干员的所有记录
            results = collection.get(where={"operator_name": query})
            metadatas = results.get("metadatas", [])
            
            # 无论有没有词条，都先展示干员专属档案标题
            st.markdown(f"<h2 class='glow-text' style='margin-bottom: 25px;'>【{query}】 档案详情</h2>", unsafe_allow_html=True)
            
            # 情况 1：数据库中有该干员的玄学词条
            if metadatas:
                # 1. 提取分盒信息
                meta_first = metadatas[0]
                try: 
                    pass_info = json.loads(meta_first.get("pass_info", "[]"))
                except Exception: 
                    pass_info = meta_first.get("pass_info", "暂无分盒信息")
                
                pass_info_str = ", ".join([str(p) for p in pass_info]) if isinstance(pass_info, list) and pass_info else str(pass_info)
                
                # 2. 渲染分盒总结卡片
                st.markdown(f"""
                <div style="background: rgba(26, 26, 26, 0.92); border: 1px solid #3d3d3d; border-left: 4px solid #FF8C00; padding: 18px; margin-bottom: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.8);">
                    <div style="font-size: 1.3rem; color: #FFFFFF; font-weight: bold; margin-bottom: 8px;">通行证分盒信息</div>
                    <div style="font-size: 1.1rem; color: #E0E0E0;">{pass_info_str}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 3. 渲染收录的玄学标签
                st.markdown("<h3 style='color: #CCCCCC; margin-bottom: 20px; font-size: 1.2rem;'>收录的玄学标签</h3>", unsafe_allow_html=True)
                cols = st.columns(3, gap="medium")
                for i, meta in enumerate(metadatas):
                    with cols[i % 3]:
                        with st.container(border=True):
                            card_body_html = f"""
                            <div class="op-tag">{meta.get('trait_tag', '未分类')}</div>
                            <div class="op-content">{meta.get('trait_content', '')}</div>
                            <div class="op-info"><b>出处：</b>{meta.get('source_type', '档案')}</div>
                            """
                            st.markdown(card_body_html, unsafe_allow_html=True)

            # 情况 2：名字在干员名单里，但数据库中还没有收录其玄学词条
            else:
                st.warning(f"【{query}】已确认属于罗德岛干员，但目前档案库中暂未收录其玄学词条与分盒数据。")
                # 自动开启补充表单，引导用户直接提交
                st.session_state["show_supplement_form"] = True

        # 分支 B：非干员名字，走愿望/需求向量搜索逻辑
       
        else:
            # 只有搜愿望时才进行向量匹配查询，节省资源
            results = collection.query(query_texts=[query], n_results=15)
            
            st.markdown("<h2 class='glow-text' style='margin-bottom: 25px;'>招募结果</h2>", unsafe_allow_html=True)

            if results["metadatas"] and len(results["metadatas"][0]) > 0:
                metadatas = results["metadatas"][0]
                distances = results["distances"][0]

                candidates = []
                for meta, dist in zip(metadatas, distances):
                    weight = float(meta.get("weight", 1.0))
                    final_distance = dist / max(weight, 0.1)
                    candidates.append({"meta": meta, "final_dist": final_distance})

                candidates.sort(key=lambda x: x["final_dist"])
                top_candidates = candidates[:3]
                all_op_names = [c["meta"].get("operator_name", "未知") for c in top_candidates]

                result_cols = st.columns(3, gap="medium")
                for i, cand in enumerate(top_candidates):
                    meta = cand["meta"]
                    try: pass_info = json.loads(meta.get("pass_info", "[]"))
                    except Exception: pass_info = meta.get("pass_info", "暂无分盒信息")
                    
                    pass_info_str = ", ".join([str(p) for p in pass_info]) if isinstance(pass_info, list) and pass_info else str(pass_info)

                    with result_cols[i]:
                        with st.container(border=True):
                            card_key = f"{query}_{meta.get('operator_name', 'unk')}_{i}"
                            current_fb = st.session_state["feedback_records"].get(card_key, None)

                            c_title, c_btn1, c_btn2 = st.columns([4.5, 1.2, 1.2], gap="small")
                            
                            with c_title:
                                st.markdown(f"<div class='op-name'>{meta.get('operator_name', '未知干员')}</div>", unsafe_allow_html=True)

                            with c_btn1:
                                if st.button("✓", key=f"v_{card_key}", type="primary" if current_fb == "correct" else "secondary"):
                                    new_fb = "correct" if current_fb != "correct" else None
                                    st.session_state["feedback_records"][card_key] = new_fb
                                    if new_fb: save_feedback(query, meta, "correct", all_op_names)
                                    st.rerun()

                            with c_btn2:
                                if st.button("✕", key=f"x_{card_key}", type="primary" if current_fb == "incorrect" else "secondary"):
                                    new_fb = "incorrect" if current_fb != "incorrect" else None
                                    st.session_state["feedback_records"][card_key] = new_fb
                                    if new_fb: save_feedback(query, meta, "incorrect", all_op_names)
                                    st.rerun()

                            card_body_html = f"""
                            <div class="op-tag">{meta.get('trait_tag', '')}</div>
                            <div class="op-content">{meta.get('trait_content', '')}</div>
                            <div class="op-info"><b>出处：</b>{meta.get('source_type', '档案')}</div>
                            <div class="op-info"><b>分盒：</b>{pass_info_str}</div>
                            """
                            st.markdown(card_body_html, unsafe_allow_html=True)
            else:
                st.warning("未能寻访到合适干员，在罗德岛直聘碰碰运气吧")

        # ================= 9. 档案补充模块 (全网通用，无论搜干员还是搜愿望都保留) =================
        st.markdown("""
        <div style="margin-top: 35px; border-top: 1px solid rgba(255, 255, 255, 0.12); padding-top: 18px; color: #CCCCCC; font-size: 0.88rem; line-height: 1.8;">
            <div>帮助人事部补充档案：</div><div>点击右上角可反馈匹配程度</div>
        </div>
        """, unsafe_allow_html=True)

        col_btn_inline, col_txt_inline = st.columns([0.1, 0.9], gap="small")
        with col_btn_inline:
            if st.button("点击这里", key="btn_toggle_supplement"):
                st.session_state["show_supplement_form"] = not st.session_state["show_supplement_form"]
                st.rerun()
        with col_txt_inline:
            st.markdown("<div style='color: #CCCCCC; font-size: 0.88rem; line-height: 1.8; margin-left: -12px;'>反馈想补充的信息</div>", unsafe_allow_html=True)

        if st.session_state["show_supplement_form"]:
            with st.container(border=True):
                st.markdown("<h3 style='color: #FFFFFF; margin-bottom: 15px; font-weight: 700; font-size: 1.15rem;'>补充干员档案信息</h3>", unsafe_allow_html=True)
                with st.form(key="supplement_form", clear_on_submit=True):
                    supp_op_name = st.text_input("干员代号", placeholder="例如：银灰")
                    supp_trait = st.text_input("特殊才能", placeholder="例如：逢考必过、能力卓著...")
                    supp_source = st.text_input("出处（选填）", placeholder="例如：干员档案3 / 语音记录")
                    supp_pass_box = st.text_input("通行证分盒（选填）", placeholder="例如：A盒")
                    
                    if st.form_submit_button("提交补充档案", use_container_width=True):
                        if not supp_op_name.strip() or not supp_trait.strip():
                            st.error("请填写“干员代号”和“特殊才能”！")
                        else:
                            save_supplement_feedback(
                                query, supp_op_name.strip(), supp_trait.strip(),
                                supp_source.strip(), supp_pass_box.strip()
                            )
                            st.toast("反馈成功！感谢您协助罗德岛人事部")
                            st.session_state["show_supplement_form"] = False
                            st.rerun()