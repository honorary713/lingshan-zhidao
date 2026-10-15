import json
from pathlib import Path

import faiss
import numpy as np

from app.knowledge.embedder import embed_texts
from app.knowledge.loader import load_documents
from app.knowledge.splitter import split_documents

INDEX_DIR = Path(__file__).resolve().parent.parent.parent / "indexes"
INDEX_FILE = INDEX_DIR / "lingshan.index"
CHUNKS_FILE = INDEX_DIR / "chunks.json"


def build_index() -> int:
    docs_dir = Path(__file__).resolve().parent.parent.parent / "knowledge_docs"
    documents = load_documents(docs_dir)
    chunks = split_documents(documents)

    texts = [chunk["text"] for chunk in chunks]
    vectors = np.array(embed_texts(texts), dtype="float32")

    # 归一化后可以用内积计算余弦相似度
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))

    with open(CHUNKS_FILE, "w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    print(f"索引构建完成：{len(chunks)} 个 chunk")
    print(f"向量维度：{vectors.shape[1]}")
    print(f"索引文件：{INDEX_FILE}")

    return len(chunks)


def rebuild_index() -> int:
    """重建索引：合并 knowledge_docs 文件夹文档 + 数据库中的知识文档。

    管理后台新增/删除知识文档后调用，确保数字人能检索到最新内容。
    """
    from app.database import list_knowledge_documents
    from app.knowledge.retriever import invalidate_cache

    docs_dir = Path(__file__).resolve().parent.parent.parent / "knowledge_docs"
    documents = load_documents(docs_dir)

    for doc in list_knowledge_documents():
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        documents.append({
            "source": doc.get("title") or f"知识库#{doc.get('id')}",
            "text": content,
        })

    chunks = split_documents(documents)
    texts = [chunk["text"] for chunk in chunks]
    vectors = np.array(embed_texts(texts), dtype="float32")
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))

    with open(CHUNKS_FILE, "w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    invalidate_cache()
    print(f"索引重建完成：{len(chunks)} 个 chunk（含数据库文档）")
    return len(chunks)


if __name__ == "__main__":
    build_index()