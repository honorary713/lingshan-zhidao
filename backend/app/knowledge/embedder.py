from openai import OpenAI

from app.config import (
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_MODEL,
)

client = OpenAI(
    api_key=EMBEDDING_API_KEY or "EMPTY",
    base_url=EMBEDDING_BASE_URL,
)

BATCH_SIZE = 10


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not EMBEDDING_API_KEY:
        raise RuntimeError("未配置 EMBEDDING_API_KEY")

    results = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )

        results.extend(item.embedding for item in response.data)

    return results


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


if __name__ == "__main__":
    vector = embed_query("中国石油大学（华东）校区有哪些")

    print(f"向量维度：{len(vector)}")
    print(f"前 5 个数值：{vector[:5]}")