"""
Embedding 服务
模型下载需要外网，当前不可用。知识库问答自动降级为 LLM 自有知识。
恢复方法：网络可用后，删掉此文件顶部 _OFFLINE 行，或将模型手动放入缓存目录。
"""
import numpy as np

_OFFLINE = True  # 改为 False 即可恢复本地模型


def get_embedding(text: str):
    """获取文本向量，离线模式下返回零向量"""
    if _OFFLINE or not text or not text.strip():
        return np.zeros(1024, dtype=np.float32)
    # 在线模式：加载 BAAI/bge-large-zh-v1.5
    try:
        import os
        os.environ.pop("HF_ENDPOINT", None)
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
        vec = model.encode(text.strip(), normalize_embeddings=True)
        return np.array(vec, dtype=np.float32)
    except Exception:
        return np.zeros(1024, dtype=np.float32)
