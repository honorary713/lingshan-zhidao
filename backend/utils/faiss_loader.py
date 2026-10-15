import os
import tempfile
import shutil
from pathlib import Path
from models.faq import FAQ
from database import SessionLocal
from services.embedding_service import get_embedding

FAQ_INDEX_FILE = Path("./faq_index.bin")
FAQ_ID_MAP_FILE = Path("./faq_id_map.npy")

def _write_faq_index(index, faq_ids):
    """写入FAQ向量库（临时目录中转，绕过Windows中文路径bug）"""
    import faiss
    import numpy as np
    _tmp_dir = tempfile.mkdtemp(prefix="faq_build_")
    try:
        _tmp_bin = os.path.join(_tmp_dir, "faq_index.bin")
        _tmp_npy = os.path.join(_tmp_dir, "faq_id_map.npy")
        faiss.write_index(index, _tmp_bin)
        np.save(_tmp_npy, np.array(faq_ids))
        shutil.copy2(_tmp_bin, str(FAQ_INDEX_FILE))
        shutil.copy2(_tmp_npy, str(FAQ_ID_MAP_FILE))
    finally:
        shutil.rmtree(_tmp_dir, ignore_errors=True)

def rebuild_faiss_index():
    """重建FAQ问答专用向量库，不影响docx生成的faiss_scenic_index文档向量"""
    import faiss
    import numpy as np
    with SessionLocal() as db:
        faq_list = db.query(FAQ).filter(FAQ.is_active == True).all()

    if not faq_list:
        print("⚠️ 当前无有效FAQ问答，生成空FAQ向量索引")
        dim = len(get_embedding("测试文本"))
        empty_index = faiss.IndexFlatL2(dim)
        _write_faq_index(empty_index, [])
        if not FAQ_INDEX_FILE.exists():
            raise RuntimeError("空索引写入失败，根目录无写入权限")
        return

    question_texts = [item.question for item in faq_list]
    faq_ids = [item.id for item in faq_list]
    vec_array = np.array([get_embedding(text) for text in question_texts], dtype=np.float32)

    dim = vec_array.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vec_array)

    try:
        _write_faq_index(index, faq_ids)
        if not (FAQ_INDEX_FILE.exists() and FAQ_ID_MAP_FILE.exists()):
            raise RuntimeError("文件写入完成后未检测到bin/npy向量文件")
        print(f"✅ FAQ向量库重建完成，共 {len(faq_list)} 条有效问答，维度: {dim}")
    except Exception as err:
        raise RuntimeError(f"FAQ向量文件写入失败：{str(FAQ_INDEX_FILE)}\n错误信息：{err}") from err