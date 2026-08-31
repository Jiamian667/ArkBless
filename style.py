# style.py
import base64

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

def get_custom_css(has_searched, bg_b64):
    """根据状态动态生成 CSS"""
    
    # 1. 动态 CSS 部分（包含 Python 变量的动态样式）
    overflow_rule = "overflow-y: auto !important;" if has_searched else "overflow: hidden !important; height: 100vh !important;"
    bg_style_rule = (
        f'background-image: url("data:image/jpeg;base64,{bg_b64}");'
        if bg_b64 else "background-color: #121212;"
    )

    dynamic_css = f"""
    html, body, .stApp {{
        {overflow_rule}
    }}

    .stApp {{
        {bg_style_rule}
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    """

    # 2. 静态 CSS 部分（包含页面排版与鸿蒙弹性适配）
    static_css = """
    /* 隐藏 Streamlit 默认 Header 与 页脚 */
    header, [data-testid="stHeader"], footer {
        display: none !important;
    }

    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0, 0, 0, 0.60);
        z-index: 0;
        pointer-events: none;
    }

    /* Streamlit 主容器设置 */
    .block-container {
        position: relative !important;
        z-index: 1;
        max-width: 1200px !important;
        padding-top: 0rem !important;
        padding-bottom: 4rem !important;
        margin: 0 auto !important;
    }

    /* 通用白色文字发光阴影 */
    .glow-text {
        color: #FFFFFF !important;
        text-shadow: 
            0 0 8px #000000,
            0 0 16px #000000,
            0 0 24px #000000,
            0 0 32px #000000;
    }

    /* ================= 介绍弹窗 (Intro Box) ================= */
    .intro-box {
        background-color: rgba(26, 26, 26, 0.92);
        border: 1px solid #3d3d3d;
        border-top: 3px solid #FFFFFF;
        padding: 40px;
        margin: 12vh auto 30px auto;
        color: #FFFFFF;
        text-align: center;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.9);
        max-width: 650px;
    }
    .intro-title {
        font-size: 1.8rem;
        font-weight: 900;
        margin-bottom: 25px;
        letter-spacing: 2px;
        color: #FFFFFF;
    }
    .intro-text-line {
        font-size: 1.05rem;
        line-height: 2.2;
        color: #CCCCCC;
    }
    .intro-highlight {
        color: #FF8C00;
        font-weight: bold;
    }

    /* ================= Screen 1 (第一屏) ================= */
    .screen1-container {
        position: relative;
        width: 100%;
        min-height: 85vh;
        display: flex;
        justify-content: center;
        align-items: center;
        box-sizing: border-box;
    }

    .center-title {
        text-align: center;
        margin-bottom: 60px;
    }
    .main-title {
        font-size: 3.8rem;
        font-weight: 900;
        letter-spacing: 6px;
        line-height: 1.1;
    }
    .sub-title {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: 3px;
        margin-top: 6px;
        opacity: 0.95;
    }

    .bottom-left-box {
        position: absolute;
        bottom: 40px;
        left: 0px;
        text-align: left;
        pointer-events: none;
    }
    .bottom-left-title {
        font-size: 2rem;
        font-weight: 900;
        line-height: 1.2;
    }
    .bottom-left-sub {
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 4px;
        opacity: 0.9;
    }

    /* ================= 弹性适配：搜索表单 ================= */
    [data-testid="stForm"] {
        position: relative;
        z-index: 10;
    }

    /* 现代特性检查：支持高级选择器的浏览器才吸附在右下角，鸿蒙老系统自动降级回普通表单 */
    @supports selector(:has(*)) {
        [data-testid="stForm"]:has(input[aria-label="需求"]) {
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
        }

        [data-testid="stForm"]:has(input[aria-label="需求"]) input,
        [data-testid="stForm"]:has(input[aria-label="需求"]) button {
            pointer-events: auto !important;
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #FFFFFF !important;
            font-weight: bold !important;
            transition: all 0.2s ease;
        }
        
        [data-testid="stForm"]:has(input[aria-label="需求"]) button:hover {
            background-color: #E0E0E0 !important;
            color: #000000 !important;
            border-color: #E0E0E0 !important;
        }
    }

    /* ================= Screen 2 (档案面板样式) ================= */
    #results-anchor {
        padding-top: 60px;
        margin-bottom: 20px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        position: relative !important;
        z-index: 200 !important;
        background: rgba(26, 26, 26, 0.92) !important;
        border: 1px solid #3d3d3d !important;
        border-top: 3px solid #FFFFFF !important;
        border-radius: 0px !important;
        padding: 18px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8) !important;
        margin-bottom: 20px !important;
    }

    .op-name {
        font-size: 1.8rem;
        font-weight: 900;
        color: #FFFFFF !important;
        margin-bottom: 6px;
        letter-spacing: 1px;
        line-height: 1.2;
    }

    .op-tag {
        font-size: 1.05rem;
        font-weight: 700;
        color: #CCCCCC !important;
        margin-bottom: 14px;
    }

    .op-content {
        background-color: #242424;
        border-left: 3px solid #FFFFFF;
        padding: 12px 14px;
        border-radius: 0px !important;
        color: #E0E0E0 !important;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 14px;
    }

    .op-info {
        font-size: 0.9rem;
        color: #AAAAAA !important;
        margin-top: 6px;
    }

    .op-info b {
        color: #FFFFFF !important;
        font-weight: bold;
    }

    /* ================= 按钮样式定制 ================= */
    div[data-testid="stButton"] > button {
        border-radius: 0px !important;
        font-weight: bold !important;
        padding: 2px 0px !important;
        width: 100% !important;
        min-height: 32px !important;
        height: 32px !important;
    }

    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #FF8C00 !important;
        color: #FFFFFF !important;
        border: 1px solid #FF8C00 !important;
    }

    div[data-testid="stButton"] > button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #CCCCCC !important;
        border: 1px solid #444444 !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        border-color: #888888 !important;
    }

    button[aria-label="点击这里"] {
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
    }
    button[aria-label="点击这里"]:hover {
        color: #FFA500 !important;
        background: transparent !important;
    }

    /* ================= 移动端弹性布局 ================= */
    @media (max-width: 768px) {
        .main-title { font-size: 2.5rem; }
        .sub-title { font-size: 1.3rem; }
        .screen1-container {
            height: auto;
            min-height: 85vh;
            padding-bottom: 20px;
        }
        .bottom-left-box {
            position: static;
            text-align: center;
            margin-top: 2rem;
        }
        [data-testid="stForm"] {
            position: static !important;
            width: 100% !important;
            margin-top: 1rem;
            pointer-events: auto !important;
            background: rgba(25, 25, 25, 0.85) !important;
            padding: 15px !important;
            border: 1px solid #3d3d3d !important;
        }
        [data-testid="stForm"] input, [data-testid="stForm"] button {
            pointer-events: auto !important;
        }
    }
    """

    return f"""
    <style>
    {dynamic_css}
    {static_css}
    </style>
    """