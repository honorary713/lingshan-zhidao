import logging
import time

logger = logging.getLogger("app.services.llm")
from openai import OpenAI

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=LLM_API_KEY or "EMPTY",
            base_url=LLM_BASE_URL,
        )

    def chat(self, messages: list[dict]) -> str:
        start = time.perf_counter()

        logger.info(
            "LLM chat 开始 model=%s messages=%d",
            LLM_MODEL,
            len(messages),
        )

        if not LLM_API_KEY:
            last_user = next(
                (message for message in reversed(messages) if message["role"] == "user"),
                None,
            )
            last_text = last_user["content"] if last_user else "无"
            return (
                f"当前是 Mock 模式，本轮收到 {len(messages)} 条消息。"
                f"最近一句：{last_text}"
            )

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.3,
        )

        usage = getattr(response, "usage", None)
        if usage:
            logger.info(
                "LLM tokens prompt=%s completion=%s total=%s",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )

        elapsed = time.perf_counter() - start
        logger.info(
            "LLM chat 完成 model=%s elapsed=%.3fs",
            LLM_MODEL,
            elapsed,
        )

        return response.choices[0].message.content

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        if not LLM_API_KEY:
            last_user = next(
                (message for message in reversed(messages) if message["role"] == "user"),
                None,
            )
            last_text = last_user["content"] if last_user else "无"
            return {
                "content": f"当前是 Mock 模式，最近一句：{last_text}",
                "tool_calls": [],
            }

        kwargs = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.3,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        usage = getattr(response, "usage", None)
        if usage:
            logger.info(
                "LLM tokens prompt=%s completion=%s total=%s",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )
        message = response.choices[0].message

        return {
            "content": message.content or "",
            "tool_calls": message.tool_calls or [],
        }


llm_service = LLMService()