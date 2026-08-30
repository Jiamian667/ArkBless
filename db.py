#前端网页的子网页
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import chromadb
from chromadb.utils import embedding_functions
import streamlit as st

@st.cache_resource(show_spinner=False)  # 把默认的 spinner 关掉，我们在 app.py 里自定义
def load_database():
    """初始化并缓存数据库连接，同时强制预热语言模型"""
    client = chromadb.PersistentClient(path="./ark_chroma_db")
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="shibing624/text2vec-base-chinese"
    )
    collection = client.get_collection(
        name="arkbless_traits", embedding_function=emb_fn
    )
    
    # ================= 核心修改：模型预热 =================
    # ChromaDB 默认是懒加载，这里我们强制进行一次无意义的查询
    # 迫使系统在此时就开始下载(首次)并加载模型到内存中
    try:
        collection.query(query_texts=["初始化系统预热"], n_results=1)
    except Exception:
        pass
        
    return collection