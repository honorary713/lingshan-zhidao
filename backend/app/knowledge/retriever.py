import logging

logger = logging.getLogger("app.knowledge.retriever")
import json
from pathlib import Path

import faiss
import numpy as np

from app.knowledge.embedder import embed_query

INDEX_DIR = Path(__file__).resolve().parent.parent.parent / "indexes"
INDEX_FILE = INDEX_DIR / "lingshan.index"
CHUNKS_FILE = INDEX_DIR / "chunks.json"

_index = None
_chunks = None


def _load_index():
    global _index, _chunks

    if _index is not None and _chunks is not None:
        return _index, _chunks

    if not INDEX_FILE.exists() or not CHUNKS_FILE.exists():
        raise RuntimeError("知识库索引不存在，请先运行 indexer.py")

    _index = faiss.read_index(str(INDEX_FILE))

    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        _chunks = json.load(file)

    return _index, _chunks


def invalidate_cache() -> None:
    """重建索引后使进程内缓存失效，下次检索时重新加载。"""
    global _index, _chunks
    _index = None
    _chunks = None


def search(
    query: str,
    top_k: int = 3,
    category: str | None = None,
) -> list[dict]:
    logger.info(
        "检索开始 query=%s category=%s top_k=%s",
        query[:120],
        category,
        top_k,
    )

    try:
        index, chunks = _load_index()
        query_vector = np.array([embed_query(query)], dtype="float32")
    except Exception as exc:
        logger.warning("向量检索不可用，已降级为空结果: %s", exc)
        return []

    faiss.normalize_L2(query_vector)

    # 全量检索后再按分类过滤：分类检索时，相关块可能因向量相似度排名靠后
    # （如“校训”查询下含校训的块排在第 15 位）而被 top_k*3 截断漏掉。
    # FAISS 在数百向量规模下全量检索开销可忽略，且能保证不漏掉同类相关块。
    candidate_k = index.ntotal
    scores, indices = index.search(query_vector, candidate_k)

    results = []

    for score, chunk_index in zip(scores[0], indices[0]):
        if chunk_index < 0:
            continue

        chunk = chunks[chunk_index]

        if category and chunk.get("category") != category:
            continue

        results.append({
            "text": chunk["text"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
            "category": chunk.get("category", "scenic_spot"),
            "score": float(score),
        })

        if len(results) >= top_k:
            break

    logger.info(
        "检索完成 query=%s category=%s results=%d scores=%s",
        query[:120],
        category,
        len(results),
        [
            f"{item['source']}:{item['score']:.4f}"
            for item in results
        ],
    )

    return results


if __name__ == "__main__":
    result = search("图书馆怎么借书", top_k=3)

    print(f"检索到 {len(result)} 条结果")

    for item in result:
        print("---")
        print(f"来源：{item['source']}")
        print(f"分类：{item['category']}")
        print(f"相似度：{item['score']:.4f}")
        print(item["text"][:150])
