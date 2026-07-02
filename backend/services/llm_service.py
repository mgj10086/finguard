"""
LLM 统一调用接口

封装 vLLM / Ollama（兼容 OpenAI API），支持：
- 同步/流式调用
- 备选 LLM fallback（如 DeepSeek API）
- 结构化输出（JSON mode）
- Token 用量统计
"""

import json
import logging
from typing import Any, AsyncGenerator, Optional

from openai import AsyncOpenAI

from backend.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服务封装"""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self._fallback_client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """主 LLM 客户端（vLLM/Ollama）"""
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
                timeout=120.0,
                max_retries=2,
            )
        return self._client

    @property
    def fallback_client(self) -> Optional[AsyncOpenAI]:
        """备选 LLM 客户端（如 DeepSeek API）"""
        if not settings.FALLBACK_LLM_BASE_URL:
            return None
        if self._fallback_client is None:
            self._fallback_client = AsyncOpenAI(
                base_url=settings.FALLBACK_LLM_BASE_URL,
                api_key=settings.FALLBACK_LLM_API_KEY,
            )
        return self._fallback_client

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
        use_fallback: bool = False,
    ) -> tuple[str, dict]:
        """
        同步调用 LLM

        Args:
            messages: 消息列表
            model: 模型名，默认使用配置
            temperature: 温度，默认使用配置
            max_tokens: 最大 token 数
            response_format: {"type": "json_object"} 启用 JSON mode
            use_fallback: 是否使用备选 LLM

        Returns:
            (content, usage_info)
        """
        client = self.fallback_client if use_fallback else self.client
        model_name = (
            settings.FALLBACK_LLM_MODEL_NAME if use_fallback
            else (model or settings.LLM_MODEL_NAME)
        )

        kwargs = dict(
            model=model_name,
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
                "model": model_name,
            }
            return content, usage
        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            if not use_fallback and self.fallback_client:
                logger.info("Falling back to backup LLM...")
                return await self.chat(
                    messages=messages, model=model,
                    temperature=temperature, max_tokens=max_tokens,
                    response_format=response_format, use_fallback=True,
                )
            raise

    async def chat_stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """流式调用 LLM"""
        stream = await self.client.chat.completions.create(
            model=model or settings.LLM_MODEL_NAME,
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def chat_structured(
        self,
        messages: list[dict],
        output_schema: dict[str, Any],
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        结构化输出 — 强制 LLM 输出合规 JSON

        Args:
            messages: 消息列表
            output_schema: JSON Schema 描述期望输出结构
            model: 模型名

        Returns:
            解析后的 dict
        """
        system_prompt = (
            "你是一个金融合规审核助手。请严格按照以下 JSON Schema 输出：\n"
            f"{json.dumps(output_schema, ensure_ascii=False, indent=2)}\n"
            "只输出 JSON，不输出其他内容。"
        )

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        content, _ = await self.chat(
            messages=full_messages,
            model=model,
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structured output: {e}\nContent: {content}")
            # 尝试从 markdown code block 中提取
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            raise


# 全局单例
llm_service = LLMService()
